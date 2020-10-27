from kivy.uix.screenmanager import Screen
from kivy.properties import *
from kivy.clock import Clock
import calendar
import locale
import time
from datetime import datetime
from datetime import timedelta
from packages import Shared
from packages.MultiPhaseDashBoardScreen import MultiPhase_DashBoard_Screen
from packages.ConfigModule import ConfigModule
from packages.TempConverter import TempConverter



class MultiPhase_Set_Screen(Screen):

    tc = TempConverter()
    temp_scale = ConfigModule.temp_scale

    T_min = ConfigModule.T_min_C     # key is a string, then we can use this trick for get values
    T_max = ConfigModule.T_max_C

    zero = 0.0
    zero_f = '{:.0f}'.format(zero)

    mindur = 0.0
    maxdur=  995
    increment = ConfigModule.time_increment
    standby_timer = None

    P1_temp_target= NumericProperty(zero)
    P2_temp_target= NumericProperty(zero)
    P3_temp_target= NumericProperty(zero)
    P4_temp_target= NumericProperty(zero)
    P5_temp_target= NumericProperty(zero)


    # I can observe property value variation with callback:
    # def on_P1_duration(self, instance, value):
    #    if(value <=0): self.P1_duration = 0.5
    # But in this case I prefer to add another dictionary comprehension in reset_all function

    P1_duration = NumericProperty(mindur+increment)
    P2_duration = NumericProperty(0.0)
    P3_duration = NumericProperty(0.0)
    P4_duration = NumericProperty(0.0)
    P5_duration = NumericProperty(0.0)
    mp_total_duration = NumericProperty(0.5)
    mp_time_end = ObjectProperty(datetime.now()+timedelta(hours=0.5))

    mp_btn1 = ObjectProperty(None)
    mp_btn2 = ObjectProperty(None)
    mp_btn3 = ObjectProperty(None)
    mp_btn4 = ObjectProperty(None)
    mp_btn5 = ObjectProperty(None)

    load_from_mem_flag = BooleanProperty(False)
    program_is_running = BooleanProperty(False)
    program = StringProperty('')
    actual_phase = NumericProperty(1)

    phase_temp_target_dict = {"1":zero, "2":zero, "3":zero, "4":zero, "5":zero}
    phase_duration_dict = {"1":mindur+increment, "2":mindur ,"3":mindur, "4":mindur, "5":mindur}


    def backhome(self):
        self.clear_all()     #clear all state button

    def on_enter(self):
        Shared.MEM_SCREEN.value = 3
        if self.standby_timer is None:
            self.standby_timer = Clock.create_trigger(self.timer, 300)
            self.standby_timer()

    def on_leave(self):
        if self.standby_timer is not None:
            self.standby_timer.cancel()
            self.standby_timer = None

    def timer(self, dt):
        self.parent.current = 'home_screen'

    def on_pre_enter(self):

        self.actual_phase = Shared.MP_ACTUAL_PHASE.value
        self.phase_temp_target_dict[Shared.MP_ACTUAL_PHASE.value] = Shared.ACTUAL_TEMP_TARGET.value

        self.program = Shared.PROGRAM[:25]
        self.program_is_running = Shared.MP_PROGRAM_IS_RUNNING # bool

        if Shared.MP_REMAINING_TIME <= 0 and Shared.MP_PROGRAM_IS_RUNNING == False and Shared.LOAD_FROM_MEM == False:    # clear all state if actual phase duration is 0
            self.clear_all()

        if Shared.LOAD_FROM_MEM == True:
            self.program = Shared.PROGRAM[:25]
            self.phase_temp_target_dict = Shared.MP_TEMP_TARGET_DICT
            self.phase_duration_dict = Shared.MP_DURATION_DICT
            self.load_from_mem_flag = True
            self.load_from_mem()
            Shared.LOAD_FROM_MEM = False        #reset flag
            self.load_from_mem_flag = False

        self.validate()


    def increment_temp(self, _phase):
        if ConfigModule.temp_scale == 'F':
            temp_increment = ConfigModule.temp_increment/1.8
        else:
            temp_increment = ConfigModule.temp_increment
        self.phase_temp_target_dict= {k:(v+temp_increment if k==str(_phase) and v < (self.T_max-temp_increment) else v) for (k,v) in self.phase_temp_target_dict.items() }
        self.validate()

    def decrement_temp(self, _phase):
        if ConfigModule.temp_scale == 'F':
            temp_increment = ConfigModule.temp_increment/1.8
        else:
            temp_increment = ConfigModule.temp_increment
        self.phase_temp_target_dict= {k:(v-temp_increment if k==str(_phase) and v > (self.T_min+temp_increment) else v) for (k,v) in self.phase_temp_target_dict.items() }
        self.validate()


    def increment_duration(self, _phase):
        self.phase_duration_dict= {k:(v+self.increment if k==str(_phase) and v < self.maxdur else v) for (k,v) in self.phase_duration_dict.items() }
        self.validate()


    def decrement_duration(self, _phase):
        self.phase_duration_dict= {k:(v-self.increment if k==str(_phase) and v > self.mindur+ self.increment else v) for (k,v) in self.phase_duration_dict.items() }
        self.validate()


    def clear_all(self):             # initial state in GUI screen: phase 1 mandatory and phase 2 selectable; other buttons disabled
        self.mp_btn1.state = 'down'
        self.mp_btn1.enabled = True
        self.mp_btn2.state = 'normal'
        self.mp_btn2.enabled = False
        self.mp_btn3.state = 'normal'
        self.mp_btn3.enabled = False
        self.mp_btn4.state = 'normal'
        self.mp_btn4.enabled = False
        self.mp_btn5.state = 'normal'
        self.mp_btn5.enabled = False
        self.reset_phase(0)
        self.validate()

    def reset_phase(self, _phase):          # pass <0> parameter reset all phases
        if self.load_from_mem_flag== False: # avoid to reset when load from memory
            self.phase_temp_target_dict= {k:(self.zero if k==str(_phase) or _phase ==0 else v) for (k,v) in self.phase_temp_target_dict.items() }
            self.phase_duration_dict = {k:(self.mindur if k==str(_phase) or _phase ==0 else v) for (k,v) in self.phase_duration_dict.items() }
            self.phase_duration_dict = {k:(self.mindur+ self.increment if k=="1" and v <=0 else v) for (k,v) in self.phase_duration_dict.items() } # when cycles end and we want to begin another program
            self.program = Shared.PROGRAM = ''
            self.validate()

        Shared.MP_ACTUAL_PHASE.value ='1' # is mandatory to reset phase in Shared variable

        self.validate()


    def load_from_mem(self):
        self.phase_temp_target_dict.update(Shared.MP_TEMP_TARGET_DICT) # copy Shared dictionary with program data
        self.phase_duration_dict.update(Shared.MP_DURATION_DICT)
        self.validate()



    def validate(self):

        self.P1_temp_target = self.phase_temp_target_dict.get('1')
        self.P2_temp_target = self.phase_temp_target_dict.get('2')
        self.P3_temp_target = self.phase_temp_target_dict.get('3')
        self.P4_temp_target = self.phase_temp_target_dict.get('4')
        self.P5_temp_target = self.phase_temp_target_dict.get('5')

        if ConfigModule.temp_scale == 'F':
            self.P1_temp_target = self.tc.c_to_f(self.P1_temp_target)
            self.P2_temp_target = self.tc.c_to_f(self.P2_temp_target)
            self.P3_temp_target = self.tc.c_to_f(self.P3_temp_target)
            self.P4_temp_target = self.tc.c_to_f(self.P4_temp_target)
            self.P5_temp_target = self.tc.c_to_f(self.P5_temp_target)

        self.P1_duration = self.phase_duration_dict.get('1')
        self.P2_duration = self.phase_duration_dict.get('2')
        self.P3_duration = self.phase_duration_dict.get('3')
        self.P4_duration = self.phase_duration_dict.get('4')
        self.P5_duration = self.phase_duration_dict.get('5')

        if self.P2_duration > self.mindur and self.program_is_running == False and Shared.LOAD_FROM_MEM == True:
            self.mp_btn2.disabled = False
            self.mp_btn2.state = 'down'

        if self.P3_duration > self.mindur and self.program_is_running == False and Shared.LOAD_FROM_MEM == True:
            self.mp_btn3.disabled = False
            self.mp_btn3.state = 'down'

        if self.P4_duration > self.mindur and self.program_is_running == False and Shared.LOAD_FROM_MEM == True:
            self.mp_btn4.disabled = False
            self.mp_btn4.state = 'down'

        if self.P5_duration > self.mindur and self.program_is_running == False and Shared.LOAD_FROM_MEM == True:
            self.mp_btn5.disabled = False
            self.mp_btn5.state = 'down'

        self.mp_total_duration = sum(self.phase_duration_dict.values())         #total duration in hours

        mp_total_seconds = self.mp_total_duration*3600                          #total duraction in seconds

        if Shared.MP_PROGRAM_IS_RUNNING == False:
            Shared.MP_TIMER_BEGIN = datetime.now()


        self.mp_time_end = Shared.MP_TIMER_BEGIN + timedelta(seconds=mp_total_seconds) #time end program/cycles; we must refer timer begin in multiphase dash
        Shared.MP_TOTAL_DURATION = self.mp_total_duration
        Shared.MP_TIME_END = self.mp_time_end
        Shared.MP_TEMP_TARGET_DICT = self.phase_temp_target_dict
        Shared.MP_DURATION_DICT = self.phase_duration_dict

    def commit(self): #deprecated
        #Shared.MP_TIMER_BEGIN = datetime.now()
        Shared.MP_TOTAL_DURATION = self.mp_total_duration
        Shared.MP_TIME_END = self.mp_time_end
        Shared.MP_TEMP_TARGET_DICT = self.phase_temp_target_dict
        Shared.MP_DURATION_DICT = self.phase_duration_dict
