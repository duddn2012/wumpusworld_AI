import subprocess
import os
import sys
import logging
import pandas as pd

#로깅 레벨을 설정
logging.getLogger().setLevel(logging.CRITICAL + 1)

NUM_CORES = 8

if len(sys.argv) != 3:
    print('Usage: score_wumpus.py UMWNetID num_runs.')
    sys.exit(1)
umw_net_id = sys.argv[1] #스크립트에 전달된 인자 중 첫 번째 인자를 UMWNetID 변수에 저장
num_runs = int(sys.argv[2]) #스크립트에 전달된 인자 중 두 번째 인자를 num_runs 변수에 저장
runs_per_core = num_runs // NUM_CORES # runs_per_core 변수에 num_runs를 NUM_CORES로 나눈 값을 저장


procs = []
seeds = range(1001,1001+num_runs,runs_per_core) #프로세스 리스트와 시드 리스트, 출력 파일 리스트를 초기화
#시드는 1001부터 시작하여 runs_per_core 만큼씩 증가하는 값들로 구성
output_files = [ '/tmp/output'+str(seed)+'.csv' for seed in seeds ]
#출력 파일 리스트는 각 시드에 대한 출력 파일 경로를 저장
for seed, output_file in zip(seeds, output_files):
#시드와 출력 파일을 이용하여 ExplorerAgent를 num_runs 번 실행하는 프로세스를 생성하고, 
#해당 프로세스를 프로세스 리스트에 추가
    with open(output_file, 'w') as f:
        procs.append(subprocess.Popen(
            ['./main_wumpus.py',umw_net_id,'suite='+str(runs_per_core),
                                                        str(seed), 'NONE'],
            stdout=f))
#모든 프로세스의 실행이 완료될 때까지 대기
print('Waiting for completion...')
[ p.wait() for p in procs ]
print('...done.')
#모든 출력 파일을 하나의 파일로 병합
cmd_line = 'cat ' + ' '.join(output_files) 
with open('/tmp/output.csv','w') as f:
    subprocess.Popen(['cat'] + output_files, stdout=f)
os.system('grep -v "^#" /tmp/output.csv > /tmp/output2.csv')
os.system('grep -v "seed" /tmp/output2.csv > /tmp/output3.csv')
os.system('head -1 /tmp/output.csv > /tmp/outputheader.csv')
os.system('cat /tmp/outputheader.csv /tmp/output3.csv > /tmp/output4.csv')
all_of_them = pd.read_csv("/tmp/output4.csv")
with open('/tmp/{}.csv'.format(umw_net_id),'w') as final:
    score_line = '# Score: min {}, max {}, mean {} med {}'.format(
        all_of_them.score.min(), all_of_them.score.max(),
        round(all_of_them.score.mean(),2),
        int(all_of_them.score.median()))
    num_steps_line = '# Num_steps: min {}, max {}, med {}'.format(
        all_of_them.num_steps.min(), all_of_them.num_steps.max(),
        round(all_of_them.num_steps.mean(),2),
        int(all_of_them.num_steps.median()))
    print(score_line)
    print(score_line, file=final)
    print(num_steps_line)
    print(num_steps_line, file=final)
    all_of_them.to_csv(path_or_buf=final,index=False)
os.system('rm /tmp/output*.csv')
print('Output in /tmp/{}.csv.'.format(umw_net_id))

num_lines = int(subprocess.run(['wc', '-l', umw_net_id + '_ExplorerAgent.py'],
    stdout=subprocess.PIPE).stdout.decode('utf-8').split(' ')[0])

os.system('touch wumpus_results.txt')
with open('./wumpus_results.txt','a') as f:
    print('{},{},{},{},{},{},{},{},{}'.format(umw_net_id,
        all_of_them.score.min(), all_of_them.score.max(),
        round(all_of_them.score.mean(),2),
        int(all_of_them.score.median()),
        all_of_them.num_steps.min(), all_of_them.num_steps.max(),
        int(all_of_them.num_steps.median()),
        num_lines), file=f)

#로깅 레벨을 설정
#스크립트에 전달된 인자의 개수를 확인하고, 올바른 개수가 아니면 메시지를 출력하고 스크립트를 종료
#스크립트에 전달된 인자 중 첫 번째 인자를 UMWNetID 변수에 저장
#스크립트에 전달된 인자 중 두 번째 인자를 num_runs 변수에 저장하고, runs_per_core 변수에 num_runs를 NUM_CORES로 나눈 값을 저장
#프로세스 리스트와 시드 리스트, 출력 파일 리스트를 초기화합니다. 시드는 1001부터 시작하여 runs_per_core 만큼씩 증가하는 값들로 구성됩니다. 출력 파일 리스트는 각 시드에 대한 출력 파일 경로를 저장
#시드와 출력 파일을 이용하여 ExplorerAgent를 num_runs 번 실행하는 프로세스를 생성하고, 해당 프로세스를 프로세스 리스트에 추가
#모든 프로세스의 실행이 완료될 때까지 대기
#모든 출력 파일을 하나의 파일로 병합
#결과 파일의 헤더 부분을 제외한 모든 라인을 추출하여 처리
#결과 파일의 헤더 부분과 추출한 결과를 이용하여 최종 결과 파일을 생성
#임시 파일들을 삭제
#결과를 wumpus_results.txt 파일에 추가

#logging: 로깅 관련 모듈
#sys: 시스템 관련 모듈
#subprocess: 서브프로세스 생성 및 제어를 위한 모듈
#os: 운영체제 관련 모듈
#pd: pandas 모듈, 데이터프레임을 다루기 위해 사용됩니다.
#range: 정수 범위를 생성하는 내장 함수
#zip: 여러 개의 이터레이터에서 값을 하나씩 꺼내어 튜플 형태로 반환합니다.
#open: 파일을 열기 위한 내장 함수
#wait: 서브프로세스가 종료될 때까지 기다립니다.
#Popen: 서브프로세스를 생성합니다.
#cat: 파일 내용을 출력하는 명령어
#to_csv: pandas 데이터프레임을 csv 파일로 저장하는 메서드
#wc: 파일의 라인 수 등을 세는 명령어
#decode: 바이트 문자열을 문자열로 디코