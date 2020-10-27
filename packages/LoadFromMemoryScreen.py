from kivy.uix.screenmanager import Screen
from kivy.properties import *
from kivy.app import App
from kivy.clock import Clock

from packages import Shared
from packages.TempConverter import TempConverter
from packages.ConfigModule import ConfigModule

from pathlib import Path
import os

logger = ConfigModule.getLogger()

class LoadFromMemory_Screen(Screen):

    load_filechooser = ObjectProperty(None)
    btn_load = ObjectProperty(None)
    btn_cancel= ObjectProperty(None)
    btn_delete = ObjectProperty(None)
    btns_disabled = BooleanProperty(True)
    standby_timer = None

    rp = str(Path(ConfigModule.app_dir.joinpath('Programs')).resolve(strict=False))

    rootpath = StringProperty(rp)

    prog_preview = StringProperty('')

    _file = StringProperty('')

    flour_lbl = ObjectProperty(None)
    water_lbl = ObjectProperty(None)
    yeast_lbl = ObjectProperty(None)
    salt_lbl = ObjectProperty(None)
    sugar_lbl = ObjectProperty(None)
    butter_lbl = ObjectProperty(None)
    milk_lbl = ObjectProperty(None)
    eggs_lbl = ObjectProperty(None)
    notes_lbl = ObjectProperty(None)
    prog_name_lbl = ObjectProperty(None)
    preview_dict = Shared.MP_TEMP_TARGET_DICT




    def on_enter(self):
        Shared.MEM_SCREEN.value = 5
        self.load_filechooser.rootpath = self.rootpath
        self.load_filechooser._update_files()
        self.btns_disabled = False
        if self.standby_timer is None:
            self.standby_timer = Clock.create_trigger(self.timer, 300)
            self.standby_timer()

    def on_leave(self):
        if self.standby_timer is not None:
            self.standby_timer.cancel()
            self.standby_timer = None

    def timer(self, dt):
        self.parent.current = 'home_screen'

    def enablebuttons(self):
        self.btns_disabled = False

    def namefile_selection(self, full_path):
        path, file = os.path.split(full_path)
        return file


    def load(self, path, filename, preview):
        app = App.get_running_app()

        if filename == '':
            self.prog_preview = f"PLEASE SELECT A FILE"
            return

        try:
            with open(os.path.join(path, filename)) as stream:
                text_loaded = stream.read()
                self.parse_file(text_loaded)

        except Exception as ex:
            self.prog_preview = f"ERROR LOADING FILE:\n {ex}"
            logger.error(f"ERROR LOADING FILE: {ex}")
            return

        #on loading success, no exceptions are detected. Then we recall function with preview parameter == False
        if preview == False:
            Shared.PROGRAM = filename
            Shared.LOAD_FROM_MEM = True
            app.root.current = 'multiphase_set_screen'

    def parse_file(self,string_stream):
        app = App.get_running_app()
        tc = TempConverter()
        program = string_stream.split('~')
        l = int(len(program)/2)-10
        #program_temp_unit = program [-1].upper()

        for n in range (l):
            Shared.MP_TEMP_TARGET_DICT[str(n+1)] = float(program[n*2])
            self.preview_dict.update(Shared.MP_TEMP_TARGET_DICT)

            Shared.MP_DURATION_DICT[str(n+1)] = float(program[(n*2)+1])

        # (chr10) ASCII carriage return
        separator = '~'
        if Shared.TEMP_UNIT_SCALE == 'F':
            self.preview_dict = {k: tc.c_to_f(v) for (k,v) in self.preview_dict.items() }

        self.prog_preview = \
            f"{(chr(10)*2)}"+ \
            f"{'1:':>8}{self.preview_dict.get('1'):>10}{app.temp_unit_scale:^8}{separator:^8}{Shared.MP_DURATION_DICT.get('1'):>8}{app.time_unit:^8}{(chr(10)*2)}" + \
            f"{'2:':>8}{self.preview_dict.get('2'):>10}{app.temp_unit_scale:^8}{separator:^8}{Shared.MP_DURATION_DICT.get('2'):>8}{app.time_unit:^8}{(chr(10)*2)}" + \
            f"{'3:':>8}{self.preview_dict.get('3'):>10}{app.temp_unit_scale:^8}{separator:^8}{Shared.MP_DURATION_DICT.get('3'):>8}{app.time_unit:^8}{(chr(10)*2)}" + \
            f"{'4:':>8}{self.preview_dict.get('4'):>10}{app.temp_unit_scale:^8}{separator:^8}{Shared.MP_DURATION_DICT.get('4'):>8}{app.time_unit:^8}{(chr(10)*2)}" + \
            f"{'5:':>8}{self.preview_dict.get('5'):>10}{app.temp_unit_scale:^8}{separator:^8}{Shared.MP_DURATION_DICT.get('5'):>8}{app.time_unit:^8}{(chr(10)*2)}"


        self.flour_lbl.text = program[11][:7]
        self.water_lbl.text = program[13][:7]
        self.yeast_lbl.text =program[15][:7]
        self.salt_lbl.text = program[17][:7]
        self.sugar_lbl.text = program[19][:7]
        self.butter_lbl.text = program[21][:7]
        self.milk_lbl.text = program[23][:7]
        self.eggs_lbl.text= program[25][:7]
        self.notes_lbl.text = program[27]


    def deletefile(self, path, filename):
        try:
            app = App.get_running_app()
            countfile = 0
            filepath = os.path.join(path, filename)
            for files in self.load_filechooser.files:
                if files == filepath:

                    countfile+=1
                    os.remove(filepath)
                    self.load_filechooser._update_files()
                    self.prog_preview = app.sm_notification_delete
                    self._file=''
                    self.prog_preview =''
                    self.prog_name_lbl.text = ''
                    return

            if countfile == 0 or filepath == '':

                self.prog_preview = app.sm_notification_error
                return

            self.load_filechooser._update_files()
            self._file=''
            filepath = ''
        except Exception as ex:
            logger.error(f"{ex}")
