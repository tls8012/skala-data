# 목표:
#   1. 비동기 처리
#   2. http는 처리하지 않음

# 상황:
#   한 작업에 1~2초 소요되는 작업을 60개 처리해야 함. 이 중 cpu부담이 적은 작업이기에 비동기로 처리.
#   이 네트워크 대기 작업은 time.sleep으로 시뮬레이트

# mock httpx request 로 진행
import time
import asyncio
from functools import partial
import logging
import json
from random import random
import httpx  # 🌟 httpx 추가

# 전역 로거 생성, 세팅
logging.basicConfig(
    filename='app.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('pipeline')

MAX_CONCURRENT = 10
TIMEOUT_TIME = 1.0
MAX_RETRIES = 3

# 🌟 1. httpx 가짜 응답을 만들어줄 Mock 핸들러 정의
def mock_handler(request: httpx.Request):
    item_id = request.url.params.get("item_id", "unknown")
    return httpx.Response(
        status_code=200, 
        json={'id': int(item_id) if item_id.isdigit() else item_id, 'ok': True}
    )

# use_real=False 역할을 수행할 mock transport 생성
mock_transport = httpx.MockTransport(mock_handler)


# 🌟 2. 비동기 httpx 요청 함수들 (실제 요청 안 날아가고 mock으로 작동)

async def fetch_async(item_id):
    async with httpx.AsyncClient(transport=mock_transport) as client:
        await asyncio.sleep(0.1)
        response = await client.get(f"https://api.example.com/items", params={"item_id": item_id})
        return response.json()

async def fetch_async_limited(item_id, semaphore):
    async with semaphore:
        async with httpx.AsyncClient(transport=mock_transport) as client:
            await asyncio.sleep(0.1)
            response = await client.get(f"https://api.example.com/items", params={"item_id": item_id})
            return response.json()

async def fetch_timeout(item_id, semaphore, multiplier=1):
    async with semaphore:
        try:
            # multiplier=1 일 때 제한시간은 1.0초
            async with asyncio.timeout(TIMEOUT_TIME * multiplier):
                # 0~2초 사이의 슬립 유도로 1.0초를 넘기면 타임아웃 발생시킴
                sleep_time = random() * (multiplier + 1)
                await asyncio.sleep(sleep_time)
                
                async with httpx.AsyncClient(transport=mock_transport) as client:
                    response = await client.get(f"https://api.example.com/items", params={"item_id": item_id})
                    return response.json()
        except TimeoutError:
            raise TimeoutError

async def fetch_backoff(item_id, semaphore):
    for attempt in range(MAX_RETRIES):
        try:
            # attempt=0일 때 multiplier=1이 되도록 attempt+1 처리
            return await fetch_timeout(item_id, semaphore, attempt + 1)
        except TimeoutError:
            if attempt == MAX_RETRIES - 1:
                raise TimeoutError
            else:
                logger.error(f"{item_id} 재시도 중... {attempt + 1}회 실패")
                await asyncio.sleep(0.1 * (attempt + 1))


# 🌟 3. 메인 실행 함수 (기존 로직 유지)

async def main(fun: callable, use_semaphore=False):
    name = f"{fun.__name__}"
    print(f"--- {name} 시작 ---")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT) if use_semaphore else None
    if use_semaphore: 
        fun = partial(fun, semaphore=semaphore)
        
    tasks = [fun(i) for i in range(60)]
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


# 🌟 4. 실행부

if __name__ == "__main__":
    # 동기식 코드는 httpx 적용 대상이 아니므로 제외하고 비동기 루프만 실행합니다.
    
    start = time.perf_counter()
    asyncio.run(main(fetch_async))
    print(f"비동기 기본: {time.perf_counter() - start: .2f}초\n")

    start = time.perf_counter()
    asyncio.run(main(fetch_async_limited, use_semaphore=True))
    print(f"비동기 세마포어: {time.perf_counter() - start: .2f}초\n")

    start = time.perf_counter()
    asyncio.run(main(fetch_timeout, use_semaphore=True))
    print(f"비동기 타임아웃: {time.perf_counter() - start: .2f}초\n")

    start = time.perf_counter()
    asyncio.run(main(fetch_backoff, use_semaphore=True))
    print(f"비동기 백오프 재시도: {time.perf_counter() - start: .2f}초\n")