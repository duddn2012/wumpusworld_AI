
import logging
import sys
from environment import Environment

from wumpus import ExplorerAgent, WumpusEnvironment
import numpy as np
import queue
from itertools import combinations

UP = 0
DOWN = 90
LEFT = 135
RIGHT = 45
PIT_PRIOR = 0.1 # the probability of a location having a pit
directions = [UP, DOWN, LEFT, RIGHT]

def is_valid(x, y):  # x,y 좌표 값이 유효한 좌표인지 확인하는 함수다.
    if x < 0 or y < 0:
        return False
    if x > 3 or y > 3:
        return False
    return True

class Inference: #인퍼런스 클래스를 정의한다.[지식 베이스의 각 셀을 나타냄]
#
    def __init__(self, pos): #인퍼런스 클래스의 생성자다. 
        self.has_pit = None #현재 위치에 구덩이가 있는지 여부를 나타내는 [T/F 값]
        self.has_live_wumpus = None #현재 위치에 살아있는 움푸스가 있는지 여부를 나타내는 [T/F 값]
        self.has_obstacle = None # 현재 위치에 장애물이 있는지 여부를 나타내는 boolean 값
        self.has_visited = False # 현재 위치를 이미 방문했는지 여부를 나타내는 [T/F 값]

        self.x_pos = pos[0] #현재 위치 x의 값
        self.y_pos = pos[1] #현재 위치 y의 값 

        if self.x_pos == 0 and self.y_pos == 0: #시작 위치일 때 객체의 속성들이 초기화
            self.has_pit = False
            self.has_obstacle = False
            self.has_visited = True
            self.has_live_wumpus = False #살아있는 움푸스가 시작 위치에 있지 않음으로 False로 설정

    def __repr__(self): # 객체를 나타내는 문자열을 반환
        return "Inference at {0}. Has Wumpus: {1} Has obstacle: {2} Has pit: {3}".format((self.x_pos, self.y_pos),
                                                                                         self.has_live_wumpus,
                                                                                         self.has_obstacle,
                                                                                         self.has_pit)

    def __eq__(self, other): # 두 개의 객체를 비교하기 위해 사용한다. 
        # 해당 매서드를 구현해 두 객체의 특징 속성이 같으면 'True'를 반환 
        return self.x_pos == other.x_pos and self.y_pos == other.y_pos

    def __hash__(self): #__hash__ 메서드는 해당 객체의 x_pos와 y_pos 속성의 튜플 값의 해시 값을 반환
        return hash((self.x_pos, self.y_pos))

class KB(): #에이전트의 세계에 대한 지식을 나타내는 Knowledge Base 클래스 KB

    def __init__(self): # 클래스 에이전트의 상태와 세계를 초기화하는 매서드
        self.agent = AgentState()  #AgentState() 클래스의 인스턴스를 self.agent 변수에 저장
        self.world = [[0 for row in range(4)] for col in range(4)] #4x4 크기의 이차원 배열 self.world를 생성
        self.init_world() 
        # init_world() 메서드를 호출하여 
        #self.world 배열의 모든 요소에 대해 Inference((row, col)) 클래스의 인스턴스를 할당



