import math

class FloatToStringTuple:

    def convert(self, number): #number = float number
        temp_str = []
        try:
            # trick to auto detect system decimal separator
            # without the use of method:
            # locale.localeconv().get('decimal_point')
            temp_str = '{:.1f}'.format(number).split('.')
            if len(temp_str)==1:
                temp_str = '{:.1f}'.format(number).split(',')
        except:
            temp_str = ['!','!']
        finally:
            return temp_str
