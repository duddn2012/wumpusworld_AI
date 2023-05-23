
import logging
import sys
import importlib
import random

from agent import *
from environment import *

class ExplorerAgent(Agent):
    images = { d : 'explorer'+d[0]+'.gif'
        for d in ['Left','Up','Down','Right']}
    possible_actions = [ 'Forward', 'TurnRight', 'TurnLeft', 'Grab', 'Shoot',
        'Climb' ]
#possible_actions은 ExplorerAgent가 가능한 액션의 리스트
    def __init__(self):
        super().__init__()
        self._bump = False #에이전트가 벽에 부딪혔는지 여부를 나타내는 플래그
        self._facing_direction = 'Up' #현재 에이전트가 바라보고 있는 방향
        self._holding = [ Arrow() ] #에이전트가 들고 있는 아이템을 저장하는 리스트

    @property
    def image_filename(self): #image_filename은 현재 에이전트가 바라보는 방향에 따라 이미지 파일 이름을 반환하는 속성
        return self.images[self._facing_direction if
            self._facing_direction else 'Up']
#_facing_direction이 없으면 기본적으로 'Up' 방향의 이미지 파일 이름을 반환

class WumpusEnvironment(XYEnvironment):

    START_SQUARE = (1,1) # 환경의 시작 위치
    CAN_COEXIST = False #에이전트와 다른 객체가 하나의 위치를 공유할 수 있는지 여부
    __instance = None
    SideWalls=True #외벽 사용 유무, 사용시 6by6으로 변경 및 외벽 추가

    
    def __init__(self, width=4, height=4):
        if WumpusEnvironment.__instance != None:
            raise Exception("Singleton class cannot be instantiated more than once")
        else:
            WumpusEnvironment.__instance = self
        if self.SideWalls:
            width=6
            height=6
            super().__init__(width, height)
            self. addSideWalls() #6,6으로 설정하여 사방에 벽 생성
        else:
            super().__init__(width, height)
        self.add_wumpus() #웜푸스 추가
        self.add_pits() #구덩이 추가
        #self.add_walls()# 벽 추가
        self.add_gold() # 금화 추가
        self._is_done_executing = False #인스턴스 변수를 False로 초기화
        self._do_scream = False #이 변수는 웜푸스가 에이전트를 공격했는지 여부
        self.die_flag = False
        
        
    @classmethod
    def get_instance(cls):
        if cls.__instance == None:
            cls()
        return cls.__instance
        
    '''
    def reset_game(self):
        stud_module = importlib.import_module('ashtabna_ExplorerAgent')
        Explorer_class = getattr(stud_module,'ashtabna_ExplorerAgent')
        explorer = Explorer_class()
        self.add_thing(explorer, self.START_SQUARE)
        self.delete_thing(self.agents[0]) # 에이전트 삭제
        self._is_done_executing = False # 게임 종료 여부 초기화
    '''
    def percept(self, agent): # 현재 환경 정보
        '''
        The percept is a 5-tuple, each element of which is a string or None,
        depending on whether that sensor is triggered:

        Element 0: 'Stench' or None
        Element 1: 'Breeze' or None
        Element 2: 'Glitter' or None
        Element 3: 'Bump' or None
        Element 4: 'Scream' or None
        '''
        things_adj = [ t for t,_ in self.things_near(self[agent], 1) #에이전트 근처에 있는 모든 객체를 저장
                if not isinstance(t, ExplorerAgent) ] #ExplorerAgent는 이웃 객체가 아니므로, things_adj 리스트에서 제외
        stench = 'Stench' if any([isinstance(x, Wumpus) for x in things_adj])\
                else None # 주변에 Wumpus 객체가 있는 경우 'Stench' 문자열 + 그렇지 않은 경우 None을 저장
        breeze = 'Breeze' if any([isinstance(x, Pit) for x in things_adj])\
                else None #변수는 주변에 Pit 객체가 있는 경우 'Breeze' 문자열 +  그렇지 않은 경우 None을 저장
        glitter = 'Glitter' \
            if len(self.list_things_at(self[agent], Gold)) > 0 else None #변수는 에이전트 위치에서 Gold 객체가 있는 경우 'Glitter' 문자열 + 그렇지 않은 경우 None을 저장
        bump = ('Bump' if agent._bump else None) #에이전트가 벽에 부딪혔을 때 'Bump' 문자열
        scream = None
        if self._do_scream:
            scream = 'Scream' # Wumpus 객체가 쏜 화살이 맞았을 때 'Scream' 문자열
            self._do_scream = False
        return (stench, breeze, glitter, bump, scream)

    def get_risk_assessment(self): #현재 환경에서 발생할 가능성이 있는 위험 요소를 계산
        risk = 0 #구현에서는 각각의 Pit 객체가 발생시킬 위험을 100으로 설정
        for x in range(self.width):
            for y in range(self.height):
                if self.list_things_at((x, y), Pit):
                    risk += 100
        return risk #모든 Pit 객체에 대해 누적하여 반환

    def execute_action(self, agent, action): #현재 에이전트가 수행한 액션을 받아서 게임을 실행
        if action not in agent.possible_actions: 
            #agent 객체는 게임에 참여하는 에이전트 + possible_actions 속성으로 가능한 액션들을 가지고 있음
            #주어진 액션이 agent.possible_actions에 있는 액션인지 확인
            #그에 맞는 처리를 수행 + 만약 액션이 possible_actions에 없다면, 프로그램을 종료
            logging.critical("Illegal action {}! Shutting down.".format(
                                                                    action))
            sys.exit(1) 
        agent.performance -= 1
        if action == 'Climb': #에이전트가 시작 지점에서 금을 가지고 있으면, 에이전트는 이 게임에서 이김
            if self[agent]==self.START_SQUARE:
                if any([ isinstance(i,Gold) for i in agent._holding ]):
                    agent.performance += 1000
                    logging.critical('You win!!! Total score: {}'.format(
                        agent.performance)) #에이전트의 점수(agent.performance)가 이에 맞게 변경
                else: # 그렇지 않으면, 에이전트는 패배 + logging 모듈을 사용하여 게임 진행 상황을 기록
                    logging.critical('Goodbye -- total score: {}'.format(
                        agent.performance)) #에이전트의 점수(agent.performance)가 이에 맞게 변경
                self._is_done_executing = True
            else:
                logging.info("Sorry, can't climb from here!")
        elif action.startswith('Turn') or action=='Forward': # 에이전트가 바라보는 방향을 회전하거나, 앞으로 이동
            super().execute_action(agent, action) #함정이나 덫이 있는지, Wumpus 몬스터가 있는지를 검사하여 에이전트의 점수를 조정
            if self.list_things_at(self[agent], Wumpus):
                agent.performance -= 1000
                XYEnvironment.get_instance().move_to(agent, (0,0))
                self.die_flag = True
                logging.critical(
                    'You were EATEN BY THE WUMPUS!! Total score: {}'.
                    format(agent.performance))
                self._is_done_executing = True
            if self.list_things_at(self[agent], Pit):
                XYEnvironment.get_instance().move_to(agent, (0,0))
                self.die_flag = True
                agent.performance -= 1000
                logging.critical('You fell into a PIT!! Total score: {}'.
                    format(agent.performance))
                self._is_done_executing = True
        elif action=='Grab': #에이전트가 현재 위치한 곳에서 금을 주웠음
            if self.list_things_at(self[agent], Gold):
                logging.info('Grabbed gold.')
                gold = self.list_things_at(self[agent], Gold)[0]
                self.delete_thing(gold)
                agent._holding.append(gold)
            else:
                logging.debug("Afraid there's nothing here to grab.")
        elif action=='Shoot': 