#init_world() 메서드는 KB 클래스의 인스턴스를 초기화하는 역할
# 이 메서드는 2중 for 루프를 사용하여 self.world라는 2차원 리스트에 위치 좌표를 전달하여
# Inference 클래스의 인스턴스를 생성
    def init_world(self):
        for row in range(len(self.world)):
            for col in range(len(self.world[row])):
                self.world[row][col] = Inference((row, col))

    def get_state(self):
        return self.agent

    def get(self, x, y):
        if is_valid(x, y):
            return self.world[x][y]

    def get_location(self):
        return self.agent.get_location()

    def set_location_start(self):
        #self.agent.set_location_start()
        #self.agent.set_direction_start()
        self.agent = AgentState()

    def get_direction(self):
        return self.agent.direction

    def get_starting_loc(self):
        return self.world[0][0]

    def has_arrow(self):
        return self.agent.has_arrow

    def has_wumpus(self, x, y):
        if is_valid(x, y):
            loc = self.world[x][y]
            if loc.has_live_wumpus:
                return True
            else:
                return False
        return None

    def is_safe(self, x, y):
        if is_valid(x, y): #현재 위치가 유효한 위치인지 확인하는 함수
            loc = self.world[x][y] #현재 위치에 해당하는 Inference 객체를 가져옴

        if not loc or loc.has_pit or loc.has_live_wumpus or loc.has_obstacle:
            return False 
        #현재 위치에 함정(pit), 살아있는 우움퍼스(live wumpus), 혹은 장애물(obstacle)이 있는 경우
        #해당 위치가 안전하지 않은 것으로 판단하고 False를 반환
        return True #안전한 경우라고 생각

    def is_maybe_safe(self, x, y):  #주어진 위치에 대해 "Maybe"로 표시된 위험 요소(갈림길, 구덩이, 능글마)가 있는지 확인
        if is_valid(x, y): #함수를 사용하여 주어진 위치(x, y)가 유효한 위치인지 확인
            loc = self.world[x][y] #유효한 위치인 경우 해당 위치의 정보를 self.world[x][y]에서 가져옴

        if loc.has_pit == "Maybe" or loc.has_live_wumpus == "Maybe":
            #해당 위치에 "Maybe"로 표시된 요소(pit, wumpus, )가 있는지 확인 + 있으면 True
            return True
        return False

    def is_visited(self, x, y): #KB 객체가 갖고 있는 world 변수의 인덱스 x,y가 이미 방문한 곳인지를 확인
        loc = None #loc 변수 초기화
        

        if is_valid(x, y): #x,y 좌표가 유효한 인덱스인지 확인하고, 유효한 인덱스라면 
            loc = self.world[x][y]  # loc 변수에 해당 좌표의 Inference 객체를 할당

        if loc and loc.has_visited: #방문 여부 확인 
            #해당 좌표가 이미 방문한 곳이라면 True를 반환
            return True
        return False

    def tell(self, percept, action): #에이전트가 퍼셉트-> 받고 그 행동을 결정하고 결과를 KB에 전달하는 메소드
        loc = self.world[self.agent.x_pos][self.agent.y_pos] #현재 위치를 기반으로 현재 위치를 가져온다.

        if action == "Shoot":
            self.agent.has_arrow = False #에이전트가 화살을 쏜 경우 / 소유 상태를 업데이트

        elif action == "Forward": #에이전트가 앞으로 전진하는 경우 + 현재 방향을 기반으로 새로운 위치로 이동
            self.agent.go(self.agent.direction)#위치에서 새로운 Inference 객체를 생성
            loc = self.world[self.agent.x_pos][self.agent.y_pos]

        elif action and action.startswith("Turn"):# 회전하는 경우 방향 변경 
            self.agent.change_orientation(action)

        self.make_inference(percept, action) #함수를 호출하여 KB에 퍼셉트와 행동에 대한 새로운 추론을 생성
        loc.has_visited = True #현재 위치를 방문했다고 표시 

        if loc.has_pit == "Maybe": 
            #해당 위치에 구덩이가 있을 가능성이 있지만, 
            #실제로는 구덩이가 없으면 has_pit을 False로 업데이트
            loc.has_pit = False

    def make_inference(self, percept, action):
        #현재 위치에서 인식한 것을 + 앞으로 취할 행동을 기반으로 일어날 일들을 추론하는 함수[중요]
        smell = percept[0]
        atmos = percept[1]
        touch = percept[3]
        sound = percept[4]
        curr_loc = self.world[self.agent.x_pos][self.agent.y_pos] #현재 Agent위치

        if touch == "Bump":#현재 위치에서 벽에 부딪혔는지 확인
            curr_loc.has_obstacle = True #장애물이 있음 
            curr_loc.has_live_wumpus = False  # 웜푸스 x 
            curr_loc.has_pit = False # 구덩이 x 
            curr_loc.has_visited = True #방문했음
            self.agent.undo() #미로 탐색을 위한 에이전트의 이전 위치로 변경

        else:
            curr_loc.has_obstacle = False #bump가 아닌 경우 해당 위치에 장애물이 없다고 표시

            if action == "Shoot": 
                shooting_loc = self.agent.go(self.agent.direction, test=True).get_location()
                #shooting_loc를 구하기 위해 self.agent.go(self.agent.direction, test=True)를 호출하여 
                #현재 방향으로 이동하는 테스트를 진행
                #이동 후의 위치 정보를 가져와 get_location() 메소드를 호출하여 튜플 형태로 반환
                shooting_loc = self.world[shooting_loc[0]][shooting_loc[1]]
                #shooting_loc = self.world[shooting_loc[0]][shooting_loc[1]]는 반환된 튜플의
                #첫 번째 원소를 shooting_loc의 x 좌표, 두 번째 원소를 y 좌표로 이용하여 
                # #self.world의 해당 위치 정보를 가져옴

                if sound == "Scream": #스크럽 소리가 들린다면
                    #해당 위치에 함정이 없고 장애물도 없다는 것을 의미
                    shooting_loc.has_pit = False
                    shooting_loc.has_obstacle = False
                    #화살 발사 위치에는 함정이나 장애물이 없음을 의미
                    
                    for row in range(len(self.world)):
                        for col in range(len(self.world[row])):
                            self.world[row][col].has_live_wumpus = False
                    #for 루프를 통해 게임판의 모든 위치들을 순회하면서, 각 위치에서 has_live_wumpus 변수를 False로 설정
                        
                            

                else:
                    shooting_loc.has_live_wumpus = False

            for direction in directions: #방향에 대해 각각 업데이트
                state = self.agent.go(direction, test=True) 
                #direction 방향으로 움직였을 때의 위치를 state 변수에 저장
             
                if state: #state 값이 존재한다면(벽에 부딪치지 않았을 때), 위치 정보
                    
                    loc = self.world[state.x_pos][state.y_pos] #위치의 정보를 loc 변수에 저장
                    if atmos == "Breeze": #atmos가 Breeze일 경우,
                        curr_loc.has_breeze = True #현재 위치에 has_breeze 값을 True로 업데이트
                        if not curr_loc.has_visited and loc.has_pit == "Maybe":
                            loc.has_pit = True
                    # loc 위치에 함정이 아직 없고 방문한 적도 없다면 has_pit 값을 True로 업데이트
                        elif not loc.has_visited and loc.has_pit is None:
                            loc.has_pit = "Maybe"
                    else:#atmos가 Breeze가 아닐 경우, loc 위치의 has_pit 값을 False로 업데이트
                        if loc.has_pit == "Maybe" or not loc.has_visited:
                            loc.has_pit = False

                    if smell == "Stench":#smell == "Stench": : 인식한 정보 중 smell이 Stench일 경우, 
                        curr_loc.has_stench = True #현재 위치에 has_stench 값을 True로 업데이트
                        if not curr_loc.has_visited and loc.has_live_wumpus == "Maybe":
                            loc.has_live_wumpus = True #loc 위치에 wumpus가 있을 가능성이 있다면 has_live_wumpus를 True로 설정한다.
                            loc.has_pit = False 
                            loc.has_obstacle = False

                            for row in range(len(self.world)):
        #for 루프를 통해 게임판의 모든 위치를 순회
                                for col in range(len(self.world[row])):
                                    room = self.world[row][col]
                                    if room.has_live_wumpus != True:
                                #각 위치에서 has_live_wumpus 값이 True가 아닌 경우 has_live_wumpus 값을 False로 설정
                                        room.has_live_wumpus = False
                    #if문 모든 조건들이 모두 False 인 경우 실행된다.
                        elif not loc.has_visited and loc.has_live_wumpus is None: 
                            loc.has_live_wumpus = "Maybe"
                    else:
                        if loc.has_live_wumpus == "Maybe" or not loc.has_visited:
                            loc.has_live_wumpus = False


