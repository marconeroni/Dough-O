from kivy.uix.screenmanager import Screen
from kivy.properties import *
from kivy.clock import Clock
from datetime import datetime

import calendar

from packages import Shared
from packages.FractionalSeparator import FloatToStringTuple
from packages.ConfigModule import ConfigModule
from packages.TempConverter import TempConverter


logger = ConfigModule.getLogger()

class PreStart_Set_Screen(Screen):

    fs = FloatToStringTuple()
    tc = TempConverter()

    temp_scale = ConfigModule.temp_scale

    month= datetime.now().month
    year = datetime.now().year

    T_min = ConfigModule.T_min_C
    T_max =  ConfigModule.T_max_C
    zero = 0.0

    temp_target_raw = zero              # float number
    temp_target_view = StringProperty('0')
    temp_target_decimal_view = StringProperty('0')
    year_start = NumericProperty(year)
    month_start = ObjectProperty(calendar.month_abbr[month])
    day_start = NumericProperty(datetime.now().day)
    hour_start = NumericProperty(datetime.now().hour)
    minute_start = NumericProperty(datetime.now().minute)

    start_date = datetime.now().strftime("%d %b %Y %H:%M")
    standby_timer = None

    def backhome(self):
        self.clear_all()


    def on_pre_enter(self):
        self.temp_target_raw = Shared.ACTUAL_TEMP_TARGET.value
        self.validate()

    def on_enter(self):
        Shared.MEM_SCREEN.value = 1
        if self.standby_timer is None:
            self.standby_timer = Clock.create_trigger(self.timer, 300)
            self.standby_timer()

    def on_leave(self):
        if self.standby_timer is not None:
            self.standby_timer.cancel()
            self.standby_timer = None

    def timer(self, dt):
        self.parent.current = 'home_screen'




    def increment_temp(self, direction):
        if ConfigModule.temp_scale == 'F':
            temp_increment = ConfigModule.temp_increment/1.8
        else:
            temp_increment = ConfigModule.temp_increment
        increment = {'+': temp_increment, '-': -temp_increment}
        self.temp_target_raw+= increment.get(direction)

        if self.temp_target_raw > self.T_max:
            self.temp_target_raw = self.zero

        if self.temp_target_raw < self.T_min:
            self.temp_target_raw = self.zero

        self.validate()


    def increment_year(self, direction):
        increment = {'+': 1, '-': -1}
        self.year_start+=increment.get(direction)
        self.validate()


    def increment_month(self, direction):
        increment = {'+': 1, '-': -1}
        self.month+=increment.get(direction)
        self.validate()


    def increment_day(self, direction):
        increment = {'+': 1, '-': -1}
        self.day_start+=increment.get(direction)
        self.validate()


    def increment_hour(self, direction):
        increment = {'+': 1, '-': -1}
        self.hour_start+=increment.get(direction)
        self.validate()


    def increment_minute(self, direction):
        increment = {'+': 1, '-': -1}
        self.minute_start+=increment.get(direction)
        self.validate()


#------------ VALIDATION SECTION ------------------------

    def validate(self):
        try:
            temp_target = self.tc.convert_only_F(self.temp_target_raw, ConfigModule.temp_scale)

            #Cannot use math.modf due to intrinsecally floating point error on fractional!!!!
            self.temp_target_view = self.fs.convert(temp_target)[0]
            self.temp_target_decimal_view = self.fs.convert(temp_target)[1]

            if self.month == 13: self.month=1
            if self.month == 0: self.month = 12
            if self.hour_start > 23 : self.hour_start = 0
            if self.hour_start <0: self.hour_start = 23
            if self.minute_start > 59: self.minute_start = 0
            if self.minute_start < 0: self.minute_start = 59

            if self.year_start > self.year+1 or self.year_start < self.year-1:
                self.year_start = self.year

            daysOfMonth = calendar.monthrange(self.year_start, self.month)[1]

            if self.day_start > daysOfMonth:
                self.day_start = 1
            if  self.day_start < 1:
                self.day_start = daysOfMonth

            self.month_start = calendar.month_abbr[self.month]

            self.start_date = datetime(self.year_start, self.month, self.day_start, self.hour_start, self.minute_start)

            now = datetime.now()
            if self.start_date < now:
                self.reset_calendar()

        except Exception as ex:
            logger.error(ex)



    def commit(self):
        Shared.ACTUAL_TEMP_TARGET.value = self.temp_target_raw  # Shared is float variable, then we pass raw value
        Shared.PRESTART_START_DATE =  self.start_date           # datetime type
        logger.info(f"SCHEDULED START TEMPERATURE TARGET: {self.temp_target_raw :.1f} C")
        logger.info(f"SCHEDULED START DATE: {self.start_date}")

    def reset_calendar(self):
        self.year_start = datetime.now().year
        self.month= datetime.now().month
        self.month_start = calendar.month_abbr[self.month]
        self.day_start = datetime.now().day
        self.hour_start = datetime.now().hour
        self.minute_start = datetime.now().minute
        self.start_date = datetime(self.year_start, self.month, self.day_start, self.hour_start, self.minute_start)


    def clear_all(self):
        self.reset_calendar()
        self.temp_target_raw = self.zero
        self.temp_target_view = '0'
        self.temp_target_decimal_view = '0'
        self.validate()
