from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.clock import Clock
from kivy.app import App

from packages.Chart import ChartWidget
from packages.TempConverter import TempConverter
from packages.FractionalSeparator import FloatToStringTuple
from packages.TimerLabel import TimerLabel
from packages.BlinkIcon import BlinkIcon
from packages.ConfigModule import ConfigModule
from packages.OutStateImage import OutStateImage
from packages.Ping import ping
from packages.Audio import PlaySound
from packages import Shared
from packages import IOInterface
from packages.IoTCloud import UbidotsConnect
from packages.NotifyHelper import NotifyHelper

from datetime import datetime
import time

logger = ConfigModule.getLogger()
io_logger = ConfigModule.getIOLogger()

class PS_IORun_Icon(BlinkIcon):
    source_on = './Icons/IORunIcon.zip'
    source_off = './Icons/IORunIcon_off.png'
    anim_delay=1

class PS_Cloud_Icon(BlinkIcon):
    source_on = './Icons/PingIcon_anim.zip'
    source_off = './Icons/cloud_64.png'
    source_disabled = './Icons/cloud_disabled_64.png'
    anim_delay=0.5

class PS_Internet_Icon(BlinkIcon):
    source_on = './Icons/Internet_anim.zip'
    source_off = './Icons/internet_64.png'
    source_disabled = './Icons/internet_disabled_64.png'
    anim_delay=0.5

class PS_Power_Icon(BlinkIcon):
    source_on = './Icons/Power_anim.zip'
    source_off = './Icons/blank_64.png'
    source_disabled = './Icons/blank_64.png'
    anim_delay=0.5

class PS_Compressor_Icon(BlinkIcon):
    source_on = './Icons/Compressor_anim.zip'
    source_off = './Icons/blank_64.png'
    source_disabled = './Icons/blank_64.png'
    anim_delay=0.3

class PrestartChart(ChartWidget):
    temp_scale= ConfigModule.temp_scale
    y_axis_max = ConfigModule.T_max_C         # compute all stuffs in Celsius unit. Conversions are made lazy
    y_axis_min = ConfigModule.T_min_C

class PSTimerLabel(TimerLabel):
    pass