class AgentState(): #에이전트의 상태를 정의

     
    def __init__(self, x=0, y=0, d=RIGHT, c=0):
        self.direction = d
        self.has_gold = False
        self.has_arrow = True
        self.x_pos = x
        self.y_pos = y
        self.cost = c


    def __eq__(self, other): # 두 에이전트의 위치를 0,0으로 설정 // 위 참고
        if self.x_pos == other.x_pos and self.y_pos == other.y_pos and self.direction == other.direction:
            return True
        return False

    def __hash__(self):
        return hash((self.x_pos, self.y_pos, self.direction))

    def __repr__(self):
        direction = self.get_direction()
        return "State at {0} facing {1}".format(self.get_location(), direction)

    def __lt__(self, other):#메서드는 두 에이전트의 비용을 비교할 때 사용
        return self.cost < other.cost 
#비용이 작은 에이전트가 더 우선순위가 높다.

    def get_location(self): #메서드는 에이전트의 위치를 반환
        return (self.x_pos, self.y_pos)

    def set_location_start(self):
        self.x_pos =0
        self.y_pos =0

    def set_direction_start(self):
        self.direction = RIGHT

    def get_direction(self):
        if self.direction == UP:
            return "up"
        elif self.direction == DOWN:
            return "down"
        elif self.direction == LEFT:
            return "left"
        elif self.direction == RIGHT:
            return "right"
