import gpiozero
import time

from multiprocessing import Process, Value, Array, active_children
from packages import Shared
from packages.ConfigModule import ConfigModule
from gpiozero import Buzzer

if ConfigModule.mockup == True: # mockup mode in Windows development or output debug
    from gpiozero.pins.mock import MockFactory
    gpiozero.Device.pin_factory = MockFactory()



logger = ConfigModule.getLogger()


class BuzzController(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    process_name = 'Buzz_loop'
    Buzzer = Buzzer(17)


    @classmethod
    def BuzzLoop(cls, buzz, enable):
        counter = 0
        while(True):

#---------------- BUZZER ------------------------------------------------
    #       0 = DISABLED
    #       1 = CONTINUOS BEEP
    #       2 = SLOW RATE CONTINUOUS BEEP
    #       3 = HIGH RATE CONTINUOUS BEEP (20 times) --> warning
    #       4 = PULSE BEEP (BLIP)--> button
    #       5 = DOUBLE BEEP - PAUSE - DOUBLE BEEP (10 times) --> end program
    #       6 = LONG BEEP - PAUSE - LONG BEEP (10 times)
    #       7 = LONG BEEP (1 time) --> start program
    #       8 = SHORT BEEP --> phase change

            if counter >= 10 or enable.value == False:
                buzz.value = 0
                counter = 0

            if buzz.value ==  0:
                #logger.info(f"BUZZER STATE CODE: {buzz.value}")
                cls.Buzzer.off()
            elif buzz.value == 1:
                logger.info(f"BUZZER STATE CODE: {buzz.value}")
                cls.Buzzer.on()
            elif buzz.value == 2:
                logger.info(f"BUZZER STATE CODE: {buzz.value}")
                cls.Buzzer.on()
                time.sleep(1)
                cls.Buzzer.off()
                time.sleep(1)
            elif buzz.value == 3:
                logger.info(f"BUZZER STATE CODE: {buzz.value}")
                cls.Buzzer.on()
                time.sleep(0.3)
                cls.Buzzer.off()
                time.sleep(0.1)
                counter+=0.5
            elif buzz.value == 4:
                logger.info(f"BUZZER STATE CODE: {buzz.value}")
                cls.Buzzer.on()
                #time.sleep(0.05)
                buzz.value = 0
            elif buzz.value == 5:
                logger.info(f"BUZZER STATE CODE: {buzz.value}")
                cls.Buzzer.on()
                time.sleep(0.1)
                cls.Buzzer.off()
                time.sleep(0.1)
                cls.Buzzer.on()
                time.sleep(0.1)
                cls.Buzzer.off()
                time.sleep(0.5)
                counter+=1
            elif buzz.value == 6:
                logger.info(f"BUZZER STATE CODE: {buzz.value}")
                cls.Buzzer.on()
                time.sleep(1)
                cls.Buzzer.off()
                time.sleep(3)
                counter+=1
            elif buzz.value == 7:
                logger.info(f"BUZZER STATE CODE: {buzz.value}")
                cls.Buzzer.on()
                time.sleep(1.5)
                cls.Buzzer.off()
                counter = 10
            elif buzz.value == 8:
                logger.info(f"BUZZER STATE CODE: {buzz.value}")
                cls.Buzzer.on()
                time.sleep(0.5)
                cls.Buzzer.off()
                counter = 10

            #logger.info(f"BUZZER STATE: {cls.Buzzer.value}")

            time.sleep(0.1)

    @classmethod
    def start_buzzer(cls):

        Buzz_process = Process(target=cls.BuzzLoop,
                            name = cls.process_name,
                            args= (
                                    Shared.BUZZER,
                                    Shared.BUZZ_ENABLE,
                                    )
                            )
        Buzz_process.start()


    @classmethod
    def stop_buzzer(cls):
        for p in active_children():
            if p.name == cls.process_name:
                logger.info(f"Terminating active processes: {p.name}")
                p.terminate()