# 목표:
#   1. 전체 파일을 한 번만 훑어 집계
#       ㄱ. 지표: 경로, 상태, 시간대 별 요약, 접속 상위 ip
# 제약:
#   바닐라 파이썬-Counter, Defaultdict, functools.reduce 등 만 사용할 것
#   tracemalloc으로 메모리 비교
# 체크포인트: 5xx 에러가 대략 8%임을 확인

import csv
from collections import Counter
from functools import reduce
from datetime import datetime
from pprint import pprint
import tracemalloc

# log generator
def read_logs(file_path):
    with open(file_path, 'r', encoding='utf-8', newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row

# 각 지표 카운터
"""by_status, by_path, by_ip, by_hour = Counter(), Counter(), Counter(), Counter()
"""
# 파일 읽을 시, 실행하는 터미널이 위치한 폴더에 주신 파일들이 담긴 utils 폴더가 존재함을 가정합니다.
"""for row in read_logs("utils/web_logs.csv"):
    by_status[row['status']] += 1
    by_ip[row['ip']] += 1
    by_path[row['path']] += 1
    hour = datetime.fromisoformat(row['timestamp']).hour
    by_hour[hour] += 1"""

# 작업 시작 전 메모리 감시
tracemalloc.start()
tracemalloc.reset_peak()

# 이걸 reduce로 처리할 수 있습니다.
def fold(accumulator: dict, row):
    accumulator['total'] += 1
    accumulator['status'][row['status']] += 1
    accumulator['ip'][row['ip']] += 1
    accumulator['hour'][datetime.fromisoformat(row['timestamp']).hour] += 1
    accumulator['path'][row['path']] += 1
    return accumulator

# reduce 사용: x + y, + z, + v...
# reduce(method, iterator, init)
init = {
    'total': 0,
    'status': Counter(),
    'ip': Counter(),
    'hour': Counter(),
    'path': Counter(),
}

results = reduce(fold, read_logs('utils/web_logs.csv'), init)

pprint(results['status'])

# ratio 계산
ratio = sum(c for s, c in results['status'].items() if int(s)>=500) / results['total'] * 100

print('=' * 40)
print(f"총 요청 수 : {results['total']}")
print(f'5xx 오류율 : {ratio:.1f}%')
print('-- 인기 경로 TOP 5 --')
for path, cnt in results['path'].most_common(5):
    print(f'  {path:<20} {cnt:>7,}')
print('-- 접속 상위 IP TOP 5 --')
for ip, cnt in results['ip'].most_common(5):
    print(f'  {ip:<20} {cnt:>7,}')

# 메모리 비교

# 현재 사용량과 코드 실행 기간 중 기록된 최대 사용량 가져오기
current, peak = tracemalloc.get_traced_memory()
print('generator memory')
print(f"현재 메모리 사용량: {current / 1024 / 1024:.2f} MiB")
print(f"기간 중 최대 메모리 사용량 (Peak): {peak / 1024 / 1024:.2f} MiB")

tracemalloc.reset_peak()

# 동일한 작업을 이번에는 리스트로 전부 로딩해서 진행
# 동일한 작업이기에 출력하지 않음

def read_all_logs(file_path):
    to_rt = []
    with open(file_path, 'r', encoding='utf-8', newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            to_rt.append(row)
    return to_rt

init = {
    'total': 0,
    'status': Counter(),
    'ip': Counter(),
    'hour': Counter(),
    'path': Counter(),
}

results = reduce(fold, read_all_logs('utils/web_logs.csv'), init)

# 현재 사용량과 코드 실행 기간 중 기록된 최대 사용량 가져오기
current, peak = tracemalloc.get_traced_memory()
print('\nList Memory')
print(f"현재 메모리 사용량: {current / 1024 / 1024:.2f} MiB")
print(f"기간 중 최대 메모리 사용량 (Peak): {peak / 1024 / 1024:.2f} MiB")