#메서드는 에이전트의 방향을 변경
    def change_orientation(self, action, test=False): 
       # action 매개변수는 "TurnLeft" 또는 "TurnRight" 중 하나가 된다.
       
        orientation = self.direction 
        #orientation 변수는 현재 방향을 나타내는 self.direction의 값을 복사
        
       # orientation 값을 변경하고, 만약 -45가 되면 135로, 180이 되면 0으로 변경
        if action == "TurnLeft":
            orientation -= 45
            if orientation == -45:
                orientation = 135
        elif action == "TurnRight":
            orientation += 45
            if orientation == 180:
                orientation = 0
                
        #만약 test 매개변수가 True인 경우, 새로운 AgentState 객체를 반환하고, 
        # test 매개변수가 False인 경우, self.direction 값을 변경
        if test:
            return AgentState(self.x_pos, self.y_pos, orientation)
        self.direction = orientation

    def reverse(self):
        self.direction += 90
        if self.direction >= 180: 
            self.direction -= 180

    def go(self, direction, test=False, restart=False): # 에이전트가 주어진 방향으로 이동하는 함수
        new_x = self.x_pos
        new_y = self.y_pos
        
        if restart == True:
            self.x_pos = 0
            self.y_pos = 0
            return 0
            
        #구문은 주어진 방향에 따라 새로운 좌표와 방향을 결정합니다. 이 구문은 현재 방향이 "Forward" 일 때만 체크
        #그렇지 않은 경우 에이전트는 제자리에 멈추게 된다.
        if direction == UP or self.direction == UP and direction == "Forward":
            new_y += 1
            direction = UP
        elif direction == DOWN or self.direction == DOWN and direction == "Forward":
            new_y -= 1
            direction = DOWN
        elif direction == LEFT or self.direction == LEFT and direction == "Forward":
            new_x -= 1
            direction = LEFT
        elif direction == RIGHT or self.direction == RIGHT and direction == "Forward":
            new_x += 1
            direction = RIGHT

        if is_valid(new_x, new_y):
            if test:
                return AgentState(new_x, new_y, direction)
            else:
                self.x_pos = new_x
                self.y_pos = new_y

        return None

    def undo(self): #에이전트가 이동한 것을 되돌리는 기능 
        if self.direction == UP:
            self.y_pos -= 1
        elif self.direction == DOWN:
            self.y_pos += 1
        elif self.direction == RIGHT:
            self.x_pos -= 1
        elif self.direction == LEFT:
            self.x_pos += 1


class ashtabna_ExplorerAgent(ExplorerAgent):

    def __init__(self): 
        #ExplorerAgent의 생성자를 호출하고, KB 객체를 생성
        #action, plan, start, goal, position 인스턴스 변수를 초기화
        super().__init__()
        self.kb = KB()
        self.action = None
        self.plan = []  
        self.start = AgentState(0, 0)
        self.goal = None
        self.position = self.start

    def program(self, percept):
        # percept(인식된 환경 정보)를 받아서 KB에 추가하고, 현재 위치를 갱신
        self.kb.tell(percept, self.action)
        self.position = self.kb.get_location()
