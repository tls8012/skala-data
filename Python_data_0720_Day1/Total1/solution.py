# api_response.json에 있는 파일들을 활용한다고 가정합니다.
# 이를 mock http request 로 보내 핸들러에서 처리하도록 합니다.

import json
import copy
import asyncio
from pathlib import Path
from random import random
from functools import partial

import httpx
import pandas as pd

from models import validate

# 40개의 api result는 전역 변수에 저장해 둡니다.

with open('utils/api_response.json', 'r') as file:
    RAW = json.load(file)
RAW = RAW['results']


# httpx mock handler

async def mock_handler(request: httpx.Request):
    item_id = int(request.url.params.get('item_id', 0))
    to_rt = copy.deepcopy(RAW[item_id])
    to_rt['ok'] = True
    await asyncio.sleep(random()*2.5)
    return httpx.Response(
        status_code=200,
        json=to_rt
    )

# use_real=False 역할을 수행할 mock transport 생성
mock_transport = httpx.MockTransport(mock_handler)

# mock fetch

MAX_RETRIES = 3
TIMEOUT_TIME = 1.0
MAX_CONCURRENT = 10

async def fetch_timeout(item_id, semaphore, multiplier=1):
    async with semaphore:
        try:
            # multiplier=1 일 때 제한시간은 1.0초
            async with asyncio.timeout(TIMEOUT_TIME * multiplier):
                async with httpx.AsyncClient(transport=mock_transport) as client:
                    response = await client.get(f"https://api.example.com/items", params={"item_id": item_id})
                    return response.json()
        except TimeoutError:
            raise TimeoutError

async def fetch_backoff(item_id, semaphore):
    for attempt in range(MAX_RETRIES):
        try:
            # attempt 수만큼 대기하는 동안 서버 상태가 좋아짐을 timeout을 늘리는 것으로 시뮬레이션
            return await fetch_timeout(item_id, semaphore, attempt)
        except TimeoutError:
            if attempt == MAX_RETRIES - 1:
                raise TimeoutError
            else:
                await asyncio.sleep(1 * (attempt + 1))

# 🌟 3. 메인 실행 함수 (기존 로직 유지)

async def simulate(fun: callable, use_semaphore=False):
    name = f"{fun.__name__}"
    print(f"--- {name} 시작 ---")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT) if use_semaphore else None
    if use_semaphore: 
        fun = partial(fun, semaphore=semaphore)
        
    tasks = [fun(i) for i in range(40)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    ok = [r for r in results if not isinstance(r, Exception)]
    fail = [r for r in results if isinstance(r, Exception)]
    
    if fail:
        serializable_fail = []
        for e in fail:
            if isinstance(e, Exception):
                serializable_fail.append({
                    "error_type": e.__class__.__name__,
                    "message": str(e)
                })
            else:
                serializable_fail.append(e)
                
        with open(f"{name}.json", 'w', encoding='utf-8') as file:
            json.dump(serializable_fail, file, ensure_ascii=False, indent=4)
            
    print(f'결과 -> 성공: {len(ok)}건 / 실패: {len(fail)}건')
    if fail: 
        print(f"실패 예시: {repr(fail[0])}")
    
    return ok

# loading into df
def loading(data, out_dir = "output") -> pd.DataFrame:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    # data has api_validator. must turn back into dict
    data = [d.model_dump() for d in data]
    # data has dict inside dict, so must flatten
    # json_normalize already has that feature.
    df = pd.json_normalize(data)
    df.to_csv(f"{out_dir}/out.csv", index=False)
    df.to_parquet(f"{out_dir}/out.parquet", index=False)
    return df

# main run

async def main():
    data = await simulate(fetch_backoff, use_semaphore=True)
    valid, invalid = validate(data)
    df = loading(valid)
    return {
        'total_got': len(data),
        'valid': len(valid),
        'invalid': len(invalid),
        'rows_saved': len(df)
    }

summary = asyncio.run(main())
print(summary)