class PreStart_DashBoard_Screen(Screen):

    tc = TempConverter()
    fs = FloatToStringTuple()
    ping = ping()
    ping.ip = ConfigModule.ubidots_ip
    start_program_audio = PlaySound()
    start_program_audio.source = ConfigModule.sounds_dir / ConfigModule.start_program_audio
    warning = PlaySound()
    warning.source = ConfigModule.sounds_dir / ConfigModule.warning_audio

    prestart_start_date=  StringProperty(Shared.PRESTART_START_DATE.strftime("%d %b %Y %H:%M"))
    temp_meas = StringProperty('0')
    temp_meas_decimal = StringProperty('0')
    temp_target_view = StringProperty('0')
    temp_target_decimal_view = StringProperty('0')
    temp_ext = NumericProperty(0)

    chart_data = NumericProperty(0)
    target_line = ObjectProperty([]*4)          # target temperature dynamic line (4 coordinates)


    ps_img_out_state = StringProperty('')       # reference to dynamic image state dashboard
    ps_img_out_label = StringProperty('')       # reference to out state label
    ps_temp_chart = ObjectProperty(None)        # reference to chart in kv file
    ps_lbl_timer = ObjectProperty(None)
    lbl_bell = ObjectProperty(None)
    ps_blink_icon = ObjectProperty(None)
    ps_wifi_toggle_btn= ObjectProperty(None)    # toggle icon button
    ps_cloud_icon = ObjectProperty(None)
    ps_internet_icon = ObjectProperty(None)
    ps_power_icon = ObjectProperty(None)
    ps_sound_toggle_btn = ObjectProperty(None)
    PS_compressor_icon = ObjectProperty(None)
    cpu_temp = StringProperty('--.-')
    cpu_temp_float = NumericProperty(0.0)
    output_status_code = NumericProperty(0)
    clockObj = None                             # kivy clock object

    outimage = OutStateImage()
    toggle_btn_states = {True: 'normal', False: 'down'}
    program_is_running = False
    ubidotsconnect = UbidotsConnect()
    notify_helper = NotifyHelper()


    def on_enter(self):
        Shared.MEM_SCREEN.value = 2


    def on_pre_enter(self):
        app = App.get_running_app()
        program_details = '{}'.format(app.prestart_dash_title)
        Shared.PROGRAM_DETAILS.value = bytes(program_details.encode())[:100]
        self.ps_img_out_state, self.ps_img_out_label= self.outimage.set_image(Shared.IO_STATUS_CODE.value, True)

        self.ps_internet_icon.set_input_state(self.ping.return_value, disabled = not ConfigModule.wi_fi)
        self.ps_cloud_icon.set_input_state(Shared.SERVER_STATUS.value, disabled = not ConfigModule.cloud) #connect to ubidots server response
        self.ps_power_icon.set_input_state(Shared.POWER_STATUS_CODE.value)
        self.ps_compressor_icon.set_input_state(Shared.COMPRESSOR_PROTECTION_CODE.value)
        sound = False if (ConfigModule.sound_volume == 0 and ConfigModule.buzzer == False) else True
        self.ps_sound_toggle_btn.state = self.toggle_btn_states.get(sound)
        self.ps_wifi_toggle_btn.state = self.toggle_btn_states.get(ConfigModule.wi_fi)
        self.ps_blink_icon.stop_blink()
        self.ubidotsconnect.start_iot_communication(ConfigModule.cloud)
        self.ping.start()
        self.ps_lbl_timer.switchtimer(False)    # set stopwatch format
        self.ps_lbl_timer.infinite = True       # it never stops


        if self.clockObj is None and Shared.IO_STATUS_CODE.value < 200:
            self.clockObj=Clock.create_trigger(self.update, 1, True)
            self.clockObj()
            self.ps_temp_chart.draw()

        now = datetime.now()
        if  Shared.PRESTART_START_DATE >= now:
            self.ps_lbl_timer.format_time = Shared.PRESTART_START_DATE.strftime("%d %b %Y %H:%M")
            self.ps_lbl_timer.stop()
            self.ps_lbl_timer.reset()
            self.lbl_bell.source = './Icons/bell_128.png'


        temp_target = self.tc.convert_only_F(Shared.ACTUAL_TEMP_TARGET.value, ConfigModule.temp_scale)
        self.temp_target_view = self.fs.convert(temp_target)[0]
        self.temp_target_decimal_view = self.fs.convert(temp_target)[1]

    def on_leave(self):
        self.ping.stop()
        self.ubidotsconnect.stop_iot_communication()

    def switch_wifi(self, enable):
        ConfigModule.wi_fi = enable
        ConfigModule.aswitch_wifi(enable)

    def stop_all(self, on_error= False):
        self.ps_lbl_timer.stop()
        self.ps_lbl_timer.reset()
        self.ps_lbl_timer.reset_phase()
        self.ps_temp_chart.stop_draw()
        self.ps_temp_chart.resize_image()
        Shared.BUZZER.value = 0
        if self.clockObj is not None:
            self.clockObj.cancel()
            self.clockObj = None
        self.ps_blink_icon.stop_blink()
        self.program_is_running = Shared.PS_PROGRAM_IS_RUNNING = False
        Shared.ENABLE_OUTPUT.value = 0
        Shared.PRGM_STATUS_CODE.value = 150


    def mute_audio(self):
        ConfigModule.mem_volume = ConfigModule.sound_volume
        ConfigModule.mem_buzzer = ConfigModule.buzzer
        ConfigModule.sound_volume = 0
        ConfigModule.buzzer = Shared.BUZZ_ENABLE.value = False
        logger.info(f"volume mute")

    def restore_audio(self):
        ConfigModule.sound_volume = ConfigModule.mem_volume
        ConfigModule.buzzer = Shared.BUZZ_ENABLE.value = ConfigModule.mem_buzzer
        logger.info(f"volume restored: {ConfigModule.sound_volume}")

    def update(self, dt):

        self.ps_power_icon.set_input_state(Shared.POWER_STATUS_CODE.value)
        self.target_line = self.ps_temp_chart.draw_target_line(Shared.ACTUAL_TEMP_TARGET.value)
        self.ps_blink_icon.set_input_state(Shared.COMPRESSOR_STATE.value or Shared.LO_HEATER_STATE.value or Shared.HI_HEATER_STATE.value)
        self.ps_compressor_icon.set_input_state(Shared.COMPRESSOR_PROTECTION_CODE.value)
        self.ps_img_out_state, self.ps_img_out_label  = self.outimage.set_image(Shared.IO_STATUS_CODE.value, True)
        ConfigModule.ethernet = self.ping.connected

        if  Shared.IO_STATUS_CODE.value > 100:
            self.warning.set_volume(100 if ConfigModule.buzzer == False else 0, control = ConfigModule.numid, card = ConfigModule.card_num)
            self.warning.aplay(100 if ConfigModule.buzzer == False else 0, card = ConfigModule.card_num)
            Shared.BUZZ_ENABLE.value = ConfigModule.buzzer
            Shared.BUZZER.value = 3
            self.stop_all()

        self.ps_wifi_toggle_btn.state = self.toggle_btn_states.get(ConfigModule.wi_fi)
        self.ps_cloud_icon.set_input_state(Shared.SERVER_STATUS.value, disabled = not ConfigModule.cloud)
        self.ps_internet_icon.set_input_state(self.ping.return_value)
        self.cpu_temp, self.cpu_temp_float = ConfigModule.read_cpu_temp(ConfigModule.temp_scale)
        Shared.CPU_TEMP.value = self.cpu_temp_float


        if datetime.now()>= Shared.PRESTART_START_DATE and Shared.IO_STATUS_CODE.value < 200:

            if self.program_is_running == False:
                self.start_program_audio.set_volume(ConfigModule.sound_volume, not ConfigModule.buzzer,control = ConfigModule.numid, card = ConfigModule.card_num)
                self.start_program_audio.play(ConfigModule.sound_volume, not ConfigModule.buzzer, card = ConfigModule.card_num, delay = 0.5)
                Shared.BUZZER.value = 7 # long beep
                Shared.PRGM_STATUS_CODE.value = 110

            logger.info('PROGRAM RUNNING')
            self.lbl_bell.source = './Icons/sand_clock_128.png'
            self.ps_lbl_timer.start(1)

            Shared.ENABLE_OUTPUT.value = 1 if Shared.POWER_STATUS_CODE.value < 350 else 0
            self.program_is_running = True

        elif datetime.now()< Shared.PRESTART_START_DATE and Shared.IO_STATUS_CODE.value < 200:
            Shared.PRGM_STATUS_CODE.value = 100 # program pending
            Shared.ENABLE_OUTPUT.value = 0
            self.program_is_running = False

        else:
            #Shared.PRGM_STATUS_CODE.value = 100 # program pending
            Shared.ENABLE_OUTPUT.value = 0
            self.program_is_running = False

        if Shared.HOME == True:
           self.ps_lbl_timer.clear_text()
           self.stop_all()
           return

        self.chart_data = Shared.TEMP_MEAS.value


        Shared.REMAINING_TIME_FMT.value= bytes(self.ps_lbl_timer.format_time.encode())[:30]

        temp_meas = self.tc.convert_only_F(Shared.TEMP_MEAS.value, ConfigModule.temp_scale)
        self.temp_meas = self.fs.convert(temp_meas)[0]
        self.temp_meas_decimal = self.fs.convert(temp_meas)[1]
        self.temp_ext = self.tc.convert_only_F(Shared.TEMP_EXT.value, ConfigModule.temp_scale)
        self.output_status_code = Shared.IO_STATUS_CODE.value