# 화살은 에이전트가 가지고 있어야 사용할 수 있음 화살을 발사하면, 에이전트가 현재 바라보는 방향으로 일정 거리만큼 탐색
            arrows = [ i for i in agent._holding if isinstance(i,Arrow) ]
            if arrows:
                agent._holding.remove(arrows[0])
                num_steps = 1
                target = self.square_in_dir(agent._facing_direction,
                    self[agent], num_steps) 
                while self.is_inbounds(target):
                    wumpi = self.list_things_at(target, Wumpus)
                    if wumpi: #Wumpus 몬스터를 만나면 죽일 수 있음 + 탐색 도중 함정이나 덫을 만나면, 에이전트는 죽음
                        logging.info("Wumpus killed!")
                        self._do_scream = True
                        self.delete_thing(wumpi[0])
                        break
                    logging.debug('Nothing at {}...'.format(target))
                    num_steps += 1
                    target = self.square_in_dir(agent._facing_direction,
                        self[agent], num_steps) 
                for obs in self.observers:
                    obs.thing_moved(Arrow(), (self[agent], target))
            else:
                logging.debug('Afraid you have no arrows left.')
        else:
            logging.debug('(Doing nothing for {}.)'.format(action))
#urn, Forward, Grab, Shoot, Climb 중 하나가 아니면, 그냥 함수를 종료 + logging 모듈을 사용하여 디버깅 메시지를 출력
  
    def add_wumpus(self):
        for x in range(self.width):
            for y in range(self.height):
                if ((self.CAN_COEXIST or (x,y) not in self.values()) and
                        (x,y) != self.START_SQUARE and 
                        random.random() < 0.1):
                    self.add_thing(Wumpus(), (x,y))
                    #return
        # Wumpus가 한 번도 생성되지 않았을 경우, 무작위로 한 곳에 생성

    def add_gold(self): #Wumpus를 무작위로 한 곳에 배치
        self.add_to_one_non_starting_square(Gold())

    def add_to_one_non_starting_square(self, thing):
        possible_squares = [(x,y) for x in range(self.width)
            for y in range(self.height)
                    if (self.CAN_COEXIST or (x,y) not in self.values()) and
                    (x,y) != self.START_SQUARE ]
        self.add_thing(thing,random.choice(possible_squares))
