import pandas as pd

from models import validate

""" 복사-붙여넣기 용 템플릿
{
      "id": 40,
      "username": "user_040",
      "email": "user40@example.com",
      "age": 62,
      "is_active": True,
      "signup_date": "2025-04-06",
      "profile": {
        "country": "DE",
        "tier": "free",
        "score": 27.83
      },
      "tags": [
        "web"
      ]
    }

"""

def test_email():
    valid, invalid = validate([{
      "id": 40,
      "username": "user_040",
      "email": "user40@example.com",
      "age": 62,
      "is_active": True,
      "signup_date": "2025-04-06",
      "profile": {
        "country": "DE",
        "tier": "free",
        "score": 27.83
      },
      "tags": [
        "web"
      ]
    },
    {
      "id": 1,
      "username": "user_040",
      "email": "user40@*().",
      "age": 62,
      "is_active": True,
      "signup_date": "2025-04-06",
      "profile": {
        "country": "DE",
        "tier": "free",
        "score": 27.83
      },
      "tags": [
        "web"
      ]
    },
    {
      "id": 1,
      "username": "user_040", # no email
      "age": 62,
      "is_active": True,
      "signup_date": "2025-04-06",
      "profile": {
        "country": "DE",
        "tier": "free",
        "score": 27.83
      },
      "tags": [
        "web"
      ]
    }])
    assert len(valid) == 1
    assert len(invalid) == 2

def test_score():
    valid, invalid = validate([{
      "id": 40,
      "username": "user_040",
      "email": "user40@example.com",
      "age": 62,
      "is_active": True,
      "signup_date": "2025-04-06",
      "profile": {
        "country": "DE",
        "tier": "free",
        "score": 27.83
      },
      "tags": [
        "web"
      ]
    },
    {
      "id": 1,
      "username": "user_040",
      "email": "user40@example.com",
      "age": 62,
      "is_active": True,
      "signup_date": "2025-04-06",
      "profile": {
        "country": "DE",
        "tier": "free",
        "score": 10000
      },
      "tags": [
        "web"
      ]
    }])
    assert len(valid) == 1
    assert len(invalid) == 1

def test_age():
    valid, invalid = validate([{
      "id": 40,
      "username": "user_040",
      "email": "user40@example.com",
      "age": -100,
      "is_active": True,
      "signup_date": "2025-04-06",
      "profile": {
        "country": "DE",
        "tier": "free",
        "score": 27.83
      },
      "tags": [
        "web"
      ]
    },
    {
      "id": 1,
      "username": "user_040",
      "email": "user40@example.com",
      "age": 62.5,
      "is_active": True,
      "signup_date": "2025-04-06",
      "profile": {
        "country": "DE",
        "tier": "free",
        "score": 10000
      },
      "tags": [
        "web"
      ]
    }])
    assert len(valid) == 0
    assert len(invalid) == 2


def test_parquet_round(tmp_path):
    df = pd.DataFrame({'id':[1,2], 'price':[10, 20.4]})
    p = tmp_path / 'test.parquet'
    df.to_parquet(p, index=False)
    back = pd.read_parquet(p)
    pd.testing.assert_frame_equal(df, back)