#위치의 안전 여부를 판단해서
#safe_locs, unsafe_locs, maybe_unsafe_locs, unvisited_safe_locs, possible_wumpus_locs에 저장
        safe_locs = []
        unsafe_locs = []
        maybe_unsafe_locs = []
        unvisited_safe_locs = []
        possible_wumpus_locs = []

        if WumpusEnvironment.get_instance().die_flag:
            self.kb.set_location_start()
            #agentState()
            WumpusEnvironment.get_instance().die_flag = False

        for row in range(4):#for 반복문을 사용하여 던전 안의 모든 위치에 대해, 그 위치에 대한 에이전트 상태를 만든다.
            #위치가 안전한지 여부를 확인
            for col in range(4):
                for direction in directions:
                    location = AgentState(row, col, direction)
                    if self.kb.is_safe(row, col):
                        safe_locs.append(location) #만약에 위치가 안전하다면 safe_locs에 추가
                        if not self.kb.is_visited(row, col):
                            unvisited_safe_locs.append(location)
                            #해당 위치가 이미 방문한 곳이 아니라면 unvisited_safe_locs에 추가
                    else:
                        unsafe_locs.append(location) #그렇지 않으면, unsafe_locs에 추가

                if self.kb.has_wumpus(row, col):
                    possible_wumpus_locs.append(AgentState(row, col, UP))
#현재 위치에 위험한 요소가 있는 경우 (wumpus가 있을 가능성), 
#가능한 wumpus 위치의 목록 (possible_wumpus_locs)에 해당 위치를 추가


                if self.kb.is_maybe_safe(row, col):#현재 위치가 안전한지 아닌지 확인
                    no_pit = Inference((row, col))
                    #위치에 구덩이가 없을 경우와 있을 경우의 불확실성을 Inference로 표현
                    no_pit.has_pit = False
                    pit = Inference((row, col))
                    pit.has_pit = True
                    maybe_unsafe_locs.append(no_pit)#이 불확실성을 maybe_unsafe_locs 리스트에 추가
                    maybe_unsafe_locs.append(pit)

        if self.plan:
            #계획의 다음 단계가 여전히 안전한지 확인
            state = AgentState(self.position[0], self.position[1], self.kb.get_direction())
            #AgentState 객체를 생성하여 현재 위치와 방향 정보를 저장
            
            state = state.go(self.plan[0], test=True)
            #이전 계획에서 다음 단계에 해당하는 위치와 방향 정보를 go() 함수를 통해 state 객체에 저장
            
            if state in unsafe_locs: 
                #state 객체가 unsafe_locs 리스트 안에 있는지 확인하여, 
                #만약에 포함되어 있다면 현재 플랜(plan)을 초기화
                self.plan = [] 
#현재 위치에서 계획한 다음 단계가 위험한 위치라면 해당 플랜(plan)을 폐기하고 새로운 계획을 수립해야한다.
        # 여기에 보물이 있다면, 출구로 나가는 최단 경로를 잡고 계획
        
        
        if percept[2] == "Glitter": #"Glitter" 퍼셉션이 감지되면 실행
            self.action = "Grab" 
            #이 경우, 에이전트는 현재 위치에서 보물을 가져 오기 위해 "Grab" 동작을 수행
            
            #make_plan 메소드를 사용하여 현재 위치에서 출발하여 미로를 탐색하고,
            #안전한 위치 목록 safe_locs를 사용하여 최단 경로를 계산
            route = self.make_plan([self.start], safe_locs)
            self.plan.extend(route) #계산된 경로는 self.plan 리스트에 추가
            self.plan.append("Climb") # 마지막으로 Climb 동작과 함께 탈출을 위한 목표가 설정
            self.goal = "Exit"
            return self.action #self.action은 "Grab"으로 설정되고 반환

        # 보물이 없다면, 안전한 장소로 가는 최단 경로를 계획
        if not self.plan and not self.goal == "Exit":
            self.plan = self.make_plan(unvisited_safe_locs, safe_locs)

        # 안전한 경로가 없다면, Wumpus가 어디에 있는지 추측하고 화살을 쏴라
        if not self.plan and self.kb.has_arrow() and not self.goal == "Exit":
            
        #현재 계획이 없고, 화살이 있으면 목표가 출구가 아닌 경우, 
        #가능한 움푹이 위치와 안전한 위치를 기반으로 발사 계획을 세움   
            plan = self.plan_shot(possible_wumpus_locs, safe_locs)
            #plan_shot 함수는 화살 발사 후 발생 가능한 모든 상황을 고려하여 최단 경로를 계산하는 함수
            if plan is not None:
                plan.append("Shoot")
                self.plan = plan
 #plan 변수에 계산된 경로가 저장되고, plan이 None이 아니면 "Shoot" 동작을 추가하여 계획
 
 #안전하지 않은 곳이 있고 + 목표지점이 출구가 아닐 대 실행
        if not self.plan and maybe_unsafe_locs and not self.goal == "Exit":
            #maybe_unsafe_locs 리스트에 대해 각 위치의 위험 확률을 계산
            probs = self.get_risk_probabilities(maybe_unsafe_locs) #리스트에서 각 위치의 위험 확률을 계산

            if probs:
                
                safest = max(probs, key=probs.get)#가장 안전할 가능성이 높은 위치를 찾아 safest 변수에 저장

