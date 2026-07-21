# load file 'adult_data.csv' into pandas and polar
# timeit time compare
# fill na, null, etc.: has odd values so carefully
# discard duplicates

from timeit import timeit

import pandas as pd
import polars as pl
import polars.selectors as cs
from tabulate import tabulate

# 이하 모든 코드는 타임잇 실행을 위해 인자 없는 wrapper 함수로 전체 정리해서 진행

DATA = "adult_data.csv"

# goal 1, 2
def pandas_(use_print = False):
    df = pd.read_csv(DATA).drop_duplicates(keep='first')
    
    if use_print:
        print(df.info()) #: timeit을 사용할 것이기에 과도한 프린트 문 지양
        print("isna:")
        print(df.isna().sum())
        print("results")
        print(tabulate(df, headers='keys', tablefmt='grid'))

    return df

# goal 3
def polars_(use_print=False):

    # use lazy
    results = (
        pl.scan_csv(DATA, schema_overrides={'amount': pl.Float64})
        .drop_nulls()
        .with_columns(cs.float().fill_nan(None))
        .with_columns(
            cs.numeric().fill_null(cs.numeric().median()),
            cs.string().fill_null(cs.string().mode().first()),
        ).unique(keep='first', maintain_order=True)
        .collect()
    )
    
    if use_print:
        print(results)
    
    return results

# if file is not there: print file not there, and quit.
try:
    df_pandas = pandas_(use_print=False)
    df_polars = polars_(use_print=False)

    # timeit
    NUMBER = 10
    pandas_time = timeit(pandas_, number=NUMBER)
    polars_time = timeit(polars_, number=NUMBER)

    print(f"pandas: {pandas_time}, \npolars: {polars_time}")
except FileNotFoundError as fe:
    print(f"{DATA} is not there!!")
except KeyError as e:
    print(e)

# finished loading

print(df_pandas.isna().sum())
