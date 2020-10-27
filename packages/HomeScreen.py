from kivy.uix.screenmanager import Screen
from kivy.properties import *
from kivy.utils import escape_markup
from kivy.clock import Clock

from packages import Shared
from packages.ClockLabel import ClockLabel
from packages.ConfigModule import ConfigModule
from packages.BlinkIcon import BlinkIcon
from packages.Ping import ping
from packages.TempConverter import TempConverter
from packages.FractionalSeparator import FloatToStringTuple
from packages.OutStateImage import OutStateImage



logger = ConfigModule.getLogger()


class HS_Internet_Icon(BlinkIcon):
    source_on = './Icons/Internet_anim.zip'
    source_off = './Icons/internet_64.png'
    source_disabled = './Icons/internet_disabled_64.png'
    anim_delay=0.5

class HS_Power_icon(BlinkIcon):
    source_on = './Icons/Power_anim.zip'
    source_off = './Icons/blank_64.png'
    source_disabled = './Icons/blank_64.png'
    anim_delay=0.5


class Home_Screen(Screen):

    tc = TempConverter()
    fs = FloatToStringTuple()
    btnwifi_state = True
    clockObj = None
    menuIconClock = None
    ping = ping()
    ping.ip = ConfigModule.ubidots_ip
    outimage = OutStateImage()


    temp_meas = StringProperty('0')
    temp_meas_decimal = StringProperty('0')
    temp_ext = NumericProperty(0.0)
    main_clock_date = ObjectProperty(None)
    main_clock_time = ObjectProperty(None)
    main_clock_seconds = ObjectProperty(None)
    btn_prestart = ObjectProperty (None)
    btn_multiphase = ObjectProperty(None)
    btn_load_from_mem = ObjectProperty(None)
    wifi_icon = ObjectProperty(None)
    speaker_icon = ObjectProperty(None)
    log_icon = ObjectProperty(None)
    hs_power_icon = ObjectProperty(None)
    wi_fi_data = StringProperty('')
    cpu_temp = StringProperty('--.-')
    cpu_temp_float = NumericProperty(0.0)
    hs_internet_icon = ObjectProperty(None)
    hs_img_out_state = StringProperty('')       # reference to dynamic image state dashboard
    hs_img_out_label = StringProperty('')


    def update_temp(self, dt):
        # disable interface when exception is detected at config startup
        if Shared.EXCEPTION_STRING != '':
            self.main_clock_date.stop()
            self.main_clock_date.text = '[font=Aldrich][b][color=#850900][size=20]'+ escape_markup(Shared.EXCEPTION_STRING)+'[/font][/size][/color][/b]'
            self.main_clock_time.text = '!!:!!'
            self.main_clock_seconds.text = '!!'
            self.btn_prestart.disabled = True
            self.btn_multiphase.disabled = True
            self.btn_load_from_mem.disabled = True
            Shared.reset_all(Shared)
            return

        temp_meas_raw = self.tc.convert_only_F(Shared.TEMP_MEAS.value, ConfigModule.temp_scale)
        self.temp_ext = self.tc.convert_only_F(Shared.TEMP_EXT.value, ConfigModule.temp_scale)

        self.temp_meas, self.temp_meas_decimal= self.fs.convert(temp_meas_raw)
        self.wi_fi_data = ConfigModule.wifi_strength()
        self.hs_img_out_state, self.hs_img_out_label= self.outimage.set_image(Shared.IO_STATUS_CODE.value, True)
        #if Shared.IO_STATUS_CODE.value > 100:
            #self.hs_img_out_state, self.hs_img_out_label= self.outimage.set_image(f"{Shared.IO_STATUS_CODE.value}", True)
        #else:
            #self.hs_img_out_state, self.hs_img_out_label= self.outimage.set_image(f"{Shared.COMPRESSOR_STATE.value}{Shared.LO_HEATER_STATE.value}{Shared.HI_HEATER_STATE.value}", True)


    def set_menu_icon(self,dt):
        self.hs_internet_icon.set_input_state(self.ping.return_value)
        self.hs_power_icon.set_input_state(Shared.POWER_STATUS_CODE.value)

        if ConfigModule.wi_fi == True:
            self.wifi_icon.source= './Icons/wifi2_64.png'
        else:
            self.wifi_icon.source= './Icons/wifi2_disabled_64.png'


        if ConfigModule.sound_volume == 0 and Shared.BUZZ_ENABLE.value == False:
            self.speaker_icon.source ='./Icons/speaker_disabled_64.png'
        else:
            self.speaker_icon.source = './Icons/speaker_64.png'


        if ConfigModule.log is True:
            self.log_icon.source = './Icons/log_64.png'
        else:
            self.log_icon.source = './Icons/log_disabled_64.png'

        self.cpu_temp, self.cpu_temp_float = ConfigModule.read_cpu_temp(ConfigModule.temp_scale)
        Shared.CPU_TEMP.value = self.cpu_temp_float


    def on_enter(self):
        Shared.MEM_SCREEN.value = 0
        Shared.HOME = True #this is a Shared set flag for tracking home transition. When back home, set True and force methods in all dashboards to stop/clear states
        self.hs_img_out_state, self.hs_img_out_label= self.outimage.set_image(Shared.IO_STATUS_CODE.value, True)
        Shared.reset_all(Shared)

        self.ping.start()

        if self.menuIconClock is None:
            self.menuIconClock=Clock.create_trigger(self.set_menu_icon, 3,True)
            self.menuIconClock()

        if self.clockObj is None:
            self.clockObj = Clock.create_trigger(self.update_temp, 1, True)
            self.clockObj()

    
        


    def on_leave(self):
        self.ping.stop()
        Shared.BUZZER.value = 0
        Shared.HOME = False
        if self.clockObj is not None:
            self.clockObj.cancel()
            self.clockObj = None

        if self.menuIconClock is not None:
            self.menuIconClock.cancel()
            self.menuIconClock = None


