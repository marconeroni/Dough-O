from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from pathlib import Path
from packages.ConfigModule import ConfigModule
from packages import Shared
from kivy.app import App
from kivy.clock import Clock


class Log_Screen(Screen):
    standby_timer = None
    reading_timer = None
    log_text = StringProperty('')

    def on_enter(self):

        if self.standby_timer is None:
            self.standby_timer = Clock.create_trigger(self.return_to_previous_screen, 300)
            self.standby_timer()
        if self.reading_timer is None:
            self.reading_timer = Clock.create_trigger(self.read_log, 2, True)
            self.reading_timer()


    def on_leave(self):

        if self.standby_timer is not None:
            self.standby_timer.cancel()
            self.standby_timer = None
        if self.reading_timer is not None:
            self.reading_timer.cancel()

    def on_pre_enter(self):
        self.read_log()

    def read_log(self,dt = 0):
        try:
            io_log=''
            io_log_path = Path(ConfigModule.log_io_filepath).resolve()
            net_log=''
            net_log_path = Path(ConfigModule.NET_log_filepath).resolve()
            
            with open(io_log_path, 'r') as log_text:
                io_log = log_text.read()

            with open(net_log_path, 'r') as log_text:
                net_log = log_text.read()
            self.log_text = f"{io_log}\n{net_log}"
        except Exception as err:
            self.log_text = f"{repr(err)}"



    def return_to_previous_screen(self, dt=0):

        if Shared.MEM_SCREEN.value == 2:
            self.parent.current = 'prestart_dashboard_screen'
        elif Shared.MEM_SCREEN.value == 4:
            self.parent.current = 'multiphase_dashboard_screen'
        else:
            self.parent.current = 'home_screen'
