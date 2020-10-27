from packages import Shared
from kivy.app import App

class OutStateImage():

    # ------------- I/O STATUS CODES:
    #               0:   ---> standby
    #               1:   ---> HI heater ON
    #               10:  ---> LO heater ON
    #               11:  ---> LO + HI heater ON
    #               100: ---> Compressor ON
    #               200: ---> generic error in reading
    #               201: ---> temperature out of range
    #               301: ---> error reading camera sensor
    #               302: ---> error reading external sensor


    out_state_mapper =  {
                            # '0 0 0 --> COMP, LO_h, HI_h
                            0: './Icons/Sleep_anim.zip',
                            1: './Icons/HI_heater_anim.zip',
                            10: './Icons/LO_heater_anim.zip',
                            11: './Icons/LO_HI_heater_anim.zip',
                            100: './Icons/Freezing_anim.zip',
                            101: './Icons/Warning_anim.zip',
                            110: './Icons/Warning_anim_anim.zip',
                            111: './Icons/Warning_anim.zip',
                            200: './Icons/Service_anim.zip',
                            201 : './Icons/Warning_anim.zip',
                            301: './Icons/Service_anim.zip',
                            302: './Icons/Service_anim.zip',
                            603: './Icons/Service_anim.zip'
                        }


    heater1_imgpath = './Icons/LO_heater_anim.zip'
    heater2_imgpath = './Icons/HI_heater_anim.zip'
    heater_1_2_imgpath = './Icons/LO_HI_heater_anim.zip'
    compressor_imgpath = './Icons/Freezing_anim.zip' #surat
    warning_imgpath = './Icons/Warning_anim.zip'
    sleeping_imgpath = './Icons/Sleep_anim.zip'
    finish_imgpath = './Icons/Finish_anim.zip'
    service_imgpath = './Icons/Service_anim.zip'
    image_state_path = './Icons/Sleep_anim.zip'
    image_label = ''
    warning = False




    def set_image(self, state_code , program_is_running):
        app = App.get_running_app()
        if program_is_running is False:
            return self.finish_imgpath, app.program_end


        out_label_mapper =  {
                                0 : app.sleeping_lbl,
                                1:  app.hi_heater_state_lbl,
                                10: app.lo_heater_state_lbl,
                                11: app.lo_hi_heater_state_lbl,
                                100: app.compressor_state_lbl,
                                101: app.warning_out_lbl,
                                110: app.warning_out_lbl,
                                111: app.warning_out_lbl,
                                200: 'ERROR 200',
                                201: 'ERROR 201',
                                301: 'ERROR 301',
                                302: 'ERROR 302',
                                603: 'ERROR 603'
                            }

        warning_codes_mapper =  {
                                    0: False,
                                    1: False,
                                    10: False,
                                    11: False,
                                    100: False,
                                    101: True,
                                    110: True,
                                    111: True,
                                    200: True,
                                    201: True,
                                    301: True,
                                    302: True,
                                    603: True
                                }


        self.image_state_path = self.out_state_mapper.get(state_code)
        self.warning = warning_codes_mapper.get(state_code)
        self.image_label = out_label_mapper.get(state_code)
        return [self.image_state_path, self.image_label]