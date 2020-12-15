#-----------------------------------------------#
#   Interface class for I/O data dispatching
#-----------------------------------------------#

from multiprocessing import Process, Value, Array, active_children
from packages import Shared
from packages.ConfigModule import ConfigModule
from packages.TempConverter import TempConverter
import gpiozero
from gpiozero import DigitalOutputDevice, DigitalInputDevice
from gpiozero import LED
from gpiozero import CPUTemperature
if ConfigModule.mockup == True: # mockup mode in Windows development or output debug
    from Test.gpiozero.pins.mock import MockFactory
    gpiozero.Device.pin_factory = MockFactory()

import threading
import time
import subprocess
from sys import platform
from datetime import datetime
from datetime import timedelta

from kivy.app import App

logger = ConfigModule.getLogger()
io_logger = ConfigModule.getIOLogger()

    # ------------- I/O STATUS CODES:
    #               0:   ---> standby
    #               1:   ---> HI heater ON
    #               10:  ---> LO heater ON
    #               11:  ---> LO + HI heater ON
    #               100: ---> Compressor ON
    #               200: ---> generic error in reading
    #               201: ---> temperature out of range
    #               301: ---> error reading chamber sensor
    #               302: ---> error reading external sensor
    #               603: ---> error reading both sensors


#-------------- POWER STATUS CODES:
#               0:   ---> ok
#               300: ---> temporary power lack detected
#               350: ---> main power failure

# ----------- RGB TABLE ---------------------------
# DEVICE    |    COLOR      |       GPIO
#--------------------------------------------------
# LO_heat   |    YELLOW     |   green + red
# HI_heat   |    PURPLE     |   red + blue
# Lo + Hi   |    RED        |   red
# Compr     |    BLUE       |   blue