#directions 리스트에 있는 각 방향에 대해
                for direction in directions:
                    goal = AgentState(safest.x_pos, safest.y_pos, direction)
                    safe_locs.append(goal)
                    #safest 위치에서 그 방향으로 가는 목적지인 goal을 만들어 safe_locs 리스트에 추가
                self.plan = self.make_plan([goal], safe_locs)
#make_plan 메서드를 이용하여 goal을 출발점으로 하여 안전한 위치인 safe_locs에 도달하기 위한 최단 경로를 계산
        
        if not self.plan: # self.plan 리스트가 비어있지 않은 경우, 다음 단계가 안전한지 확인
            plan = self.make_plan([self.start], safe_locs)
 # self.plan 리스트가 비어있는 경우, self.start 지점에서 시작하여 Climb 명령어를 실행하도록 계획을 수립
            plan.append("Climb")
            self.plan = plan
 #Climb 명령어를 실행하는 계획을 수립

        self.action = self.plan.pop(0)
        #self.plan 리스트에서 다음 액션을 꺼내 self.action 변수에 저장
        return self.action


#주어진 세계(world)에서 지정된 위치(query)가 참 가능한지 확인하는 데 사용
#이 함수는 이전에 구축된 지식베이스(self.kb)를 사용하지 않음
#함수는 주어진 world에 대한 전체 가능성을 고려하기 때문에, 현재 지식 베이스와는 별개의 작업을 수행
    def is_possible(self, world, query):
        if world[world.index(query)].has_pit:
            #지정된 위치가 함정(has_pit)이 있다면 거짓(False)을 반환
            return False
#world 리스트의 각 원소는 Square 객체이며, query는 Square 객체 중 하나
        for square in world: #지정된 세계 상태(world)에서 쿼리(query) 위치가 안전한지 확인
            adjacent_squares = self.get_adjacent_pairs(square)
#get_adjacent_pairs() 메소드를 사용하여 쿼리 위치의 인접한 4개 위치 쌍을 검사하며, 모든 위치 쌍이 함정을 포함하지 않는지 확인
            for pair in adjacent_squares:
                #함정이 없는 위치 쌍이 없다면, 해당 쿼리 위치가 안전하지 않은 것으로 간주하고 False를 반환
                if self.all_false(pair, world):
                    return False
        return True

    def get_adjacent_pairs(self, square):
        #get_adjacent_pairs 함수는 인자로 받은 square 주변의 상, 하 위치를 튜플 형태로 반환
        up_square = (square.x_pos - 1, square.y_pos + 1)
        down_square = (square.x_pos + 1, square.y_pos - 1)
        #up_square와 down_square 변수를 설정해줍니다. 이 변수들은 square 주변의 상, 하 위치
        squares = []

        if is_valid(up_square[0], up_square[1]):
            squares.append((Inference(up_square), square))
