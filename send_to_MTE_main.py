""" 
MakeCmdFromCSV this module reads PSI scenariy.csv file and convert it to MTE comands
"""
import serial

import MTE_Counter
import MTE_Generator
import names_parameters
import measurement
import make_psi
import MTE_parameters
import report

#------
import datetime as dt

import time

#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
#-----Функция main. Режимы работы: основной-непрерывный прогон точек ПСИ, отладочный - меню управления МТЕ
#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
def main():
    #debug_mode = True        #True == режим отладки - работает меню и обмен данными только с устройствами МТЕ
    debug_mode = False      # # False == режим ПСИ - автоматический перебор точек, измерения и по МТЕ и по Биному

    log_time_file = open("Time_log.txt", "w")     # 'a'	открытие на дозапись, информация добавляется в конец файла.
    log_time_file.flush()

    if debug_mode == True:
        TopMenuItems()
        counter_MTE, generator_MTE, parameters_MTE = init_main_MTE()
        HandleMenu(counter_MTE, generator_MTE, parameters_MTE,log_time_file)
    else:
        do_PSI(log_time_file)

    log_time_file.close()

#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
#-----Функция инициализации Бинома
#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
def init_main_Binom():  
    #make_psi.deinit() 
    make_psi.init()

#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
#-----Функция инициализации МТЕ
#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
def init_main_MTE():
    # Создание большого списка сигналов. Один экземпляр класса сигнал для одной точки ПСИ
    #set_pnts_for_PSI = create_dict_test_points("PSI_Binom3_5_57.csv")
    measurement.create_dict_test_points("PSI_Binom3_5_57_for_debug.csv")
    #measurement.create_dict_test_points("PSI_Binom3_5_57.csv")
    #1.1 - inits serial ports
    timeout_cnt = 0.5
    timeout_gen = 0.5
    ser_Generator   = serial.Serial("COM2", 19200, timeout=timeout_cnt, parity=serial.PARITY_NONE, rtscts=0)
    ser_Counter     = serial.Serial("COM3", 19200, timeout=timeout_gen, parity=serial.PARITY_NONE, rtscts=0)
    #1.2 - Create objects MTE device
    #1.2.1 - MTE Counter
    write_str = "MODE1;DB1;SU0;SP1,1;SP2,1;SP35,1;SP13,1;T0;MAN;YI0\r"   # mode of send/get command by COM4 'Counter' port # режим токовых входов 12 А (по умолчанию стоит 120 А)
    counter_MTE = MTE_Counter.C_MTE_Counter(ser_Counter, timeout_cnt, write_str, 0, 0)
    #1.2.2 - MTE Generator
    write_str = "MODE1;T1\r"   # mode of send/get command by COM1 'Generator' port
    generator_MTE = MTE_Generator.C_MTE_Generator(ser_Generator, timeout_gen, write_str, 0, 0)
    #1.2.3 - MTE Parameters - класс для генерации команд установки сигнала на генератор МТЕ и диапазонов измерения на генератор и счетчик МТЕ
    parameters_MTE = MTE_parameters.C_MTE_parameters()

    return counter_MTE, generator_MTE, parameters_MTE

