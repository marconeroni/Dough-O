from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ObjectProperty
from pathlib import Path
from packages.ConfigModule import ConfigModule
from packages import Shared
from threading import Thread
import subprocess
import time
from kivy.clock import Clock



logger = ConfigModule.getLogger()

class Camera_Screen(Screen):
    standby_timer = None
    photo_taker = None
    photo_loader = None
    info_text = StringProperty('')
    chamber_shot = ObjectProperty(None)
    photo_counter = 0
    photo_name = "chamber_shot"


    def on_enter(self):
        if self.standby_timer is None:
            self.standby_timer = Clock.create_trigger(self.timer, 120)
            self.standby_timer()
        if self.photo_taker is None:
            self.photo_taker = Clock.create_trigger(self.take_photo, 2,True)
            self.photo_taker()
        if self.photo_loader is None:
            self.photo_loader = Clock.create_trigger(self.load_photo, 2.5,True)
            self.photo_loader()


    def on_leave(self):
        if self.standby_timer is not None:
            self.standby_timer.cancel()
            self.standby_timer = None
        if self.photo_taker is not None:
            self.photo_taker.cancel()
            self.photo_taker = None
        if self.photo_loader is not None:
            self.photo_loader.cancel()
            self.photo_loader = None

    def timer(self, dt):
        self.parent.current = 'home_screen'

    def take_photo(self,dt):
            try:
                if self.photo_counter < 1:
                    self.photo_counter+=1
                else:
                    self.photo_counter = 0
                self.photo_name = f"chamber_shot_{self.photo_counter}"
                subprocess.run(["fswebcam", "-r", "1280x720", self.photo_name])
            except Exception as ex:
                logger.error(ex)


    def load_photo(self,dt):
        try:
            photo_source = f"/home/pi/{self.photo_name}"
            self.chamber_shot.source = photo_source
        except Exception as ex:
            logger.error(ex)


    def return_to_previous_screen(self, dt=0):
        if Shared.MEM_SCREEN.value == 2:
            self.parent.current = 'prestart_dashboard_screen'
        elif Shared.MEM_SCREEN.value == 4:
            self.parent.current = 'multiphase_dashboard_screen'
        else:
            self.parent.current = 'home_screen'