#up_square가 유효한 위치인지 확인하고 유효하다면 (Inference(up_square), square) 튜플을 squares 리스트에 추가
        if is_valid(down_square[0], down_square[1]):
            squares.append((Inference(down_square), square))
#own_square가 유효한 위치인지 확인하고 유효하다면 (Inference(down_square), square) 튜플을 squares 리스트에 추가
        return squares

    def all_false(self, queries, world):
        for loc in queries:#queries에 있는 각 위치를 반복하여 loc 변수에 할당
            if loc in world:#현재 위치가 world에 존재하는지 확인
                square = world[world.index(loc)]#world에서 loc 위치의 인덱스를 가져와 해당 square 변수에 할당
            else:
                return False
            if square.has_pit:#해당 square에 구덩이가 있는지 확인
                return False# 구덩이가 발견되면 False를 반환
        return True#구덩이가 발견되지 않으면 True를 반환

    def get_risk_probabilities(self, frontier):#frontier 안의 각 정점에서 함정이 없을 확률을 계산
        probs = {} #probs 딕셔너리를 만들어서, 이 딕셔너리에는 frontier 안의 각 정점에서 함정이 없을 확률을 저장

        for square in frontier:
#frontier 안의 각 정점을 하나씩 순회하면서, 각 정점에서 함정이 없을 확률을 계산
            if square.has_pit:
                continue

            probs[square] = []
            pit_combs = combinations(frontier, len(set(frontier)))
#pit_combs 리스트를 만들어서, frontier 안의 정점들의 모든 조합을 저장
            for world in pit_combs:#pit_combs 리스트를 하나씩 순회하면서
                unique_combo = set(world) #중복이 없는 조합만 계산
                prob = 1
                if len(unique_combo) == len(world) and self.is_possible(world, square):
                    for loc in world:
                        if loc != square: # 쿼리 정점을 제외하고
                            if loc.has_pit:
                                prob = prob * PIT_PRIOR # 함정이 있을 확률을 곱해줌
                            else:
                                prob = prob * (1 - PIT_PRIOR) # 함정이 없을 확률을 곱해줌
                    probs[square].append(prob)
 # 함정이 없을 확률을 계산
            probs[square] = sum(probs[square]) * (1 - PIT_PRIOR)

        return probs
    #모든 정점에서 함정이 없을 확률을 저장한 딕셔너리 probs를 반환

    def get_valid_actions(self, location):
        #get_valid_actions 함수는 에이전트의 위치를 인자로 받아 현재 가능한 행동의 리스트를 반환하는 함수
        actions = ["TurnLeft", "TurnRight", "Forward"]

#directions 리스트를 이용해 현재 에이전트의 바라보는 방향을 확인하고,
#이 방향으로 이동이 가능한지 direction_valid 함수를 이용해 확인
        for direction in directions:
            if direction == location.direction:
                if not self.direction_valid(location, direction):
                    actions.remove("Forward")

        return actions
 
    def direction_valid(self, location, direction):
        # 함수는 에이전트가 현재 위치에서 해당 방향으로 이동이 가능한지 검사
        loc = location.go(direction, test=True)
        #location.go(direction, test=True) 를 통해 현재 위치에서 해당 방향으로 이동이 가능한지 확인
        if loc:
            return True
        return False
#test=True 옵션을 주어 에이전트가 움직이지는 않고, 가능한 경우 해당 위치를 반환
#만약 해당 방향으로 이동이 불가능하면 None 을 반환
#따라서 반환값이 None이 아니면 해당 방향으로 이동이 가능한 것으로 판단하고 True를 반환하고,
#그렇지 않으면 False를 반환

    def take_action(self, state, action):
        if action == "Forward":
            return state.go(state.direction, test=True)
        elif action.startswith("Turn"):
            return state.change_orientation(action, test=True)

    def get_distance(self, loc, dest):
        return abs(loc.x_pos - dest.x_pos) + abs(loc.y_pos - dest.y_pos)

    def plan_shot(self, wumpus_locs, world):
        shooting_locs = [] 

       
        for state in wumpus_locs: #state를 이용하여 wumpus의 위치를 찾음 / directions 리스트의 모든 방향에 대해 다음을 수행
            loc = state.get_location()
            row = loc[0]
            col = loc[1]
            wumpus = AgentState(row, col)
            for direction in directions:
                pos = wumpus.go(direction, test=True) #wumpus.go(direction, test=True)를 호출하여,
                if pos:#현재 wumpus 위치에서 direction 방향으로 이동한 위치인 pos를 구함
                    pos.reverse()
                    shooting_locs.append(pos)
