# 목표:
#   1. pydantic 으로 입력 데이터 검증
# 제약:
#   try-catch-finally 사용, logging 사용
# 유효 무효 레코드 건 수와, 실패 사유 표로 출력

import json
import re
import logging

from pydantic import BaseModel, ValidationError, Field, field_validator

# 주어진 json 파일은 깨지지 않았다고 가정

with open('utils/api_response.json', 'r') as file:
    raw_data = json.load(file)
raw_data = raw_data['results']

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
    
# 전역 로거 생성, 세팅
logging.basicConfig(
    filename='app.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s' # [시간 - 등급 - 메시지] 형태로 기록
)
logger = logging.getLogger('pipeline')

# 유효 무효로 나누기

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
        logger.error(e)
    finally:
        logger.info("정리 끝")

print(f'전체 {len(raw_data)}건 → 유효 {len(valid)} / 오염 {len(invalid)}')

print(f"{'행':<4}{'필드':<12}{'사유'}")
for item in invalid:
    for err in item['error']:
        field = '.'.join(str(x) for x in err['loc'])
        print(f"{item['index']} {field} {err['msg']}")