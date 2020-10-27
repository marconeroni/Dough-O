from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty
from kivy.clock import Clock
from packages.ConfigModule import ConfigModule





class Info_Screen(Screen):
    standby_timer = None
    info_text = StringProperty('')

    def on_enter(self):
        if self.standby_timer is None:
            self.standby_timer = Clock.create_trigger(self.timer, 120)
            self.standby_timer()

    def on_leave(self):
        if self.standby_timer is not None:
            self.standby_timer.cancel()
            self.standby_timer = None

    def timer(self, dt):
        self.parent.current = 'home_screen'

    def on_pre_enter(self):
        try:
            info_path = ConfigModule.app_dir / 'Readme.txt'
            with open(info_path, 'r') as info_text:
                self.info_text = info_text.read()
        except Exception as err:
            self.info_text = f"{repr(err)}"