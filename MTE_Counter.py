"""
MTE_device - base class for classes MTE_Generator and MTE_counter
"""

from MTE_Device import C_MTE_device

#import math

from math import (pi, atan, sqrt)

import datetime as dt

'''
---Обработчики меню

SetMenuHandler()		-- общее меню установки параметров счетчика
SU_handler()		    -- подменю начать/остановить автопередачу данных
SetTimeMenuHandler()	-- подменю параметров установки времени измерения
set_SP_list()	        -- подменю конфигурации содежимого списка автовыдачи результатов
GetMenuHandler()		-- меню выбора параметров измерения: общие или спектр
GetCommonMenuHandler()	-- подменю выбора измерений "общих параметров" 

--Set/Get команды

get_mean_values()		        --списки усредненных значений "короткой посылки"
set_meas_time(meas_time)		--установить время измерения счетчика МТЕ
set_ext_sync_mode()	            --установить режим внешней синхронизации для счетчика
set_ranges_for_CNT()	        --установить диапазоны измерения для счетчика
get_current_FREQ()	            --запросить текущую частоту сигнала
start_auto_measure()	        --начать автопередачу данных
stop_auto_measure()	            --остановить автопередачу данных

get_all_spectrum()              --Запросить, считать и распарсить все спектры со счетчика МТЕ

--Вспомогательные функции

send_to_MTE(write_str)		            --переопределение метода "передать команду устройству МТЕ"
readByTimeT(readTime,MTE_measured_Time) --считать в буфер данные за время Т
parse_accumulateResult_answer(text)	    --распарсить принятые функцией readByTimeT значения
calc_mean_ABC(list_A,list_B,list_C,list_mean,text_file) --расчитать средние значения списков значений и сохранить результаты в список
parse_MTE_answer_No_CR(text)	        --распарсить ответ счетчика МТЕ из значений по 3-м фазам без символа возврата каретки
parse_MTE_answer_Freq_No_CR(text)       --распарсить ответ счетчика МТЕ значения частоты без символа возврата каретки
parse_MTE_answer_Time()	                --распарсить строку-ответ от МТЕ "текущее" время измерения
get_spectrum_from_counter(numUI,numPhase)-- запрос и считывание буфера спектра со счетчика МТЕ 
get_UI_max_range()	                -- узнать текущий диапазон измерения. Необходимо для расчета спектра
parse_MTE_Harm_answer(text)	        --парсинг буфера со значениями спектра, полученные со счетчика МТЕ
'''

class C_MTE_Counter(C_MTE_device):
    def __init__(self ,ser, ser_timeout, start_cmd,b_print_cmd,b_print_answ):
        # Необходимо вызвать метод инициализации родителя.
        # В Python 3.x это делается при помощи функции super()
        #http://pythonicway.com/education/python-oop-themes/21-python-inheritance

        super().__init__(ser, ser_timeout, start_cmd,b_print_cmd,b_print_answ)
        #-------------------------------------------------------
        #-------------------------------------------------------
        #----Первый элемент в строке: название пункта меню для консольного управления,
        # ---Второй элемент: флаг - включен или нет этот элемент в список автовыдачи
        # ---Третий элемент: команда управления (идентификатор) для МТЕ---------------
        #-------------------------------------------------------
        self.resultList_mas =[ \
        "\r\nChoose element in 'result list':\r\n'+'(in list)/'-'(not in list)",        0,     0,
            "       1 - Phase currents [A]: I1, I2, I3",                                1,     1,
            "       2 - Phase to neutral voltages [V]: U1, U2, U3",                     1,     2,
            "       3 - Phase to phase voltages [V]: U12, U23, U31",                    0,     12,
            "       4 - Powers Active [W]: P1, P2, P3",                                 0,     3,
            "       5 - Powers Reactive [var]: Q1, Q2, Q3",                             0,     4,
            "       6 - Powers Full [VA]: S1, S2, S3",                                  0,     5,
            "       7 - Phase angles current to voltage [°]: phiUI1, phiUI2, phiUI3",   0,     9,
            "       8 - Phase angles between voltages [°]: phiU1U2, phiU2U3, phiU3U1",  0,     22,     
            "       9 - Phase angles between currents [°]: phiI1I2, phiI2I3, phiI3I1",  0,     23,
            "       10 - Absolute phase angles (r-virtual reference) [°]: \
        phiAbsU1, phiAbsU2, phiAbsU3, phiAbsI1, phiAbsI2, phiAbsI3",                    1,    35,
            "       11 - Frequency [Hz]: freq",                                         1,    13,
            "\r\n12 - Remove all elements from list",                                   0,    98,
            "\r\n13 - Back",                                                            0,    2345] 

        self.num_elem_in_row = 3
        self.len_resultList_mas = int(len(self.resultList_mas) / self.num_elem_in_row)

        self.GetCommonMenuItems_mas = [  "\r\nChoose common params values:",             0,  0,
                                        "1 - Currents [A]: I1, I2, I3",                 1,  1,
                                        "2 - Voltages [V]: U1, U2, U3",                 2,  2,
                                        "3 - Powers Active [W]: P1, P2, P3",            3,  3,
                                        "4 - Powers Reactive [var]: Q1, Q2, Q3",        4,  4,
                                        "5 - Powers Full [VA]: S1, S2, S3",             5,  5,
                                        "6 - Angle UI [°]: phiUI1, phiUI2, phiUI3",     6,  9,
                                        "7 - Linear Voltages [V]: U12, U23, U31",       7,  12,
                                        "8 - Angle UU [°]: phiU1U2, phiU2U3, phiU3U1",  8,  21,
                                        "9 - Angle II [°]: phiI3I1, phiI3I1, phiI3I1",  9,  22,
                                        "10 - Frequency [Hz]: freq",                    10,  13,
                                        "11 - Back",                                    11,  123] 
    
        self.harm_dict = {    0: 1, 1: 2, 2: 3, 3: "RSU", 4: "RSI"}
        self.numUI = 0
        self.numPhase = 0

        self.UI_max = 0
        self.freq = 0

        self.list_module = []
        self.list_angle = []

        # Списки результатов измерения спектров
        self.list_Ua_mod = []
        self.list_Ua_ang = []
        self.list_Ub_mod = []
        self.list_Ub_ang = []
        self.list_Uc_mod = []
        self.list_Uc_ang = []

        self.list_Ia_mod = []
        self.list_Ia_ang = []
        self.list_Ib_mod = []
        self.list_Ib_ang = []
        self.list_Ic_mod = []
        self.list_Ic_ang = []

        self.list_m = [self.list_Ua_mod,\
                    self.list_Ub_mod,\
                    self.list_Uc_mod,\
                    self.list_Ia_mod,\
                    self.list_Ib_mod,\
                    self.list_Ic_mod]

        self.list_a = [self.list_Ua_ang,\
                    self.list_Ub_ang,\
                    self.list_Uc_ang,\
                    self.list_Ia_ang,\
                    self.list_Ib_ang,\
                    self.list_Ic_ang]

                            # Списки для сохранения распарсенных значений
        self.list_I = []
        self.list_U = []
        self.list_P = []
        self.list_Q = []
        self.list_S = []
        self.list_Uu = []
        self.list_Frq = []
        self.list_pUI = []
        self.list_pUU = []
        self.list_pII = []
        self.list_paUI = []

        # список префиксов - начала строк в ответе от счетчика МТЕ
        self.prefix_mas ={      "E@" : self.list_I,
                                "EA" : self.list_U, 
                                "EK" : self.list_Uu,
                                "EB" : self.list_P,
                                "EC" : self.list_Q,
                                "ED" : self.list_S,
                                "EH" : self.list_pUI,
                                "E^" : self.list_pUU,
                                "E_" : self.list_pII,
                                "El" : self.list_paUI,
                                "EL" : self.list_Frq}

        self.len_prefix_mas = len(self.prefix_mas)

        # списки для сохранения средних значений
        self.list_I_mean = []
        self.list_U_mean = []
        self.list_phi_II_mean = []
        self.list_phi_UU_mean = []
        self.freq_mean = 0

        self.list_ampl_full = []
        self.list_angle_full = []

        self.list_phiABS_mean = []

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Переопределение метода посылки команд для счетчика
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def send_to_MTE(self,write_str):
        #print("Send cmd to Counter")
        self.send_direct_cmd(write_str)

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Меню установки параметров счетчика
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def SetMenuHandler(self):
        while(True):
            #-----Меню установки параметров для счетчика
            print("\r\nSet menu:")
            print("1 - Meas Time menu")
            print("2 - Set result list config SP")
            print("3 - Set automatic send results SU")
            print("4 - Read results from MTE by T [sec]")
            print("5 - Back")

            num = int(input())

            if num == 5:
                print("\r\nPressed: 4 - Back")
                return
            elif num == 1:
                print("\r\nPressed: 1 - Set Time")
                print("Choose measurment Time params:")
                self.SetTimeMenuHandler()
            elif num == 2:
                print("\r\nPressed: 2 - Set result list config SP")
                print("Set result list config SP:")
                self.set_SP_list()
            elif num == 3:
                print("\r\nPressed: 3 - Set automatic send results SU")
                print("Set automatic send results SU:")
                self.SU_handler()
            elif num == 4:
                print("\r\nPressed: 4 - Read results from MTE by T [sec]")
                print("Input measured time in sec.:")
                readTime = float(input())
                print("Input time interval between measurements in sec.:")
                MTE_measured_Time = float(input())

                self.stop_auto_measure()                           # остановить предыдущую передачу данных
                self.send_to_MTE("T"+str(MTE_measured_Time)+"\r")  # установить новое время измерения
                self.start_auto_measure()                          # запустить новую передачу данных 
                self.readByTimeT(readTime,MTE_measured_Time)   
                self.stop_auto_measure()                          # запустить новую передачу данных 
            else:
                print("Something go wrong! input num (1-4) in 'set 'Counter MTE' menu params'.")

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Считать данные за время Т
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def readByTimeT(self,readTime,MTE_measured_Time):
        numElemInResultList = 0     # подсчет числа элементов в списке результатов
        realNumByte = 0
        margin_percent = 7.5
        NumByte_and_margin = 0

        for number in range(self.len_resultList_mas):                     # подсчет того, сколько элементов в списке выдачи результатов будет
            if self.resultList_mas[number*self.num_elem_in_row + 1] == 1:
                if self.resultList_mas[number*self.num_elem_in_row + 2] == 10:  # abs angles
                    realNumByte += 58
                elif self.resultList_mas[number*self.num_elem_in_row + 2] == 4:  # angles U I 
                    realNumByte += 11
                elif self.resultList_mas[number*self.num_elem_in_row + 2] == 11:  # angles U I 
                    realNumByte += 13
                else:
                    realNumByte += 31

                numElemInResultList = numElemInResultList + 1

        NumByte_and_margin = realNumByte * (100.0 + margin_percent) / 100.0
        '''
        print("numElemInResultList: EXIT " + str(numElemInResultList) +\
            "   realNumByte: "           + str(realNumByte) +\
            "   realNumByte + margin: "  + str(NumByte_and_margin) +\
            "   MTE_measured_Time     "  + str(MTE_measured_Time))
        '''

        symb_num = int(NumByte_and_margin * readTime / MTE_measured_Time) # [symbols]
        #print("accumulateResultsFromMTE(ser,readTime,symb_num)")

        self.ser_port.flushInput()
        self.ser_port.flushOutput()

        self.ser_port.timeout = 0.3
        prev_timeout = self.ser_port.timeout

        #print(" timeout "+str(readTime) + " symb_num " + str(symb_num))
        self.ser_port.timeout = readTime # [sec]

        read_textFromMTE = self.ser_port.read(symb_num)
        #print("read_textFromMTE: "+read_textFromMTE.decode())
        self.ser_port.timeout = prev_timeout
        self.parse_accumulateResult_answer(read_textFromMTE)                      # парсинг результатов