#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
#-----Функция проверки на корректность введенных номеров начально и конечной точек ПСИ
#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
def do_PSI(log_time_file):
    
    st_pnt = 1
    end_pnt = 2
    if not check_pnts(st_pnt, end_pnt):
        return

    ##################################

    list_mte_end_time = []      #время окончания считывания данных со счетчика МТЕ
    list_mte_delta_time = []    #интервал считывания данных со счетчика МТЕ
    list_blob_time = []         #время последней записи в BLOB-ячейку со статистикой

    ##################################

    
    cur_pnt = st_pnt
    # Инициализация для получения данных с Бинома
    init_main_Binom()
    # Инициализация для управления МТЕ
    counter_MTE, generator_MTE, parameters_MTE = init_main_MTE()
    try:

        make_psi.binom_data.open_svg_channel()


        while cur_pnt <= end_pnt:
            print("\r\n"+"current PSI point is "+str(cur_pnt)+"\r\n")
            #1.3 - Set PSI point on Generator
            sig = measurement.measurement_storage.get_etalon_signal(cur_pnt)
            parameters_MTE.init_data(sig)
            set_PSI_pnt_flag_Generator = generator_MTE.set_PSI_point(sig,parameters_MTE, log_time_file)
            if set_PSI_pnt_flag_Generator == True:      # проверка установки точки ПСИ по генератору пройдена  
                counter_MTE.ser_port.timeout = 1
                counter_MTE.set_ranges_for_CNT(parameters_MTE.get_ranges_CNT())     # Установка диапазонов для Счетчика
                # 1.3.2 - Check by Counter
                set_PSI_pnt_flag_Counter = counter_MTE.check_PSI_pnt(sig, parameters_MTE.get_exist_harms_flag(), log_time_file)
                if set_PSI_pnt_flag_Counter == True:      # проверка установки точки ПСИ по генератору пройдена  
                    #4 Read data from MTE Counter


                    # опыт с непрерывным измерением за 5, 10, 15 сек. на счетчике МТЕ
                    #1 установить нужное время измерения на счетчике
                    #2 открыть канал svg
                    #3 найти начало 5-ти секундного интервала
                    #4 сон на 5 секунд
                    #5 считать и сохранить данные со счетчика мте
                    #6 считать данные с Бинома

                    test_read_by_one_meas = False
                    #test_read_by_one_meas = True

                    if test_read_by_one_meas == True:

                        meas_time_CNT = 5 # [sec.]
                        #meas_time_CNT = 10 # [sec.]
                        #meas_time_CNT = 20 # [sec.]

                        #1
                        counter_MTE.set_meas_time(meas_time_CNT)

                        #2
                        #print(str(dt.datetime.now())+"  before open svg channel")
                        make_psi.binom_data.open_svg_channel()
                        print(str(dt.datetime.now())+"  after  open svg channel")

                        #3
                        py_second = dt.datetime.now().second
                        t_time = dt.datetime.now()
                        while py_second % 5 != 0:
                            t_time = dt.datetime.now()
                            py_second = t_time.second

                        before_st_mte_meas = dt.datetime.now()
                        print(str(before_st_mte_meas)+"       choose 5 sec start")

                        #4
                        time.sleep(meas_time_CNT + 0.4)

                        cur_mte_time = dt.datetime.now()
                        delta_mte_time = cur_mte_time - t_time
                        print(str(cur_mte_time.time())+         "         cur_mte_time")
                        print(str(delta_mte_time)+       "         delta_time")

                        #5
                        list_ampl_full = []
                        list_angle_full = []
                        freq_Cnt = 0.0
                        freq_Cnt, list_ampl_full, list_angle_full  = counter_MTE.get_meas_from_counter()
                        '''
                        print("Counter MTE measurements")
                        for a_elem in zip(list_ampl_full, list_angle_full):
                            print(str(a_elem[0])+" ")
                            print(str(a_elem[1])+" ")
                        print(str(freq_Cnt))
                        '''
                        flag = 2
                        measurement.measurement_storage.set_mte_measured_signal(flag,cur_pnt,freq_Cnt,list_ampl_full,list_angle_full)
                        
                        #6
                        t_now = dt.datetime.now()
                        print(str(t_now)+     "         t_now before read Binom data")
                        make_psi.binom_data.read_data(cur_pnt)
                        cur_blob_time = make_psi.binom_data.get_blob_time()
                        t_now = dt.datetime.now()
                        print(str(t_now)+     "         t_now after  read Binom data")


                    else:
                        ####
                        counter_MTE.ser_port.timeout = 0.2
                        counter_MTE.start_auto_measure()    # Включить режим автовыдачи результатов   

                        meas_time_CNT = 5 # [sec.]
                        #meas_time_CNT = 10 # [sec.]
                        #meas_time_CNT = 20 # [sec.]

                        ###################     Установить время измерения генератора равным 5 секундам
                        meas_time_GEN = 5 # [sec.]
                        generator_MTE.ser_port.timeout = 0.2
                        generator_MTE.set_meas_time(meas_time_GEN)

                        #print(str(dt.datetime.now())+"  before open svg channel")
                        #make_psi.binom_data.open_svg_channel()
                        #print(str(dt.datetime.now())+"  after  open svg channel")

                        ################
                        # ищем начало 5-ти секундного интервала
                        
                        py_second = dt.datetime.now().second
                        t_time = dt.datetime.now()
                        while py_second % 5 != 0:
                            t_time = dt.datetime.now()
                            py_second = t_time.second

                        before_st_mte_meas = dt.datetime.now()
                        print(str(before_st_mte_meas)+"       choose 5 sec start")

                        #make_psi.binom_data.open_svg_channel()
                        #print(str(dt.datetime.now())+"  after  open svg channel")

                        ####
                        #counter_MTE.ser_port.timeout = 0.1
                        #counter_MTE.start_auto_measure()    # Включить режим автовыдачи результатов     
                        ##################
                        #make_psi.binom_data.open_svg_channel()
                        ##################
                        # считать данные со счетчика за время meas_time_CNT, с интервалом между новыми данными 1.0 сек.
                        counter_MTE.readByTimeT(meas_time_CNT,1.0)

                        cur_mte_time = dt.datetime.now()
                        delta_mte_time = cur_mte_time - t_time
                        print(str(cur_mte_time.time())+         "         cur_mte_time")
                        print(str(delta_mte_time)+       "         delta_time")

                        # выключить режим автовыдачи результатов после окончания интеравала записи Т
                        counter_MTE.ser_port.timeout = 0.2
                        counter_MTE.stop_auto_measure()
                        # считать результаты измерений с Бинома

                        t_now = dt.datetime.now()
                        print(str(t_now)+     "         t_now before read Binom data")

                        make_psi.binom_data.read_data(cur_pnt)
                        cur_blob_time = make_psi.binom_data.get_blob_time()

                        t_now = dt.datetime.now()
                        print(str(t_now)+     "         t_now after  read Binom data")

                        ###################
                        # получить усредненные данные 'короткой посылки' от счетчика МТЕ
                        list_ampl_full = []
                        list_angle_full = []
                        freq_Cnt = 0.0
                        freq_Cnt, list_ampl_full, list_angle_full  = counter_MTE.get_mean_values()
                        '''
                        print("Counter MTE measurements")
                        for a_elem in zip(list_ampl_full, list_angle_full):
                            print(str(a_elem[0])+" ")
                            print(str(a_elem[1])+" ")
                        print(str(freq_Cnt))
                        '''
                        # по непонятным причинам, передача измерений через zip не работает, поэтому передаю по списочно
                        flag = 2
                        measurement.measurement_storage.set_mte_measured_signal(flag,cur_pnt,freq_Cnt,list_ampl_full,list_angle_full)
                        
                    # считать измерения с генератора МТЕ
                    list_Gen_ampl_full = []
                    list_Gen_angle_full = []
                    freq_Gen = 0.0
                    freq_Gen, list_Gen_ampl_full, list_Gen_angle_full = generator_MTE.get_meas_from_generator()
                    flag = 1
                    '''
                    print("Generator MTE measurements")
                    for a_elem in zip(list_Gen_ampl_full, list_Gen_angle_full):
                        print(str(a_elem[0])+" ")
                        print(str(a_elem[1])+" ")
                    print(str(freq_Gen))
                    #'''
                    measurement.measurement_storage.set_mte_measured_signal(flag,cur_pnt,freq_Gen,list_Gen_ampl_full,list_Gen_angle_full)
                    
                    
                    #cur_mte_time       str(datetime.now().time()) == '14:57:06.416287'
                    #cur_blob_time

                    list_mte_delta_time.append(delta_mte_time)          #интервал считывания данных со счетчика МТЕ
                    list_mte_end_time.append(cur_mte_time.time())       #время окончания считывания данных со счетчика МТЕ
                    list_blob_time.append(cur_blob_time.time())


            cur_pnt += 1

        #формирование отчета о ПСИ

        make_psi.binom_data.close_svg_channel()

        list_of_times = [list_mte_delta_time, list_mte_end_time, list_blob_time]

        for idx in range(len(list_mte_delta_time)):
            print("mte_delta  "+str(list_of_times[0][idx]) +\
                "mte_end    "+str(list_of_times[1][idx]) + \
                "blob_time  "+str(list_of_times[2][idx]) )

        report.generate_report(st_pnt, end_pnt, list_of_times)
    #'''
    except Exception as ex:
        print("Exception occur:", ex)
    finally:
        counter_MTE.ser_port.close()
        generator_MTE.ser_port.close()
        make_psi.deinit()
    #'''

    print("Ask finished")

