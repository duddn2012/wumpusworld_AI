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

    def __init__(self):
        super().__init__()
        self._bump = False 
        self._facing_direction = 'Up' 
        self._holding = [ Arrow(),Arrow() ]

    @property
    def image_filename(self): 
        return self.images[self._facing_direction if
            self._facing_direction else 'Up']





class WumpusEnvironment(XYEnvironment):

    START_SQUARE = (1,1) 
    CAN_COEXIST = False 
    __instance = None
    SideWalls=True 

    
    def __init__(self, width=4, height=4):
        if WumpusEnvironment.__instance != None:
            raise Exception("Singleton class cannot be instantiated more than once")
        else:
            WumpusEnvironment.__instance = self
        if self.SideWalls:
            width=6
            height=6
            super().__init__(width, height)
            self. addSideWalls()
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
 
 


    def percept(self, agent): 
        things_adj = [ t for t,_ in self.things_near(self[agent], 1) 
                if not isinstance(t, ExplorerAgent) ] 
        stench = 'Stench' if any([isinstance(x, Wumpus) for x in things_adj])\
                else None 
        breeze = 'Breeze' if any([isinstance(x, Pit) for x in things_adj])\
                else None 
        glitter = 'Glitter' \
            if len(self.list_things_at(self[agent], Gold)) > 0 else None 
        bump = ('Bump' if agent._bump else None) 
        scream = None
        if self._do_scream:
            scream = 'Scream'
            self._do_scream = False
        return (stench, breeze, glitter, bump, scream)

   
    
    def get_risk_assessment(self): 
        risk = 0 
        for x in range(self.width):
            for y in range(self.height):
                if self.list_things_at((x, y), Pit):
                    risk += 100
        return risk

    def execute_action(self, agent, action):
        if action not in agent.possible_actions: 
            logging.critical("Illegal action {}! Shutting down.".format(
                                                                    action))
            sys.exit(1) 
        agent.performance -= 1
        if action == 'Climb':
            if self[agent]==self.START_SQUARE:
                if any([ isinstance(i,Gold) for i in agent._holding ]):
                    agent.performance += 1000
                    logging.critical('You win!!! Total score: {}'.format(
                        agent.performance)) 
                else: 
                    logging.critical('Goodbye -- total score: {}'.format(
                        agent.performance)) 
                self._is_done_executing = True
            else:
                logging.info("Sorry, can't climb from here!")
        elif action.startswith('Turn') or action=='Forward': 
            super().execute_action(agent, action) 
            if self.list_things_at(self[agent], Wumpus):
                agent.performance -= 1000
                XYEnvironment.get_instance().move_to(agent, (1,1))
                self.die_flag = True
                logging.critical(
                    'You were EATEN BY THE WUMPUS!! Total score: {}'.
                    format(agent.performance))
                self._is_done_executing = True
            if self.list_things_at(self[agent], Pit):
                XYEnvironment.get_instance().move_to(agent, (1,1))
                self.die_flag = True
                agent.performance -= 1000
                logging.critical('You fell into a PIT!! Total score: {}'.
                    format(agent.performance))
                self._is_done_executing = True
        elif action=='Grab': 
            if self.list_things_at(self[agent], Gold):
                logging.info('Grabbed gold.')
                gold = self.list_things_at(self[agent], Gold)[0]
                self.delete_thing(gold)
                agent._holding.append(gold)
            else:
                logging.debug("Afraid there's nothing here to grab.")
        elif action=='Shoot': 
            arrows = [ i for i in agent._holding if isinstance(i,Arrow) ]
            if arrows:
                agent._holding.remove(arrows[0])
                num_steps = 1
                target = self.square_in_dir(agent._facing_direction,
                    self[agent], num_steps) 
                while self.is_inbounds(target):
                    wumpi = self.list_things_at(target, Wumpus)
                    if wumpi: 
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
  
    def add_wumpus(self):
        for x in range(self.width):
            for y in range(self.height):
                if ((self.CAN_COEXIST or (x,y) not in self.values()) and
                        (x,y) != self.START_SQUARE and 
                        random.random() < 0.1):
                    self.add_thing(Wumpus(), (x,y))
                    #return

    def add_gold(self): 
        self.add_to_one_non_starting_square(Gold())

    def add_to_one_non_starting_square(self, thing):
        possible_squares = [(x,y) for x in range(self.width)
            for y in range(self.height)
                    if (self.CAN_COEXIST or (x,y) not in self.values()) and
                    (x,y) != self.START_SQUARE ]
        self.add_thing(thing,random.choice(possible_squares))

    def add_pits(self, pit_prob=.1): 
        for x in range(self.width):
            for y in range(self.height):
                if ((self.CAN_COEXIST or (x,y) not in self.values()) and
                        (x,y) != self.START_SQUARE and 
                        random.random() < pit_prob):
                    self.add_thing(Pit(), (x,y))

    def add_walls(self, wall_prob=.1): 
        for x in range(self.width):
            for y in range(self.height):
                if ((self.CAN_COEXIST or (x,y) not in self.values()) and
                        (x,y) != self.START_SQUARE and 
                        random.random() < wall_prob):
                    self.add_thing(Wall(), (x,y))

    def addSideWalls(self): 
            for i in range(self.height):
                self.add_thing(Wall(), (self.width-1,i))
                self.add_thing(Wall(), (0,i))
            for i in range(self.width):
                self.add_thing(Wall(), (i,0))
                self.add_thing(Wall(), (i,self.height-1))

    def should_shutdown(self): 
        return self._is_done_executing


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