#singleton!!!!
class IOInterface(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance


    LO_heater = DigitalOutputDevice(13)
    HI_heater = DigitalOutputDevice(19)
    Compressor = DigitalOutputDevice(26)
    Fan = DigitalOutputDevice(6)
    Red_LED = LED(16)       #RED
    Green_LED = LED(20)     #GREEN
    Blue_LED = LED(21)      #BLUE
    Power_LED = LED(5)     #POWER
    #RGB LED power pin GREEN --> +5V
    #connect to RED pin of RGB power LED

    if ConfigModule.mockup == True:

        Wd_pow = Value('i', 1)
    else:
        Wd_pow = DigitalInputDevice(22) # power watchdog

    @classmethod
    def rgb_mapper(cls, lo_heater, hi_heater, compressor):

        states = f"{lo_heater}{hi_heater}{compressor}"
        codes =   { #lHc    R G B
                    '000': (0,0,0, 'NONE'    ),
                    '001': (0,0,1, 'BLUE'   ),
                    '010': (1,0,1, 'PURPLE' ),
                    '011': (1,1,1, 'WHITE'  ),
                    '100': (1,1,0, 'YELLOW' ),
                    '101': (1,1,1, 'WHITE'  ),
                    '110': (1,0,0, 'RED'    ),
                    '111': (1,1,1, 'WHITE'  )

                    }

        return codes.get(states)

    io_status_codes = { 0: 'OK',
                        200: 'GENERIC ERROR IN READING',
                        201: 'TEMPERATURE OUT OF RANGE',
                        301: 'ERROR READING CHAMBER SENSOR',
                        302: 'ERROR READING EXTERNAL SENSOR',
                        603: "ERROR READING BOTH SENSORS",
                        50: 'COMPRESSOR PROTECTION RUNNING'
                        }

    int_sens_offset = float(ConfigModule.int_sens_offset)
    ext_sens_offset = float(ConfigModule.ext_sens_offset)

    temp_scale = ConfigModule.temp_scale
    tc  = TempConverter()
    comp_on_counter = 0 # compressor start counter
    ups_shutdown_counter = 0
    power_loss_flag = False
    time_sd = datetime.now() + timedelta(minutes=1)

    loop_sleep = 3 # while loop pause



    comp_prot_time_start = datetime.now()
    comp_prot_expire_time = datetime.now() + timedelta(minutes=1)
    enable_comp = True
    disable_comp_timer = False
    process_name = 'IO_Process'
    pwm = False
    stop_check_sensor_1 = False
    stop_check_sensor_2 = False
    status_603_flag = False # need a flag to prevent multiple writing in log; once issue 603 detected, is necessary to restart app
    status_201_flag = False



    @classmethod
    def shutdown(cls):
        logger.info(f"POWER FAILURE. PERFORMING SAFE SHUTDOWN...")
        if (platform == 'linux' or platform == 'linux2'):
            cmd = ["shutdown", "-h", "now"]
            sb= subprocess.run(
                                cmd,
                                check = True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True
                               )
            if sb.returncode == 1:
                logger.error(f"{sb.stdout}")

    @classmethod
    def reset_output(cls):
        Shared.ENABLE_OUTPUT.value = 0
        cls.LO_heater.off()
        cls.HI_heater.off()
        cls.Compressor.off()

        logger.info('OUTPUT DEVICES OFF!!!')

    @classmethod
    def comp_prot(cls):
       cls.enable_comp = True


    comp_prot_timer = threading.Timer(abs(ConfigModule.COMP_PROT), comp_prot)


    @classmethod
    def IO_loop(cls,T_meas, T_ext, T_targ, lo_heater, hi_heater, compressor, enable, cpu_temp, status_code, power_status, compressor_protection_code):

        while(True):
            if ConfigModule.mockup == True:
                with open('./Test/power.txt','r') as test_value:
                    power_test = int(test_value.read())
                    cls.Wd_pow.value=power_test
            try:

                if cls.Wd_pow.value == 1: # reset shutdown counter if watchdog signal is detected (power)
                    power_status.value = 0
                    cls.time_sd = datetime.now() + timedelta(minutes=1)
                    if cls.power_loss_flag == True: # True if power loss was detected
                        power_status.value = 300
                        logger.error(f"POWER RESTORED!")
                        io_logger.info(f"POWER RESTORED!")
                    cls.power_loss_flag = False

                elif cls.Wd_pow.value == 0 and ConfigModule.ups_shutdown !=0 and power_status.value !=350:
                    power_status.value = 350
                    cls.time_sd = (datetime.now() + timedelta(seconds=ConfigModule.ups_shutdown))
                    time_formatted = cls.time_sd.strftime("%d/%b/%y %H:%M:%S")
                    logger.error(f"MAIN POWER FAILURE DETECTED !!!")
                    io_logger.error(f"MAIN POWER FAILURE DETECTED !!!")
                    logger.info(f"SHUTDOWN IN {int(ConfigModule.ups_shutdown/60)} MINUTES AT TIME: {time_formatted}")
                    io_logger.info(f"SHUTDOWN IN {int(ConfigModule.ups_shutdown/60)} MINUTES AT TIME: {time_formatted}")

                    cls.power_loss_flag = True # flag that we have power loss
                else:
                    pass

                if datetime.now() >= cls.time_sd and ConfigModule.ups_shutdown !=0:
                    enable.value = 0
                    cls.reset_output()
                    logger.info('SHUTDOWN SYSTEM!!!')
                    io_logger.info('SHUTDOWN SYSTEM!!!')
                    power_status.value = 360
                    time.sleep(5) # wait to send notification mail...
                    cls.shutdown()
                    break

                int_sens_path = f"{ConfigModule.devices_dir}/{ConfigModule.id_sens_int}/w1_slave"
                ext_sens_path = f"{ConfigModule.devices_dir}/{ConfigModule.id_sens_ext}/w1_slave"
                # READING EXAMPLE:
                #31 00 4b 46 ff ff 02 10 72 : crc=72 YES
                #31 00 4b 46 ff ff 02 10 72 t=15000
                retries = 0
                while retries <= 5 and cls.stop_check_sensor_1 == False:
                    with open(int_sens_path, "r") as stream_int:
                        data_int = stream_int.read()
                        if ConfigModule.mockup == True: time.sleep(1)
                        if "YES" in data_int:
                            (discard, sep, reading) = data_int.partition(' t=')
                            temp = float(reading) / 1000.0
                            T_meas.value = temp + ConfigModule.int_sens_offset
                            logger.info(f"CHAMBER TEMPERATURE: {T_meas.value} C")
                            #if status_code.value <=200: status_code.value = 0
                            if temp >= 85:
                                if retries >=5:
                                    status_code.value = 301
                                    enable.value = 0
                                    cls.reset_output()
                                    logger.error(f"STATUS CODE: {status_code.value}, CHAMBER MEASURE: {T_meas.value}")
                                    io_logger.error(f"ERROR {status_code.value}: {cls.io_status_codes.get(status_code.value)}")
                                    cls.stop_check_sensor_1 = True
                            else:
                                break
                        else:
                            if retries >=5:
                                status_code.value = 301
                                T_meas.value = 85
                                enable.value = 0
                                cls.reset_output()
                                logger.error(f"STATUS CODE: {status_code.value}, CHAMBER MEASURE: {T_meas.value}")
                                io_logger.error(f"ERROR {status_code.value}: {cls.io_status_codes.get(status_code.value)}")
                                cls.stop_check_sensor_1 = True

                    logger.info(f"RETRIES READING INTERNAL SENSOR: {retries} OF 5")
                    time.sleep(1)
                    retries+=1


                retries = 0
                while retries <= 5 and cls.stop_check_sensor_2 == False:
                    with open(ext_sens_path, "r") as stream_ext:
                        data_ext = stream_ext.read()
                        if ConfigModule.mockup == True: time.sleep(1)
                        if "YES" in data_ext:
                            (discard, sep, reading) = data_ext.partition(' t=')
                            temp = float(reading) / 1000.0
                            T_ext.value =  temp + ConfigModule.ext_sens_offset
                            logger.info(f"EXTERNAL TEMPERATURE: {T_ext.value} C")
                            #if status_code.value <=200: status_code.value = 0
                            if temp >= 85:
                                if retries >=5:
                                    status_code.value = 302
                                    logger.error(f"STATUS CODE: {status_code.value}, EXT MEASURE: {T_ext.value}")
                                    io_logger.error(f"ERROR {status_code.value}: {cls.io_status_codes.get(status_code.value)}")
                                    enable.value = 0
                                    cls.stop_check_sensor_2 = True
                            else:
                                break

                        else:
                            if retries >=5:
                                status_code.value = 302
                                T_ext.value = 85
                                logger.error(f"STATUS CODE: {status_code.value}, EXT MEASURE: {T_ext.value}")
                                io_logger.error(f"ERROR {status_code.value}: {cls.io_status_codes.get(status_code.value)}")
                                enable.value = 0
                                cls.reset_output()
                                cls.stop_check_sensor_2 = True

                    logger.info(f"RETRIES READING EXTERNAL SENSOR: {retries} OF 5")
                    time.sleep(1)
                    retries+=1


                if cls.stop_check_sensor_1 == True and cls.stop_check_sensor_2 == True and cls.status_603_flag == False:
                    status_code.value = 603
                    io_logger.error(f"ERROR {status_code.value}: {cls.io_status_codes.get(status_code.value)}")
                    cls.status_603_flag = True
                    enable.value = 0



                # disable output when over range

                if (T_meas.value >= ConfigModule.T_max_C + 5  or T_meas.value <= ConfigModule.T_min_C - 5) and status_code.value < 300 and cls.status_201_flag == False:

                    status_code.value = 201
                    io_logger.error(f"ERROR {status_code.value}: {cls.io_status_codes.get(status_code.value)}")
                    cls.status_201_flag = True
                    enable.value = 0
                    cls.reset_output()


                if status_code.value <=200 and power_status.value <300:
                    cls.Power_LED.off()
                else:
                    cls.Power_LED.blink(0.5,0.5)

        #------------ CODE EXECUTION WHEN ENABLED ----------------------------------------------------

                if enable.value == 1:

        #--------------- OUTPUT ALGHORITM -------------------------------------------------------------

                    if T_meas.value <= (T_targ.value - abs(ConfigModule.HH_HL)):
                        cls.HI_heater.on()
                        cls.LO_heater.on()
                        cls.Compressor.off()
                        cls.pwm = False


                    elif (T_meas.value > T_targ.value - abs(ConfigModule.HH_HL)) and (T_meas.value <= T_targ.value - abs(ConfigModule.HH)):
                        cls.HI_heater.on()
                        cls.LO_heater.off()
                        cls.Compressor.off()
                        cls.pwm = False



                    elif (T_meas.value > T_targ.value - abs(ConfigModule.HH)) and (T_meas.value <= T_targ.value - abs(ConfigModule.HL)):
                        cls.HI_heater.off()
                        cls.LO_heater.on()
                        cls.Compressor.off()
                        cls.pwm = False



                    elif T_meas.value > T_targ.value - abs(ConfigModule.HL) and T_meas.value <= T_targ.value - abs(ConfigModule.HL_PWM):
                        # need to flag when threading blink begins.If blinking time > time.sleep, blink not works in while loop (blink seems to restart on every cycle)
                        if cls.pwm == False:
                            cls.LO_heater.blink(abs(ConfigModule.ON_PWM), abs(ConfigModule.OFF_PWM))
                            cls.pwm = True
                        cls.HI_heater.off()
                        cls.Compressor.off()

                    # when temperature rising into hysteresys area, pwm remains True until NEG_OFF because there is no evaluation case.
                    # When temperature falls out from target, outupt remains OFF until it reaches HL_PWM value
                    # This prevents continuous outputs switching around HL_PWM value

                    elif T_meas.value > T_targ.value-abs(ConfigModule.NEG_OFF) and T_meas.value <= T_targ.value + abs(ConfigModule.POS_OFF):
                        cls.reset_output()
                        enable.value = 0
                        cls.pwm = False



                    elif T_meas.value > T_targ.value + abs(ConfigModule.COMP):
                        cls.pwm = False
                        cls.HI_heater.off()
                        cls.LO_heater.off()
                        if cls.enable_comp == True: # at startup we assume that the compressor can be turned on safely
                            cls.Compressor.on()
                            compressor_protection_code.value = 0
                            cls.disable_comp_timer = False
                            cls.comp_on_counter +=1


    #--------------- COMPRESSOR PROTECTION -------------- WARNING: This routine must be inserted AFTER output evalutation.
                    if  cls.Compressor.value ==0  and cls.comp_prot_timer.is_alive() is False and cls.disable_comp_timer == False and cls.comp_on_counter !=0 : #is_alive() is true just before start until just after stop
                        compressor_protection_code.value = 0
                        cls.comp_prot_timer = threading.Timer(ConfigModule.COMP_PROT, cls.comp_prot)
                        cls.comp_prot_timer.start() # now is_alive() is False
                        cls.enable_comp = False
                        cls.comp_prot_time_start = datetime.now()
                        cls.comp_prot_expire_time = cls.comp_prot_time_start + timedelta(seconds = ConfigModule.COMP_PROT-cls.loop_sleep-10)
                        logger.info('COMPRESSOR PROTECTION TIMER START')


                    if  (datetime.now() > cls.comp_prot_expire_time) and cls.disable_comp_timer == False:
                        while cls.comp_prot_timer.is_alive() is True:
                            cls.comp_prot_timer.cancel()
                        logger.info('COMPRESSOR PROTECTION TIMER EXPIRED')
                        compressor_protection_code.value = 0
                        cls.comp_prot()
                        cls.comp_prot_expire_time = datetime.now()+ timedelta(seconds=100)
                        cls.disable_comp_timer = True


                    if cls.comp_prot_timer.is_alive() is True:
                        elapsed = (datetime.now()-cls.comp_prot_time_start).seconds
                        compressor_protection_code.value = 300
                        logger.info(f"COMPRESSOR AVAILABLE IN : {ConfigModule.COMP_PROT - elapsed :.0f} SECONDS")
                        print(f"COMPRESSOR AVAILABLE IN : {ConfigModule.COMP_PROT - elapsed :.0f} SECONDS")



    #---------------------------------------------------------------------------------------------------
                # when Shared.ENABLE_OUTPUT == 0
                else:
                    cls.reset_output()

    #--------------------------------- FAN -------------------------------------------------------------
                if cpu_temp.value >=70:
                    cls.Fan.on()
                else:
                    cls.Fan.off()

            # read output values from GPIO pins
                hi_heater.value = cls.HI_heater.value
                lo_heater.value = cls.LO_heater.value
                compressor.value = cls.Compressor.value

                if status_code.value < 200:
                    status_code.value = int(f"{compressor.value}{lo_heater.value}{hi_heater.value}")

                cls.Red_LED.value, cls.Green_LED.value, cls.Blue_LED.value, color = cls.rgb_mapper( lo_heater.value,
                                                                                                        hi_heater.value,
                                                                                                        compressor.value)
                logger.info(f"RGB LED COLOR: {color}")
                logger.info(f"LO HEATER STATE: {lo_heater.value}")
                logger.info(f"HI HEATER STATE: {hi_heater.value}")
                logger.info(f"COMPRESSOR STATE: {compressor.value}")


                time.sleep(cls.loop_sleep)

            except Exception as err:
                logger.error(err)
                status_code.value = 200
                io_logger.error(f"ERROR {status_code.value}: {cls.io_status_codes.get(status_code.value)}")
                cls.reset_output()

    @classmethod
    def start_io_interface(cls):

        IO_process = Process(target=cls.IO_loop,
                             name = cls.process_name,
                             args= (
                                    Shared.TEMP_MEAS,
                                    Shared.TEMP_EXT,
                                    Shared.ACTUAL_TEMP_TARGET,
                                    Shared.LO_HEATER_STATE,
                                    Shared.HI_HEATER_STATE,
                                    Shared.COMPRESSOR_STATE,
                                    Shared.ENABLE_OUTPUT,
                                    Shared.CPU_TEMP,
                                    Shared.IO_STATUS_CODE,
                                    Shared.POWER_STATUS_CODE,
                                    Shared.COMPRESSOR_PROTECTION_CODE
                                    )
                            )
        IO_process.start()

    @classmethod
    def stop_io_interface(cls):
        for p in active_children():
            if p.name == cls.process_name:
                logger.info(f"Terminating active processes: {p.name}")
                p.terminate()