from kivy.uix.screenmanager import Screen
from kivy.properties import *
from kivy.app import App
from kivy.utils import escape_markup
from kivy.core.audio import SoundLoader

import subprocess
import pathlib
import os
import glob
import time

import asyncio
import smtplib
from email.message import EmailMessage

from threading import Thread
from packages import Shared
from pathlib import Path
from packages.NotifyHelper import NotifyHelper
from packages.ConfigModule import ConfigModule
from packages.TempConverter import TempConverter
from sys import platform
from packages.Audio import PlaySound
from kivy.clock import Clock



logger = ConfigModule.getLogger()


class Settings_Screen(Screen):
    __files = ConfigModule.lang_files
    __filecounter = 0
    __temp_scale = {'C': 'celsius', 'F': 'farenheit'}
    __temp_scale_raw = 'C'
    __sens_ids_dict = {True: '', False:''}
    __config_dict = {}
    sound = PlaySound()
    notify = NotifyHelper()
    sound.source = ConfigModule.sounds_dir / ConfigModule.end_program_audio


    language = StringProperty('')
    temp_scale = StringProperty('')
    int_sens_offset = BoundedNumericProperty(0.0,min=-5,max=5, errorvalue =0.0)
    ext_sens_offset = BoundedNumericProperty(0.0,min=-5,max=5, errorvalue = 0.0)
    wi_fi = BooleanProperty(True)
    cloud = BooleanProperty(False)
    log = BooleanProperty(False)
    buzzer = BooleanProperty(False)
    lbl_set_notify = ObjectProperty(None)
    temp_increment = NumericProperty(0.1)
    time_increment = NumericProperty(0.5)

    wi_fi_switch = ObjectProperty(None)
    cloud_switch = ObjectProperty (None)
    log_switch = ObjectProperty(None)
    buzzer_switch= ObjectProperty(None)
    mail_notify_switch = ObjectProperty(None)
    sound_slider = ObjectProperty(None)
    sound_slider_mem_volume = NumericProperty(0)
    id_sens_int = StringProperty('')
    id_sens_ext = StringProperty('')
    reboot_counter = 0
    reboot_counter_str = StringProperty('')
    reboot_clock = None
    standby_timer = None


    def load_backup_config(self):
        try:
            #print(ConfigModule.config_backup_path)
            app = App.get_running_app()
            ConfigModule.read_config(ConfigModule.config_backup_path)
            self.ParseConfig()
            self.lbl_set_notify.text = \
            '[font=Aldrich][b][color=#ff0339][size=20]'+escape_markup('{}'.format(app.settings_notify_backup_load))+'[/font][/size][/color][/b]'
        except Exception as err:
            err = 'MISSING OR CORRUPTED BACKUP FILE!'
            logger.error(f"{err}\n{err}")
            self.lbl_set_notify.text = \
                '[font=Aldrich][b][color=#ff0339][size=15]'+escape_markup('{}'.format(err))+'[/font][/size][/color][/b]'

    def on_pre_enter(self):
        self.lbl_set_notify.text = ''
        self.reboot_counter_str =''
        ConfigModule.read_config()
        self.ParseConfig()

    def on_enter(self):
        Shared.MEM_SCREEN.value = 6
        if self.standby_timer is None:
            self.standby_timer = Clock.create_trigger(self.timer, 300)
            self.standby_timer()

    def app_stop(self):
        app = App.get_running_app()
        Shared.reset_all(Shared)
        time.sleep(0.3)
        app.stop()

    def on_leave(self):
        if self.reboot_clock is not None and self.reboot_counter >=5:
            self.reboot_clock.cancel()
        if self.standby_timer is not None:
            self.standby_timer.cancel()
            self.standby_timer = None

    def timer(self, dt):
        self.parent.current = 'home_screen'


