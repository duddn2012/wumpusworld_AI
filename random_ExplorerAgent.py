
from wumpus import ExplorerAgent

import random
import logging
#ExplorerAgent를 상속하는 random_ExplorerAgent 클래스를 정의
class random_ExplorerAgent(ExplorerAgent):
#random_ExplorerAgent 클래스는
#ExplorerAgent의 program 메서드를 오버라이드하여 임의의 행동을 선택하는 로직을 추가
    def __init__(self):
        super().__init__()
#program 메서드에서는 self.possible_actions 리스트 중에서 임의의 행동을 선택하여 반환
    def program(self, percept):
        action = random.choice(self.possible_actions)
        logging.debug("Doing action {}.".format(action))#로깅 모듈을 이용해 선택한 행동을 디버깅 모드에서 출력
        return action
