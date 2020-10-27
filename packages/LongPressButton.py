from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.uix.button import Button
from kivy.base import runTouchApp
from kivy.factory import Factory

class LongPressButton(Factory.Button):
    __events__ = ('on_long_press', )

    long_press_time = Factory.NumericProperty(0.4) # do not go below this value on raspberry with TFT 

    def on_state(self, instance, value):
        if value == 'down':
            lpt = self.long_press_time
            self._clockev = Clock.create_trigger(self._do_long_press, lpt, True) #self._clockev = Clock.schedule_once(self._do_long_press, lpt)
            self._clockev()
        else:
            self._clockev.cancel()

    def _do_long_press(self, dt):
        self.dispatch('on_long_press')

    def on_long_press(self, *largs):
        pass