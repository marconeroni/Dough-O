from kivy.clock import Clock
from kivy.uix.label import Label
from kivy.properties import StringProperty
from datetime import datetime


class ClockLabel(Label):
    def __init__(self,**kwargs):
        super().__init__()
        self.start()

    ClockObj = None
    time_now = StringProperty('')
    date_now= StringProperty('')
    time_now_mills= StringProperty('')
    seconds_now= StringProperty('')
    time_now_seconds= StringProperty('')
    date_now_short= StringProperty('')
    is_running = True

    def start(self):
        if self.ClockObj is None:
            self.ClockObj= Clock.create_trigger(self.update, 0.5, True)
            self.ClockObj()
            self.is_running = True

    def stop(self):
        if self.ClockObj is not None:
            self.ClockObj.cancel()
            self.ClockObj = None
            self.is_running = False

    def update(self, dt):
        time_n=datetime.now()
        self.time_now_mills = (time_n.strftime("%d/%m/%Y, %H:%M:%S.%f")[:-4])
        self.time_now_seconds = (time_n.strftime("%d/%m/%Y  %H:%M:%S"))
        self.seconds_now = (time_n.strftime("%S"))
        self.time_now= (time_n.strftime("%H:%M"))
        self.date_now = (time_n.strftime("%a %d %b %Y"))
        self.date_now_short = (time_n.strftime("%d %b %Y"))