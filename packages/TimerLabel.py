from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.properties import *
from kivy.app import App
from kivy.event import EventDispatcher

from datetime import datetime



class TimerLabel(Label):
    def __init__(self, **kwargs):
        self.clockObj=None
        self.__counter = 0                      # first tick occurs after 1 second
        self.__minutes_remaining=0
        self.__seconds_remaining=0
        self.__hours_remaining=0
        self.__minutes_elapsed=0
        self.__seconds_elapsed=0
        self.__hours_elapsed=0
        self._time_format_flag =True
        self.register_event_type('on_counter')
        super().__init__()                      # without this there are troubles with self.__counter


    time_begin= ObjectProperty(datetime.now())
    duration= NumericProperty(0.5) #duration in hours, minimum 0.5
    phase_duration = NumericProperty(0.0)
    phase = NumericProperty(1)
    remaining_time=StringProperty('')
    remaining_time_in_seconds = NumericProperty(0.0)
    elapsed_time = StringProperty('')
    format_time =StringProperty('---:--:--')
    end_phase = BooleanProperty(False)
    is_active = False
    infinite = False        # if True, timer never stops. Remember to set switchtimer (False) if you want stopwatch behavior!


    def read_counter(self, remaining_time, infinite):
        if remaining_time <= 0 and infinite is False:
            self.dispatch('on_counter')
        else:
            self.__counter+=1

    def on_counter(self):
        self.stop()
        self.reset()

    def switchtimer(self, force_flag):

        if force_flag is not None:
            self._time_format_flag = force_flag
        else:
            self._time_format_flag = not self._time_format_flag

    def reset(self):
        self.end_phase = True
        self.phase_duration = 0.0
        self.__counter=0

    def clear_text(self):
        self.format_time = '---:--:--'

    def reset_phase(self):
        self.phase = 1


    def update(self, dt):

        self.remaining_time_in_seconds= int((self.duration*3600)-self.__counter)

        if self.remaining_time_in_seconds <=0:
            self.remaining_time_in_seconds = 0


        self.__minutes_remaining, self.__seconds_remaining = divmod(self.remaining_time_in_seconds, 60)
        self.__hours_remaining, self.__minutes_remaining = divmod(self.__minutes_remaining, 60)

        self.__minutes_elapsed, self.__seconds_elapsed = divmod(self.__counter, 60)
        self.__hours_elapsed, self.__minutes_elapsed = divmod(self.__minutes_elapsed, 60)

        self.remaining_time ='-{:02.0f}:{:02.0f}:{:02.0f}'.format(self.__hours_remaining, self.__minutes_remaining, self.__seconds_remaining)

        self.elapsed_time= '+{:03.0f}:{:02.0f}:{:02.0f}'.format(self.__hours_elapsed, self.__minutes_elapsed, self.__seconds_elapsed)

        timer_view = {True: self.remaining_time, False: self.elapsed_time}

        self.format_time = timer_view.get(self._time_format_flag)

        self.read_counter(self.remaining_time_in_seconds, self.infinite)


    def start(self, phase):
        if self.clockObj is None:
            self.end_phase = False
            self.clockObj=Clock.create_trigger(self.update, 1,True)
            self.clockObj()
            self.is_active = True
            self.phase = phase


    def stop(self):
        if self.clockObj is not None:
            self.clockObj.cancel()
            print('Timer stopped!')
            self.clockObj = None
            self.is_active = False