#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
#-----Отладочный режим работы: консольное меню управления устройствами МТЕ
#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
def HandleMenu(counter_MTE, generator_MTE,parameters_MTE,log_time_file):
    """
    Main menu: control 'Generator MTE':PPS 400.3 and 'Counter MTE':PRS 440.3
    """
    while(True):
        #try:
        top_menu_item = int(input())
        #top_menu_item = 6
        if top_menu_item == 6:
            print("\r\n Enter PSI point (1 - 156) number: ")
            cur_pnt = int(input())
            #cur_pnt = 132
            if cur_pnt > 0 and cur_pnt < 157:

                sig = measurement.measurement_storage.get_etalon_signal(cur_pnt)
                parameters_MTE.init_data(sig.get_main_freq_vector(),sig.get_frequency())
                parameters_MTE.generate_harm_cmd(sig)
                set_PSI_pnt_flag_Generator = generator_MTE.set_PSI_point(sig,parameters_MTE,log_time_file)

                if set_PSI_pnt_flag_Generator == True:      # проверка установки точки ПСИ по генератору пройдена  
                    counter_MTE.ser_port.timeout = 1.25
                    counter_MTE.set_ranges_for_CNT(parameters_MTE.get_ranges_CNT())    # Установка диапазонов для Счетчика
                    counter_MTE.ser_port.timeout = 0.5
                    ### Проверка по счетчику
                    
                    #set_PSI_pnt_flag_Counter = counter_MTE.check_PSI_point_harms(sig)

                    set_PSI_pnt_flag_Counter = counter_MTE.check_PSI_pnt(sig,\
                                        parameters_MTE.get_exist_harms_flag(), log_time_file)
                    print("set_PSI_pnt_flag_Counter" + str(set_PSI_pnt_flag_Counter))
                    '''

                    if set_PSI_pnt_flag_Generator == True:      # проверка установки точки ПСИ по генератору пройдена 
                        counter_MTE.start_auto_measure()
                        
                        readTime = 3
                        MTE_measured_Time = 0.25
                        counter_MTE.readByTimeT(readTime,MTE_measured_Time)
                        
                        #9 - выключить режим автовыдачи результатов после окончания интеравала записи Т
                        counter_MTE.stop_auto_measure()
                    '''

        elif top_menu_item == 10:
            print("Pressed: 10 - shutdown program and RESET devices")  #10 exit with Reset devices
            write_str = "R\r"
            counter_MTE.send_to_MTE(write_str)
            generator_MTE.send_to_MTE(write_str)
            return
        elif top_menu_item == 1:
            print("\r\nChoose 'MTE counter' configure params:")     #1 set/get params from/to 'Counter MTE'
            counter_MTE.SetMenuHandler()
        elif top_menu_item == 2:                              
            print("\r\nChoose 'MTE counter' measured menu:")
            counter_MTE.GetMenuHandler()                            
        elif top_menu_item == 3:
            print("\r\n Input Direct command to 'MTE counter':")
            directCommandToMTE = str(input())
            print("Command to send: ", directCommandToMTE)
            counter_MTE.send_to_MTE(directCommandToMTE + "\r")
        elif top_menu_item == 4:
            print("Reset Counter MTE")
            counter_MTE.send_to_MTE("R\r")
            counter_MTE.send_to_MTE("MODE1;DB1\r")
        elif top_menu_item == 5:
            print("\r\nChoose 'MTE generator' measured menu:")                        
            generator_MTE.GetMenuHandler()
        elif top_menu_item == 9:
            print("Pressed: 9 - shutdown programm")  
            write_str = "SU0\r"     # закончить автоматическую передачу данных
            counter_MTE.send_to_MTE(write_str)  #9 exit from this programm
            return
        elif top_menu_item == 7:
            print("\r\n Input Direct command to 'MTE generator':")
            directCommandToMTE = str(input())
            print("Command to send: ", directCommandToMTE)
            write_directCommandToMTE = directCommandToMTE + "\r"

            generator_MTE.send_to_MTE(write_directCommandToMTE)

        elif top_menu_item == 8:
            print("Reset Generator MTE")
            write_str = "R\r"
            generator_MTE.send_to_MTE(write_str)
            
        TopMenuItems() 
    
    counter_MTE.ser_port.close()
    generator_MTE.ser_port.close()

#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
#-----Функция проверки на корректность введенных номеров начально и конечной точек ПСИ
#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
def check_pnts(st_pnt, end_pnt):
    return (0 < st_pnt <= 160) and (0 < end_pnt <= 160) and (st_pnt <= end_pnt)

#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
#-----Консольное меню для отладочного режима работы функции main
#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
def TopMenuItems():
    print("\r\nTop menu:")
    print("1 - 'MTE counter':    Configure params")
    print("2 - 'MTE counter':    Measured menu")
    print("3 - 'MTE counter':    Send Direct command")
    print("4 - 'MTE counter':    Reset Counter MTE")
    print("5 - 'MTE generator':  Measured menu")
    print("6 - 'MTE generator':  Choose PSI point (1 - 156)")
    print("7 - 'MTE generator':  Send Direct command")
    print("8 - 'MTE generator':  Reset Generator MTE")
    print("9 - shutdown program")
    print("10 - shutdown program and RESET devices")


if __name__ == "__main__":
    main()