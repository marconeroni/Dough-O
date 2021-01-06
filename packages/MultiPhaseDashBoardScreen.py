from kivy.uix.screenmanager import Screen
from kivy.properties import *
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.app import App

from datetime import datetime, timedelta

from packages.BlinkIcon import BlinkIcon
from packages.Chart import ChartWidget
from packages import IOInterface
from packages import Shared
from packages.TimerLabel import TimerLabel
from packages.FractionalSeparator import FloatToStringTuple
from packages.TempConverter import TempConverter
from packages.OutStateImage import OutStateImage
from packages.Audio import PlaySound
from packages.ConfigModule import ConfigModule
from packages.Ping import ping
from packages.IoTCloud import UbidotsConnect


logger = ConfigModule.getLogger()

class MPBlinkIcon(BlinkIcon):
    source_on = './Icons/IORunIcon.zip'
    source_off = './Icons/IORunIcon_off.png'
    anim_delay=1

class MP_Cloud_Icon(BlinkIcon):
    source_on = './Icons/PingIcon_anim.zip'
    source_off = './Icons/cloud_64.png'
    source_disabled = './Icons/cloud_disabled_64.png'
    anim_delay=0.5

class MP_Internet_Icon(BlinkIcon):
    source_on = './Icons/Internet_anim.zip'
    source_off = './Icons/internet_64.png'
    source_disabled = './Icons/internet_disabled_64.png'
    anim_delay=0.5

class MP_Power_icon(BlinkIcon):
    source_on = './Icons/Power_anim.zip'
    source_off = './Icons/blank_64.png'
    source_disabled = './Icons/blank_64.png'
    anim_delay=0.5

class MP_Compressor_Icon(BlinkIcon):
    source_on = './Icons/Compressor_anim.zip'
    source_off = './Icons/blank_64.png'
    source_disabled = './Icons/blank_64.png'
    anim_delay=0.3

class MultiPhaseChart(ChartWidget):
    temp_scale= ConfigModule.temp_scale
    y_axis_max = ConfigModule.T_max_C         # compute all stuffs in Celsius unit. Conversions are calculated subsequently
    y_axis_min = ConfigModule.T_min_C

class MPTimerLabel(TimerLabel):
    def __init__(self, **kwargs):
        super().__init__()

