
import locale
import configparser
import glob
import os
import logging
import subprocess
import time
import shutil



from sys import stdout
from sys import platform
from pathlib import Path
from datetime import datetime
from kivy.config import Config
from threading import Thread, Event
from zipfile import ZipFile




Config.set('kivy', 'log_enable', 0)
Config.set('kivy', 'log_name', 'kivy_%y-%m-%d_%_.txt')
#Config.set('kivy', 'log_level', 'debug')
Config.set('kivy', 'log_maxfiles', 0)
Config.set('graphics', 'width', 800)
Config.set('graphics', 'height', 480)
Config.set('graphics', 'resizable', False)
Config.set('graphics', 'borderless', '1')
Config.set('kivy', 'keyboard_mode', 'systemanddock')





#singleton
class ConfigModule(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance


    #app logger level INFO
    logger = logging.getLogger('app logger')
    io_logger = logging.getLogger('I/O logger')
    net_logger = logging.getLogger('net logger')
    logger.setLevel(logging.INFO)
    io_logger.setLevel(logging.INFO)
    net_logger.setLevel(logging.INFO)
    config = configparser.ConfigParser()
    log_dir= ''
    log_io_filepath = ''
    NET_log_filepath = ''
    devices_dir = ''
    cur_dir = Path(__file__)
    app_dir = cur_dir.parents[1]
    pi_dir = cur_dir.parents[2]
    config_file_path = app_dir / 'config.ini'
    config_backup_path = pi_dir / 'backup.ini'
    config_recovery_path = cur_dir.joinpath('recovery.ini')
    sounds_dir = app_dir.joinpath('Sounds')
    event = Event()


    localization = ''
    language = 'italiano'
    lang_files = []
    temp_scale = 'C'
    int_sens_offset= 0.0
    ext_sens_offset = 0.0
    wi_fi = True
    ethernet = True
    log = False
    buzzer = False
    io_interface = True
    temp_increment = 0.1
    time_increment = 0.5
    dp_separator = '.'
    cloud = False
    mail_notify = False
    mockup = False
    auto_reboot = True
    ups_shutdown = 60


    T_min_C = -18
    T_max_C = 50
    id_sens_int = ''
    id_sens_ext = ''
    sens_ids = ['NOT_FOUND','NOT_FOUND']
    exception_string = '' # if exception string is not none, home screen print the exception
    ubidots_key = ''
    ubidots_token = ''
    ubidots_url = ''
    ubidots_ip = ''
    ubidots_api = ''
    ubidots_device_label = ''
    ub_var_temp_int = ''
    ub_var_temp_ext = ''
    ub_var_temp_target = ''
    ub_var_remaining_time = ''
    ub_var_out_state = ''
    ub_var_t_unit_scale = ''
    ub_var_prgm_details = ''
    ub_var_duration = ''
    ub_var_power_status = ''

    mail_sender = ''
    mail_receiver = ''
    host = 'smtp.gmail.com'
    port = 465
    username= ''
    password = ''


    sound_volume = 0
    mem_volume = 0
    mem_buzzer = False
    HH_HL = -7
    HH = -4
    HL = -2
    HL_PWM = -0.5
    NEG_OFF = -0.2
    POS_OFF = 0.2
    COMP = 1
    ON_PWM = 70
    OFF_PWM = 50
    COMP_PROT = 480
    button_audio  = ''
    button_ok_audio = ''
    button_cancel_audio = ''
    start_program_audio = ''
    end_program_audio = ''
    cross_phase_audio = ''
    warning_audio = ''
    alert_audio = ''
    numid ='6'
    card_num = '1'


    @classmethod
    def getLogger(cls):
        return cls.logger

    @classmethod
    def getIOLogger(cls):
        return cls.io_logger

    @classmethod
    def getNETLogger(cls):
        return cls.net_logger

    

    @classmethod
    def init_logger(cls):

        log_stream = logging.StreamHandler(stdout)
        #log_stream.setLevel(logging.INFO)
        log_stream_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s : %(lineno)d - %(message)s")
        log_stream.setFormatter(log_stream_formatter)
        cls.logger.addHandler(log_stream)
        #cls.cur_dir= Path(__file__)             # current dir of config module
        #cls.app_dir = cls.cur_dir.parents[1]
        cls.config_file_path = cls.app_dir / 'config.ini'
        cls.config_recovery_path = cls.cur_dir.joinpath('recovery.ini')
        cls.config.read(f"{cls.config_file_path}", encoding ='utf-8')




        if platform == "linux" or platform == "linux2":
            log_filepath = str(Path(cls.config['PATHS']['log']).joinpath('RASP.txt'))
            cls.log_io_filepath = str(Path(cls.config['PATHS']['log']).joinpath('IO_LOG.txt'))
            cls.NET_log_filepath = str(Path(cls.config['PATHS']['log']).joinpath('NET_LOG.txt'))
            cls.log_dir = str(Path(cls.config['PATHS']['log']))
            kivy_log_filedir = cls.log_dir = cls.config['PATHS']['log']
            Config.set('kivy', 'log_dir', kivy_log_filedir)
            cls.delete_logs(kivy_log_filedir, filter(lambda x:x.startswith('kivy'), os.listdir(kivy_log_filedir)))
        else:
            log_filepath = str(cls.cur_dir.parents[1].joinpath('Logs').joinpath('WIN.txt'))
            cls.log_io_filepath = str(cls.cur_dir.parents[1].joinpath('Logs').joinpath('IO_LOG.txt'))
            cls.NET_log_filepath = str(cls.cur_dir.parents[1].joinpath('Logs').joinpath('NET_LOG.txt'))
            cls.log_dir = str(cls.cur_dir.parents[1].joinpath('Logs'))
            cls.delete_logs(cls.log_dir, filter(lambda x:x.startswith('kivy'), os.listdir(cls.log_dir)))
            Config.set('kivy', 'log_dir', cls.log_dir )



        cls.copy_zip_logs(Path(cls.log_dir)) # copy log files generated at the previous power up

        log_verbose = cls.to_bool(cls.config['APP']['log'])

        #cls.delete_logs(kivy_log_dir, filter(lambda x:x.startswith('kivy'), os.listdir(kivy_log_dir)))
        Config.set('kivy', 'log_enable', log_verbose)
        log_file = logging.FileHandler(log_filepath, mode='w')
        log_io = logging.FileHandler(cls.log_io_filepath, mode = 'w')
        log_NET = logging.FileHandler(cls.NET_log_filepath, mode = 'w')
        # set filter level for log file
        if log_verbose is True:
            log_file.setLevel(logging.NOTSET)
            log_stream.setLevel(logging.NOTSET)
            Config.set('kivy', 'log_level', 'debug')
        else:
            log_file.setLevel(logging.ERROR)
            log_stream.setLevel(logging.ERROR)
            Config.set('kivy', 'log_level', 'critical')

        log_file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s : %(lineno)d - %(message)s")
        log_file.setFormatter(log_file_formatter)
        cls.logger.addHandler(log_file)

        log_io.setLevel(logging.INFO)
        log_io_formatter = logging.Formatter("%(asctime)s - %(message)s","%Y-%b-%d %H:%M:%S")
        log_io.setFormatter(log_io_formatter)
        log_NET.setFormatter(log_io_formatter)

        cls.io_logger.addHandler(log_io)
        cls.net_logger.addHandler(log_NET)

        cls.logger.info(f"Log path: {log_filepath}")
        cls.logger.info(f"GUI log path: {cls.log_io_filepath}")
        cls.logger.info(f"NET log path: {cls.NET_log_filepath}")
        cls.logger.info(f'Running on platform: {platform}')
        cls.logger.critical('[ GENERAL LOGGER READY ]') # some providers blocks email with emtpty .txt attachment!
        cls.io_logger.info('[ I/O LOGGER READY ]')
        cls.net_logger.info('[ NET LOGGER READY ]')

    @classmethod
    def copy_zip_logs(cls, folder_path):
        try:
            files = os.listdir(folder_path)
            logs = list(filter(lambda file: file.endswith('.txt'), files))
            zip_file_path = folder_path / 'last'/ 'logs.zip'
            zip_fold = ZipFile(zip_file_path, 'w')
            for file in logs:
                try:
                    shutil.copy2(folder_path / file, folder_path / 'last' / ('LAST_'+ file))
                    zip_fold.write(folder_path / file)
                except Exception as ex:
                    cls.logger.error(ex)

            zip_fold.close()
        except Exception as ex:
            cls.logger.error(ex)

    @classmethod
    def delete_logs(cls, log_dir, file_filter):

        lst = [os.path.join(log_dir, x) for x in file_filter ]
        for filename in lst:
            try:
                os.unlink(filename)
            except PermissionError as e:
                cls.logger.info(f"Logger: Skipped file {filename}, {e}")

    @classmethod
    def list_devices(cls):
        try:
            if cls.mockup == False:
                cls.devices_dir = cls.config['PATHS']['devices']
            else:
                cls.devices_dir = './Test/sys/bus/w1/devices/'
            devices = os.listdir(cls.devices_dir)
            devices = list(filter(lambda _id: _id.startswith('28'), devices))
        except Exception:
            cls.exception_string = 'ERR-001:\nUnable to read 1-wire device path!-('
            cls.logger.debug(cls.exception_string)
            raise FileNotFoundError(cls.exception_string)

        if len(devices) == 0:
            cls.exception_string = ('\n\n\n\nERR-002:\nNo sensor found!\nCheck hardware!-(')
            cls.sens_ids = ['None', 'None']
            cls.logger.debug(cls.exception_string)
            if cls.mockup == True:
                cls.sens_ids = ['Mockup', 'Mockup']
                return True

        elif len(devices) == 1:
            cls.exception_string= (f"\n\n\n\nERR-003:\nOnly one sensor found:\n{devices[0]} !-(")
            cls.logger.debug(cls.exception_string)
            cls.sens_ids = [devices[0], devices[0]]
            if cls.mockup == True:
                return True

        elif len(devices) == 2:
            cls.logger.info('[Sensor successfully initialized!]')
            cls.sens_ids = [devices[0], devices[1]]
            return True

        else:
            cls.exception_string =  f"\n\n\n\n[This firmware version accepts only 2 sensors\nbut I have detected {len(devices)}]"
            cls.logger.error(cls.exception_string)
            cls.sens_ids = [devices[0], devices[1]]

        return False

    @classmethod
    def to_bool(cls,value):
        value= value.upper()
        states = { 'TRUE': True, 'FALSE': False}
        return states.get(value)

    @classmethod
    def to_int(cls,value):
        states = {True: 1, False: 0}
        return states.get(value)

    @classmethod
    def check_sensors(cls):

        devices = cls.sens_ids
        id_sens_int = cls.config['SENSORS']['id_sens_int']
        id_sens_ext = cls.config['SENSORS']['id_sens_ext']
        if id_sens_int in devices and id_sens_ext in devices:
            cls.logger.info(f"Sensor {devices[0]} checked ok!")
            cls.logger.info(f"Sensor {devices[1]} checked ok!")
        else:
            msg = f"\n\nYou have replaced one or more sensor.\nYou need to reconfigure them!"
            cls.logger.error(msg)
            cls.exception_string = msg
            cls.id_sens_int = devices[0]
            cls.id_sens_ext = devices[1]

    @classmethod
    def read_controller_par(cls):
        try:
            cls.HH_HL = float(cls.config['CONTROLLER']['hh_hl'])
            cls.HH = float(cls.config['CONTROLLER']['hh'])
            cls.HL = float(cls.config['CONTROLLER']['hl'])
            cls.HL_PWM = float(cls.config['CONTROLLER']['hl_pwm'])
            cls.NEG_OFF = float(cls.config['CONTROLLER']['neg_off'])
            cls.POS_OFF = float(cls.config['CONTROLLER']['pos_off'])
            cls.COMP = float(cls.config['CONTROLLER']['comp'])
            cls.ON_PWM = float(cls.config['CONTROLLER']['on_pwm'])
            cls.OFF_PWM = float(cls.config['CONTROLLER']['off_pwm'])
            cls.COMP_PROT = 60*(float(cls.config['CONTROLLER']['comp_prot']))
            if cls.COMP_PROT < 60:
                cls.COMP_PROT = 60
        except Exception as err:
            cls.exception_string = f"ERROR READING\nCONTROLLER PARAM [config.ini]:\n{err}"
            cls.logger.error(f"{err}")

    @classmethod
    def read_config(cls, file_path = config_file_path):
        try:

            cls.config.read(f"{file_path}", encoding ='utf-8')
            #set mouse cursor
            show_cursor = cls.config['APP']['show_cursor']
            Config.set('graphics','show_cursor', show_cursor)
            #cls.localization = cls.config['LOCALE']['locale']
            cls.mockup = cls.to_bool(cls.config['APP']['mockup'])
            cls.language = cls.config['APP']['language']
            cls.temp_scale = (cls.config['APP']['temp_unit_scale']).upper()
            cls.int_sens_offset= float(cls.config['SENSORS']['int_offset'])
            cls.ext_sens_offset = float(cls.config['SENSORS']['ext_offset'])
            cls.wi_fi = cls.to_bool(cls.config['APP']['wi_fi'])
            cls.log = cls.to_bool(cls.config['APP']['log'])
            cls.temp_increment = float(cls.config['APP']['temp_increment'])
            cls.time_increment = float(cls.config['APP']['time_increment'])
            cls.buzzer = cls.mem_buzzer = cls.to_bool(cls.config['APP']['buzzer'])
            cls.cloud = cls.to_bool(cls.config['APP']['cloud'])
            cls.auto_reboot = cls.to_bool(cls.config['APP']['auto_reboot'])
            cls.mail_notify = cls.to_bool(cls.config['APP']['mail_notify'])
            cls.ups_shutdown = 60* int(cls.config['APP']['ups_shutdown'])
            if cls.ups_shutdown < 60 and cls.ups_shutdown != 0:
                cls.ups_shutdown = 60
            cls.id_sens_int = cls.config['SENSORS']['id_sens_int']
            cls.id_sens_ext = cls.config['SENSORS']['id_sens_ext']
            #cls.dp_separator = locale.localeconv().get('decimal_point')
            cls.T_min_C = float(cls.config['BOUNDS']['T_min_C'])
            cls.T_max_C = float(cls.config['BOUNDS']['T_max_C'])
            cls.sound_volume = float(cls.config['AUDIO']['sound_volume'])
            cls.ubidots_key = cls.config['UBIDOTS']['key']
            cls.ubidots_token = cls.config['UBIDOTS']['token']
            cls.ubidots_url = cls.config['UBIDOTS']['url']
            cls.ubidots_ip = cls.config['UBIDOTS']['ip']
            cls.ubidots_api = cls.config['UBIDOTS']['api']
            cls.ubidots_device_label = cls.config['UBIDOTS']['device_label']
            cls.ub_var_temp_int = cls.config['UBIDOTS']['var_temp_int']
            cls.ub_var_temp_ext = cls.config['UBIDOTS']['var_temp_ext']
            cls.ub_var_temp_target = cls.config['UBIDOTS']['var_temp_target']
            cls.ub_var_remaining_time = cls.config['UBIDOTS']['var_remaining_time']
            cls.ub_var_duration = cls.config['UBIDOTS']['var_duration']
            cls.ub_var_out_state = cls.config['UBIDOTS']['var_out_state']
            cls.ub_var_t_unit_scale = cls.config['UBIDOTS']['var_t_unit_scale']
            cls.ub_var_prgm_details = cls.config['UBIDOTS']['var_prgm_details']
            cls.ub_var_power_status = cls.config['UBIDOTS']['var_power_status']

            cls.mail_sender = cls.config['SMTP']['mail_sender']
            cls.mail_receiver = cls.config['SMTP']['mail_receiver']
            cls.host = cls.config['SMTP']['host']
            cls.port = int(cls.config['SMTP']['port'])
            cls.username= cls.config['SMTP']['username']
            cls.password = cls.config['SMTP']['password']

            cls.numid= cls.config['AUDIO']['numid']
            cls.card_num= cls.config['AUDIO']['card_num']
            cls.button_audio  = cls.config['AUDIO']['button']
            cls.button_ok_audio  = cls.config['AUDIO']['button_ok']
            cls.button_cancel_audio  = cls.config['AUDIO']['button_cancel']
            cls.start_program_audio = cls.config['AUDIO']['start_program']
            cls.end_program_audio = cls.config['AUDIO']['end_program']
            cls.cross_phase_audio = cls.config['AUDIO']['cross_phase']
            cls.warning_audio = cls.config['AUDIO']['warning']
            cls.alert_audio = cls.config['AUDIO']['alert']
            cls.io_interface = cls.to_bool(cls.config['APP']['io_interface'])

        except Exception as ex:
            error = f"Error reading config.ini file: {ex}"
            cls.exception_string = f"ERROR READING CONFIG FILE!\n{ex}"
            cls.logger.error(error)
            #cls.logger.info(error)

        cls.read_controller_par()
        #cls.set_locale(cls.localization)
        cls.getlangfiles()
        cls.aswitch_wifi(cls.wi_fi)
        trust = cls.list_devices()
        if trust == True: cls.check_sensors()


    @classmethod # is mandatory to check strength signal after enable
    def switch_wifi(cls, enable):
        # sudo iwlist wlan0 scan | egrep "Cell|ESSID|Signal|Rates"
        sb=None
        try:
            if platform == "linux" or platform == "linux2":

                    cmd = []
                    if enable == False:
                        cls.wi_fi = False
                        cmd = ["sudo", "rfkill", "block", "wifi"]
                        #cmd = ["sudo", "ifconfig", "wlan0", "down"]

                    else:
                        cls.wi_fi = True
                        cmd = ["sudo", "rfkill", "unblock", "wifi"]
                        #cmd = ["sudo", "ifconfig", "wlan0", "up"]

                    sb = subprocess.run(cmd) # rfkill has no value return
                    cls.event.wait(20) # wait for connection (non-blocking GUI) before check signal strength
                    cls.wifi_strength()
                    cls.logger.info(f"Wi-Fi switched: {enable}")
                    #cls.logger.info(f"{cmd[2]} {cmd[3]} STDOUT_VALUE: {repr(stdout_value)}")
                    #cls.logger.info(f"STDOUT_ERR: {repr(stdout_err)}")

            if platform == "win32" or platform == "win64":
                if enable == False:
                    os.system("netsh interface set interface 'Ethernet' disabled")
                    cls.logger.info('WI FI DISABLED!')
                    cls.wi_fi = False

                else:
                    os.system("netsh interface set interface 'Ethernet' enabled")
                    cls.logger.info('WI FI ENABLED!')
                    cls.event.wait(20)
                    cls.wifi_strength()


        except Exception as err:
            sb.kill()
            cls.logger.error(err)
            cls.wi_fi = False
        finally:
            return

    @classmethod
    def aswitch_wifi(cls, enable):
        async_switch = Thread(target = cls.switch_wifi, args = (enable,))
        async_switch.start()



    @classmethod
    def wifi_strength(cls):
        return_string = ''
        error_str = 'EE/EE\n-EE dbm'
        if (platform != "linux" and platform != "linux2"):
            cls.wi_fi = False
            return error_str
        sb=None
        try:
            # for PIPE linux commands in subprocess, I must create process separately or send string with shell=True.
            # last case is not recommanded for security reasons, but in this case I prefer to keep the code simply
            cmd = 'sudo iwconfig wlan0 | grep -i --color signal'
            sb = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell = True, universal_newlines=True)
            stdout_value, stdout_err = sb.communicate()
            if stdout_value == '' or stdout_value is None:
                sb.kill()
                return error_str
            splitted = stdout_value.strip().split(" ")
            return_string = f"{splitted[1]}\n {splitted[4]} dbm"
            return_string = return_string.replace('Quality=','').replace('level=','').strip()
            cls.logger.info(sb.stdout)
            cls.logger.info(f"STDOUT_ERR: {repr(stdout_err)}")
            cls.wi_fi = True

        except Exception as err:
            sb.kill()
            cls.logger.error(f"wi-fi strenght getter {err}")
            cls.wi_fi = False
            return_string = f"{error_str :^16}"
            #return f"{error_str :^16}"
        finally:
            return return_string
        # EXAMPLE OF OUTPUT:
        # Link Quality=41/70  Signal level=-69 dBm

    @classmethod
    def awifi_strength(cls):
        async_strength = Thread(target = cls.wifi_strength)
        async_strength.start()


    @classmethod
    def getlangfiles(cls):
        try:
            langdir=cls.app_dir.joinpath('Lang')
            files = os.listdir(langdir)
            cls.lang_files = list(filter(lambda file: file.endswith('.py'), files))

        except Exception as ex:
            error = f"Unable to load language file: {ex}"
            cls.logger.error(error)
            #cls.logger.info(error)

    @classmethod
    def set_locale(cls,localization):
        try:

            if localization == '':
                locale.setlocale(locale.LC_ALL, '') # system default
            else:
                locale.setlocale(locale.LC_TIME, localization)
        except Exception as ex:
            error = f"Unable to set locale: {ex}"
            cls.logger.error(error)
            locale.setlocale(locale.LC_ALL, '') # system default
            #cls.logger.info(error)

    @classmethod
    def ping(cls):
        if platform == 'win32' or platform == 'win64':
            cmd = ["ping", cls.ubidots_ip]
            sb= subprocess.run(
                                cmd,
                                check = True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True
                               )
            if sb.returncode == 0:
                cls.logger.info(f"{sb.stdout}")
                return 1
            else:
                return 0


    @classmethod
    def aping(cls):
        async_ping = Thread(target = cls.ping)
        async_ping.start()

    @classmethod
    def read_cpu_temp(cls, temp_scale):
        error_str = '--.-', '99.9'
        if platform != "linux" and platform != "linux2":
            return error_str
        sb=None
        try:
            # reading example: "temp=42.0'C"
            cmd = "sudo /opt/vc/bin/vcgencmd measure_temp"
            sb = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            stdout_value, stdout_err = sb.communicate()
            (discard, sep, reading) = stdout_value.partition('temp=')
            reading = reading.replace('\'C','').strip()
            reading_float = float(reading)
            if temp_scale == 'F':
                reading_float = (reading_float * 1.8) +32

            reading = f"{reading_float}"
            cls.logger.info(sb.stdout)
            cls.logger.info(f"STDOUT_ERR: {repr(stdout_err)}")

        except Exception as err:
            sb.kill()
            cls.logger.error(err)
            return error_str

        return reading, reading_float



    @classmethod
    def write_config(cls, backup=False,**kwargs):
        try:
            cls.config['APP']['language'] = kwargs['language']
            cls.config['APP']['wi_fi'] = kwargs['wi_fi']
            cls.config['APP']['log'] = kwargs['log']
            cls.config['APP']['temp_unit_scale'] = kwargs['temp_unit_scale']
            cls.config['APP']['temp_increment'] = kwargs['temp_increment']
            cls.config['APP']['time_increment'] = kwargs['time_increment']
            cls.config['APP']['cloud'] = kwargs['cloud']
            cls.config['APP']['mail_notify'] = kwargs['mail_notify']
            cls.config['SENSORS']['int_offset'] = kwargs['int_offset']
            cls.config['SENSORS']['ext_offset'] = kwargs['ext_offset']
            cls.config['APP']['buzzer'] =  kwargs['buzzer']
            cls.config['SENSORS']['id_sens_int'] = kwargs['id_sens_int']
            cls.config['SENSORS']['id_sens_ext'] = kwargs['id_sens_ext']
            cls.config['AUDIO']['sound_volume'] = kwargs['sound_volume']

            if backup == False:
                conf_path = cls.config_file_path
            else:
                conf_path = cls.config_backup_path

            with open(conf_path, 'w', encoding='utf-8') as configfile:
                cls.config.write(configfile)
            cls.read_config()
        except Exception as ex:
            cls.logger.error(ex)
            #cls.logger.info(ex)
            raise ex


