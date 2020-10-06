"""
MTE_device - base class for classes MTE_Generator and MTE_counter
"""
#import serial


class C_MTE_device:
    def __init__(self ,ser, ser_timeout, start_cmd,b_print_cmd,b_print_answ):
        self.ser_port = ser
        self.ser_timeout = ser_timeout

        self.b_print_cmd = b_print_cmd
        self.b_print_answ = b_print_answ

        self.textFromMTE = []
        self.meas_time = -1

        self.send_cmd_to_device(start_cmd)

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def read_by_time_T(self,read_time,buffer_len,timeout):                       # Send reset command to MTE device
        
        prev_timeout = self.ser_port.timeout  # [sec]
        self.ser_port.timeout = timeout       # [sec]

        self.ser_port.flushInput()
        self.ser_port.flushOutput()

        textFromMTE = self.ser_port.read(buffer_len)

        self.ser_port.timeout = prev_timeout   # [sec]

        return textFromMTE.decode()


    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def reset_device(self):                       # Send reset command to MTE device
        self.send_cmd_to_device("R\r")

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def send_direct_cmd(self, str_cmd): 

        len_cmd = len(str_cmd)
        if len_cmd == 0:
            print("Input empty 'direct command'")
            return
        elif len_cmd > 1:
            if  str_cmd.endswith(";"):
                self.send_cmd_to_device(str_cmd)

            else:
                if  str_cmd.endswith("\r"):
                    self.send_cmd_to_device(str_cmd)
                else:
                    str_cmd = str_cmd + "\r"
                    self.send_cmd_to_device(str_cmd)

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def set_measure_time(self, meas_time):     # send measured time in sec. [float]
        
        if meas_time < 0.0:
            print("Error set measured time. Measured time less zero: "+str(meas_time))
            return
        elif int(meas_time) == 0:
            print("External sync mode enable")
            self.meas_time = int(meas_time)
        else:
            self.meas_time = meas_time

        str_cmd = "T"+str(self.meas_time)+"\r"
        self.send_cmd_to_device(str_cmd)


    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_measure_time(self):     # send measured time in sec. [float]
        return self.meas_time

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def send_cmd_to_device(self, str_cmd):            # send command to MTE Device

        self.ser_port.flushInput()
        self.ser_port.flushOutput()

        self.ser_port.write(str_cmd.encode())

        # выводим в консоль отправленную команду
        if self.b_print_cmd == 1:					
            print("send command to MTE: " + str_cmd)
            print("Waiting for MTE answer: ") 

        textFromMTE = self.ser_port.read(1800)
        
        self.textFromMTE = textFromMTE.decode()

        # выводим в консоль принятый ответ на команду
        if self.b_print_answ == 1:					
            print("Answer from MTE: " + self.textFromMTE)
            
        return self.textFromMTE

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Парсинг строки ответа "частоты"
    '''
    >>> try:
    ...     for line in f:
    ...         ints.append(int(line))
    ... except ValueError:
    ...     print('Это не число. Выходим.')
    ... except Exception:
    ...     print('Это что ещё такое?')
    ... else:
    ...     print('Всё хорошо.')
    ... finally:
    ...     f.close()
    ...     print('Я закрыл файл.')
    ...     # Именно в таком порядке: try, группа except, затем else, и только потом finally.
    '''

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def parse_MTE_answer_Freq(self,text): 
        try:            
            mStr = text.split(",")               # Делим строку результата на блоки.
            if len(mStr) == 2:
                if mStr[1].startswith("--") or (len(mStr[1]) <= 1):
                    vFreq = 0                  # Нет значения в результатах измерений 
                else:
                    lastVal = mStr[1]       # Убираем в конце символ <CR>
                    vFreq = float(lastVal[0:len(lastVal)-1:1])     # переводим значение во float
            else:
                #print("parse_MTE_answer_Freq_No_CR:  len(mStr) != 2   len(mStr) = "+str(len(mStr)))
                vFreq = -1 
        except Exception:
            print('parse_MTE_answer_Freq Error')
            vFreq = -1 
        else:
            #print('Всё хорошо.')
            pass
        finally:
            return vFreq

        
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Парсинг строки ответа "частоты"
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def parse_MTE_answer_Freq_text(self,text):             
        try:
            mStr = text.split("=")               # Делим строку результата на блоки.
            if len(mStr) == 2:
                if mStr[1].startswith("--") or (len(mStr[1]) <= 1):
                    vFreq = 0                  # Нет значения в результатах измерений 
                else:
                    lastVal = mStr[1]       # Убираем в конце символ <CR>
                    vFreq = float(lastVal[0:len(lastVal)-1:1])     # переводим значение во float
            else:
                #print("parse_MTE_answer_Freq_No_CR:  len(mStr) != 2   len(mStr) = "+str(len(mStr)))
                vFreq = -1 
        except Exception:
            print('parse_MTE_answer_Freq_text Error')
            vFreq = -1 
        else:
            #print('Всё хорошо.')
            pass
        finally:
            return vFreq

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Парсинг строки ответа из 3-х параметров: фаза А, фаза В, фаза С
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def parse_MTE_answer(self):              # парсить ответ от МТЕ по общим параметрам: 3 числа по 3 фазам
        try:
            mStr = self.textFromMTE.split(",")               # Делим строку результата на блоки.
            len_mStr = len(mStr)

            if len_mStr >1:
                if mStr[1].startswith("--") or (len(mStr[1]) <= 1): #: # фаза А
                    vA = 0                  # Нет значения в результатах измерений 
                else:
                    vA = float(mStr[1])     # переводим значение во float
            else:
                #print("parse_MTE_answer_No_CR:  len_mStr < 1   mStr = " + str(mStr))
                vA = -1

            if len_mStr >2:
                if mStr[2].startswith("--") or (len(mStr[2]) <= 1): #: # фаза Б
                    vB = 0                  # Нет значения в результатах измерений 
                else:
                    vB = float(mStr[2])     # переводим значение во float
            else:
                #print("parse_MTE_answer_No_CR:  len_mStr < 2   mStr = " + str(mStr))
                vB = -1

            if len_mStr >3:
                if (mStr[3].startswith("--")) or (len(mStr[3]) <= 1): #: # фаза C
                    vC = 0                  # Нет значения в результатах измерений 
                else:
                    lastVal = mStr[3]
                    vC = float(lastVal[0:len(lastVal)-1:1])     # переводим значение во float
            else:
                vC = -1

        except Exception:
            print('parse_MTE_answer Error')
            vA = -1
            vB = -1
            vC = -1
        else:
            #print('Всё хорошо.')
            pass
        finally:
            return vA, vB, vC
 
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Парсинг строки ответа из 3-х параметров: фаза А, фаза В, фаза С
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def parse_MTE_answer_text(self,text):              # парсить ответ от МТЕ по общим параметрам: 3 числа по 3 фазам
        
        result_list = []
        
        try:
            mStr = text.split(",")               # Делим строку результата на блоки.
            len_mStr = len(mStr)
            

            if len_mStr >1:
                if mStr[1].startswith("--") or (len(mStr[1]) <= 1): result_list.append(0.0) # фаза А   # Нет значения в результатах измерений 
                else: result_list.append(float(mStr[1]))
            else:
                #print("parse_MTE_answer_text:  len_mStr < 1   mStr = " + str(mStr))
                result_list.append(-1.0)

            if len_mStr >2:
                if mStr[2].startswith("--") or (len(mStr[2]) <= 1): result_list.append(0.0)
                else: result_list.append(float(mStr[2]))
            else:
                #print("parse_MTE_answer_text:  len_mStr < 2   mStr = " + str(mStr))
                result_list.append(-1.0)

            if len_mStr >3:
                if (mStr[3].startswith("--")) or (len(mStr[3]) <= 1): result_list.append(0.0)
                else: result_list.append(float(mStr[3][0:len(mStr[3])-1:1]))
            else:
                #print("parse_MTE_answer_text:  len_mStr < 3   mStr = " + str(mStr))
                result_list.append(-1.0)

        except Exception:
            print('parse_MTE_answer_text Error')
            result_list.append(-1.0)
            result_list.append(-1.0)
            result_list.append(-1.0)
        else:
            #print('Всё хорошо.')
            pass
        finally:
            return result_list

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Запросить текущее время с устройства МТЕ
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_MTE_Device_current_Time(self):              # парсить ответ от МТЕ по общим параметрам: 3 числа по 3 фазам
        t_str = self.send_cmd_to_device("TIME\r")
        #пример строки ответа: "TIME=22.03.00 14:00:03" ('00' == '2000')
        # получение строки после знака равно
        time_str = t_str.split("=")
        if len(time_str) != 2:
            print("Wrong text_time_str. Length after split('=') not equal 2. 'time_str': "+str(time_str))
            return 0,0,0, 0,0,0     # дд.мм.гг чч:мм:сс
        
        d_t_str = time_str[1].split(" ")
        if len(d_t_str) != 2:
            print("Wrong d_t_str. Length after split('=') not equal 2. 'd_t_str': "+d_t_str)
            return 0,0,0, 0,0,0     # дд.мм.гг чч:мм:сс

        # подстрока с датой
        date_str = d_t_str[0].split(".")
        if len(date_str) != 3:
            print("Wrong date_str. Length after split('=') not equal 3. 'date_str': "+date_str)
            return 0,0,0, 0,0,0     # дд.мм.гг чч:мм:сс
        py_day   = int(date_str[0])
        py_month = int(date_str[1])
        py_year  = int(date_str[2])

        # подстрока со временем
        t_time_str = d_t_str[1].split(":")
        if len(t_time_str) != 3:
            print("Wrong t_time_str. Length after split('=') not equal 3. 't_time_str': "+t_time_str)
            return 0,0,0, 0,0,0     # дд.мм.гг чч:мм:сс
        py_hour    = int(t_time_str[0])
        py_minute  = int(t_time_str[1])
        py_second  = int(t_time_str[2])

        return py_year,py_month,py_day, py_hour,py_minute,py_second

if __name__ == "__main__":
    pass



        