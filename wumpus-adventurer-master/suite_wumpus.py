

import logging
import random
from wumpus import *
from collections import namedtuple

Result = namedtuple('Result','score num_steps')

class Suite():

    def __init__(self, seeds=range(10)): # Suite 객체를 생성할 때 사용할 seed 값들을 인자로 받음
        self.seeds = seeds

    def run(self, Explorer_class, max_steps=10000): #run 함수에서는 seed 값을 하나씩 가져와 Wumpus 게임을 실행
        scores = []
        for seed in self.seeds: #
            logging.critical('Running seed {}...'.format(seed))
            random.seed(seed)#random.seed(seed)를 통해 해당 seed 값으로 랜덤 값을 생성
            we = WumpusEnvironment() #WumpusEnvironment 클래스를 이용해 게임을 실행하고, Explorer_class 객체를 START_SQUARE 위치에 추가
            we.add_thing(Explorer_class(), we.START_SQUARE)
            step = 0
            while step < max_steps  and  not we.should_shutdown(): #게임을 실행하면서 max_steps 값에 도달하거나 게임 종료 조건이 되면 게임을 종료
                we.step()
                step += 1
            scores.append(Result(we.agents[0].performance, step)) #각 게임 결과는 Result 클래스의 인스턴스로 저장
        return scores
