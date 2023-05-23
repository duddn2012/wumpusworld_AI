

import logging
import importlib
import sys
import statistics

from environment import *
from agent import *
from wumpus import *
from visualize import *


def print_usage(): #함수는 스크립트 사용 방법을 출력
    print('Usage: main_wumpus.py explorer_name [interactive|auto|suite=3] ' +
        '[seed] [debugLevel|NONE].')

if len(sys.argv) not in [2,3,4,5]:
    print_usage()
    sys.exit(1)
#sys.argv는 명령줄에서 스크립트를 실행할 때 전달되는 인수들의 리스트입니다.
#인수의 개수가 2, 3, 4, 5가 아닌 경우에는 print_usage() 함수를 호출하고 프로그램을 종료

if len(sys.argv) > 2:
    interactive = sys.argv[2] == 'interactive'
    do_suite = sys.argv[2].startswith('suite=3')
    if do_suite:
        try:
            num_runs = int(sys.argv[2][sys.argv[2].index('=')+1:])
        except:
            print_usage()
            print("('suite=#' parameter must be numeric.)")
            sys.exit(2)
else:
    interactive = True #interactive 변수는 sys.argv[2]가 "interactive"인 경우 True로 설정
    do_suite = False

if len(sys.argv) > 3:
    try:
        seed = int(sys.argv[3])
        if seed == 0:
            seed = random.randrange(10000)
    except:
        print_usage()
        print("('seed' must be numeric.)")
        sys.exit(3)
else:
    seed = random.randrange(10000)

if len(sys.argv) > 4:
    if sys.argv[4] == 'NONE':#sys.argv[4]가 'NONE'인 경우, logging.getLogger().setLevel(logging.CRITICAL + 1)을 호출
        logging.getLogger().setLevel(logging.CRITICAL + 1) #호출하여 로그를 끈다.
    else:
        logging.getLogger().setLevel(sys.argv[4])#sys.argv[4]에 지정된 로깅 레벨로 설정
else:
    logging.getLogger().setLevel('CRITICAL')#sys.argv[4]가 없는 경우에는 로그 레벨을 'CRITICAL'로 설정

try:#try-except 문에서는 필자가 작성한 모듈을 import. sys.argv[1]에는 모듈의 이름이 저장되어 있음
    stud_module = importlib.import_module(sys.argv[1] + '_ExplorerAgent')
    Explorer_class = getattr(stud_module,sys.argv[1] + '_ExplorerAgent')
    # getattr 함수를 사용하여 모듈에서 Explorer_class 클래스를 가져옴
except Exception as err:
    print(str(err))
    sys.exit(2)
#Explorer_class가 ExplorerAgent 클래스를 상속받지 않은 경우, 클래스 이름을 출력하고 프로그램을 종료
#그렇지 않은 경우, Explorer_class를 인스턴스화하고, WumpusEnvironment와 함께 VisualXYEnvironment를 생성하여 실행
if not issubclass(Explorer_class, ExplorerAgent):
    print("{} doesn't inherit from ExplorerAgent.".format(
        Explorer_class.__name__))
    sys.exit(3)

# ExplorerAgent 클래스를 상속한 학생의 에이전트가 잘 동작하는지를 평가하기 위한 코드
if do_suite:
    from suite_wumpus import *
    results = Suite(range(seed,seed+num_runs)).run(Explorer_class)
    #인수로 지정한 실행 횟수(num_runs)와 난수 생성을 위한 시드(seed)를 설정하고, 로깅 레벨(logging level)을 지정
    scores, steps = ([ score for score,_ in results ],
                    [ steps for _,steps in results ])
    print('seed,score,num_steps')
    for i,(score, num_steps) in enumerate(results):
        print('{},{},{}'.format(seed+i,score,num_steps))
    print('# Score: min {}, max {}, mean {}'.format(min(scores),max(scores),
        int(statistics.mean(scores))))
    #do_suite 변수가 True인 경우, 
    #test_wumpus.py 파일과 같은 디렉토리에 있는 suite_wumpus.py 모듈을 불러와서 Suite 클래스를 이용해 여러 번의 실행 결과를 수집
    win = 0
    death = 0
    for i in scores:
        if i > 0:
            win += 1
        elif i <= -1000:
            death += 1
    print('# Num steps: min {}, max {}, med {}'.format(min(steps),max(steps),
        int(statistics.median(steps))))
    print('Percent death: {}, Percent won: {}'.format(death/num_runs, win/num_runs))
else:  #do_suite가 False인 경우, 학생의 ExplorerAgent 클래스의 인스턴스를 생성하고, 
       #seed를 이용해 난수 생성기를 초기화한 후, WumpusEnvironment와 함께 추가
    explorer = Explorer_class()
    print('Using seed {}.'.format(seed))
    random.seed(seed)
    we = WumpusEnvironment()
    we.add_thing(explorer, we.START_SQUARE)
    ve = VisualXYEnvironment(we, 100, 100, 'Wumpus world')
    ve.start(interactive)
