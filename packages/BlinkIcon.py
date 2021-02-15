from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.image import Image
from kivy.clock import Clock

class BlinkIcon(ButtonBehavior,Image):

    source_disabled = ''
    source_off= ''
    source_on = ''
    anim_delay= 0.5

    def set_input_state(self, state, disabled = False):
        if disabled == False:
            if state == 0 or state >=400: # set 0 and >=400 values ok; icon not blink
                self.source = self.source_off
            else:
                self.source= self.source_on

        else:
            self.source = self.source_disabled

    def stop_blink(self):
        self.source = self.source_off