class MultiPhase_DashBoard_Screen(Screen):
    tc = TempConverter()
    fs = FloatToStringTuple()
    crossphase_sound = PlaySound()
    crossphase_sound.source = ConfigModule.sounds_dir / ConfigModule.cross_phase_audio
    endprogram_sound = PlaySound()
    endprogram_sound.source = ConfigModule.sounds_dir / ConfigModule.end_program_audio
    warning = PlaySound()
    warning.source = ConfigModule.sounds_dir / ConfigModule.warning_audio
    start_program_audio = PlaySound()
    start_program_audio.source = ConfigModule.sounds_dir / ConfigModule.start_program_audio
    ping = ping()
    ping.ip = ConfigModule.ubidots_ip

    temp_scale = ConfigModule.temp_scale
    cpu_temp = StringProperty('--.-')
    cpu_temp_float = NumericProperty(0.0)
    output_status_code = NumericProperty(0)


    mp_temp_chart = ObjectProperty(None) #link to chart in kv file
    mp_chart_data = NumericProperty(0)

    mp_img_out_state = StringProperty('')
    mp_img_out_label = StringProperty('')

    lbl_timer = ObjectProperty(None)
    icon_timer = ObjectProperty(None)

    temp_meas = StringProperty('0')
    temp_meas_decimal = StringProperty('0')

    actual_temp_target_raw = 0
    actual_temp_target = StringProperty('0')
    actual_temp_target_decimal = StringProperty('0')


    P1_temp_target = NumericProperty(0)
    P2_temp_target = NumericProperty(0)
    P3_temp_target = NumericProperty(0)
    P4_temp_target = NumericProperty(0)
    P5_temp_target = NumericProperty(0)

    P1_duration = NumericProperty(0.5)
    P2_duration = NumericProperty(0.0)
    P3_duration = NumericProperty(0.0)
    P4_duration = NumericProperty(0.0)
    P5_duration = NumericProperty(0.0)

    total_duration = NumericProperty(0.5)

    actual_phase = StringProperty('')
    actual_phase_duration = NumericProperty(0.5)

    target_line = ObjectProperty([]*4)
    temp_ext = NumericProperty(0.0)
    temp_ext_decimal = NumericProperty(0.0)

    timerlabel = StringProperty('')
    time_end = StringProperty('')

    program = StringProperty('')
    program_is_running = BooleanProperty(True)

    mp_blink_icon = ObjectProperty(None)                    # reference to blink icon
    mp_wifi_toggle_btn = ObjectProperty(None)
    mp_sound_toggle_btn = ObjectProperty(None)
    mp_internet_icon: ObjectProperty(None)
    mp_cloud_icon: ObjectProperty(None)
    mp_power_icon = ObjectProperty(None)
    MP_compressor_icon = ObjectProperty(None)


    clockObj = None

    outimage = OutStateImage()
    toggle_btn_states = {True: 'normal', False: 'down'}
    ubidotsconnect = UbidotsConnect()


    def on_pre_enter(self):
        self.mp_img_out_state,self.mp_img_out_label= self.outimage.set_image(Shared.IO_STATUS_CODE.value, Shared.MP_REMAINING_TIME.value)
        self.mp_internet_icon.set_input_state(self.ping.return_value, disabled = not not (ConfigModule.wi_fi or ConfigModule.ethernet))
        self.mp_cloud_icon.set_input_state(Shared.SERVER_STATUS.value, disabled = not ConfigModule.cloud)
        self.mp_power_icon.set_input_state(Shared.POWER_STATUS_CODE.value)
        self.mp_compressor_icon.set_input_state(Shared.COMPRESSOR_PROTECTION_CODE.value)
        sound = False if (ConfigModule.sound_volume == 0 and ConfigModule.buzzer == False)  else True
        self.mp_sound_toggle_btn.state = self.toggle_btn_states.get(sound)
        self.mp_wifi_toggle_btn.state = self.toggle_btn_states.get(ConfigModule.wi_fi)
        self.mp_blink_icon.stop_blink()
        self.ubidotsconnect.start_iot_communication(ConfigModule.cloud)
        self.ping.start()



    def on_enter(self):
        Shared.MEM_SCREEN.value = 4
        self.P1_temp_target = Shared.MP_TEMP_TARGET_DICT.get('1')
        self.P2_temp_target = Shared.MP_TEMP_TARGET_DICT.get('2')
        self.P3_temp_target = Shared.MP_TEMP_TARGET_DICT.get('3')
        self.P4_temp_target = Shared.MP_TEMP_TARGET_DICT.get('4')
        self.P5_temp_target = Shared.MP_TEMP_TARGET_DICT.get('5')

        if ConfigModule.temp_scale =='F':
            self.P1_temp_target = self.tc.c_to_f(Shared.MP_TEMP_TARGET_DICT.get('1'))
            self.P2_temp_target = self.tc.c_to_f(Shared.MP_TEMP_TARGET_DICT.get('2'))
            self.P3_temp_target = self.tc.c_to_f(Shared.MP_TEMP_TARGET_DICT.get('3'))
            self.P4_temp_target = self.tc.c_to_f(Shared.MP_TEMP_TARGET_DICT.get('4'))
            self.P5_temp_target = self.tc.c_to_f(Shared.MP_TEMP_TARGET_DICT.get('5'))

        self.P1_duration = Shared.MP_DURATION_DICT.get('1')
        self.P2_duration = Shared.MP_DURATION_DICT.get('2')
        self.P3_duration = Shared.MP_DURATION_DICT.get('3')
        self.P4_duration = Shared.MP_DURATION_DICT.get('4')
        self.P5_duration = Shared.MP_DURATION_DICT.get('5')

        #self.time_end = Shared.MP_TIME_END.strftime("%d/%b/%y %H:%M:%S")
        self.program_is_running = Shared.MP_PROGRAM_IS_RUNNING = True
        self.lbl_timer.duration = self.actual_phase_duration = Shared.MP_ACTUAL_PHASE_DURATION.value = Shared.MP_DURATION_DICT.get(str(self.lbl_timer.phase))
        Shared.ACTUAL_TEMP_TARGET.value = Shared.MP_TEMP_TARGET_DICT.get(str(self.lbl_timer.phase))
        actual_temp_target_view = self.tc.convert_only_F(Shared.ACTUAL_TEMP_TARGET.value, ConfigModule.temp_scale)
        self.actual_temp_target = self.fs.convert(actual_temp_target_view)[0]
        self.actual_temp_target_decimal = self.fs.convert(actual_temp_target_view)[1]

        self.total_duration = Shared.MP_TOTAL_DURATION

        self.program = Shared.PROGRAM[:25]

        if self.clockObj is None and Shared.IO_STATUS_CODE.value < 200:
            self.clockObj=Clock.create_trigger(self.update, 0.5, True)
            self.program_is_running = Shared.MP_PROGRAM_IS_RUNNING = True
            self.clockObj()
            self.mp_temp_chart.draw()


        if self.lbl_timer.is_active == False and Shared.IO_STATUS_CODE.value < 200:#self.outimage.warning == False:
            self.lbl_timer.start(self.lbl_timer.phase)
            if self.lbl_timer.phase == 1:
                self.start_program_audio.set_volume(ConfigModule.sound_volume, not ConfigModule.buzzer, control = ConfigModule.numid,card = ConfigModule.card_num)
                self.start_program_audio.play(ConfigModule.sound_volume, not ConfigModule.buzzer, card = ConfigModule.card_num)
                Shared.BUZZER.value = 7


    def switch_wifi(self, enable):
        ConfigModule.wi_fi = enable
        ConfigModule.aswitch_wifi(enable)


    def mute_audio(self):
        ConfigModule.mem_volume = ConfigModule.sound_volume
        ConfigModule.sound_volume = 0
        ConfigModule.buzzer = Shared.BUZZ_ENABLE.value = False
        logger.info(f"volume mute")

    def restore_audio(self):
        ConfigModule.sound_volume = ConfigModule.mem_volume
        ConfigModule.buzzer = Shared.BUZZ_ENABLE.value = ConfigModule.mem_buzzer
        logger.info(f"volume restored: {ConfigModule.sound_volume}")


    def stop_all(self, on_error= False):
        self.lbl_timer.stop()
        self.lbl_timer.reset()
        self.lbl_timer.reset_phase()
        self.mp_temp_chart.stop_draw()
        self.mp_temp_chart.resize_image()
        Shared.BUZZER.value = 0
        if self.clockObj is not None:
            self.clockObj.cancel()
            self.clockObj = None
        self.mp_blink_icon.stop_blink()
        self.program_is_running = Shared.MP_PROGRAM_IS_RUNNING = False
        Shared.ENABLE_OUTPUT.value = 0
        Shared.PRGM_STATUS_CODE.value = 150



    def end_program(self, on_error = False):
        logger.info('[PROGRAM COMPLETED!]')
        self.program_is_running = Shared.MP_PROGRAM_IS_RUNNING = False
        self.lbl_timer.reset_phase()
        self.mp_blink_icon.stop_blink()
        Shared.ENABLE_OUTPUT.value = 0
        Shared.PRGM_STATUS_CODE.value = 150




    def on_leave(self):
        if self.program_is_running == False:    # stop all if program ends and we leave window
            self.stop_all()
        self.ubidotsconnect.stop_iot_communication()
        self.ping.stop()

    # update running even after program ending, for continuos temperature measurement
    def update(self, dt):   
        # real time duration - end time calculation. Useful when a phase is interrupted before end 
        totals_updates = {k:(0 if k<=str(self.lbl_timer.phase) else v) for (k,v) in Shared.MP_DURATION_DICT.items() }
        total_dur_from_now = sum(totals_updates.values())*3600+self.lbl_timer.remaining_time_in_seconds
        self.time_end = (datetime.now() + timedelta(seconds=total_dur_from_now)).strftime("%d/%b/%y   %H:%M")
        total_dur = ((datetime.now() + timedelta(seconds=total_dur_from_now)) - Shared.MP_TIMER_BEGIN).seconds/3600
        self.total_duration = f"{total_dur:.1f}"
        # ---------------------------------------------
        program_details = ''
        app = App.get_running_app()
        if self.program_is_running == True:
            Shared.ENABLE_OUTPUT.value = 1 if Shared.POWER_STATUS_CODE.value < 350 else 0
            Shared.PRGM_STATUS_CODE.value =110

            program_details = '{} --> {} {} --> {}: {}'.format(app.multiphase_dash_title, app.multiphase_dash_phase, Shared.MP_ACTUAL_PHASE.value, app.multiphase_program_lbl.upper(), Shared.PROGRAM )[:100]

        self.mp_power_icon.set_input_state(Shared.POWER_STATUS_CODE.value)
        self.target_line = self.mp_temp_chart.draw_target_line(Shared.ACTUAL_TEMP_TARGET.value)
        self.mp_blink_icon.set_input_state(Shared.COMPRESSOR_STATE.value or Shared.LO_HEATER_STATE.value or Shared.HI_HEATER_STATE.value)
        self.mp_compressor_icon.set_input_state(Shared.COMPRESSOR_PROTECTION_CODE.value)
        self.mp_img_out_state, self.mp_img_out_label  = self.outimage.set_image(Shared.IO_STATUS_CODE.value,Shared.MP_PROGRAM_IS_RUNNING)
        ConfigModule.ethernet = self.ping.connected

        if  Shared.IO_STATUS_CODE.value > 100:
            self.warning.set_volume(100 if ConfigModule.buzzer == False else 0, control = ConfigModule.numid, card = ConfigModule.card_num)
            self.warning.aplay(100 if ConfigModule.buzzer == False else 0, card = ConfigModule.card_num)
            Shared.BUZZ_ENABLE.value = ConfigModule.buzzer
            Shared.BUZZER.value = 3
            self.stop_all()


        self.mp_wifi_toggle_btn.state = self.toggle_btn_states.get(ConfigModule.wi_fi)
        #self.mp_internet_icon.set_input_state(self.ping.return_value, disabled = not ConfigModule.wi_fi)
        self.mp_internet_icon.set_input_state(self.ping.return_value)
        self.mp_cloud_icon.set_input_state(Shared.SERVER_STATUS.value, disabled = not ConfigModule.cloud)

        self.cpu_temp, self.cpu_temp_float = ConfigModule.read_cpu_temp(ConfigModule.temp_scale)
        Shared.CPU_TEMP.value = self.cpu_temp_float

        if Shared.HOME == True:     # stops if we back home from settings screen
            self.lbl_timer.clear_text()
            self.stop_all()
            return

        Shared.MP_REMAINING_TIME.value = self.lbl_timer.remaining_time_in_seconds
        self.actual_phase = Shared.MP_ACTUAL_PHASE.value =  str(self.lbl_timer.phase)
        Shared.REMAINING_TIME_FMT.value= bytes(self.lbl_timer.format_time.encode())
        if(self.lbl_timer.end_phase == True and self.program_is_running == True and Shared.IO_STATUS_CODE.value <= 100):

            if (self.P2_duration > 0 and self.lbl_timer.phase == 1): #timer start if actual phase finish is 1
                self.lbl_timer.duration = self.P2_duration
                Shared.ACTUAL_TEMP_TARGET.value = self.P2_temp_target
                self.lbl_timer.start(2) # now timer begins counting phase 2
                self.crossphase_sound.set_volume(ConfigModule.sound_volume, not ConfigModule.buzzer,control = ConfigModule.numid, card = ConfigModule.card_num)
                self.crossphase_sound.aplay(ConfigModule.sound_volume, not ConfigModule.buzzer, card = ConfigModule.card_num)
                Shared.BUZZER.value = 8
                Shared.PRGM_STATUS_CODE.value = 120


            elif(self.P3_duration > 0 and self.lbl_timer.phase == 2):
                self.lbl_timer.duration = self.P3_duration
                Shared.ACTUAL_TEMP_TARGET.value = self.P3_temp_target
                self.lbl_timer.start(3)
                self.crossphase_sound.set_volume(ConfigModule.sound_volume, not ConfigModule.buzzer,control = ConfigModule.numid, card = ConfigModule.card_num)
                self.crossphase_sound.aplay(ConfigModule.sound_volume, not ConfigModule.buzzer, card = ConfigModule.card_num)
                Shared.BUZZER.value = 8
                Shared.PRGM_STATUS_CODE.value = 120


            elif(self.P4_duration > 0 and self.lbl_timer.phase == 3):
                self.lbl_timer.duration = self.P4_duration
                Shared.ACTUAL_TEMP_TARGET.value = self.P4_temp_target
                self.lbl_timer.start(4)
                self.crossphase_sound.set_volume(ConfigModule.sound_volume, not ConfigModule.buzzer, control = ConfigModule.numid, card = ConfigModule.card_num)
                self.crossphase_sound.aplay(ConfigModule.sound_volume, not ConfigModule.buzzer, card = ConfigModule.card_num)
                Shared.BUZZER.value = 8
                Shared.PRGM_STATUS_CODE.value = 120


            elif(self.P5_duration > 0 and self.lbl_timer.phase == 4):
                self.lbl_timer.duration = self.P5_duration
                Shared.ACTUAL_TEMP_TARGET.value = self.P5_temp_target
                self.lbl_timer.start(5)
                self.crossphase_sound.set_volume(ConfigModule.sound_volume, not ConfigModule.buzzer,control = ConfigModule.numid, card = ConfigModule.card_num)
                self.crossphase_sound.aplay(ConfigModule.sound_volume, not ConfigModule.buzzer, card = ConfigModule.card_num)
                #Shared.ENABLE_OUTPUT.value = 1
            else:
                self.end_program()
                program_details = '{}'.format(app.program_end.upper())[:100]
                self.endprogram_sound.set_volume(ConfigModule.sound_volume, not ConfigModule.buzzer,control = ConfigModule.numid, card = ConfigModule.card_num)
                self.endprogram_sound.aplay(ConfigModule.sound_volume, not ConfigModule.buzzer, card = ConfigModule.card_num)
                Shared.BUZZER.value = 5



        logger.info(f"([ACTUAL PHASE: {self.actual_phase}, RUNNING: {self.program_is_running}]")

        Shared.PROGRAM_DETAILS.value = bytes(program_details.encode())
        temp_meas = self.tc.convert_only_F(Shared.TEMP_MEAS.value, ConfigModule.temp_scale)
        self.temp_meas = self.fs.convert(temp_meas)[0]
        self.temp_meas_decimal = self.fs.convert(temp_meas)[1]
        self.temp_ext = self.tc.convert_only_F(Shared.TEMP_EXT.value, ConfigModule.temp_scale)
        self.output_status_code = Shared.IO_STATUS_CODE.value
        Shared.ACTUAL_TEMP_TARGET.value = Shared.MP_TEMP_TARGET_DICT.get(str(self.lbl_timer.phase))
        actual_temp_target_view = self.tc.convert_only_F(Shared.ACTUAL_TEMP_TARGET.value, ConfigModule.temp_scale)
        self.actual_temp_target = self.fs.convert(actual_temp_target_view)[0]
        self.actual_temp_target_decimal = self.fs.convert(actual_temp_target_view)[1]

        self.mp_chart_data = Shared.TEMP_MEAS.value

        Shared.MP_ACTUAL_PHASE_DURATION.value = self.actual_phase_duration = self.lbl_timer.duration
        Shared.MP_ELAPSED_TIME =self.lbl_timer.elapsed_time
        Shared.MP_ELAPSED_TIME_IN_SECONDS.value =self.lbl_timer._counter

