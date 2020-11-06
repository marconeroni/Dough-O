#################
fw='1.0.1'
#################
#Additional sound effects from https://www.zapsplat.com

#import tracemalloc
#tracemalloc.start()

import os
from types import ModuleType
os.environ['KIVY_AUDIO'] = 'sdl2'
from packages.ConfigModule import ConfigModule
ConfigModule.init_logger()
ConfigModule.read_config() # important!!: read config BEFORE all imports !!!!!!

from packages.IOInterface import IOInterface
from packages.BuzzController import BuzzController
from packages.IoTCloud import UbidotsConnect
from packages.NotifyHelper import NotifyHelper

from packages.HomeScreen import Home_Screen
from packages.PrestartSetScreen import PreStart_Set_Screen
from packages.PrestartDashBoardScreen import PreStart_DashBoard_Screen
from packages.MultiPhaseSetScreen import MultiPhase_Set_Screen
from packages.MultiPhaseDashBoardScreen import MultiPhase_DashBoard_Screen
from packages.SaveMenuScreen import SaveMenu_Screen
from packages.LoadFromMemoryScreen import LoadFromMemory_Screen
from packages.SettingsScreen import Settings_Screen
from packages.InfoScreen import Info_Screen
from packages.LogScreen import Log_Screen
from packages.LongPressButton import LongPressButton
from packages.Audio import PlaySound
from packages import Shared


import importlib
import pathlib
import multiprocessing
from sys import platform


from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, CardTransition
from kivy.clock import Clock
from kivy.core.text import LabelBase

use_kivy_settings = False

logger = ConfigModule.getLogger()

Builder.load_file("./kv/prestart_set_screen.kv")
Builder.load_file("./kv/prestart_dashboard_screen.kv")
Builder.load_file("./kv/multiphase_set_screen.kv")
Builder.load_file("./kv/multiphase_dashboard_screen.kv")
Builder.load_file("./kv/loadfrommemory_screen.kv")
Builder.load_file("./kv/settings_screen.kv")
Builder.load_file("./kv/savemenu_screen.kv")
Builder.load_file("./kv/info_screen.kv")
Builder.load_file("./kv/log_screen.kv")
Builder.load_file("./kv/home_screen.kv")



class Main(ScreenManager):
    transition= CardTransition()


