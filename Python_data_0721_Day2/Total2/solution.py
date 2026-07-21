# 목표
#   eda-sklearn pipeline 구성

import polars as pl
import pandas as pd
import plotly.express as px
from scipy import stats

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from sklearn.metrics import roc_auc_score, classification_report

import joblib

DATA = "utils/telco_churn.csv"

df_polar = pl.read_csv(DATA)

print(df_polar.shape)
print(df_polar.columns)
print(df_polar.head())
print(df_polar.describe())

print(df_polar.group_by('churn').len())

print(df_polar.group_by('churn').agg([
    pl.col('monthly_charges').mean().alias('평균 요금'),
    pl.col('tenure_months').mean().alias('평균 가입 기간'),
    pl.len().alias('인원')
]))

df = df_polar.to_pandas()

fig = px.box(df, x='churn', y='monthly_charges')

#fig.show()

cy = df[df['churn'] == 1]['monthly_charges']
cn = df[df['churn'] == 0]['monthly_charges']

t, p = stats.ttest_ind(cy, cn, equal_var=False)

print(f"p 값: {p}, t: {t}")

# 카이제곱
table = pd.crosstab(df['contract'], df['churn'])
chi2, p_chi, dof, expected = stats.chi2_contingency(table)
print(f"카이제곱: {chi2}, p: {p_chi}")

num_cols = ['tenure_months', 'monthly_charges', 'total_charges', 'num_services']
cat_cols = ['gender', 'senior', 'contract', 'payment_method']

preprocessor = ColumnTransformer([
    ('num', Pipeline([
        ('fillna', SimpleImputer(strategy='mean')),
        ('scale', StandardScaler())
    ]), num_cols),
    ('cat', OneHotEncoder(handle_unknown='ignore'), cat_cols)
])

x = df[num_cols + cat_cols]
y = df['churn']

x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=42, stratify=y
)

pipe = Pipeline([
    ('prep', preprocessor),
    ('model', RandomForestClassifier(n_estimators=200, random_state=42))
])
pipe.fit(x_train, y_train)

proba = pipe.predict_proba(x_test)[:, 1]
auc = roc_auc_score(y_test, proba)
print(f"roc-auc origina = {auc}")

joblib.dump(pipe, 'churn_model.pkl') # 전처리까지

# round-test
loaded = joblib.load('churn_model.pkl')
proba = loaded.predict_proba(x_test)[:, 1]
auc = roc_auc_score(y_test, proba)
print(f"roc-auc reloaded = {auc}")