##################################################################################################
##################################################################################################
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Парсинг ответа от счетчика принятый за время Т
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def parse_accumulateResult_answer(self,read_textFromMTE):                          # парсинг ответа от МТЕ, принятый за 5 секунд
        ###########################################
        #debug_mode = True
        debug_mode = False
        ###########################################
        if debug_mode == True:
            test_str_5_elem = "b'SU1=O\rER\rES\rE@,5.001339,5.00003,5.001231\rEA,57.76325,57.71013,57.74432\rEH,0.038849,0.044070,0.031906,L\rE^,240.0191,239.9860,239.9950\rEL,49.99083\rER\rE@,5.001186,5.000005,5.001219\rEA,57.75099,57.71399,57.75558\rEH,0.038849,0.044070,0.031906,L\rE^,239.9988,240.0141,239.9871\rEL,49.99083\rER\rE@,5.001320,5.000041,5.001228\rEA,57.75211,57.71454,57.75629\rEH,0.042160,0.046394,0.035217,L\rE^,239.9975,240.0124,239.9901\rEL,49.99083\rER\rE@,5.001270,5.000020,5.001273\rEA,57.74904,57.71450,57.75566\rEH,0.041992,0.047525,0.033432,L\rE^,239.9970,240.0139,239.9891\rEL,49.99083\rER\rE@,5.001400,4.999927,5.001226\rEA,57.74955,57.71360,57.75586\rEH,0.041046,0.045223,0.032196,L\rE^,239.9975,240.0124,239.9901\rEL,49.99083\r’"
            #test_str_1_elem = "b'SU1=O\rER\rES\rE@,5.000437,4.999800,5.001024\rEA,57.76325,57.71013,57.74432\rEB,288.8413,288.5386,288.7787\rEH,0.038849,0.044070,0.031906,L\rE^,240.0191,239.9860,239.9950\rEL,49.99083\r'"
            textFromMTE = test_str_5_elem
        else:
            textFromMTE = read_textFromMTE.decode()
        ###########################################

        #0 обнуление списков перед новой партией сохранения считанных данных
        for prefix_keys in self.prefix_mas:
            self.prefix_mas[prefix_keys].clear()

        # разбор текста принятого за T секунд в режиме автоответа от счетчика МТЕ
        #1 деление строки по символам "ER" - получаем строку ответов за 1 сек
        mStr_ER = textFromMTE.split("ER")
        #2число элементов после деления на ER равно числу посылок
        num_dataCont = len(mStr_ER) - 1
        #print("num_dataCont = " + str(num_dataCont))

        #3 цикл перебора и парсинга полных ответов от МТЕ
        for numCont in range(num_dataCont):

            mStr_r = mStr_ER[numCont+1].split('\r')
            len_str_r = len(mStr_r)
            
            for num_r in range(len_str_r):          # парсим значения
                cur_str = mStr_r[num_r] 
                if cur_str.startswith("EL"):  # частота
                    freq = self.parse_MTE_answer_Freq_No_CR(cur_str)
                    if freq != -1: self.prefix_mas["EL"].append(freq)

                elif cur_str.startswith("El"):  # абсолютные фазовые углы
                    self.prefix_mas["El"].extend(self.parse_MTE_answer_ANGLES_No_CR(cur_str))

                else:
                    for prefix_keys in self.prefix_mas:                     # Сохранение распарсенных данных в списки
                        if cur_str.startswith(prefix_keys):
                            vA, vB, vC = self.parse_MTE_answer_No_CR(cur_str)
                            if vA != -1: self.prefix_mas[prefix_keys].append(vA)
                            if vB != -1: self.prefix_mas[prefix_keys].append(vB)
                            if vC != -1: self.prefix_mas[prefix_keys].append(vC)
                            break
                
        #mean_Received_Data()    #4 усреднение принятых данных

        #4 усреднение принятых данных
        self.list_I_mean = []
        self.list_U_mean = []
        #self.list_phi_II_mean = []
        #self.list_phi_UU_mean = []
        self.freq_mean = 0

        self.list_phiABS_mean = []

        """
        text_file = open("Output.txt", "w")     # 'a'	открытие на дозапись, информация добавляется в конец файла.
        text_file.flush()
        """
        text_file = 0

        for mas_prefix in self.prefix_mas: 
            cur_List_len = len(self.prefix_mas[mas_prefix])
            if cur_List_len != 0:                                   # Если в списке есть значения, проводим усреднение
                
                #for idx in range(cur_List_len):
                #    print(self.prefix_mas[mas_prefix][idx])    # вывод на экран всех элементов принятых значений

                if mas_prefix.startswith("EL"):               # для частоты

                    self.freq_mean = sum(self.prefix_mas[mas_prefix])/len(self.prefix_mas[mas_prefix])
                    #print(" freq:  mean: " + str(self.freq_mean) + "   numElem: " + str(len(self.prefix_mas[mas_prefix])))

                elif mas_prefix.startswith("El"):       # для абсолютных фазовых сдвигов
                    self.calc_mean_ABC_angle(   self.prefix_mas[mas_prefix][0:cur_List_len:6],\
                                                self.prefix_mas[mas_prefix][1:cur_List_len:6],\
                                                self.prefix_mas[mas_prefix][2:cur_List_len:6],\
                                                self.prefix_mas[mas_prefix][3:cur_List_len:6],\
                                                self.prefix_mas[mas_prefix][4:cur_List_len:6],\
                                                self.prefix_mas[mas_prefix][5:cur_List_len:6],\
                                                self.list_phiABS_mean,text_file) 

                elif mas_prefix.startswith("E@"): 
                    self.calc_mean_ABC( self.prefix_mas[mas_prefix][0:cur_List_len:3],\
                                        self.prefix_mas[mas_prefix][1:cur_List_len:3],\
                                        self.prefix_mas[mas_prefix][2:cur_List_len:3],\
                                        self.list_I_mean,text_file) 

                elif mas_prefix.startswith("EA"): 
                    self.calc_mean_ABC( self.prefix_mas[mas_prefix][0:cur_List_len:3],\
                                        self.prefix_mas[mas_prefix][1:cur_List_len:3],\
                                        self.prefix_mas[mas_prefix][2:cur_List_len:3],\
                                        self.list_U_mean,text_file)                    

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Получить списки усредненных значений "короткой посылки"
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_mean_values(self):    
        self.list_ampl_full = []
        self.list_angle_full = []

        self.list_ampl_full.extend(self.list_U_mean)
        self.list_ampl_full.extend(self.list_I_mean)

        self.list_angle_full.extend(self.list_phiABS_mean)
        #self.list_angle_full.extend(self.list_phi_UU_mean)
        #self.list_angle_full.extend(self.list_phi_II_mean)

        return self.freq_mean, self.list_ampl_full, self.list_angle_full

