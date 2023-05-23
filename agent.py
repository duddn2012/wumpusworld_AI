

import abc


class Thing(abc.ABC): # Thing class에선 추상 클래스인 abc.ABC를 상속하고 있음 __repr__ 매서드를 구현한다.
    def __repr__(self):  # 객체의 문자열 표현을 반환한다.
        return '<{}>'.format(getattr(self, '__name__', self.__class__.__name__))
    #format 매서드를 사용해서 클래스의 이름 또는 객체의 이름을 < > 로 감싸서 반환
    #name 속성이 존재하면 그 값을 반환 + 그렇지 않으면 class/name의 값을 반환

    def is_alive(self): #Thing 클래스 안에 'is alive' 매서드가 정의
        return hasattr(self, 'alive') and self.alive #alive 속성을 가지고 있는 경우에만 'True'를 반환한다.
    #해당 객체가 살아있는지 확인하는 매서드다.


class Agent(Thing): 
    def __init__(self): #생성자 매서드를 정의 __init__은 클래스가 인스턴스화 될 때 자동으로 호출되는 매서드
        self.alive = True #alive 속성 초기화 
        self.performance = 0 #performance도 초기화

    @abc.abstractmethod
    def program(self, percept):
        pass