class MainApp(App):

    logger.info(f"Firmware version: {fw}")

    try:
        lm = None
        btn_ok = PlaySound()
        btn_ok.source = ConfigModule.sounds_dir / ConfigModule.button_ok_audio
        btn_ok.set_volume(ConfigModule.sound_volume, not ConfigModule.buzzer, control = ConfigModule.numid, card = ConfigModule.card_num) # with this line, we set volume app at startup!!!!
        btn_cancel = PlaySound()
        btn_cancel.source =ConfigModule.sounds_dir / ConfigModule.button_cancel_audio
        btn = PlaySound()
        btn.source = ConfigModule.sounds_dir / ConfigModule.button_audio
        warning = PlaySound()
        warning.source = ConfigModule.sounds_dir / ConfigModule.warning_audio

        Shared.TEMP_UNIT_SCALE = ConfigModule.temp_scale
        Shared.EXCEPTION_STRING = ConfigModule.exception_string
        Shared.TEMP_INCREMENT = ConfigModule.temp_increment

        # set app temp_unit_scale with degree char for reference facilitation in kv files
        temp_unit_scale = chr(176) + Shared.TEMP_UNIT_SCALE



        LabelBase.register(
                            name="Aldrich",
                            fn_regular=f"{ConfigModule.app_dir.joinpath('Fonts','Aldrich-Regular.ttf')}",
                            fn_bold=f"{ConfigModule.app_dir.joinpath('Fonts','Aldrich-Regular.ttf')}"
                          )
        lm = importlib.import_module('.'.join(['Lang', ConfigModule.language])) #subfolders are specified with 'dot' in module import

        import_check = 0

        while(import_check <1):
            try:

                time_unit = lm.time_unit

        #----------------- ASSIGN LANGUAGE STRING LABELS -------------------------

                if platform == 'win32' or platform == 'win64':
                    locale = lm.locale_win
                else:
                    locale = lm.locale_linux

                ConfigModule.set_locale(locale)
                btn_main_prestart = lm.btn_main_prestart [:25]
                btn_main_multiphase = lm.btn_main_multiphase [:17]
                btn_main_load_from_mem = lm.btn_main_load_from_mem [:25]
                btn_main_settings = lm.btn_main_settings [:25]
                prestart_set_title = lm.prestart_set_title [:27]
                prestart_set_temp_target = lm.prestart_set_temp_target [:25]
                prestart_set_start = lm.prestart_set_start [:27]
                prestart_dash_title = lm.prestart_dash_title [:27]
                camera_temp_lbl = lm.camera_temp[:25]
                ext_temp_lbl = lm.ext_temp[:25]


                multiphase_set_title = lm.multiphase_set_title[:28]
                multiphase_set_temptarget = lm.multiphase_set_temptarget [:20]
                multiphase_set_duration = lm.multiphase_set_duration [:20]
                multiphase_phase1_btn = lm.multiphase_phase1_btn[:8]
                multiphase_phase2_btn = lm.multiphase_phase2_btn[:8]
                multiphase_phase3_btn = lm.multiphase_phase3_btn[:8]
                multiphase_phase4_btn = lm.multiphase_phase4_btn[:8]
                multiphase_phase5_btn = lm.multiphase_phase5_btn[:8]
                multiphase_program_lbl = lm.multiphase_program_lbl[:10]
                multiphase_total_lbl = lm.multiphase_total_lbl[:12]
                multiphase_end_lbl = lm.multiphase_end_lbl[:7]
                multiphase_dash_title = lm.multiphase_dash_title[:25]
                multiphase_dash_phase = lm.multiphase_dash_phase[:7]
                program_end = lm.program_end [:20]
                no_program = lm.no_program

                sm_notification_overwrite = lm.sm_notification_overwrite
                sm_notification_error = lm.sm_notification_error
                sm_notification_ok = lm.sm_notification_ok
                sm_notification_delete = lm.sm_notification_delete
                sm_notification_btn_cancel = lm.sm_notification_btn_cancel
                sm_notification_btn_save = lm.sm_notification_btn_save
                sm_notification_btn_delete = lm.sm_notification_btn_delete
                sm_notification_btn_note = lm.sm_notification_btn_note
                lm_notification_btn_load = lm.lm_notification_btn_load

                settings_title = lm.settings_title
                settings_lang = lm.settings_lang
                settings_scale = lm.settings_scale
                settings_offset_int = lm.settings_offset_int
                settings_offset_ext= lm.settings_offset_ext
                settings_wifi= lm.settings_wifi
                settings_cloud = lm.settings_cloud
                settings_wifi_btn = lm.settings_wifi_btn
                settings_log= lm.settings_log
                settings_fw=lm.settings_fw
                settings_notify_ok = lm.settings_notify_ok
                settings_notify_reboot = lm.settings_notify_reboot
                settings_increment_temp = lm.settings_increment_temp
                settings_increment_time = lm.settings_increment_time
                settings_buzzer = lm.settings_buzzer
                settings_id_sens_int = lm.settings_id_sens_int
                settings_id_sens_ext = lm.settings_id_sens_ext
                settings_sounds = lm.settings_sounds
                settings_mail_notify = lm.settings_mail_notify
                settings_send_btn = lm.settings_send_btn
                settings_test_btn = lm.settings_test_btn
                settings_mail_ok = lm.settings_mail_ok
                settings_notify_backup = lm.settings_notify_backup
                settings_notify_backup_load = lm.settings_notify_backup_load

                mail_subj_io_state = lm.mail_subj_io_state
                mail_header_io_state = lm.mail_header_io_state

                mail_subj_prgm_state = lm.mail_subj_prgm_state
                mail_header_prgm_state = lm.mail_header_prgm_state

                mail_subj_power_state = lm.mail_subj_power_state
                mail_header_power_state = lm.mail_header_power_state

                mail_subj_log = lm.mail_subj_log
                mail_header_log = lm.mail_header_log


                io_0 =  lm.io_0
                io_200 = lm.io_200
                io_201 = lm.io_201
                io_301 = lm.io_301
                io_302 = lm.io_302
                io_603 = lm.io_603
                io_50 = lm.io_50

                prgm_0 =  lm.prgm_0
                prgm_100 = lm.prgm_100
                prgm_110 = lm.prgm_110
                prgm_120 = lm.prgm_120
                prgm_130 = lm.prgm_130
                prgm_150 = lm.prgm_150

                power_0 =  lm.power_0
                power_300 = lm.power_300
                power_350 = lm.power_350
                power_360 = lm.power_360


                lo_heater_state_lbl = lm.lo_heater_state_lbl
                hi_heater_state_lbl = lm.hi_heater_state_lbl
                lo_hi_heater_state_lbl = lm.lo_hi_heater_state_lbl
                compressor_state_lbl = lm.compressor_state_lbl
                warning_out_lbl = lm.warning_out_lbl
                warning_in_lbl = lm.warning_in_lbl
                sleeping_lbl = lm.sleeping_lbl
                firmware = fw
                import_check = 2
            except Exception as ex:
                print(ex)
                logger.error(ex)
                lm = importlib.import_module('.'.join(['Lang', 'backup','italiano'])) #subfolders are specified with 'dot' in module import

