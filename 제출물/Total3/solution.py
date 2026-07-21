# 목표
# 자동화: 수동, scheduler, cron; jinja
# 모듈화

import report

import time

# scheduler

import argparse


def simple(timer):
    if timer == 0:
        print('starting')
        report.run_once()
        print('done')
        return
    
    while True:
        report.run_once()
        time.sleep(timer)

# schedule:
import schedule

def scheduler(timer):
    # 기존 동작처럼 첫 작업은 즉시 실행하고, 이후 작업을 예약합니다.
    report.run_once()
    schedule.every(timer).seconds.do(report.run_once)
    while True:
        schedule.run_pending()
        time.sleep(1)

# crontab

# 이건 맥이라 코드에서 직접 실행하지는 않고, 터미널에서 진행합니다.

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--interval', type=int, default=0,
                    help='초 단위 반복, 0이면 1회만 실행')
    args = ap.parse_args()

    if args.interval < 0:
        ap.error('--interval은 0 이상의 정수여야 합니다')
    
    #simple(args.interval)
    scheduler(args.interval)

if __name__ == "__main__":
    main()