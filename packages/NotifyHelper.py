from kivy.clock import Clock
from kivy.app import App
from kivy.properties import NumericProperty
from kivy.event import EventDispatcher

import time
import smtplib, ssl

from email.message import EmailMessage
from threading import Thread
from datetime import datetime

from packages import Shared
from packages.ConfigModule import ConfigModule
from packages.TempConverter import TempConverter



logger = ConfigModule.getLogger()
io_logger = ConfigModule.getIOLogger()
net_logger = ConfigModule.getNETLogger()



class NotifyHelper(EventDispatcher):

    io_status_mail_sended = False
    observer_clock = None
    tc = TempConverter()

    io_status_code = NumericProperty(0)
    power_status_code = NumericProperty(0)
    prgm_status_code = NumericProperty(0)


    def start_observer(self):
        if self.observer_clock is None:
            self.observer_clock = Clock.create_trigger(self.read_status, 0.5, True)
            self.observer_clock()

    def read_status(self, dt):
        self.io_status_code = Shared.IO_STATUS_CODE.value
        self.prgm_status_code = Shared.PRGM_STATUS_CODE.value
        self.power_status_code = Shared.POWER_STATUS_CODE.value


    def on_io_status_code(self,*kwargs):

        self.build_mail(send=ConfigModule.mail_notify, io_status_code=Shared.IO_STATUS_CODE.value, prgm_status_code = 0, power_status_code=0)

    def on_prgm_status_code(self,*kwargs):

        self.build_mail(send=ConfigModule.mail_notify, io_status_code=0, prgm_status_code = Shared.PRGM_STATUS_CODE.value, power_status_code=0)

    def on_power_status_code(self,*kwargs):

        self.build_mail(send=ConfigModule.mail_notify, io_status_code=0, prgm_status_code = 0, power_status_code=Shared.POWER_STATUS_CODE.value)

    def sendmail(self, sender, receiver, subject, body, timeout, attachment_1='', attachment_2='', enable =True):
        #set google access for less secure apps:  https://myaccount.google.com/lesssecureapps?pli=1
        if enable == False: return

        try:

            msg = EmailMessage()
            msg["From"] = sender
            msg["Subject"] = subject
            msg["To"] = receiver
            msg.set_content(body)

            for files in attachment_1:
                msg.add_attachment(open(files, "r").read(), filename=files)
            for files in attachment_2:
                msg.add_attachment(open(files, "r").read(), filename=files)

            context = ssl.create_default_context()

            with smtplib.SMTP_SSL(ConfigModule.host, ConfigModule.port, context=context, timeout= timeout) as server:
                server.login(ConfigModule.username, ConfigModule.password)
                server.send_message(msg)
        except Exception as ex:
            logger.error(f"SEND MAIL ERROR: {ex}")
            net_logger.error(f"SEND MAIL ERROR: {ex}")
            raise
        finally:
            self.mail_is_sending = False


    def asendmail(self, sender, receiver, subject, body, timeout, attachment_1='', attachment_2 ='', enable = True):
        if enable == False: return
        self.mail_is_sending = True
        async_send = Thread(target =self.sendmail, args = (sender, receiver ,subject, body, timeout, attachment_1, attachment_2, enable,))
        async_send.start()


#----------------------------STATUS TABLE-------------------
#io_0 =         'STANDBY'
#io_1 =         'HI heater ON'
#io_10 =        'LO heater ON'
#io_11 =        'HI + LO heater ON'
#io_100 =       'COMPRESSOR ON'
#io_200 =       'GENERIC ERROR IN READING'
#io_201 =       'TEMPERATURE OUT OF RANGE'
#io_301 =       'ERROR READING CAMERA SENSOR'
#io_302 =       'ERROR READING EXTERNAL SENSOR'
#io_603 =       'ERROR READING BOTH SENSORS'
#io_50 =        'COMPRESSOR PROTECTION RUNNING'

#prgm_0 =       'IDLE'
#prgm_100 =     'PROGRAM RUNNING'
#prgm_110 =     'START PROGRAM'
#prgm_120 =     'CHANGE PHASE'
#prgm_130 =     'STOP PROGRAM'
#prgm_150 =     'END PROGRAM'

