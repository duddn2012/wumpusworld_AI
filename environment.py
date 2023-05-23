
import logging
import abc
import random
import collections

from agent import *


#AI 에이전트와 환경 간의 상호작용을 모델링하는 "에이전트 기반 모델"을 구현하기 위한 클래스 Environment를 정의
class Environment(collections.UserDict):
#UserDict 클래스를 상속 +  딕셔너리 객체를 확장 + 에이전트 프로그램을 실행하는 데 필요한 메서드와 속성을 추가
#에이전트 프로그램은 각 에이전트의 행동을 결정하는 데 사용
    __instance = None

    def __init__(self):
        if Environment.__instance != None:
            raise Exception("Singleton class cannot be instantiated more than once")
        else:
            Environment.__instance = self
        super().__init__()
        self.agents = []
        self.observers = []
        #self.safe_locs = []
        
    @classmethod
    def get_instance(cls):
        if cls.__instance == None:
            cls()
        return cls.__instance
        
        
#@abc는 Python의 내장 모듈인 abc (Abstract Base Classes) 모듈의 데코레이터
#@abc.abstractmethod는 추상 메서드 (Abstract Method)를 정의하는 데 사용
    @abc.abstractmethod
    def percept(self, agent):
        """Return the percept that the agent sees at this point."""
#주어진 에이전트가 현재 상태에서 볼 수 있는 것들을 반환하는 추상 메서드 + 이 메서드는 서브클래스에서 구현

    @abc.abstractmethod
    def execute_action(self, agent, action):
        """Change the world to reflect this action."""
#주어진 에이전트가 취한 행동을 환경에 적용

    def add_observer(self, observer):
        self.observers.append(observer)
#add_observer 메서드는 관찰자(observer)를 추가하는 메서드+ self.observers 리스트에 observer를 추가
    def default_location(self, thing):
        """Default location to place a new thing with unspecified location."""
        return None
#default_location 메서드는 인자로 주어진 thing을 위치하지 않은 채로 추가할 때 기본 위치를 지정해주는 메서드

    def exogenous_change(self):
        """If there is spontaneous change in the world, override this."""
        pass
#외부적인 변화(exogenous change)를 처리하기 위한 메서드입니다. 이 메서드는 아무런 동작을 하지 않는 빈 메서드
#이 메서드를 필요에 따라 오버라이드하여 외부적인 변화를 처리

    def is_done(self):
        """By default, we're done when we can't find a live agent."""
        return not any(agent.is_alive() for agent in self.agents)
        
    
#step() 메소드는 환경을 한 타임 스텝(한 번의 실행)만큼 진행하는 메소드
    def step(self):
        """Run the environment for one time step. If the
        actions and exogenous changes are independent, this method will
        do. If there are interactions between them, you'll need to
        override this method."""
        if not self.is_done():#is_done() 메소드를 호출하여 환경의 상태가 종료상태인지 확인
            actions = []
            for agent in self.agents:
                if agent.alive:
                    actions.append(agent.program(self.percept(agent)))
                    #program() 메소드를 호출하여 해당 에이전트의 액션을 결정
                else:
                    actions.append("")
            for (agent, action) in zip(self.agents, actions):
                self.execute_action(agent, action)#이후, 결정된 액션을 execute_action() 메소드를 이용하여 실제로 수행
            self.exogenous_change()#exogenous_change() 메소드를 호출하여 환경이 변화하는 경우에 대응

    def run(self, steps=1000): #run() 메소드는 step() 메소드를 여러 번 호출하여 환경을 지정된 횟수만큼 실행
        """Run the Environment for given number of time steps."""
        for step in range(steps):
            if self.is_done():
                return
            self.step()
#list_things_at 함수는 특정 위치에 있는 tclass 클래스의 객체들을 리스트로 반환
    def list_things_at(self, location, tclass=Thing):
        """Return all things exactly at a given location."""
        return [thing for thing, loc in self.items()
                if loc == location and isinstance(thing, tclass)]
#some_things_at 함수는 특정 위치에 있는 객체들 중 tclass 클래스나 이를 상속받은 클래스의 객체가 있는지 여부를 반환
    def some_things_at(self, location, tclass=Thing):
        """Return true if at least one of the things at location
        is an instance of class tclass (or a subclass)."""
        return self.list_things_at(location, tclass) != []

