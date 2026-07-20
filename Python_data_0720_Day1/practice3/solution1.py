# 목표:
#   1. 비동기 처리
#   2. http는 처리하지 않음

# 상황:
#   한 작업에 1~2초 소요되는 작업을 60개 처리해야 함. 이 중 cpu부담이 적은 작업이기에 비동기로 처리.
#   이 네트워크 대기 작업은 time.sleep으로 시뮬레이트

import time
import asyncio
from functools import partial
import logging
import json

# 전역 로거 생성, 세팅
logging.basicConfig(
    filename='app.log', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s' # [시간 - 등급 - 메시지] 형태로 기록
)
logger = logging.getLogger('pipeline')

# 동기 시뮬레이션:

def fetch_sync(item_id):
    time.sleep(0.1)
    return {'id':item_id, 'ok':True}

start = time.perf_counter()
results = [fetch_sync(i) for i in range(60)]
print(f"동기: {time.perf_counter() - start: .2f}초\n") # 1초 대신 0.1초로 대체, ~6sec

# 비동기 시뮬레이션

async def fetch_async(item_id):
    await asyncio.sleep(0.1)
    return {'id':item_id,'ok':True}

async def main(fun:callable, use_semaphore=False):
    name = f"{fun.__name__}"
    print(f"{name} 시작")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT) if use_semaphore else None
    if use_semaphore: fun = partial(fun, semaphore=semaphore)
    tasks = [fun(i) for i in range(60)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    ok   = [r for r in results if not isinstance(r, Exception)]
    fail = [r for r in results if isinstance(r, Exception)]
    # fail 저장 코드:
    if fail:
        serializable_fail = []
        for e in fail:
            if isinstance(e, Exception):
                serializable_fail.append({
                    "error_type": e.__class__.__name__, # 🌟 방금 배운 그 __name__ 입니다! (예: 'TimeoutError')
                    "message": str(e)
                })
            else:
                # 혹시 예외 객체가 아니라 일반 딕셔너리 실패 데이터가 섞여 있다면 그대로 유지
                serializable_fail.append(e)
                
        with open(f"{name}.json", 'w', encoding='utf-8') as file:
            json.dump(serializable_fail, file, ensure_ascii=False, indent=4)
    print(f'성공 {len(ok)}건 / 실패 {len(fail)}건')
    if fail: print(fail[0])

start = time.perf_counter()
asyncio.run(main(fetch_async))
print(f"비동기: {time.perf_counter() - start: .2f}초") # 1초 대신 0.1초로 대체, ~0.2sec

# 동시성 크기 제어: semaphores
# 일정 개수 이상은 제한

MAX_CONCURRENT = 10 # 적당히 작은 수

async def fetch_async_limited(item_id, semaphore):
    async with semaphore:
        await asyncio.sleep(0.1)
        return {'id':item_id, 'ok':True}

start = time.perf_counter()
asyncio.run(main(fetch_async_limited, use_semaphore=True))
print(f"비동기 세마포어: {time.perf_counter() - start: .2f}초\n") # 1초 대신 0.1초로 대체, ~2sec

# timeout & backoff
# 를 시뮬레이트하기 위해 랜덤 부여
from random import random

TIMEOUT_TIME = 1.0
MAX_RETRIES = 3

async def fetch_timeout(item_id, semaphore, multiplier = 1):
    async with semaphore:
        try:
            async with asyncio.timeout(TIMEOUT_TIME * multiplier):
                sleep_time = random()*(multiplier+1)
                await asyncio.sleep(sleep_time)
                return {'id':item_id, 'ok':True}
        except TimeoutError:
            #return {'id':item_id, 'ok':False, 'reason': 'timeout'}
            raise TimeoutError
        
start = time.perf_counter()
asyncio.run(main(fetch_timeout, use_semaphore=True))
print(f"비동기 타임아웃: {time.perf_counter() - start: .2f}초\n") # 확률적으로 반은 실패

# backoff: 서버 오류를 timeout으로, 좋아지는 서버 상태는 timeout의 배율로 시뮬레이트

async def fetch_backoff(item_id, semaphore):
    for attempt in range(MAX_RETRIES):
        try:
            return await fetch_timeout(item_id, semaphore, attempt)
        except TimeoutError:
            if attempt - MAX_RETRIES == -1:
                raise TimeoutError
            else:
                logger.error(f"{item_id} 재시도 중... {attempt} 초 대기")
                await asyncio.sleep(0.1*attempt)

start = time.perf_counter()
asyncio.run(main(fetch_backoff, use_semaphore=True))
print(f"비동기 재시도: {time.perf_counter() - start: .2f}초\n") # 확률이 나아짐