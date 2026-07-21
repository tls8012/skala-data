# 목표:
#   1. 야생 데이터 전처리
#       ㄱ. 중앙값 채우기, 타입 정규화, iqr
#   2. 간단한 데이터 분석
#       ㄱ. 그룹별 요약, 피벗 테이블, 머지
# 체크포인트: 윈저라이징: iqr

import pandas as pd
import polars as pl
import polars.selectors as cs

DATA = "utils/sales_raw.csv"
df = pd.read_csv(DATA)
# 데이터의 상태 확인
print(df.shape)
print(df.info())
print(df.describe())
print(df.isna().sum())
print(df.head())

# typing
# coerce = 에러 발생 시 NaN값으로 강제 입력
df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
df['discount'] = pd.to_numeric(df['discount'], errors='coerce')

df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')

df['category'] = df['category'].astype('category')
df['region'] = df['region'].astype('category')

print(df.dtypes)

# 결측치 채우기
df_filled = (pl.scan_csv(DATA, schema_overrides={'amount': pl.Float64})
      .drop_nulls(subset=['order_date', 'order_id']) # 날짜가 비어 있으면 오류로 판단
        .fill_nan(None) # NaN값을 null로 변경
        .with_columns(
            cs.numeric().fill_null(cs.numeric().median()), # 숫자는 중간값으로
            cs.string().fill_null(cs.string().mode().first()), # 문자는 최빈값으로
        )
        .collect()).to_pandas()

print(df_filled.isna().sum())

# 아마 분석할 열이 필요할 거 같아서, 분석할 '행 당 매출'을 만듦니다.
df_filled['sale'] = df['quantity'] * df['unit_price']

# iqr 1.5
# 위에서 만든 행 당 매출을 기준으로 합니다.
def iqr_(df, k=1.5):
    q1, q3 = df['sale'].quantile(0.25), df['sale'].quantile(0.75)
    iqr = q3-q1
    return df['sale'].clip(lower=q1-k*iqr, upper=q3+k*iqr)

print("처리 전 minmax", df_filled['sale'].min(), df_filled['sale'].max())
df_filled['sale'] = iqr_(df_filled)
print("처리 후 minmax", df_filled['sale'].min(), df_filled['sale'].max())

# groupby
# category별 분석
summary_cat = df_filled.groupby('category').agg(
    건수=('sale', 'count'),
    평균가=('sale', 'mean'),
    중앙값=('sale', 'median'),
    총매출=('sale', 'sum'),
).round(3)
# region 별
summary_reg = df_filled.groupby('region').agg(
    건수=('sale', 'count'),
    평균가=('sale', 'mean'),
    중앙값=('sale', 'median'),
    총매출=('sale', 'sum'),
).round(3)
print(summary_cat)
print(summary_reg)

# pivot table
pivot = df_filled[['sale', 'category', 'region']].pivot_table(
    index='category',
    columns='region',
    aggfunc='sum',
    fill_value=0
).round(3)
print(pivot)

# merge: merge할 데이터가 없어서, 임의로 다른 두 개의 데이터를 머지합니다.
# 머지는 인덱스 기준으로 발생합니다.
merged = df_filled.merge(pd.read_csv('utils/telco_churn.csv'), left_index=True, right_index=True, how='left')
print(len(df_filled))
print(len(merged))

# copy on write
pd.options.mode.copy_on_write = True

# df[df['sale'] > 100000]['flag'] = 1

df_filled.loc[df_filled['sale'] > 100000, 'flag'] = 1