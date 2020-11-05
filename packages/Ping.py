from kivy.clock import Clock
from threading import Thread
from sys import platform
import subprocess
import os

from packages.ConfigModule import ConfigModule


logger = ConfigModule.getLogger()
net_logger = ConfigModule.getNETLogger()

class ping:

    ClockObj = None
    is_running = False
    ip = ''
    return_value = 0
    connected = False
    net_logger_flag = False

    def start(self, enable = True):
        if enable == False:
            self.return_value = 0
            self.is_running = False
            return

        if self.ClockObj is None:
            self.ClockObj= Clock.create_trigger(self.aping, 30, True)
            self.ClockObj()
            self.is_running = True


    def stop(self):
        if self.ClockObj is not None:
            self.ClockObj.cancel()
            self.ClockObj = None
            self.is_running = False

    def update(self):
        try:
            if platform == 'win32' or platform == 'win64':
                cmd = ["ping", self.ip]
                sb= subprocess.run  (
                                    cmd,
                                    check = True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    universal_newlines=True
                                    )
                if sb.returncode == 0:
                    logger.info(f"{sb.stdout}")
                    self.return_value = 1
                    self.connected = True
                else:
                    self.return_value = 0
                    self.connected = False
            else:
                cmd = ["ping", self.ip, "-c1", "-W2", "-q"]
                sb = subprocess.call(cmd, stdout=open(os.devnull,"w"), timeout=3)
                if sb == 0:
                    self.return_value = 1
                    self.connected = True
                else:
                    self.return_value = 0
                    self.connected = False
            logger.debug(f"[SUBPROC. PING CALL RETURN VALUE: {sb}")
            self.net_logger_flag = False
        except Exception as ex:    
            if self.net_logger_flag == False: # write once logger
                logger.error(ex)
                net_logger.error(ex)
                self.net_logger_flag = True
                raise
            return 0

    def aping(self,dt):
        async_ping = Thread(target = self.update)
        async_ping.start()