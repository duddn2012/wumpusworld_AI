
import tkinter as tk
import tkinter.ttk as ttk
import logging

from environment import *
#GUI 부분
class VisualXYEnvironment:
    '''A "view" to the XYEnvironment's "model".'''

    IMAGE_DIR = 'images'
    SMALL = False
#xy_env는 이 뷰가 표현하는 XYEnvironment 모델 객체
#max_thing_width와 max_thing_height는 한 개의 Thing이 차지하는 최대 가로 길이와 세로 길이
#title은 이 뷰가 띄우는 tkinter 창의 제목
    def __init__(self, xy_env, max_thing_width, max_thing_height,
            title='CPSC 415'):
        '''Initialize this view with a model to give a view of.'''
        self.xy_env = xy_env
        if self.SMALL: 
            #self.SMALL은 이 클래스의 클래스 변수로, 
            #만약 True이면 max_thing_width와 max_thing_height를 2로 나누어 크기를 줄임
            max_thing_width /= 2
            max_thing_height /= 2
   # CANVAS_HEIGHT는 캔버스의 크기를 나타내며, 
        self.CANVAS_WIDTH = max_thing_width * self.xy_env.width
        self.CANVAS_HEIGHT = max_thing_height * self.xy_env.height
        self.square_width = max_thing_width #square_width와 square_height는 Thing 하나의 크기를 나타냄
        self.square_height = max_thing_height
        self.title = title
        self.image_cache = {} #이미지 캐싱을 위한 딕셔너리
        self._setup_graphics() # tkinter 창을 설정하는 메소드
        self.xy_env.add_observer(self) #xy_env.add_observer(self)는 이 뷰를 XYEnvironment 객체의 옵저버로 등록하는 코드
        self.still_running = True #self.still_running은 뷰가 여전히 실행 중인지를 나타내는 변수
        self.total_steps = 0 #self.total_steps는 지금까지 수행된 단계의 수를 나타내는 변수

    def start(self, interactive): #시뮬레이션을 시작하는데 사용
        logging.info('starting {}...'.format(
            'interactive' if interactive else 'auto'))
        self.draw_entire_environment()
        if not interactive: #interactive가 False인 경우
            self.continuous.set(True) #continuous와 delay라는 tkinter 변수를 설정한 다음, run_until() 메소드를 호출하여 시뮬레이션을 실행
            self.delay.set(1)
            self.run_until(10000000000)
            #run_until() 메소드는 시뮬레이션을 반복적으로 실행하며, 시뮬레이션이 완료되거나 최대 스텝 수에 도달할 때까지 반복
        self.root_window.mainloop()
        logging.info('...done!') #메소드가 끝나면 logging 메시지가 출력

    def thing_moved(self, thing, animation_start_end=()):
        '''If animation_start_end is empty, simply record that this thing has
        been moved. Otherwise, display it moving from one location to the
        other (the elements of the tuple).'''
        if animation_start_end: #만약 animation_start_end가 비어있으면, 단순히 이 thing이 움직였음을 기록
            self.animate_thing(thing, *animation_start_end)
        else: #animation_start_end가 비어있지 않으면, 이 thing을 하나의 위치에서 다른 위치로 움직이는 것을 보여준다.
            self.redraw_entire_environment()

    def thing_deleted(self, thing):
        self.redraw_entire_environment()

    def calculate_coords(self, loc): #주어진 위치(loc)를 캔버스에서의 좌표로 변환하여 반환
        return (self.square_width * loc[0],
                self.CANVAS_HEIGHT - self.square_height * (loc[1] + 1))
#변환된 좌표는 첫 번째 원소가 캔버스의 x 좌표, 두 번째 원소가 캔버스의 y 좌표
#loc는 튜플로, 첫 번째 원소는 가로 좌표, 두 번째 원소는 세로 좌표

    def animate_thing(self, thing, loc1, loc2): #thing 객체를 loc1에서 loc2로 이동
        def do_anim():
#do_anim 내부 함수를 정의하고, after 메서드를 사용하여 do_anim 함수를 1밀리초 뒤에 호출
            FRAMES = 20
            the_image = self.draw(thing, loc1)
            orig_x, orig_y = self.calculate_coords(loc1)
            new_x, new_y = self.calculate_coords(loc2)
            delta_x = int((new_x - orig_x) / FRAMES)
            delta_y = int((new_y - orig_y) / FRAMES)
            def moveme(delta_x, delta_y):
#do_anim 함수 내부에서는 FRAMES만큼 반복하면서 moveme 내부 함수를 호출하여 thing 객체의 이미지를 delta_x, delta_y만큼 이동
                self.canvas.move(the_image, delta_x, delta_y)
                self.canvas.update_idletasks()
            for i in range(FRAMES+1):
                self.canvas.after(i*10, moveme, delta_x, delta_y)
            self.canvas.after((FRAMES+5)*10,lambda:
                self.canvas.delete(the_image)) #10밀리초마다 canvas를 업데이트합니다. 이동이 끝난 후에는 the_image 객체를 삭제
        self.canvas.after(1, do_anim)