###IMPORTANT!! Sensors offset are not converted in farenheit because the little difference not make convenient to write additional code: therefore, farenheit offset il less accurated (sorry)
    def ParseConfig(self):


        self.language = ConfigModule.language
        self.__temp_scale_raw = ConfigModule.temp_scale
        self.temp_scale = self.__temp_scale.get(self.__temp_scale_raw)
        self.int_sens_offset = ConfigModule.int_sens_offset
        self.ext_sens_offset = ConfigModule.ext_sens_offset
        self.temp_increment = ConfigModule.temp_increment
        self.time_increment = ConfigModule.time_increment
        self.sound_slider.value = self.sound_slider_mem_volume= ConfigModule.sound_volume
        self.wi_fi = ConfigModule.wi_fi
        self.wi_fi_switch.active = ConfigModule.wi_fi
        self.cloud = ConfigModule.cloud
        self.cloud_switch.active  = ConfigModule.cloud
        self.log = ConfigModule.log
        self.log_switch.active = ConfigModule.log
        self.buzzer = ConfigModule.buzzer
        self.buzzer_switch.active = ConfigModule.buzzer
        self.mail_notify_switch.active = ConfigModule.mail_notify


        # insert ids in dictionary
        self.__sens_ids_dict.update({True: ConfigModule.sens_ids[0], False: ConfigModule.sens_ids[1]})
        self.id_sens_int = ConfigModule.sens_ids[0] if ConfigModule.id_sens_int == '' else ConfigModule.id_sens_int
        self.id_sens_ext = ConfigModule.sens_ids[1] if ConfigModule.id_sens_ext == '' else ConfigModule.id_sens_ext
        self.__filecounter = self.__files.index(self.language+'.py') #indexing counter to avoid redondant click on language button selection


    def check_audio_out(self):
        if self.sound_slider.value > 0:
            self.buzzer_switch.active = False



    def reboot(self, dt):
        logger.info(f"REBOOT...{self.reboot_counter}")
        self.reboot_counter+=1
        self.reboot_counter_str = str(self.reboot_counter)
        if (platform == 'linux' or platform == 'linux2') and ConfigModule.auto_reboot == True and self.reboot_counter >= 5:
            cmd = ["reboot"]
            sb= subprocess.run(
                                cmd,
                                check = True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True
                               )
            if sb.returncode == 1:
                logger.error(f"{sb.stdout}")



    def clear_notify(self):
        self.lbl_set_notify.text = ''

    def change_lang(self, direction):
        self.clear_notify()
        limit = len(self.__files)
        self.__filecounter+= direction

        if self.__filecounter >= limit or self.__filecounter <= -limit:
            self.__filecounter = 0

        self.language = self.__files[self.__filecounter] [:-3]

    def change_temp_unit(self, unit):
        self.clear_notify()
        self.temp_scale = self.__temp_scale.get(unit)
        self.__temp_scale_raw = unit


    def change_offset(self, sensor, increment): #sensor must be a string : 'int' or 'ext'
        self.clear_notify()
        if sensor == 'int':
            self.int_sens_offset+=increment
        elif sensor == 'ext':
            self.ext_sens_offset+=increment

    def change_temp_increment(self, _increment):
        self.temp_increment+=_increment
        if self.temp_increment <=0.1 or self.temp_increment >= 1:
            self.temp_increment = 0.1

    def change_time_increment(self, _increment):
        self.time_increment+=_increment
        if self.time_increment <=0.5 or self.time_increment >= 10.5:
            self.time_increment = 0.5


    # swap ids of sensors. location can be 'ext' or 'int'
    def change_int_sens_id(self, location):
        self.id_sens_int = self.__sens_ids_dict.get(location)
        #swap
        location = not location
        self.id_sens_ext = self.__sens_ids_dict.get(location)

    def test_sound(self):
        try:
            self.sound.set_volume(self.sound_slider.value, not ConfigModule.buzzer,control = ConfigModule.numid, card = ConfigModule.card_num)
            self.sound.play(self.sound_slider.value, not ConfigModule.buzzer,card = ConfigModule.card_num)
        except Exception as ex:
            #logger.info(ex)
            logger.error(ex)

    def send_log(self):
        try:
            app = App.get_running_app()

            log_files_path = Path(ConfigModule.log_dir) / '*.txt'
            last_log_files_path = Path(ConfigModule.log_dir) / 'last' / '*.txt'
            last_log_files = glob.glob(str(last_log_files_path))
            log_files= glob.glob(str(log_files_path))
            self.notify.sendmail    (
                                    sender = ConfigModule.mail_sender,
                                    receiver = ConfigModule.mail_receiver,
                                    subject = app.mail_subj_log,
                                    body = app.mail_header_log,
                                    timeout = 3,
                                    attachment_1 = log_files,
                                    attachment_2= last_log_files
                                    )


            self.lbl_set_notify.text ='[font=Aldrich][b][color=#ff0339][size=20]'+escape_markup('{}'.format(app.settings_mail_ok))+'[/font][/size][/color][/b]'
        except Exception as ex:
            self.lbl_set_notify.text ='[font=Aldrich][b][color=#ff0339][size=15]'+escape_markup('{}'.format(ex))+'[/font][/size][/color][/b]'
            logger.error(ex)





    def set_default(self):
        self.clear_notify()
        self.language = 'english'
        self.temp_scale = self.__temp_scale['C']
        self.int_sens_offset  = 0.0
        self.ext_sens_offset  = 0.0
        self.temp_increment = 0.5
        self.time_increment = 0.5
        self.buzzer_switch.active = False
        self.log_switch.active = False
        self.wi_fi_switch.active = True
        self.cloud_switch.active = False
        self.mail_notify_switch.active = False
        self.sound_slider.value = 1


    def commit(self, backup = False):
        self.clear_notify()
        app = App.get_running_app()
        self.__config_dict = {'language':self.language,
                              'temp_unit_scale': self.__temp_scale_raw,
                              'wi_fi': f"{self.wi_fi_switch.active}" ,
                              'cloud': f"{self.cloud_switch.active}",
                              'log': f"{self.log_switch.active}",
                              'mail_notify': f"{self.mail_notify_switch.active}",
                              'int_offset': f"{self.int_sens_offset:.1f}",
                              'ext_offset': f"{self.ext_sens_offset:.1f}",
                              'temp_increment': f"{self.temp_increment:.1f}",
                              'time_increment': f"{self.time_increment:.1f}",
                              'buzzer': f"{self.buzzer_switch.active}",
                              'id_sens_int': f"{self.id_sens_int}",
                              'id_sens_ext': f"{self.id_sens_ext}",
                              'sound_volume': f"{self.sound_slider.value:.0f}"
                             }
        Shared.BUZZ_ENABLE.value = self.buzzer_switch.active

        try:
            ConfigModule.write_config(backup, **self.__config_dict)
        except Exception as ex:
            err = 'ERROR WRITING CONFIGURATION FILE!'
            logger.error(f"{err}\n{ex}")
            self.lbl_set_notify.text = \
                '[font=Aldrich][b][color=#ff0339][size=15]'+escape_markup('{}'.format(err))+'[/font][/size][/color][/b]'
            return
        notify_text = {True : app.settings_notify_reboot, False: app.settings_notify_ok, None: 'Error in config.ini auto_reboot value!' }
        self.lbl_set_notify.text = \
            '[font=Aldrich][b][color=#ff0339][size=20]'+escape_markup('{}'.format(notify_text.get(ConfigModule.auto_reboot)))+'[/font][/size][/color][/b]'

        if backup == True:
            self.lbl_set_notify.text = \
            '[font=Aldrich][b][color=#ff0339][size=20]'+escape_markup('{}'.format(app.settings_notify_backup))+'[/font][/size][/color][/b]'
            return

        logger.info(f"CONFIG FILE SUCCESSFULLY UPDATED!")
        self.reboot_counter = 0
        if self.reboot_clock is None:
            self.reboot_clock=Clock.create_trigger(self.reboot, 1, True)
            if ConfigModule.auto_reboot == True:
                self.reboot_clock()