#power_0 =      'OK'
#power_300 =    'MAIN POWER RESTORED'
#power_350 =    'MAIN POWER FAILURE'
#power_360 =    'SYSTEM SHUTDOWN'
#------------------------------------------------------------


    def build_mail(self, io_status_code=0, prgm_status_code = 150, power_status_code=0, temp_meas=0, 
                    temp_target=0, program='', program_details = '', mail_subject='', mail_heading='', attachment = '', timeout = 5, send = False):

        if send == False: return
        app = App.get_running_app()

        try:
            screen_name =       {
                                0: app.no_program,
                                1: app.prestart_set_title,
                                2: app.prestart_dash_title,
                                3: app.multiphase_set_title,
                                4: app.multiphase_dash_title,
                                5: app.no_program,
                                6: app.no_program,
                                7: app.no_program
                                }

            io_status_codes =   {
                                0:   app.io_0,
                                200: app.io_200,
                                201: app.io_201,
                                301: app.io_301,
                                302: app.io_302,
                                603: app.io_603,
                                50:  app.io_50
                                }

            prgm_status_codes =     {
                                    0:   app.prgm_0,
                                    100: app.prgm_100,
                                    110: app.prgm_110,
                                    120: app.prgm_120,
                                    130: app.prgm_130,
                                    150: app.prgm_150
                                    }


            power_status_codes =   {
                                    0:   app.power_0,
                                    300: app.power_300,
                                    350: app.power_350,
                                    360: app.power_360
                                    }



            time_now = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
            temp_target_c = Shared.ACTUAL_TEMP_TARGET.value
            temp_target_f = self.tc.c_to_f(Shared.ACTUAL_TEMP_TARGET.value)
            temp_camera_c = Shared.TEMP_MEAS.value
            temp_camera_f = self.tc.c_to_f (Shared.TEMP_MEAS.value)
            temp_ext_c = Shared.TEMP_EXT.value
            temp_ext_f = self.tc.c_to_f (Shared.TEMP_EXT.value)
            program = Shared.PROGRAM
            program_details = Shared.PROGRAM_DETAILS.value

            if io_status_code >=200:

                out_state_mail_body =   f"{time_now}\n{screen_name.get(Shared.MEM_SCREEN.value)}\n" +\
                                        f"{app.multiphase_program_lbl.upper()}: {program}\n" +\
                                        f"{app.multiphase_dash_phase}: {Shared.MP_ACTUAL_PHASE.value}\n" +\
                                        f"{app.mail_header_io_state} {io_status_codes.get(io_status_code)}\n" +\
                                        f"{app.prestart_set_temp_target.upper()}: {temp_target_c} °C / {temp_target_f} °F\n" +\
                                        f"{app.camera_temp_lbl.upper()}: {temp_camera_c:.1f} °C / {temp_camera_f:.1f} °F\n" +\
                                        f"{app.ext_temp_lbl.upper()}: {temp_ext_c:.1f} °C / {temp_ext_f:.1f} °F"

                mail_subject = app.mail_subj_io_state
                mail_body = out_state_mail_body


                self.asendmail( sender = ConfigModule.mail_sender,
                                receiver = ConfigModule.mail_receiver,
                                subject = mail_subject,
                                body = mail_body,
                                attachment_1= attachment,
                                timeout = timeout,
                                enable = send
                                )



            if prgm_status_code >=100:

                prgm_state_mail_body =  f"{time_now}\n{screen_name.get(Shared.MEM_SCREEN.value)}\n" +\
                                        f"{app.multiphase_program_lbl.upper()}: {program}\n"+\
                                        f"{app.multiphase_dash_phase}: {Shared.MP_ACTUAL_PHASE.value}\n" +\
                                        f"{app.mail_header_prgm_state} {prgm_status_codes.get(prgm_status_code)}\n" +\
                                        f"{app.prestart_set_temp_target.upper()}: {temp_target_c} °C / {temp_target_f} °F\n" +\
                                        f"{app.camera_temp_lbl.upper()}: {temp_camera_c:.1f} °C / {temp_camera_f:.1f} °F\n" +\
                                        f"{app.ext_temp_lbl.upper()}: {temp_ext_c:.1f} °C / {temp_ext_f:.1f} °F"

                mail_subject = app.mail_subj_prgm_state
                mail_body = prgm_state_mail_body




                self.asendmail( sender = ConfigModule.mail_sender,
                                receiver = ConfigModule.mail_receiver,
                                subject = mail_subject,
                                body = mail_body,
                                attachment_1= attachment,
                                timeout = timeout,
                                enable = send
                                )


            if power_status_code >=300:
                power_state_mail_body = f"{time_now}\n{screen_name.get(Shared.MEM_SCREEN.value)}\n" +\
                                        f"{app.multiphase_program_lbl.upper()}: {program}\n" +\
                                        f"{app.multiphase_dash_phase}: {Shared.MP_ACTUAL_PHASE.value}\n" +\
                                        f"{app.mail_header_power_state} {power_status_codes.get(power_status_code)}\n" +\
                                        f"{app.prestart_set_temp_target.upper()}: {temp_target_c} °C / {temp_target_f} °F\n" +\
                                        f"{app.camera_temp_lbl.upper()}: {temp_camera_c:.1f} °C / {temp_camera_f:.1f} °F\n" +\
                                        f"{app.ext_temp_lbl.upper()}: {temp_ext_c:.1f} °C / {temp_ext_f:.1f} °F"

                mail_subject = app.mail_subj_power_state
                mail_body = power_state_mail_body




                self.asendmail( sender = ConfigModule.mail_sender,
                                receiver = ConfigModule.mail_receiver,
                                subject = mail_subject,
                                body = mail_body,
                                attachment_1= attachment,
                                timeout = timeout,
                                enable = send
                                )
        except Exception as ex:
            logger.error(ex)