#이전에 그려진 모든 객체를 지우고, xy_env에서 받아온 thing과 그 위치(loc)를 사용하여 각 객체를 화면에 그림
    def draw_entire_environment(self):
        self.canvas.delete('thing')
        for thing, loc in self.xy_env.items():
            self.draw(thing, loc)

    def redraw_entire_environment(self):
        self.draw_entire_environment()

    def draw(self, thing, loc):#draw 함수는 하나의 thing과 그 위치(loc)를 받아와서, 이를 화면에 그리는 역할
        x, y = self.calculate_coords(loc)
        if self.SMALL:# thing 객체의 이미지 파일을 불러와서 화면에 표시
            basename = thing.image_filename.replace('.','_small.')
        else:
            basename = thing.image_filename
        filename = '{}/{}'.format(self.IMAGE_DIR,basename) #
        if filename not in self.image_cache:
            self.image_cache[filename] = tk.PhotoImage(file=filename)
        return self.canvas.create_image(x + self.square_width // 2,
            y + self.square_height // 2,
            image=self.image_cache[filename], tags='thing')#이미지 캐시(image_cache)에 저장

    def run_until(self, steps=1000):
        #steps 매개변수를 받아 게임이 실행되는 동안 self.total_steps 변수를 1씩 증가시키며 self.progress 라벨에 현재까지 실행된 횟수를 출력
        self.progress.set("Vroom! ({} steps)".format(self.total_steps))
        if self.total_steps > steps:
            self.still_running = False#self.still_running 변수가 False인 경우, 즉 steps 횟수가 지나면 게임 실행을 중단
        self.total_steps += 1
        if self.still_running:
            self.xy_env.step() 
            #self.xy_env.step() 함수를 호출하여 게임을 한 단계 실행
            self.score.set(str(self.xy_env.agents[0].performance
                    if self.xy_env.agents else '') + ' pts')
            #self.continuous 변수가 True이고 게임이 종료되지 않은 경우, 
            #self.delay 매개변수로 설정된 시간만큼 대기하고 run_until 함수를 재귀적으로 호출
            if self.continuous.get() and not self.xy_env.should_shutdown():
                self.root_window.after(int(self.delay.get()),
                    self.run_until,steps)
            elif self.continuous.get() and self.xy_env.should_shutdown():
                print('Finished in {} moves for a score of {}!'
                    .format(self.total_steps, self.score.get()))

    def _setup_graphics(self):
        self.root_window = tk.Tk() # tk.Tk()로 윈도우 창을 생성하고, 이를 저장 + 창의 배경 색상을 설정하고, 제목을 설정
        self.root_window.grid()
        self.root_window.title(self.title)
        self.root_window.config(background='white')

        self.progress = tk.StringVar() ; self.progress.set('') # GUI에서 진행 상황을 나타내는 라벨을 생성하고, 이를 저장합니다. 초기값은 빈 문자열("")
        ttk.Label(self.root_window,background='white',foreground='red',
            anchor='center', textvariable=self.progress).grid(
            row=2,column=0,columnspan=4)

        self.score = tk.StringVar() ; self.score.set('') #GUI에서 점수를 나타내는 라벨을 생성하고, 이를 저장합
        ttk.Label(self.root_window,background='white',foreground='blue',
            anchor='center', textvariable=self.score).grid(
            row=2,column=4,columnspan=1)
#ttk.Label, ttk.Entry, ttk.Button, ttk.Checkbutton를 사용하여 GUI의 버튼, 체크박스, 라벨 등을 생성하고 이를 배치
        ttk.Label(self.root_window,text='# iterations:',
            background='white').grid(row=1,column=0, sticky='e')

        num_iter_var = tk.IntVar() ; num_iter_var.set(200)

        ttk.Entry(self.root_window,textvariable=num_iter_var,width=5).grid(
            row=1,column=1,sticky='w')
        ttk.Button(self.root_window,text='Go',
            command=lambda : self.run_until(num_iter_var.get())).grid(
            row=1,column=2, sticky='W')
        self.continuous = tk.BooleanVar() #self.continuous: GUI에서 체크박스에 대한 불리언 값을 저장
        ttk.Checkbutton(self.root_window,text='Continuous',
            variable=self.continuous).grid(row=1,column=3)

        ttk.Label(self.root_window,text='delay (ms):',
            background='white').grid(row=1,column=4, sticky='e')
        self.delay = tk.StringVar() #self.delay: GUI에서 Spinbox로부터 딜레이 값을 저장
        tk.Spinbox(self.root_window,values=[10,50,100,500,1000],width=4,
            textvariable=self.delay).grid(row=1,column=5)
        self.delay.set(100)

        self.root_window.bind('<Return>', #self.root_window.bind(): <Return> 키가 눌리면 실행되는 콜백 함수를 등록
            lambda x: self.run_until(num_iter_var.get()))
        self.canvas = tk.Canvas(self.root_window,
            width=self.CANVAS_WIDTH, height=self.CANVAS_HEIGHT, bg='black')

        self.canvas.grid(row=0,column=0,columnspan=6,sticky='we') #self.canvas: GUI에서 캔버스를 생성하고 이를 저장
 
