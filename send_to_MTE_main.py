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

#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
#-----Функция main. Режимы работы: основной-непрерывный прогон точек ПСИ, отладочный - меню управления МТЕ
#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
def main():
    #debug_mode = True       # True == режим отладки - работает меню и обмен данными только с устройствами МТЕ
    debug_mode = False       # False == режим ПСИ - автоматический перебор точек, измерения и по МТЕ и по Биному

    log_time_file = open("Time_log.txt", "w")     # 'a'	открытие на дозапись, информация добавляется в конец файла.
    log_time_file.flush()

    if debug_mode == True:
        TopMenuItems()
        ser_Counter, ser_Generator, counter_MTE, generator_MTE, parameters_MTE = init_main_MTE()
        HandleMenu(ser_Counter, ser_Generator, counter_MTE, generator_MTE, parameters_MTE,log_time_file)
    else:
        do_PSI(log_time_file)

    log_time_file.close()

#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
#-----Функция инициализации Бинома
#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
def init_main_Binom():  
    make_psi.deinit() 
    make_psi.init()

#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
#-----Функция инициализации МТЕ
#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
def init_main_MTE():
    # Создание большого списка сигналов. Один экземпляр класса сигнал для одной точки ПСИ
    #set_pnts_for_PSI = create_dict_test_points("PSI_Binom3_5_57.csv")
    measurement.create_dict_test_points("PSI_Binom3_5_57.csv")
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

    return ser_Counter, ser_Generator, counter_MTE, generator_MTE, parameters_MTE

#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
#-----Функция проверки на корректность введенных номеров начально и конечной точек ПСИ
#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
def do_PSI(log_time_file):
    
    st_pnt = 25
    end_pnt = 55
    if not check_pnts(st_pnt, end_pnt):
        return

    cur_pnt = st_pnt
    # Инициализация для получения данных с Бинома
    init_main_Binom()
    # Инициализация для управления МТЕ
    #set_pnts_for_PSI, ser_Counter, ser_Generator, counter_MTE, generator_MTE, parameters_MTE = init_main_MTE()
    ser_Counter, ser_Generator, counter_MTE, generator_MTE, parameters_MTE = init_main_MTE()
    
    #try:
    while cur_pnt <= end_pnt:
        print("\r\n"+"current PSI point is "+str(cur_pnt)+"\r\n")
        #1.3 - Set PSI point on Generator
        #measurement.make_signal_from_csv_source(set_pnts_for_PSI, cur_pnt)    # 
        sig = measurement.measurement_storage.get_etalon_signal(cur_pnt)
        parameters_MTE.init_data(sig.get_main_freq_vector(),sig.get_frequency())
        parameters_MTE.generate_harm_cmd(sig)
        set_PSI_pnt_flag_Generator = generator_MTE.set_PSI_point(sig,parameters_MTE, log_time_file)

        if set_PSI_pnt_flag_Generator == True:      # проверка установки точки ПСИ по генератору пройдена  
            counter_MTE.ser_port.timeout = 1
            counter_MTE.set_ranges_for_CNT(parameters_MTE.get_ranges_CNT())     # Установка диапазонов для Счетчика
            # 1.3.2 - Check by Counter
            set_PSI_pnt_flag_Counter = counter_MTE.check_PSI_pnt(sig,\
                                    parameters_MTE.get_exist_harms_flag(), log_time_file)

            if set_PSI_pnt_flag_Counter == True:      # проверка установки точки ПСИ по генератору пройдена  
                #4 Read data from MTE Counter

                ###################
                # ищем начало 5-ти секундного интервала
                py_second = dt.datetime.now().second
                while py_second % 5 != 0:
                    py_second = dt.datetime.now().second
                    #py_year,py_month,py_day, py_hour,py_minute,py_second = counter_MTE.get_MTE_current_Time()
                    #print(str(dt.datetime.now()))


                counter_MTE.start_auto_measure()    # Включить режим автовыдачи результатов     

                ##################
                make_psi.binom_data.open_svg_channel()
                ##################
        
                readTime = 5
                MTE_measured_Time = 1
                counter_MTE.readByTimeT(readTime,MTE_measured_Time)

                
                # считать результаты измерений с Бинома
                make_psi.binom_data.read_data(cur_pnt)

                # выключить режим автовыдачи результатов после окончания интеравала записи Т
                counter_MTE.stop_auto_measure()

                # получить усредненные данные 'короткой посылки' от счетчика МТЕ
                list_ampl_full = []
                list_angle_full = []
                freq, list_ampl_full, list_angle_full  = counter_MTE.get_mean_values()
                # по непонятным причинам, передача измерений через zip не работает, поэтому передаю по списочно
                measurement.measurement_storage.set_mte_measured_signal(cur_pnt,freq,list_ampl_full,list_angle_full)

                cur_pnt+=1

    #формирование отчета о ПСИ
    report.generate_report(st_pnt, end_pnt)
    '''
    except Exception as ex:
        print("Exception occur:", ex)
    finally:
        ser_Counter.close()
        ser_Generator.close()
        make_psi.deinit()
    '''

    

    

    print("Ask finished")
    

#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
#-----Отладочный режим работы: консольное меню управления устройствами МТЕ
#-----------------------------------------------------------------------------------#
#-----------------------------------------------------------------------------------#
def HandleMenu(ser_Counter, ser_Generator, counter_MTE, generator_MTE,parameters_MTE,log_time_file):
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
    
    ser_Counter.close()
    ser_Generator.close()

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