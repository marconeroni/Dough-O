
class TempConverter:

    def c_to_f(self, temp_c):
        temp_f = (temp_c *1.8)+32
        return temp_f

    def f_to_c(self, temp_f):
        temp_c = (temp_f-32)/1.8
        return temp_c

    def convert(self, temp, unit):
        if unit == 'C' or unit == 'c':
            _temp = (temp *1.8)+32

        elif unit == 'F' or unit == 'f':
            _temp = (temp-32)/1.8

        else:
            _temp = temp

        return _temp

    def convert_only_F(self, temp, unit):
        if unit == 'F' or unit == 'f':
            _temp = (temp *1.8)+32

        elif unit == 'C' or unit == 'c':
            _temp = temp

        return _temp



    def reset(self, temp, unit):
        if unit == 'C' or unit == 'c':
            _temp = 0

        elif unit == 'F' or unit == 'f':
            _temp = 32

        else:
            _temp = temp

        return _temp
