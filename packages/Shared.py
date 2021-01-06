from datetime import datetime
from multiprocessing import Value, Array, Lock
from ctypes import c_char, c_wchar, c_bool
lock = Lock()


TEMP_UNIT_SCALE = 'C'
TEMP_MEAS = Value('d', 0.0)
TEMP_EXT = Value('d', 0.0)
ENABLE_OUTPUT = Value('i',  0)
ACTUAL_TEMP_TARGET= Value('d', 0.0)
BUZZER = Value('i',  0)
BUZZ_ENABLE = Value(c_bool, False)
CHAMBER_LIGHT= Value('i',  0)
SERVER_STATUS = Value('i',  400)
IO_STATUS_CODE = Value('i', 0)
PRGM_STATUS_CODE = Value('i', 0)
POWER_STATUS_CODE = Value('i', 0)
REMAINING_TIME_FMT =  Array(c_char, b'------------------------------', lock = lock) #30 chars max
PROGRAM_DETAILS = Array(c_char, b'----------------------------------------------------------------------------------------------------', lock = lock) #100 chars max

CPU_TEMP = Value('d', 0.0)

TEMP_INCREMENT = 0.5
EXCEPTION_STRING = ''



LO_HEATER_STATE = Value('i',  0)
HI_HEATER_STATE= Value('i',  0)
COMPRESSOR_STATE = Value('i',  0)
COMPRESSOR_PROTECTION_CODE = Value('i',0)


TEMP_BOUND_MIN = -18      # Shared bounds are setted in every validation event. This facilitate chart draw
TEMP_BOUND_MAX = 45

LO_HEATER_STATE_LBL = ''
HI_HEATER_STATE_LBL = ''
LO_HI_HEATER_STATE_LBL =''
COMPRESSOR_STATE_LBL = ''
SLEEPING_LBL = ''
WARNING_LBL = ''

HOME = True
LOAD_FROM_MEM = False
PROGRAM = ''
MEM_SCREEN = Value('i',  0)


#-------------------PRESTART VARIABLES--------------------------
PRESTART_START_DATE= datetime.now()







#-------------------MULTIPHASE VARIABLES--------------------------
MP_ELAPSED_TIME = 0.0
MP_REMAINING_TIME = Value('d', 0.0)
MP_ELAPSED_TIME_IN_SECONDS = Value('d', 0.0)
MP_TIME_END = datetime.now()
MP_TOTAL_DURATION= 0.5
MP_ACTUAL_PHASE_DURATION = Value('d', 0.5)

MP_ACTUAL_PHASE = Value(c_wchar,  '1')

MP_DURATION_DICT = {}
MP_PRG_DURATION_DICT = {}
MP_TEMP_TARGET_DICT = {}

MP_TIMER_BEGIN = datetime.now()
MP_PROGRAM_IS_RUNNING = False




def reset_all(self):
    self.ENABLE_OUTPUT.value = 0
    self.HOME = True
    self.LOAD_FROM_MEM = False
    self.PROGRAM = ''
    self.CHAMBER_LIGHT.value = 0
    self.LO_HEATER_STATE.value = 0
    self.HI_HEATER_STATE.value= 0
    self.COMPRESSOR_STATE.value = 0
    self.COMPRESSOR_PROTECTION_CODE.value =0
    #self.IO_STATUS_CODE.value = 0
    self.PRGM_STATUS_CODE.value = 0
    self.PRESTART_START_DATE= datetime.now()
    

    #self.MP_ELAPSED_TIME.value = 0.0
    self.MP_TIME_END = datetime.now()
    self.MP_TOTAL_DURATION= 0.5
    self.MP_ACTUAL_PHASE_DURATION.value = 0.5
    self.ACTUAL_TEMP_TARGET.value = 0
    self.MP_ACTUAL_PHASE.value = '1'
    self.BUZZER.value = 0
    #self.BUZZ_ENABLE.value  = False
    #self.POWER_STATUS_CODE.value = 0

    self.MP_DURATION_DICT = {}
    self.MP_PRG_DURATION_DICT = {}
    self.MP_TEMP_TARGET_DICT = {}

    self.MP_TIMER_BEGIN = datetime.now()
    self.MP_TIMER_NOW = 0.0
    self.MP_PROGRAM_IS_RUNNING = False
    self.TEMP_BOUND_MIN = 0
    self.TEMP_BOUND_MAX = 0




TEST_MULTIPROCESS_OUT = {}