#add_thing 함수는 thing을 environment에 추가합니다.  
    def add_thing(self, thing, location=None):
        """Add a thing to the environment, setting its location. For
        convenience, if thing is an agent program we make a new agent
        for it. (Shouldn't need to override this."""
        if not isinstance(thing, Thing): #만약 thing이 Thing 클래스의 객체가 아닌 경우
            thing = Agent(thing) # Agent 객체로 변환
        if thing in self:##이미 존재하는 thing일 경우, 에러 메시지를 출력
            print("Can't add the same thing twice")
        else:#만약 thing이 Agent 클래스의 객체라면,
            self[thing] = (location if location is not None
                                        else self.default_location(thing))
            if isinstance(thing, Agent):
                thing.performance = 0 #thing의 performance를 0으로 초기화하고
                self.agents.append(thing)#self.agents에 추가

    def delete_thing(self, thing): #delete_thing 함수는 thing을 environment에서 삭제
        """Remove a thing from the environment."""
        try:
            del self[thing] #만약 thing이 self.agents에 속한 객체라면, self.agents에서 삭제
        except ValueError as e:
            pass
        if thing in self.agents:
            self.agents.remove(thing)
        for obs in self.observers: #self.observers에 속한 모든 observer에 대해서 thing_deleted 함수를 호출
            obs.thing_deleted(thing)

    def move_to(self, thing, destination): #move_to 함수는 thing 객체를 새로운 위치(destination)로 이동
        '''Move the thing to a new location. (Being in the plain Environment
        class, this has nothing intrinsically to do with a coordinate system
        or the like.)'''
        self[thing] = destination
        self.notify_observers(thing)

    def notify_observers(self, thing): #notify_observers 함수는 주어진 thing 객체가 움직였음을 observer들에게 알리기 위해 사용
        for o in self.observers:
            o.thing_moved(thing)
#각 observer는 thing_moved 메서드를 가지고 있어 이 메서드를 호출하여 thing 객체가 이동

    def should_shutdown(self):#특정한 환경에서 중단 조건을 신호하기 위해 오버라이드할 수 있음
        '''Can be overridden by specialized environments to signal a stopping
        condition.'''
        return False


class XYEnvironment(Environment): #2D 평면 상의 위치를 (x, y) 좌표로 나타내는 환경 클래스+#Environment 클래스를 상속받아 구현
    """This class is for environments on a 2D plane, with locations
    labelled by (x, y) points, either discrete or continuous.
    """
    
    __instance = None
    
#width와 height 변수로 평면의 크기를 설정
    def __init__(self, width=10, height=10):
        if XYEnvironment.__instance != None:
            raise Exception("Singleton class cannot be instantiated more than once")
        else:
            XYEnvironment.__instance = self
        super().__init__()
        self.width = width
        self.height = height

        # Sets iteration start and end (no walls).
        self.x_start, self.y_start = (0, 0)
        self.x_end, self.y_end = (self.width, self.height)
        

    @classmethod
    def get_instance(cls):
        if cls.__instance == None:
            cls()
        return cls.__instance

    perceptible_distance = 1
#things_near 함수는 location 위치에서 radius 반경 내에 있는 모든 사물을 반환
    def things_near(self, location, radius=None, manhattan=True):
        """Return all things within radius of location."""
        if radius is None:
            radius = self.perceptible_distance
        if manhattan:
#manhattan 인자가 True인 경우, 맨해튼 거리(가로, 세로 축으로만 이동하여 
#목표 지점에 도달할 때 필요한 이동 횟수)를 계산하여 반경 내에 있는 사물을 반환
            return [(thing, abs(loc[0] - location[0]) + 
                            abs(loc[1] - location[1]))
                for thing, loc in self.items() if 
                            abs(loc[0] - location[0]) + 
                            abs(loc[1] - location[1]) <= radius]
        radius2 = radius * radius
        def dist_sq(x,y): #manhattan 인자가 False인 경우, dist_sq 함수를 사용하여 반지름 내에 있는 사물들을 반환
            #dist_sq 함수는 두 점 사이의 거리를 제곱값으로 계산하는 함수
            return x^2 + y^2
        return [(thing, radius2 - dist_sq(location, self[thing]))
                for thing, loc in self.things if dist_sq(location, loc) 
                                                                <= radius2]
#반환되는 리스트는 (thing, distance) 형식으로, thing은 사물 객체이고 distance는 location과 thing 사이의 거리

    def percept(self, agent):#percept 함수는 인자로 받은 agent의 위치를 중심으로 things_near 함수를 호출하여 일정 반경 내에 있는 사물들을 인식
        """By default, agent perceives things within a default radius."""
        return self.things_near(self[agent])

    def execute_action(self, agent, action):#인자로 받은 agent가 수행할 동작 action을 처리
        '''Have the agent carry out this action. If a move in a compass
        direction, it may work, or may not, depending on whether there's an
        obstacle there. The next percept (2nd element of tuple) will tell the
        agent whether this happened.'''
        agent._bump = False
        if action in ['Left','Up','Right','Down']:
            agent._bump = self.try_to_move_in_dir(agent, action)
            # 이동이 가능하면 try_to_move_in_dir 함수를 호출하여 agent를 해당 방향으로 이동
        elif action == 'Forward':#Forward: agent가 현재 바라보는 방향으로 이동하려고 시도
            agent._bump = self.try_to_move_in_dir(agent,
                agent._facing_direction)
        elif action == 'TurnLeft':
            directions = [ 'Up','Left','Down','Right','Up' ]
            agent._facing_direction = directions[
                directions.index(agent._facing_direction) + 1]
        elif action == 'TurnRight':
            directions = [ 'Up','Right','Down','Left','Up' ]
            agent._facing_direction = directions[
                directions.index(agent._facing_direction) + 1]
        elif action == 'NoOp':#NoOp: 아무 동작도 수행하지 않음
            pass
        else:
            logging.critical("UNKNOWN action {}!!".format(action))
        self.notify_observers(agent)
