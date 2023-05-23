
from wumpus import ExplorerAgent

import random

#ExplorerAgent를 상속받는 manual_ExplorerAgent 클래스를 정의
class manual_ExplorerAgent(ExplorerAgent):
    '''Note: run this in "auto" mode.'''
#사용자에게 직접 입력을 받아 움직임을 결정하는 에이전트
    def __init__(self):
        super().__init__()
#현재 지각(percept)을 출력하고, 가능한 행동들을 나열하여 사용자로부터 입력을 받음
    def program(self, percept):
        print("The percept I just got is: {}".format(percept))
        action = input(', '.join([str(i) + '.' + x for i, x in enumerate(
                self.possible_actions)]) + '? ')
        return self.possible_actions[int(action)]
