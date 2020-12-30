from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ObjectProperty
from pathlib import Path
from packages.ConfigModule import ConfigModule
from packages import Shared
from threading import Thread
import subprocess
import os
from kivy.clock import Clock



logger = ConfigModule.getLogger()

class Camera_Screen(Screen):
    standby_timer = None
    photo_taker = None
    info_text = StringProperty('')
    chamber_shot = ObjectProperty(None)
    photo_counter = 0
    photo_source = '/home/pi/chamber_shot'
    logger_err_flag = True


    def on_enter(self):
        self.logger_err_flag = True
        Shared.CHAMBER_LIGHT.value = 1
        if self.standby_timer is None:
            self.standby_timer = Clock.create_trigger(self.timer, 60)
            self.standby_timer()
        if self.photo_taker is None:
            self.photo_taker = Clock.create_trigger(self.take_photo, 1,True)
            self.photo_taker()


    def on_leave(self):
        Shared.CHAMBER_LIGHT.value = 0
        if self.standby_timer is not None:
            self.standby_timer.cancel()
            self.standby_timer = None
        if self.photo_taker is not None:
            self.photo_taker.cancel()
            self.photo_taker = None
        

    def timer(self, dt):
        self.parent.current = 'home_screen'

    def take_photo(self,dt):
            try:
                self.chamber_shot.reload() # refresh widget cache
                subprocess.Popen(["fswebcam", "-r", ConfigModule.camera_resolution, "--no-banner", self.photo_source], stdout=subprocess.PIPE)
                self.chamber_shot.source = self.photo_source
            except Exception as ex:
                if self.logger_err_flag == True:
                    logger.error(ex)
                    self.logger_err_flag = False



    def return_to_previous_screen(self, dt=0):
        if Shared.MEM_SCREEN.value == 2:
            self.parent.current = 'prestart_dashboard_screen'
        elif Shared.MEM_SCREEN.value == 4:
            self.parent.current = 'multiphase_dashboard_screen'
        else:
            self.parent.current = 'home_screen'