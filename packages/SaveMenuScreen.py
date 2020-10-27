from kivy.uix.screenmanager import Screen
from kivy.properties import *
from kivy.uix.textinput import TextInput
from kivy.app import App
from kivy.clock import Clock

import pathlib
import os

from packages import Shared
from packages.ConfigModule import ConfigModule

logger = ConfigModule.getLogger()


class IconTextInput(TextInput):
    multiline: False
    font_size: 15
    valign: 'center'
    def insert_text(self, substring, from_undo=False):
        if len(self.text) < 7:
            s = substring
        else:
           return
        return super().insert_text(s, from_undo=from_undo)


class SaveMenu_Screen(Screen):
    ConfigModule = ConfigModule()
    save_filechooser= ObjectProperty(None)
    standby_timer = None

    save_text_input = ObjectProperty(None)
    btn_save = ObjectProperty(None)
    btn_cancel= ObjectProperty(None)
    btn_delete = ObjectProperty(None)
    lbl_notification = StringProperty('')
    btns_disabled = BooleanProperty(True)

    flour_text_input = ObjectProperty(None)
    water_text_input = ObjectProperty(None)
    yeast_text_input = ObjectProperty(None)
    salt_text_input = ObjectProperty(None)
    sugar_text_input = ObjectProperty(None)
    butter_text_input = ObjectProperty(None)
    milk_text_input = ObjectProperty(None)
    eggs_text_input = ObjectProperty(None)
    notes_text_input = ObjectProperty(None)

    #rp = rootpath
    rp = str(pathlib.Path(ConfigModule.app_dir.joinpath('Programs')).resolve(strict=False)) 

    rootpath = StringProperty(rp)

    program = '' # string stream to save in txt
    overwrite = BooleanProperty(False)


    def on_enter(self):
        Shared.MEM_SCREEN.value = 7
        self.save_filechooser.rootpath = self.rootpath
        self.save_filechooser._update_files()
        self.btns_disabled = False
        self.lbl_notification=''
        self.overwrite = False
        Shared.LOAD_FROM_MEM = True # important!!!!
        if self.standby_timer is None:
            self.standby_timer = Clock.create_trigger(self.timer, 300)
            self.standby_timer()

    def on_leave(self):
        if self.standby_timer is not None:
            self.standby_timer.cancel()
            self.standby_timer = None

    def timer(self, dt):
        self.parent.current = 'multiphase_set_screen'



    def enablebuttons(self):
        self.btns_disabled = False



    def save(self, path, filename):
        try:
            app = App.get_running_app()

            for files in self.save_filechooser.files:
                path, file = os.path.split(files) #tuple that split path and files

                if filename == file and self.overwrite == False:
                    self.lbl_notification = app.sm_notification_overwrite
                    self.overwrite = True
                    return
            if filename == '':
                self.lbl_notification = app.sm_notification_error
                return

            with open(os.path.join(path, filename), 'w') as stream:
                stream.write(self.program)

            self.lbl_notification = app.sm_notification_ok
            Shared.PROGRAM = self.save_text_input.text
            self.save_text_input.text=''
            self.overwrite = False

            self.save_filechooser._update_files() # this method refresh file list, see library implementation
        except Exception as ex:
            logger.error(f"{ex}")


    def deletefile(self, path, filename):

        try:
            app = App.get_running_app()
            countfile = 0
            filepath = os.path.join(path, filename)
            for files in self.save_filechooser.files:
                if files == filepath:

                    countfile+=1
                    os.remove(filepath)
                    self.save_filechooser._update_files()
                    self.lbl_notification = app.sm_notification_delete
                    self.save_text_input.text = ''
                    self.clear_fields()
                    return
            if countfile == 0 or filepath == '':

                self.lbl_notification = app.sm_notification_error
                self.save_text_input.text = self.namefile_selection(self.save_filechooser.selection[0] if len(self.save_filechooser.selection) >0 else '')
                return

            self.save_filechooser._update_files()
            filepath = ''
            self.save_text_input.text=filepath
        except Exception as ex:
            logger.error(f"{ex}")




    def namefile_selection(self, full_path):
            path, file = os.path.split(full_path)
            return file


    def clear_fields(self):
        #self.save_text_input.text = ''
        self.flour_text_input.text = ''
        self.water_text_input.text = ''
        self.yeast_text_input.text = ''
        self.salt_text_input.text = ''
        self.sugar_text_input.text = ''
        self.butter_text_input.text = ''
        self.milk_text_input.text = ''
        self.eggs_text_input.text = ''
        self.notes_text_input.text = ''

    def saveprogram(self):
        try:
            separator = '~'
            self.program = \
                str(Shared.MP_TEMP_TARGET_DICT.get('1')) + separator + \
                str(Shared.MP_DURATION_DICT.get('1')) + separator + \
                str(Shared.MP_TEMP_TARGET_DICT.get('2')) + separator + \
                str(Shared.MP_DURATION_DICT.get('2')) + separator + \
                str(Shared.MP_TEMP_TARGET_DICT.get('3')) + separator + \
                str(Shared.MP_DURATION_DICT.get('3')) + separator + \
                str(Shared.MP_TEMP_TARGET_DICT.get('4')) + separator + \
                str(Shared.MP_DURATION_DICT.get('4')) + separator + \
                str(Shared.MP_TEMP_TARGET_DICT.get('5')) + separator + \
                str(Shared.MP_DURATION_DICT.get('5')) + separator + \
                'FLOUR' + separator + self.flour_text_input.text.replace('~',' ') + separator + \
                'WATER' + separator + self.water_text_input.text.replace('~',' ') + separator + \
                'YEAST' + separator + self.yeast_text_input.text.replace('~',' ') + separator + \
                'SALT'  + separator + self.salt_text_input.text.replace('~',' ') + separator + \
                'SUGAR' + separator + self.sugar_text_input.text.replace('~',' ') + separator + \
                'BUTTER'+ separator + self.butter_text_input.text.replace('~',' ') + separator + \
                'MILK'  + separator + self.milk_text_input.text.replace('~',' ') + separator + \
                'EGGS'  + separator + self.eggs_text_input.text.replace('~',' ') + separator + \
                'NOTES' + separator + self.notes_text_input.text.replace('~',' ') + separator + \
                'TEMP_UNIT' + separator + \
                Shared.TEMP_UNIT_SCALE
        except Exception as ex:
                logger.error(f"ERROR FORMATTING PROGRAM FILE: {ex} -- {self.program}")