##################################################################################################
##################################################################################################
##################################################################################################
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Вычисление мат ожидания для 3-х списков
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def calc_mean_ABC(self,list_A, list_B, list_C, list_mean,text_file):
        
        mean_A = sum(list_A) / len(list_A)
        mean_B = sum(list_B) / len(list_B)
        mean_C = sum(list_C) / len(list_C)

        list_mean.append(mean_A)
        list_mean.append(mean_B)
        list_mean.append(mean_C)

        print("mean_A, mean_B, mean_C: " + str(list_mean[0]) + "  "+str(list_mean[1]) + "  "+str(list_mean[2]))

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Вычисление мат ожидания по углам фазовых сдвигов для 3-х списков
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def calc_mean_ABC_angle(self,list_U_A, list_U_B, list_U_C,list_I_A, list_I_B, list_I_C, list_mean,text_file):
        
        # дебажный print
        #max_len = max([len(list_A),len(list_B),len(list_C)])
        '''
        for elem in list_U_A: print("elem A: "+str(elem))
        for elem in list_U_B: print("elem B: "+str(elem))
        for elem in list_U_C: print("elem C: "+str(elem))
        print("\r\n")
        for elem in list_I_A: print("elem A: "+str(elem))
        for elem in list_I_B: print("elem B: "+str(elem))
        for elem in list_I_C: print("elem C: "+str(elem))
        print("\r\n")
        '''

        # правильные списки значений
        tr_list_U_A = []
        tr_list_U_B = []
        tr_list_U_C = []

        tr_list_I_A = []
        tr_list_I_B = []
        tr_list_I_C = []

        list_of_angle_list = [list_U_A, list_U_B, list_U_C,
                              list_I_A, list_I_B, list_I_C]
        
        true_list_of_angle_list = [ tr_list_U_A, tr_list_U_B, tr_list_U_C,
                                    tr_list_I_A, tr_list_I_B, tr_list_I_C]

        #########################
        list_index = 0

        for elem_list in list_of_angle_list:
            for elem in elem_list:
                if elem != 9999.0:
                    true_list_of_angle_list[list_index].append(elem)
            # на случай если список вдруг пуст (актуально для точек где фазы тока равны нулю)
            if len(true_list_of_angle_list[list_index]) == 0:
                true_list_of_angle_list[list_index].append(0.0)

            list_index += 1
        '''
        print("elems After\r\n")
        for elem in tr_list_U_A: print("elem A: "+str(elem))
        for elem in tr_list_U_B: print("elem B: "+str(elem))
        for elem in tr_list_U_C: print("elem C: "+str(elem))
        print("\r\n")
        for elem in tr_list_I_A: print("elem A: "+str(elem))
        for elem in tr_list_I_B: print("elem B: "+str(elem))
        for elem in tr_list_I_C: print("elem C: "+str(elem))
        print("\r\n")
        '''
        mean_U_A = sum(tr_list_U_A) / len(tr_list_U_A)
        mean_U_B = sum(tr_list_U_B) / len(tr_list_U_B)
        mean_U_C = sum(tr_list_U_C) / len(tr_list_U_C)

        mean_I_A = sum(tr_list_I_A) / len(tr_list_I_A)
        mean_I_B = sum(tr_list_I_B) / len(tr_list_I_B)
        mean_I_C = sum(tr_list_I_C) / len(tr_list_I_C)

        list_mean.append(mean_U_A)
        list_mean.append(mean_U_B)
        list_mean.append(mean_U_C)

        list_mean.append(mean_I_A)
        list_mean.append(mean_I_B)
        list_mean.append(mean_I_C)

        #print("mean_U_A, mean_U_B, mean_U_C: " + str(list_mean[0]) + "  "+str(list_mean[1]) + "  "+str(list_mean[2])) 
        #print("mean_I_A, mean_I_B, mean_I_C: " + str(list_mean[3]) + "  "+str(list_mean[4]) + "  "+str(list_mean[5]))      

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Парсинг строки ответ "данные по 3-м фазам" без символа возврата каретки
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def parse_MTE_answer_No_CR(self,text_data):              # парсить ответ от МТЕ по общим параметрам: 3 числа по 3 фазам
        
        mStr = text_data.split(",")               # Делим строку результата на блоки.
        len_mStr = len(mStr)
        if len_mStr >1:
            if mStr[1].startswith("--") or (len(mStr[1]) <= 1): #: # фаза А
                vA = 0                  # Нет значения в результатах измерений 
            else:
                vA = float(mStr[1])     # переводим значение во float
        else:
            print("parse_MTE_answer_No_CR:  len_mStr < 1   mStr = " + str(mStr))
            vA = -1
        if len_mStr >2:
            if mStr[2].startswith("--") or (len(mStr[2]) <= 1): #: # фаза Б
                vB = 0                  # Нет значения в результатах измерений 
            else:
                vB = float(mStr[2])     # переводим значение во float
        else:
            print("parse_MTE_answer_No_CR:  len_mStr < 2   mStr = " + str(mStr))
            vB = -1
        if len_mStr >3:
            if (mStr[3].startswith("--")) or (len(mStr[3]) <= 1): #: # фаза C
                vC = 0                  # Нет значения в результатах измерений 
            else:
                vC = float(mStr[3])
        else:
            print("parse_MTE_answer_No_CR:  len_mStr < 3   mStr = " + str(mStr))
            vC = -1 

        return vA, vB, vC

        #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Парсинг строки ответ 
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def parse_MTE_answer_ANGLES_No_CR(self,text_data): 
        mStr = text_data.split(",")               # Делим строку результата на блоки.
        len_mStr = len(mStr)
        ang_list = []
        for idx in range(1,7):
            if len_mStr > idx:
                if mStr[idx].startswith("--") or (len(mStr[idx]) <= 1): ang_list.append(9999.0)
                else: ang_list.append(float(mStr[idx]))
            else:
                print("parse_MTE_answer_No_CR:  len_mStr < 1   mStr = " + str(mStr))
                ang_list.append(9999.0)

        return ang_list
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Парсинг строки ответ "частота" без символа возврата каретки
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def parse_MTE_answer_Freq_No_CR(self, text_data):              # парсить ответ от МТЕ по общим параметрам: 3 числа по 3 фазам
        #print("parse_MTE_answer: " + textFromMTE)
        mStr = text_data.split(",")               # Делим строку результата на блоки.

        if len(mStr) == 2:
            if mStr[1].startswith("--") or (len(mStr[1]) <= 1): #
                vFreq = 0                  # Нет значения в результатах измерений 
            else:
                lastVal = mStr[1]       
                vFreq = float(lastVal)     # переводим значение во float
        else:
            print("parse_MTE_answer_Freq_No_CR:  len(mStr) != 2   len(mStr) = "+str(len(mStr)))
            vFreq = -1 

        return vFreq  