# execute_action 함수는 notify_observers 함수를 호출하여 agent가 수행한 동작에 대해 환경의 관측자들에게 알림
    def try_to_move_in_dir(self, agent, direction):
        return self.move_to(agent, self.square_in_dir(direction, self[agent]))
#GridWorld를 구현

#square_in_dir 함수: 주어진 위치(location)에서 주어진 방향(direction)으로 num_steps만큼 이동한 위치를 반환
    def square_in_dir(self, direction, location, num_steps=1):
        '''Return the location that is num_steps in the given direction from
        the given location.'''
        x,y = location
        if direction == 'Left':
            return (x-num_steps,y)
        elif direction == 'Right':
            return (x+num_steps,y)
        elif direction == 'Up':
            return (x,y+num_steps)
        elif direction == 'Down':
            return (x,y-num_steps)

    def default_location(self, thing):
        return (random.choice(self.width), random.choice(self.height))
#객체를 목적지(destination)로 이동시키고, 만약 목적지가 장애물이거나 경계를 벗어난 위치라면 _bump 속성을 True로 설정
    def move_to(self, thing, destination):
        thing._bump = (self.some_things_at(destination, Obstacle) or
            not self.is_inbounds(destination))
        if not thing._bump:
            self[thing] = destination
            super().move_to(thing, destination)
        return thing._bump

    def add_thing(self, thing, location=(0, 0)):
        if self.is_inbounds(location):
            super().add_thing(thing, location)
#add_thing 함수: 객체를 지정된 위치(location)에 추가합니다. 해당 위치가 경계를 벗어난 위치가 아니면 super().add_thing을 호출하여 객체를 추가


    def is_inbounds(self, location):# 위치가 격자의 경계를 벗어나지 않았는지 확인
        """Checks to make sure that the location is inbounds (within walls if
        we have walls)"""
        x, y = location
        return not (x < self.x_start or x >= self.x_end or y < self.y_start 
                                                        or y >= self.y_end)
#격자의 경계는 x_start, x_end, y_start, y_end 속성으로 정의

# 범위 내에서 (벽 안쪽에서) 랜덤한 위치를 반환 + exclude 매개변수를 통해 제외할 위치를 지정
    def random_location_inbounds(self, exclude=None):
        """Returns a random location that is inbounds (within walls if we have
        walls)"""
        location = (random.randint(self.x_start, self.x_end),
                    random.randint(self.y_start, self.y_end))
        if exclude is not None:
            while(location == exclude):
                location = (random.randint(self.x_start, self.x_end),
                            random.randint(self.y_start, self.y_end))
        return location

    def add_walls(self): # 격자 상의 모든 테두리에 벽을 추가
        """Put walls around the entire perimeter of the grid."""
        for x in range(self.width):
            self.add_thing(Wall(), (x, 0))
            self.add_thing(Wall(), (x, self.height - 1))
        for y in range(self.height):
            self.add_thing(Wall(), (0, y))
            self.add_thing(Wall(), (self.width - 1, y))
#x_start, y_start, x_end, y_end 변수를 업데이트하여, 벽을 포함한 격자 범위를 정의
        
        self.x_start, self.y_start = (1, 1)
        self.x_end, self.y_end = (self.width - 1, self.height - 1)
#turn_heading() 함수는 heading 방향을 기준으로, 왼쪽 (inc=+1) 혹은 오른쪽 (inc=-1) 방향으로 회전한 방향을 반환
    def turn_heading(self, heading, inc):
        """Return the heading to the left (inc=+1) or right (inc=-1) of
        heading."""
        return turn_heading(heading, inc)

#GridWorld에서 에이전트가 이동할 때 부딪히게 되면서 이동을 방해하는 장애물을 정의
class Obstacle(Thing):
    """Something that can cause a bump, preventing an agent from
    moving into the same square it's in."""
    image_filename = 'question.gif'


class Wall(Obstacle):
    image_filename = 'wall.gif'