#주어진 Thing을 가능한 모든 위치에서 선택한 다음, 이전 Thing이 있는 위치가 아니며 시작 위치가 아닌 위치 중에서 무작위로 선택한 위치에 Thing을 추가

    def add_pits(self, pit_prob=.1): # 각 위치에 대해 pit_prob의 확률로 Pit을 배치
        for x in range(self.width):
            for y in range(self.height):
                if ((self.CAN_COEXIST or (x,y) not in self.values()) and
                        (x,y) != self.START_SQUARE and 
                        random.random() < pit_prob):
                    self.add_thing(Pit(), (x,y))

    def add_walls(self, wall_prob=.1): #각 위치에 대해 wall_prob의 확률로 Wall을 배치
        for x in range(self.width):
            for y in range(self.height):
                if ((self.CAN_COEXIST or (x,y) not in self.values()) and
                        (x,y) != self.START_SQUARE and 
                        random.random() < wall_prob):
                    self.add_thing(Wall(), (x,y))

    def addSideWalls(self): #모든 방면에 벽 위치
            for i in range(self.height):
                self.add_thing(Wall(), (self.width-1,i))
                self.add_thing(Wall(), (0,i))
            for i in range(self.width):
                self.add_thing(Wall(), (i,0))
                self.add_thing(Wall(), (i,self.height-1))

    def should_shutdown(self): #is_done_executing이 True이면 True를 반환
        return self._is_done_executing

#나머지 이미지파일 지정 
class Wumpus(Thing):
    image_filename = 'wumpus.gif'

class Pit(Thing):
    image_filename = 'pit.gif'

class Wall(Obstacle):
    image_filename = 'wumpus_wall.gif'

class Gold(Thing):
    image_filename = 'gold.gif'

class Arrow(Thing):
    image_filename = 'arrow.gif'
