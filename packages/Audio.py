import subprocess
from kivy.core.audio import SoundLoader
from packages.ConfigModule import ConfigModule
from sys import platform
from threading import Thread
import time

logger = ConfigModule.getLogger()

class PlaySound:
    # int range amixer volume :-10239 - 400

    volume = 0
    mute = False
    mem_volume = 0
    source = ''
    busy = False

    def set_output_device(self, device): # 0= auto, 1 = headphones, 2 = HDMI
        try:
            numid = f"numid={device}"
            sb0= subprocess.run(["amixer","cset", numid],
                                check = True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True)
            if sb0.returncode == 0: logger.info(f"{sb0.stdout}")
        except subprocess.CalledProcessError as err:
            logger.error(err)
        finally:
            return

    # values accepted: 0 to 100
    def set_volume(self, volume, enable= True, control = '0', card = '0'):
        if enable == False or (platform != "linux" and platform != "linux2"):
            return
        sb1=None
        try:
            if volume > 100: volume = 100
            if volume <= 0 :
                volume = 0
                self.mute = True
            else:
                self.mute = False
            volume_percentage = f"{abs(volume)}%"
            numid = f"numid={control}"
            sb1= subprocess.run(["sudo","amixer", "-c", card, "cset", numid, volume_percentage],
                                check = True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True)
            if sb1.returncode == 0: logger.info(f"{sb1.stdout}")

        except Exception as err:
            sb1.kill()
            logger.error(err)

        # store volume value
        self.mem_volume = volume

    # volume parameter mandatory only on Windows platform (debug environment)
    def play(self, volume = 1 , enable = True, card = '0', delay = 0):
        if enable == False or self.mute == True:
            self.busy = False
            return
        sb2=None
        try:
            time.sleep(delay)
            if platform == 'win32' or platform == 'win64' and self.busy==False:
                sound = SoundLoader.load(str(self.source))
                sound.volume = volume/100
                if sound.state == 'stop':
                    self.busy = True
                    sound.play()
                else:
                    sound.stop()
            elif platform == 'linux' or platform == 'linux2' and self.busy==False:
                self.busy = True
                default_card= f"default:CARD={card}"
                sb2 = subprocess.Popen(["sudo", "aplay","-D", default_card, str(self.source)],stdout=subprocess.PIPE) #"-N" non-blocking
                stdout_value, stdout_err = sb2.communicate()
                logger.info(f"STDOUT_VALUE: {repr(stdout_value)}")
                logger.info(f"STDOUT_ERR: {repr(stdout_err)}")

        except Exception as err:
            sb2.kill()
            logger.error(err)
        finally:
            self.busy = False

    # play sound in async mode
    def aplay(self, volume = 1, enable = True, card = 0, delay = 0):
        if enable == False or self.mute ==True:
            return
        async_play = Thread(target = self.play, args = (volume, enable, card, delay,))
        async_play.start()

