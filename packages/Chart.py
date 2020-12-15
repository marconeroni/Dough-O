from kivy.graphics import Line
from kivy.graphics import Color
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.clock import Clock
from kivy.properties import NumericProperty
from kivy.utils import escape_markup
from datetime import datetime
from datetime import timedelta
from packages.TempConverter import TempConverter


# data: bind to measured temperature MANDATORY
# update_dt = change clock update deafult = 1 second
# total_time_x = total time in x axis default = 60 minutes
# draw(): begin draw
# stop_draw() : end draw
# Config.set('graphics', 'resizable', True)

class ChartWidget(RelativeLayout):

    def __init__(self, **kwargs):
        self.grid_points_x = [0, 0]
        self.grid_points_y = [0, 0]
        self.label_points_x = [0, 0]
        self.label_points_y = [0, 0]
        self.signal_points = [0, 0]
        self.zero_y = 0  # zero line point
        self.zero_x = 0

        self.clockObj = None  # command clock
        self.x_point = self.zero_x
        self.increment_update = 0
        self.increment_redraw = 0
        self.last_value = 0

        super(ChartWidget, self).__init__(**kwargs)
        with self.canvas.before:

            Color(0.1, 0.1, 0)
            self.x_zero_line = Line(points=[0, self.zero_y, self.width, self.zero_y], width=1.3)

            self.y_zero_line = Line(points=[self.zero_x, 0, self.zero_x, self.height], width=1.3)

            self.grid_line_x = Line(points=[None])
            self.grid_line_y = Line(points=[None])

            Color(1., .1, 0)
            self.signal_line = Line(points=None, width = 1.2)


        Clock.schedule_once(self.drawbackground)
        self.bind(size=self.resize_image, pos=self.resize_image)  # bind to method for resizing image


    '''
    due to the rounding without decimal places of the labels on the Y axis, 
    it is better to make sure that the sum of the minimum and maximum temperatures 
    is divisible by the y_axis_scale. It also applies on X axis

    '''
    tc = TempConverter()
    clocktick = NumericProperty(1)      # delta
    x_axis_scale = NumericProperty(5)   # minutes
    x_axis_max = NumericProperty(60)    # minutes
    y_axis_scale = NumericProperty(5)   # grades
    y_axis_max = NumericProperty(30)    # max value in y
    y_axis_min = NumericProperty(-20)   # min value in y axis
    data = NumericProperty(-18)
    temp_scale = 'C'


    # this function must be called outside this class, in chart instance on KV file.
    # TEMP TARGET is variable and must be updated with no chart canvas redraw
    def draw_target_line(self, temp_value, temp_unit_scale = 'C'):
        if temp_unit_scale == 'F':
            temp_value = self.tc.f_to_c(temp_value)
        y_target_point = (((self.height - self.zero_y) / self.y_axis_max) * temp_value) + self.zero_y
        return [self.zero_x, y_target_point, self.width, y_target_point ]

    def resize_image(self, *args):
        self.zero_y = (self.height / (self.y_axis_max - self.y_axis_min)) * - self.y_axis_min
        self.zero_x = 30 # zero point start for signal line / axis intersection
        self.drawbackground()
        self.signal_points.clear()
        self.x_point = self.zero_x

    def drawbackground(self, *args):
        self.grid_points_x.clear()
        self.grid_points_y.clear()
        self.label_points_x.clear()
        self.label_points_y.clear()
        self.clear_widgets()
        self.x_zero_line.points = ([0, self.zero_y, self.width, self.zero_y])
        self.y_zero_line.points = ([self.zero_x, 0, self.zero_x, self.height])

        x_axis_scale_pixel = round((self.width / (self.x_axis_max)) * self.x_axis_scale)
        y_axis_scale_pixel = round((self.height / (self.y_axis_max - self.y_axis_min)) * self.y_axis_scale)

        x_count = 0
        for x in range(0+self.zero_x, round(self.width), x_axis_scale_pixel):

            self.grid_points_x.extend([x, self.height, x + x_axis_scale_pixel, self.height,
                                       x + x_axis_scale_pixel, 0])

            self.grid_line_x.points = self.grid_points_x

            str_td = datetime.now() + timedelta(minutes=self.x_axis_scale * x_count)  # divide total time in x axis (len x_labels-1)

            if x_count > 0: # hide first label

                lbl_x = Label(markup=True,
                              text= '[font=./Fonts/Aldrich-Regular][color=#5D5D5D][size=10]' + escape_markup(
                                  str_td.strftime("%H:%M")) + '[/font][/size][/color]')
                lbl_x.pos_hint = {'x': (x / self.width) - 0.5, 'y': (1 / self.height) * self.zero_y - 0.53}

                self.add_widget(lbl_x, x)

            x_count += 1
        x_count = 0

        y_count = self.y_axis_min

        for y in range(0, round(self.height), y_axis_scale_pixel):
            y_ax_lbl = self.tc.convert_only_F(y_count, self.temp_scale)

            self.grid_points_y.extend([self.width, y, self.width, y + y_axis_scale_pixel, 0, y + y_axis_scale_pixel])
            self.grid_line_y.points = self.grid_points_y

            if y_count > self.y_axis_min:
                lbl_y = Label(markup=True,
                              text='[font=./Fonts/Aldrich-Regular][color=#5D5D5D][size=10]' + escape_markup(
                                  f"{y_ax_lbl:.0f}") + '[/font][/size][/color]')
                lbl_y.pos_hint = {'x': -0.48, 'y': (y / self.height) - 0.5}
                self.add_widget(lbl_y, y)

            y_count += self.y_axis_scale
        y_count = self.y_axis_min

    def update(self, dt):

        y_point = (((self.height - self.zero_y) / self.y_axis_max) * self.data) + self.zero_y

        self.increment_update = (self.width * self.clocktick)/(self.x_axis_max*60) # chart_width (pixel) : x_axis_max (minutes) = increment : clocktick (seconds)
        self.x_point += self.increment_update

        #if self.data >= self.y_axis_max: self.data = self.y_axis_min ----> #TEST ONLY: comment or delete this line on deploy

        if y_point >= self.height: # limit line draw on top widget's limit; comment this line if you want to extend draw over widget (not recommended)!
            y_point = self.height

        self.signal_points.extend([self.x_point, y_point])
        self.signal_line.points = self.signal_points



        if (self.signal_points[-2]) >= self.width:  # limit horizontal drawing, first value of last point's tuple

            self.last_value = self.signal_points[-1]
            self.signal_points.clear()
            self.signal_points = [self.zero_x, self.last_value]
            self.x_point = self.zero_x
            self.drawbackground()


    def draw(self):
        if self.clockObj is None:
            self.clockObj = Clock.create_trigger(self.update, self.clocktick, True)
            self.clockObj()
            self.drawbackground()

    def stop_draw(self):
        if self.clockObj is not None:
            self.clockObj.cancel()
            self.drawbackground()
            self.clockObj = None