#       
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Обработчик команд автовыдачи списка результатов
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def SU_handler(self):
        print("\r\nStart/Stop automatic sending result menu")
        print("1 - Start automatic sending result")
        print("0 - Stop automatic sending result")
        SU_num = int(input())
        if SU_num == 1:     self.start_auto_measure()
        elif SU_num == 0:   self.stop_auto_measure()
        else: print("Input wrong command 'SU_handler'")
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Обработчик времени измерения счетчика
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def SetTimeMenuHandler(self):
        print("1 - Get current measured Time in seconds")
        print("2 - Set Meas Time In seconds")
        print("3 - Set External sync")
        print("4 - Back")
        num = int(input())

        if num == 4:
            print("\r\nPressed: 4 - Back")
        elif num == 1:
            print("\r\nPressed: 1 - Get current measured Time in seconds")
            self.send_to_MTE("T\r")
            self.parse_MTE_answer_Time()
        elif num == 2:
            print("\r\nPressed: 2 - Meas Time In seconds")
            print("Enter Meas Time In seconds:")
            
            mTime = str(input())
            
            if (int(float(mTime))) != 0:
                print("Entering Meas Time In seconds: " + mTime)
            else:
                print("\r\nExternal synchronization mode activated!")
            
            write_str = "T" + mTime + "\r"
            self.send_to_MTE(write_str)
        elif num == 3:
            print("\r\nExternal synchronization mode activated!")

            write_str = "T0\r"
            self.send_to_MTE(write_str)
        else:
            print("\r\nSomething go wrong! input num (1-4) in 'set time menu'") 
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Парсинг строки-времени измерения от счетчика
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def parse_MTE_answer_Time(self):         
        mStr = self.textFromMTE.split("=")               # Делим строку результата на блоки.
        if len(mStr) == 2:
            m_time = float(mStr[1])
        else:
            m_time = -1
            print("Can't read measurement time")
            return
        if m_time == 0:             # Внешняя синхронизация
            print("\r\n'T = 0' -> Set 'External synchronization' mode") 
        else:
            print("\r\nCurrent measured Time is: ", str(m_time), " sec.") 

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Установить время измерения счетчика
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def set_meas_time(self, meas_time):
        if int(meas_time) == 0 or float(meas_time) == 0.0:
            print("Set external sync mode for MTE Counter")
            meas_time = 0.0
        self.set_measure_time(meas_time)

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Установить режим внешней синхронизации счетчика
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def set_ext_sync_mode(self):
        self.set_measure_time(0.0)

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Начать автопередачу результатов со счетчика МТЕ
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def start_auto_measure(self):
        self.send_to_MTE("SU1\r")

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Закончить автопередачу результатов со счетчика МТЕ
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def stop_auto_measure(self):
        self.send_to_MTE("SU0\r")

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Установить параметры списка автовыдачи результатов
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def set_SP_list(self):
        SP_menu_num = -1

        write_str = "SP0,0\r"# очистка всего списка перед началом работы
        self.send_cmd_to_device(write_str)

        while(True):
            if SP_menu_num == 12:           # Remove all elements from list
                write_str = "SP0,0\r"
                self.send_cmd_to_device(write_str)

                for number in range(self.len_resultList_mas):
                    if number > 0 and number < 12:
                        plus_min_str = "-"
                        self.resultList_mas[number*self.num_elem_in_row+1] = 0
                    else:
                        plus_min_str = ""
                    print(plus_min_str + self.resultList_mas[number*self.num_elem_in_row])

            elif SP_menu_num == 13:
                return 

            elif SP_menu_num >= 1 and SP_menu_num <= 11:
                print("Choosen list element:      (+/-)   " + self.resultList_mas[number*self.num_elem_in_row])
                print("0 - remove element from list")
                print("1 - add element to list")
                print("2 - add this element and remove all another from the list")
                
                eleCmd_num = int(input())

                if eleCmd_num == 0:                             # Удалить элемент из списка    
                    plus_min_str = "-"
                    self.resultList_mas[SP_menu_num*self.num_elem_in_row+1] = 0
                    write_str = "SP" + str(self.resultList_mas[SP_menu_num*self.num_elem_in_row+2]) + "," + \
                                str(self.resultList_mas[SP_menu_num*self.num_elem_in_row+1]) + "\r"
                    self.send_cmd_to_device(write_str)

                elif eleCmd_num == 1:                             # Добавить элемент в список
                    plus_min_str = "+"
                    self.resultList_mas[SP_menu_num*self.num_elem_in_row+1] = 1
                    write_str = "SP" + str(self.resultList_mas[SP_menu_num*self.num_elem_in_row+2]) + "," + \
                                str(self.resultList_mas[SP_menu_num*self.num_elem_in_row+1]) + "\r"
                    self.send_cmd_to_device(write_str)

                elif eleCmd_num == 2:                               # Исключить все элементы, кроме выбранного

                    for number in range(self.len_resultList_mas):
                        if number > 0 and number < 12:
                            self.resultList_mas[number*self.num_elem_in_row+1] = 0
                    
                    plus_min_str = "+"
                    self.resultList_mas[SP_menu_num*self.num_elem_in_row+1] = 1
                    write_str = "SP" + str(self.resultList_mas[SP_menu_num*self.num_elem_in_row+2]) + "," + \
                                str(2) + "\r"
                    self.send_cmd_to_device(write_str)

                else:
                    print("Input wrong command 'choosen list elem'")

            elif SP_menu_num == -1:

                full_cmd = ""
                for number in range(self.len_resultList_mas):
                    if number > 0 and number < 12:
                        write_str = "SP" + str(self.resultList_mas[number*self.num_elem_in_row+2]) + "," + \
                                    str(self.resultList_mas[number*self.num_elem_in_row+1]) + ";"
                        full_cmd = full_cmd + write_str
                    
                self.send_cmd_to_device(full_cmd)

            else:
                print("Input wrong command 'SP_menu_num'")

            write_str = []

            for number in range(self.len_resultList_mas):
                if number > 0 and number < 12:
                    if self.resultList_mas[number*self.num_elem_in_row+1] == 0:
                        wr_str = "-"
                    else:
                        wr_str = "+"
                else:
                    wr_str = ""

                print(wr_str + self.resultList_mas[number*self.num_elem_in_row])

            SP_menu_num = int(input())

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Обработчик измерения общих параметров счетчика
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def GetMenuHandler(self):
        while(True):
            print("GetCommonMenu_Handler")
            print("\r\nGet menu:")
            print("1 - Common params measurements")
            print("2 - Harmonics measurements")
            print("3 - Back")

            num = int(input())

            if num == 3:
                print("\r\nPressed: 3 - Back")
                return
            elif num == 1:
                print("\r\nPressed: 1 - Common params measurements")
                for ind in range(int(len(self.GetCommonMenuItems_mas)/3)):
                    print(self.GetCommonMenuItems_mas[ind*3])

                GetCommon_menu_num = int(input())
                self.GetCommonMenuHandler(GetCommon_menu_num)  # обработчик ответа от счетчика МТЕ

            elif num == 2:
                print("\r\nPressed: 2 - Harmonics measurements")
                # режим гармоник -> выбор фазы -> выбор ток/напряжение -> парсим ответ
                print("\r\nChoose phase A/B/C:")
                print("1 - A")
                print("2 - B")
                print("3 - C")
                print("4 - Back")
                #  меню выбора гармоник     выбор фазы ->
                GetHarmPhase_num = int(input())
                if GetHarmPhase_num == 4:
                    print("\r\nPressed: 4 - Back")
                else:
                    print("\r\nChoose phase U/I:")
                    print("1 - U")
                    print("2 - I")
                    print("3 - Back")
                    GetHarmUI_num = int(input())
                    if GetHarmUI_num == 3:
                        print("\r\nPressed: 3 - Back")
                    else:
                        self.get_spectrum_from_counter(GetHarmUI_num,GetHarmPhase_num, GetHarmPhase_num + GetHarmUI_num*3)
            else:
                print("Something go wrong! input num (1-4) 'Measure menu 'Counter MTE''.")
            
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Обработчик измерения общих параметров счетчика
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def GetCommonMenuHandler(self,num):
        if num == 11:
            print("\r\nPressed: 11 - Back")
            return
        elif num >= 1 and num < 10:
            print("Waiting for measured: " + self.GetCommonMenuItems_mas[num*3]) 
            write_str = "?" + str(self.GetCommonMenuItems_mas[num*3+2]) + ";"
            self.send_cmd_to_device(write_str)

        elif num == 10:
            print("Waiting for measured: FREQ")
            #write_str = "FRQ\r"
            #self.send_cmd_to_device(write_str)   

        else:
            print("Something go wrong! input num set menu item.")
            return

        if num != 10:
            vA = vB = vC = 0
            vA, vB, vC = self.parse_MTE_answer()   #2 парсим считанную строку
            print("\r\nValue A: ",str(vA),\
                "Value B: ",str(vB),\
                "Value C: ",str(vC))                     #3 выводим распарсенный результат
        else:
            vFreq = 0
            vFreq = self.get_current_FREQ()      #2 парсим считанную строку
            print("\r\nFreq is: ",str(vFreq), "  Hz")                      #3 выводим распарсенный результат

    ################################################################################
    ################################################################################
    ################################################################################
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Запросить, считать и распарсить все спектры со счетчика МТЕ
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_all_spectrum(self):

        #команда - запрос спектра
        #get_spectrum_from_counter(self,numUI,numPhase)

        numUI_mas = [1,2]   # 1-U, 2-I
        numPhase_mas = [1,2,3]   # 1-A, 2-B, 3-C

        idx_list = 0

        for idx_ui in range(len(numUI_mas)):                # цикл: напряжение/ток
            for idx_ph in range(len(numPhase_mas)):         # цикл: по фазам А/B/C
                self.get_spectrum_from_counter(numUI_mas[idx_ui],numPhase_mas[idx_ph],idx_ph+idx_ui*3)
                idx_list += 1

        # чтение и парсинг ответа
        # сохранение принятых значений.

    ################################################################################
    ################################################################################
    ################################################################################
    
        # выдать окончательный результат в виде: (list_Ua_mag, list_Ua_ang), (list_Ub_mag, list_Ub_ang), ...
        # где  list_Ua_mag - список из 32-х значений типа float с амплитудами гармоник напряжения фазы А: 0-нулевая гармоника, 1-основная частота, 2-я, 3-я, ... 31-я гармоника

    ################################################################################
    ################################################################################
    ################################################################################

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Измерение спектра (счетчик)
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_spectrum_from_counter(self,numUI,numPhase,num_list_m):
        
        self.numUI = numUI
        self.numPhase = numPhase
        harmCommand = self.harm_dict[self.numUI+2] + str(self.harm_dict[self.numPhase-1]) + "\r"            # строка: команда запроса спектра с генератора МТЕ
        harm_text = self.send_cmd_to_device(harmCommand) # команда - получить спектр
        self.UI_max = self.get_UI_max_range()            # узнать текущий диапазон измерения счетчика МТЕ
        #self.freq = self.get_current_FREQ()             # запросить текущую частоту сигнала

        self.parse_MTE_Harm_answer(harm_text,num_list_m)           # парсинг строки-спектра от генератора МТЕ

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Установить диапазоны для счетчика
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def set_ranges_for_CNT(self,ranges_CNT):
        self.send_to_MTE(ranges_CNT)
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Узнать текущую частоту
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_current_FREQ(self):      # запросить текущую частоту сигнала
        write_str = "?13\r"
        self.send_cmd_to_device(write_str)
        #vFreq = self.parse_MTE_answer_Freq()
        mStr = self.textFromMTE.split(",")               # Делим строку результата на блоки.
        if len(mStr) == 2:
            if mStr[1].startswith("--") or (len(mStr[1]) <= 1):
                vFreq = 0                  # Нет значения в результатах измерений 
            else:
                lastVal = mStr[1]       # Убираем в конце символ <CR>
                vFreq = float(lastVal[0:len(lastVal)-1:1])     # переводим значение во float
        else:
            print("parse_MTE_answer_Freq_No_CR:  len(mStr) != 2   len(mStr) = "+str(len(mStr)))
            vFreq = -1 
        return vFreq
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Узнать текущий диапазон измерения
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_UI_max_range(self):             # узнать текущй диапазон измерения

        #### Begin узнать текущй диапазон измерения  ->
            #1 запрос текущего напряжения/тока
        if self.numUI == 1:                      # Значения токов
            #! print("Waiting for measured: " + get_common_params_Counter.GetCommonMenuItems_mas[(numUI+1)*3]) 
            write_str = "?" + str(self.GetCommonMenuItems_mas[(self.numUI+1)*3+2])+ "\r"
        elif self.numUI == 2:                      # Значения напряжений
            #! print("Waiting for measured: " + get_common_params_Counter.GetCommonMenuItems_mas[(numUI-1)*3]) 
            write_str = "?" + str(self.GetCommonMenuItems_mas[(self.numUI-1)*3+2])+ "\r"
        else:
            print("Error UI num in parse MTE harms")
            return
        
        self.send_cmd_to_device(write_str)

        vA, vB, vC = self.parse_MTE_answer()       #2 парсим считанную строку
        UI_max = 0
        if self.numPhase == 1:
            UI_max = vA
        if self.numPhase == 2:
            UI_max = vB
        if self.numPhase == 3:
            UI_max = vC

        #2 определение границы диапазона по таблице
        UI_cur_max_range = 0    # диапазон максимальный

        #### Диапазоны тока и напряжения для чтения значений гармоник
        U_max_ranges_mas = [ 0.4,5.0,65.0,130.0,260.0,520.0 ]
        I_max_ranges_mas = [ 0.004,0.012,0.04,0.12,0.4,1.2,4.0,12.0 ] 

        if self.numUI == 2:                        # Значения токов
            len_dict = len(I_max_ranges_mas)
            for idx in range(len_dict):
                if UI_max < I_max_ranges_mas[idx] :
                    UI_cur_max_range = I_max_ranges_mas[idx]
                    break
        elif self.numUI == 1:                      # Значения напряжений
            len_dict = len(U_max_ranges_mas)
            for idx in range(len_dict):
                if (int(UI_max)+1) < U_max_ranges_mas[idx]:     # округление напряжения основной гармоники вверх для правильной установки диапазона
                    UI_cur_max_range = U_max_ranges_mas[idx]
                    break
        else:
            print("Error UI num in parse MTE harms")
            return -1

        if UI_cur_max_range == 0:
            print("Error UI_cur_max_range (MTE harms)  UI_cur_max_range == " + str(UI_cur_max_range) + " \r\n Main harmonics amplitude is zero") 
        print("UI_cur_max_range: " + str(UI_cur_max_range))

        return UI_cur_max_range

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Парсинг строки-спектра (спектр)
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def parse_MTE_Harm_answer(self,harm_text,num_list_m):# парсинг строки-спектра от генератора МТЕ
        # формат принимаемой строки: RS(U/I)<ph>=<0/1>,<re0><im0><re1><im1> ... <re31><im31>
        # формат значения: <re[i]> = (+/-)Z.zzzzE(+/-)Z (итого 10 символов)
        #   распарсенное значение: re[i] = float(str_re_i[0:7:1])*10**float(str_re_i[8:10:1])
        
        # распарсить значения -> сгруппировать Ре и Им части в массивы -> расчет окончательного результата

        print("\r\nparse_MTE_Harm_answer self.textFromMTE" + str(harm_text)+"\r\n")

        textFromMTE_common = harm_text.split(",")
        #flafNewVal = textFromMTE_common[0][-1]      # доступны ли новые данные для считывания

        ### Begin распарсить значения -> сгруппировать Ре и Им части в массивы ->
        re_im_str = textFromMTE_common[1]       # строка только из форматированных значений Re и Im
        len_re_im_div20 = 32         # 31 + 1 = 32 - Число гармоник которое считает МТЕ (31) плюс основная гармоника

        t_re = t_im = 0 # промежуточные переменные для формирования значений Ре и Им
        t_idx = 0

        list_re = []
        list_im = []

        for idx in range(len_re_im_div20):
            t_idx = idx*20
            t_re = float(re_im_str[t_idx:t_idx+7:1])*10**float(re_im_str[t_idx+8:t_idx+10:1])
            list_re.append(t_re)
            t_idx = t_idx + 10
            t_im = float(re_im_str[t_idx:t_idx+7:1])*10**float(re_im_str[t_idx+8:t_idx+10:1])
            list_im.append(t_im)
        ### End распарсить значения -> сгруппировать Ре и Им части в массивы ->

        # шапка таблицы результатов измерения гармоник
        print('{0:^4s} {1:^14s} {2:^14s}'.format("harm №", "Abs","Ang, [°]"))

        self.list_m[num_list_m].clear()
        self.list_a[num_list_m].clear()

        radToDeg_coef = 180.0 / pi
        harm_coef = self.UI_max / 32767.0

        for idx in range(len_re_im_div20):
            list_re[idx] = list_re[idx] * harm_coef    # списки со значениями Ре (и Им)
            list_im[idx] = list_im[idx] * harm_coef

            self.list_m[num_list_m].append( sqrt(list_re[idx]*list_re[idx] + list_im[idx]*list_im[idx]) )
            #list_angle.append( radToDeg_coef * math.atan2(list_im[idx], list_re[idx])) 
            self.list_a[num_list_m].append( radToDeg_coef * atan(list_im[idx]/list_re[idx])) 

            print('{0:4d} {1:14f} {2:14f}'.format(idx, self.list_m[num_list_m][idx], self.list_a[num_list_m][idx]))

        #! Вызовы функции Дмитрия: "получить значения спектра:  1) амплитуд гармоник [list_module] (0..31) \
        #                                                       2) фаз гармоник      [list_angle]  (0..31) \ 
        #                                                       3) напряжение/ток                  (0,1)   \
        #                                                       4) фаза A/B/C                      (0,1,2) \  


    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Проверка установки точки ПСИ по счетчику МТЕ
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def check_PSI_pnt(self,sig, exist_harms_flag, log_time_file): 
        if exist_harms_flag == True:
            return self.check_PSI_point_harms(sig)

        ask_str_mas = ["?2;","?1;","?21;","?9;","?13;"]      
        meas_vals = []
        # отправка команды получение ответа (по одной)
        self.ser_port.flushInput()
        self.ser_port.flushOutput()

        main_sig = sig.get_main_freq_vector()
        etalon_freq = sig.get_frequency()
        measfreq = 0
        keys_vect_dict = ["Ua", "Ub", "Uc", "Ia", "Ib", "Ic"]
        etalon_vals = []
        for idx_keys in keys_vect_dict: 
            etalon_vals.append(main_sig.get_ampl(idx_keys))

        for idx_k in range(len(keys_vect_dict)):    
            
            # В 'Сигнале' эталонные значения фазового сдвига для тока не такие же, как и в .csv файле
            # правильные значения (как в .csv файле) = phi_I_signal_X - phi_U_signal_X
            if idx_k > 2: t_phase = main_sig.get_phase(keys_vect_dict[idx_k]) - main_sig.get_phase(keys_vect_dict[idx_k-3])
            else: t_phase = main_sig.get_phase(keys_vect_dict[idx_k])
            etalon_vals.append(t_phase)

        ##########################
        N_total_iter = 5    #  Сколько раз повторно спрашиваем измерения с генератора МТЕ
        delta = 2           # [%]
        margin_angle = 2    # [град.]
        set_PSI_point_flag = [] # список флагов: пройдена ли проверка по этому параметру. 
        #Сигнал считается установленным когда по всем параметрам пройдена проверка. Наиболее часто не устанавливается сигнал тока фазы А

        self.ser_port.timeout = 0.2     # интервал между опросами коротких команд
        ##########################
        print("check_PSI_point Counter")

        for check_gen_iter in range(N_total_iter):              # Внешний цикл по итерациям - опрос-анализ ответа от МТЕ
            #print("check_cnt_iter: "+str(check_gen_iter+1))

            wr_str = "check_cnt_iter,"+str(check_gen_iter+1)+"\r\n"
            log_time_file.write(wr_str)

            self.ser_port.flushInput()
            self.ser_port.flushOutput()         
            set_PSI_point_flag.clear()
            check_set_PSI = False

            for ask_idx in range(len(ask_str_mas)):
                self.ser_port.write(ask_str_mas[ask_idx].encode())  
                textFromMTE = self.ser_port.read(800)
                try:
                    textFromMTE = textFromMTE.decode()
                except: #expression as identifier:
                    break
                    #pass
                
                meas_vals = []# обнуление списков после каждой итерации опроса
                
                if ask_idx < 2:   
                    #print("textFromMTE"+textFromMTE)                  # Обработка ответов на запрос 1-ампл. тока, 2-ампл. напряжения
                    meas_vals.extend(self.parse_MTE_answer_text(textFromMTE))
                    #for m_vals in meas_vals: print(m_vals)

                    for t_idx in range(3):
                        phase_idx = ask_idx*3 + t_idx
                        if etalon_vals[phase_idx] >= 0.001: cur_delta = abs((etalon_vals[phase_idx] - \
                            meas_vals[t_idx])/etalon_vals[phase_idx]) * 100.0
                        elif meas_vals[t_idx] != 0.0: cur_delta = abs(meas_vals[t_idx])# * 100.0
                        else: cur_delta = 0
                    
                        if cur_delta > delta:
                            #print("Error on phase "+str(t_idx)+": measured value: " + str(meas_vals[t_idx])+" etalon value: " + \
                            #    str(etalon_vals[phase_idx]) +" calc delta %: "+str(cur_delta)+" max delta %: "+str(delta))
                            set_PSI_point_flag.append(False)
                        else: set_PSI_point_flag.append(True)

                elif ask_idx == 2 or ask_idx == 3:  # 2 - phase_UU,  3 - phase_UI
                    #print("textFromMTE"+textFromMTE)
                    meas_vals.extend(self.parse_MTE_answer_text(textFromMTE))

                    for t_idx in range(3):
                        meas_vals[t_idx] *= (-1)
                        
                    if ask_idx == 2:
                        #meas_vals[2] = meas_vals[2] #*(-1)
                        #meas_vals[1] = meas_vals[0] *(-1)
                        meas_vals[2] = meas_vals[2] *(-1)
                        meas_vals[1] = meas_vals[0] #*(-1)
                        meas_vals[0] = 0.0

                    if ask_idx == 3:
                        for idd in range(len(meas_vals)):
                            if meas_vals[idd] > 180.0: meas_vals[idd] -= 360

                    for t_idx in range(3):
                        phase_idx = ask_idx*3 + t_idx

                        if etalon_vals[phase_idx - 3*(ask_idx-1)] == 0.0:
                            continue

                        if (meas_vals[t_idx] < -180.0): meas_vals[t_idx] += 360
                        if (meas_vals[t_idx] > 180.0): meas_vals[t_idx] -= 360                            

                        if abs((abs(etalon_vals[phase_idx]) - 180.0)) < margin_angle:
                            if abs((abs(meas_vals[t_idx]) - 180.0)) < margin_angle:
                                if etalon_vals[phase_idx] > 0:
                                    meas_vals[t_idx] = abs(meas_vals[t_idx])
                                else:
                                    meas_vals[t_idx] = (-1)*abs(meas_vals[t_idx])

                        if etalon_vals[phase_idx] != 0.0: cur_delta = abs((etalon_vals[phase_idx] - \
                            meas_vals[t_idx])/etalon_vals[phase_idx]) * 100.0
                        elif meas_vals[t_idx] != 0.0: cur_delta = abs(meas_vals[t_idx])# * 100.0
                        else: cur_delta = 0

                        if cur_delta > delta:
                            #print("Error on phase "+str(t_idx)+": measured value: " + str(meas_vals[t_idx])+" etalon value: " + str(etalon_vals[phase_idx]) +" calc delta %: "+str(cur_delta)+" max delta %: "+str(delta))
                            set_PSI_point_flag.append(False)
                        else: 
                            set_PSI_point_flag.append(True)

                    #print("meas_vals: "+str(meas_vals[0])+" "+str(meas_vals[1])+" "+str(meas_vals[2])+" ")
                    #print("etal_vals: "+str(etalon_vals[ask_idx*3])+" "+str(etalon_vals[ask_idx*3+1])+" "+str(etalon_vals[ask_idx*3+2])+" ")

                    #for m_vals in meas_vals: print(m_vals)

                else:
                    measfreq = self.parse_MTE_answer_Freq(textFromMTE)
                    #print("vfreq: "+str(measfreq))
                    if etalon_vals[phase_idx] != 0.0: cur_delta = abs((etalon_freq - measfreq)/etalon_freq) * 100.0
                    else: cur_delta = 0
                    if cur_delta > delta:
                        #print("Error in Frequency measured value: " + str(measfreq)+" etalon value: " + str(etalon_freq) +" calc delta %: "+str(cur_delta)+" max delta %: "+str(delta))
                        set_PSI_point_flag.append(False)
                    else: set_PSI_point_flag.append(True)
                        
            check_set_PSI = True
            for flag_elem in set_PSI_point_flag:
                if flag_elem == False:
                    check_set_PSI = False
                    break
            #
            wr_str = "after check_CNT iter,"+str(dt.datetime.now())+","+str(dt.datetime.now().hour)+ ","+str(dt.datetime.now().minute)+ ","+str(dt.datetime.now().second)+ ","+"\r\n"
            #wr_str = "after check_CNT iter,"+str(datetime.datetime.now().time())+"\r\n"
            log_time_file.write(wr_str)
            #print(wr_str)
            #
            if check_set_PSI == True:
                break
            
            self.ser_port.timeout = 0.3
            self.ser_port.write("".encode())        # перерыв между опросами в одной итерации равный 1 секунде
            self.ser_port.timeout = 0.2

        #print("finally Counter: check_set_PSI == "+str(check_set_PSI))
        return check_set_PSI

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Установить на счетчике МТЕ текущее время (время компьютера)
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def set_MTE_current_Time(self):#,py_t):
        # формат команды: "TIME22,3,0,14,0,0;" - установить дату 22.03.2000, время 14:00:00
        self.ser_port.timeout = 0.2
        py_t = dt.datetime.now()
        list_py_t = [py_t.day, py_t.month, py_t.year - 2000, py_t.hour, py_t.minute, py_t.second]
        for elem in range(len(list_py_t)): list_py_t[elem] = str(list_py_t[elem])
        #dots = '..'
        #my_str = dots.join(['1', '2'])  # '1..2'
        time_str = "TIME" + ','.join(list_py_t) + ";"

        self.send_cmd_to_device(time_str)

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Запросить текущее время с устройства МТЕ
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_MTE_current_Time(self):              # парсить ответ от МТЕ по общим параметрам: 3 числа по 3 фазам
        return self.get_MTE_Device_current_Time()

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Проверка установки сигнала по гармоникам для счетчика
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def check_PSI_point_harms(self,sig):
        counter_for_reset = 0
        maxIter_reset_cmd = 2

        is_PSI_pnt_set = False

        while((is_PSI_pnt_set != True)and(counter_for_reset < maxIter_reset_cmd)):
            #self.is_PSI_pnt_set = True
            #self.ser_port.timeout = 4
            #self.SET_cmd()
            is_PSI_pnt_set = self.check_harms(sig)
            counter_for_reset += 1
        
        print("finally set_PSI_point_flag HARMS: "+str(is_PSI_pnt_set))
        return is_PSI_pnt_set 

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Проверка установки сигнала по гармоникам для счетчика
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def check_harms(self,sig):
        # Алгоритм работы следующий:
        # запрсили-сохранили-распарсили все спектры с генератора
        # проверяем по всем амплитудам гармоник и по всем фазам установку сигнала

        keys_vect_dict = ["Ua", "Ub", "Uc", "Ia", "Ib", "Ic"]
        #1 запрсили-сохранили-распарсили все спектры с генератора
        
        self.get_all_spectrum()

        print("self.list_Ua_ang, "+str(len(self.list_Ua_ang))+"\r\n"+\
                " self.list_Ub_ang, "+str(len(self.list_Ub_ang))+"\r\n"+\
                " self.list_Uc_ang, "+str(len(self.list_Uc_ang))+"\r\n"+\
                " self.list_Ia_ang, "+str(len(self.list_Ia_ang))+"\r\n"+\
                " self.list_Ib_ang, "+str(len(self.list_Ib_ang))+"\r\n"+\
                " self.list_Ic_ang, "+str(len(self.list_Ic_ang))+"\r\n" )
        
        print(" self.list_Ua_mod, "+str(len(self.list_Ua_mod))+"\r\n"+\
                " self.list_Ub_mod, "+str(len(self.list_Ub_mod))+"\r\n"+\
                " self.list_Uc_mod, "+str(len(self.list_Uc_mod))+"\r\n"+\
                " self.list_Ia_mod, "+str(len(self.list_Ia_mod))+"\r\n"+\
                " self.list_Ib_mod, "+str(len(self.list_Ib_mod))+"\r\n"+\
                " self.list_Ic_mod, "+str(len(self.list_Ic_mod))+"\r\n" )

        #print("list_magn " + str(len(list_magn)))
        #print("list_angl " + str(len(list_angl)))

        #2 проверяем по амплитудам гармоник и по всем фазам установку сигнала
        
        ##########################
        delta = 10               # [%]
        #margin_angle = 2        # [град.]
        ##########################

        set_PSI_point_flag = True

        for idx_harm_num in range(2, 32):   # цикл по всем гармоникам

            cur_harm_signal = sig.get_vector_harm(idx_harm_num)    # текущий объект Vector_values с параметрами idx_harm_num гармоники

            for idx_phase in range(6):              # цикл по содержимому векторов

                
                etalon_ampl = cur_harm_signal.get(keys_vect_dict[idx_phase])[0] 
                measered_ampl = self.list_m[idx_phase][idx_harm_num]

                if etalon_ampl != 0.0: 
                    cur_delta = abs((etalon_ampl - measered_ampl)/etalon_ampl) * 100.0

                    if etalon_ampl < 0.5:
                        #cur_delta /= 10.0
                        cur_delta *= (1.0/delta) / 3.0
                    #print("idx_phase: "+str(idx_phase)+"  idx_harm_num " + str(idx_harm_num))
                    #print("etalon_ampl: "+str(etalon_ampl)+"  measered_ampl " + str(round(measered_ampl,5))+" cur_delta"+str(round(cur_delta,5)))
                elif measered_ampl != 0.0: 
                    cur_delta = abs(measered_ampl)# * 100.0

                else: cur_delta = 0

                
                if cur_delta > delta:
                    print("Error on phase "+str(idx_phase)+" harm num: "+str(idx_harm_num)+\
                          ": measered_ampl: " + str(measered_ampl)+" etalon_ampl: " + str(etalon_ampl) +\
                                " calc delta %: "+str(cur_delta)+" max delta %: "+str(delta))
                    set_PSI_point_flag = False
                #else:   set_PSI_point_flag = True

                ################################
                """
                etalon_phase = cur_harm_signal.get(keys_vect_dict[idx_phase])[1] 
                measered_phase = self.list_a[idx_phase][idx_harm_num]

                if etalon_phase != 0.0: cur_delta = abs((etalon_phase - measered_phase)/etalon_phase) * 100.0
                elif measered_phase != 0.0: cur_delta = abs(measered_phase) # * 100.0
                else: cur_delta = 0

                print("idx_phase: "+str(idx_phase)+"  idx_harm_num " + str(idx_harm_num))
                print("etalon_phase: "+str(etalon_phase)+"  measered_ampl " + str(round(measered_phase,5))+" cur_delta"+str(round(cur_delta,5)))


                if cur_delta > delta:
                    print("Error on phase "+str(idx_phase)+" harm num: "+str(idx_harm_num)+\
                          ": measered_phase: " + str(measered_phase)+" etalon_phase: " + str(etalon_phase) +\
                                " calc delta %: "+str(cur_delta)+" max delta %: "+str(delta))
                    set_PSI_point_flag = False
                else:   set_PSI_point_flag = True
                """

        print("finally set_PSI_point_flag HARMS: "+str(set_PSI_point_flag))
        return set_PSI_point_flag



if __name__ == "__main__":
    pass



        