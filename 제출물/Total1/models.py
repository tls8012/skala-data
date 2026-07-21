import re
from pydantic import BaseModel, ValidationError, Field, field_validator


# email regex 미리 전역으로 컴파일

email_regex = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

# pydantic schema 생성

class profile_validator(BaseModel):
    country: str
    tier: str
    score: float= Field(le=100)

class api_validator(BaseModel):
    id: int
    username: str
    email: str
    age: int= Field(gt=0)
    is_active: bool
    signup_date: str
    profile: profile_validator
    tags: list[str]

    @field_validator('email')
    @classmethod # 빠지면 안됨!
    def email_check(cls, email:str) -> str:
        if not email_regex.search(email):
            raise ValueError("Wrong Email!")
        return email
    
# 유효 무효로 나누기

def validate(raw_data):
    valid, invalid = [], []
    for row_num, row in enumerate(raw_data):
        try:
            valid.append(api_validator(**row))
        except ValidationError as e:
            invalid.append({
                'index': row_num,
                'data': row,
                'error': e.errors()
            })
        finally:
            print("정리 끝")
    return valid, invalid