#--------------- END OF LANGUAGE STRING LABELS ASSIGNMENT-----

#-------------- DEFINE GLOBAL APP BUTTON SOUNDS---------------

        def btn_ok_sound(self):
            self.btn_ok.set_volume(ConfigModule.sound_volume, not ConfigModule.buzzer, control = ConfigModule.numid, card = ConfigModule.card_num)
            self.btn_ok.aplay(ConfigModule.sound_volume, not ConfigModule.buzzer, card = ConfigModule.card_num)
            Shared.BUZZER.value = 4

        def btn_cancel_sound(self):
            self.btn_cancel.set_volume(ConfigModule.sound_volume, not ConfigModule.buzzer, control = ConfigModule.numid, card = ConfigModule.card_num)
            self.btn_cancel.aplay(ConfigModule.sound_volume, not ConfigModule.buzzer, card = ConfigModule.card_num)
            Shared.BUZZER.value = 4

        def btn_sound(self):
            self.btn.set_volume(ConfigModule.sound_volume, not ConfigModule.buzzer, control = ConfigModule.numid, card = ConfigModule.card_num)
            self.btn.aplay(ConfigModule.sound_volume, not ConfigModule.buzzer, card = ConfigModule.card_num)
            Shared.BUZZER.value = 4

        def play_warning(self):
            self.warning.set_volume(100, not ConfigModule.buzzer, control = ConfigModule.numid, card = ConfigModule.card_num)
            self.warning.aplay(100, not ConfigModule.buzzer, card = ConfigModule.card_num)
            Shared.BUZZ_ENABLE.value = True
            Shared.BUZZER.value = 4

    except Exception as ex:
        print(ex) # logger is not ready...
        logger.error(ex)
        for p in multiprocessing.active_children():
            p.terminate()




    def on_stop(self):
       for p in multiprocessing.active_children():
            logger.info(f"Terminating active processes: {p.name}")
            p.terminate()

    def build(self):
        return Main()

if __name__ == '__main__':
    #required only for Windows platform
    multiprocessing.freeze_support()
    Shared.BUZZ_ENABLE.value = ConfigModule.buzzer
    # Enable Processes only if no errors are detected in configuration and I/O interface is enabled via config
    if ConfigModule.exception_string == '' and ConfigModule.io_interface == True:
        IOInterface.start_io_interface()
        notify = NotifyHelper()
        notify.start_observer()
        if ConfigModule.buzzer == True:
            BuzzController.start_buzzer()

    MainApp().run()

#snapshot = tracemalloc.take_snapshot()
#top_stats = snapshot.statistics('lineno')
#for stat in top_stats[:10]:
    #print(stat)
