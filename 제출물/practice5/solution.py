# 목표:
#   1. pandas로 기본 eda: info, isnull.sum
#       a. IQR로 이상치 처리
#   2. region, category 별 총매출, 평균, 건수를 named agg로 계산, 총매출 내림차순 정렬
#       a. named agg: agg(total=('amount', 'sum'))
#   3. polars의 lazy 작업
#       a. scan_csv->filter->group_by->agg->sort->collect
#   4. duckdb로 동일 집계를 sql로 작성
#   5. timeit으로 세 장치 실행 시간 비교, 최소 3회 이상

from timeit import timeit

import pandas as pd
import polars as pl
import polars.selectors as cs
import duckdb
from tabulate import tabulate

# 이하 모든 코드는 타임잇 실행을 위해 인자 없는 wrapper 함수로 전체 정리해서 진행

DATA = "events_large.csv"

# goal 1, 2
def pandas_(use_print = False):
    df = pd.read_csv(DATA)
    
    # na 값은 최빈값으로 입력, 여러 최빈값 대비 가장 위 1개
    # 날짜 빈 칸은 에러로 간주
    df = df.dropna()

    results = (
        df.groupby('event_type')
        .agg(
            cnt = ('amount', 'count'), avg=('amount', 'mean')
        )
        .sort_values('cnt',ascending=False)
        .reset_index()
    )

    if use_print: print(tabulate(results, headers='keys', tablefmt='grid'))

    return results

# goal 3
def polars_(use_print=False):

    # use lazy
    results = (
        pl.scan_csv(DATA, schema_overrides={'amount': pl.Float64})
        .drop_nulls()
        .group_by("event_type")
        .agg(
            [
             pl.len().alias('cnt'),
             pl.col('amount').mean().alias('avg')]
        )
        .sort('cnt', descending=True)
        .collect()
    )
    
    if use_print:
        print(results)
    
    return results.to_pandas()

# goal 4
def duck_(use_print=False):
    # sql은 잘 모르기 때문에 적절한 도움을 받았습니다.
    results = duckdb.sql(f"""
        select event_type,
            count(amount) as cnt,
            avg(amount) as avg
        from {DATA}
        group by event_type
        order by cnt desc
    """).df()
    if use_print:
        print(tabulate(results, headers='keys', tablefmt='grid'))
    return results

# if file is not there: print file not there, and quit.
try:
    panda = pandas_(use_print=True)
    polar = polars_(use_print=True)
    duck = duck_(use_print=True)

    pd.testing.assert_frame_equal(panda, polar, check_dtype=False, atol=1e-6)
    pd.testing.assert_frame_equal(panda, duck, check_dtype=False, atol=1e-6)

    # timeit
    NUMBER = 10
    pandas_time = timeit(pandas_, number=NUMBER)
    polars_time = timeit(polars_, number=NUMBER)
    duck_time =   timeit(duck_, number=NUMBER)

    print(f"pandas: {pandas_time}, \npolars: {polars_time}, \nduck: {duck_time}")
except FileNotFoundError as fe:
    print(f"{DATA} is not there!!")
except KeyError as e:
    print(e)