#만약 pos가 유효한 위치라면, pos 리스트를 뒤집고(reverse()) shooting_locs 리스트에 추가
        return self.make_plan(shooting_locs, world, exact=True)
#wumpus_locs에 대해 반복한 뒤, self.make_plan(shooting_locs, world, exact=True)를 호출하여 
#shooting_locs 리스트에 있는 위치들을 순서대로 이동하면서 움퍼스를 쏘도록 하는 계획 설정

    def is_allowed(self, state, world, exact): 
        # 현재 상태(state)가 월드(world) 내에 허용 가능한 상태인지를 나타내는 부울값을 반환
        if exact: # exact 매개 변수가 True이면, 상태(state)가 월드(world)에 정확하게 있는지 확인
            if state in world:
                return True
        else:#False이면, 월드 내에서 현재 상태(state)와 일치하는 위치가 있는지 확인
            for loc in world:
                if state.get_location() == loc.get_location():
                    return True
        return False

    def is_goal(self, state, goal, exact):
        if exact:
            if state == goal:
                return True
        else:
            if state.get_location() == goal.get_location():
                return True
        return False
#목적지(dest)까지 이동하기 위한 계획을 만드는 함수
    def make_plan(self, dest, world, exact=False):
        paths = []
        goals = dest
        curr_state = self.kb.get_state() #현재 상태를 curr_state로 지정
        
#현재 상태(curr_state)에서 출발하여 goal에 도착하기 위한 최적의 경로를 찾음
        for goal in goals:
            cost = np.inf
            path = []
            frontier = queue.PriorityQueue()#이 경로는 frontier queue에 저장 + 경로의 길이가 최소가 되도록 우선순위를 계산
            explored = {}  # explored 딕셔너리에는 최소 경로가 저장
            frontier.put(curr_state) #딕셔너리의 키는 상태(State)
            explored[curr_state] = [] #해당 상태까지의 최소 경로가 값으로 저장

#frontier에서 하나의 상태(State)를 꺼내고, 이 상태에서 이동할 수 있는 유효한 액션을 구함
            while not frontier.empty() and frontier.queue[0].cost < cost:
                state = frontier.get()
#각 액션에 대해 새로운 상태(State)를 생성
                if self.is_goal(state, goal, exact):  # 새로운 상태가 goal에 도달했다면, 현재까지의 최소 경로를 반환
                    return explored[state]#만약 도착하지 않았다면, 이 새로운 상태를 explored에 추가
                actions = self.get_valid_actions(state)
                
                for action in actions: #현재 상태에서 가능한 모든 액션을 수행 + 최적의 경로를 찾는다.
                    frontier_path = explored[state] + [action]
                    frontier_cost = len(frontier_path)
                    result = self.take_action(state, action)
#현재 상태와 액션을 인자로 받아 새로운 상태를 생성하는 take_action 메소드를 호출

                    if self.is_allowed(result, world, exact) and (result not in explored.keys() or frontier_cost < len(explored[result])):
                        path_cost = self.get_distance(result, goal) + frontier_cost
                        result.cost = path_cost
                        frontier.put(result)  # 가장 가까운 곳에 
                        explored[result] = frontier_path  # 위치를 탐색된 위치로 표시

                        #이 위치가 목표로 이어지고 도달하는 경로가 현재 솔루션보다 짧다면
                        if self.is_goal(result, goal, exact) and frontier_cost < cost:
                            path = frontier_path
                            cost = frontier_cost

            paths.append((path, cost))

        if paths:
            return min(paths, key = lambda t: t[1])[0]
        return None
#마지막으로, 모든 목적지에 대한 최적 경로를 찾은 후, 경로의 길이가 최소인 경로를 반환 + 경로가 없다면 None을 반환