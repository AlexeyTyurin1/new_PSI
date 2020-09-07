""" 
MakeCmdFromCSV this module reads PSI scenariy.csv file and convert it to MTE comands
"""

import serial

import MTE_Counter
import MTE_Generator

#import vector_signal
import collections
import csv
import names_parameters
import measurement

#-------------------------------
import make_psi

import svgrequest 
import time

import datetime as dt


import MTE_parameters



def init_main_MTE():
    ##################################
    # Создание большого списка сигналов. Один экземпляр класса сигнал для одной точки ПСИ
    set_pnts_for_PSI = create_dict_test_points("PSI_Binom3_5_57.csv")
    ##################################

    ##################################
    #1.1 - inits serial ports
    #'''
    ser_Generator   = serial.Serial("COM2", 19200, timeout=0.5, parity=serial.PARITY_NONE, rtscts=0)
    ser_Counter     = serial.Serial("COM3", 19200, timeout=0.5, parity=serial.PARITY_NONE, rtscts=0)
    #'''
    '''
    ser_Counter   = serial.Serial("COM5", 19200, timeout=0.5, parity=serial.PARITY_NONE, rtscts=0)
    ser_Generator = serial.Serial("COM3", 19200, timeout=0.5, parity=serial.PARITY_NONE, rtscts=0)
    '''
    #1.2 - Create objects MTE device
    #1.2.1 - MTE Counter
    #write_str = "MODE1;DB1;SU0;SP1,1;SP2,1;SP22,1;SP9,1;SP13,1;T0;MAN;YI0;SU0\r"   # mode of send/get command by COM4 'Counter' port # режим токовых входов 12 А (по умолчанию стоит 120 А)
    
    #'''
    write_str = "MODE1;DB1;SU0;SP1,1;SP2,1;SP22,1;SP9,1;SP13,1;T0;MAN;YI0\r"   # mode of send/get command by COM4 'Counter' port # режим токовых входов 12 А (по умолчанию стоит 120 А)
    #'''
    #write_str = "MODE1;DB1;SU0;SP1,1;SP2,1;SP22,1;SP9,1;SP13,1;T1;MAN;YI0\r"


    counter_MTE = MTE_Counter.C_MTE_Counter(ser_Counter, 0.5, write_str, 0, 0)
    #1.2.2 - MTE Generator
    write_str = "MODE1;T1\r"   # mode of send/get command by COM1 'Generator' port
    generator_MTE = MTE_Generator.C_MTE_Generator(ser_Generator, 0.5, write_str, 0, 0)
    ##################################
    #1.2.3 - MTE Parameters - класс для генерации команд установки сигнала на генератор МТЕ и диапазонов измерения на генератор и счетчик МТЕ
    parameters_MTE = MTE_parameters.C_MTE_parameters()
    ##################################

    ##################################
    ##################################
    '''
    set_time = datetime.datetime.now()
    counter_MTE.set_MTE_current_Time(set_time)
    print("set_time: "+str(set_time))

    get_time = datetime.datetime.now()#datetime.datetime(counter_MTE.get_MTE_current_Time())
    print("get_time: "+str(get_time))
    '''
    ##################################
    ##################################

    return set_pnts_for_PSI, ser_Counter, ser_Generator, counter_MTE, generator_MTE, parameters_MTE


def init_main_Binom():   
    ##################################
    make_psi.init()
    ##################################

def check_pnts(st_pnt, end_pnt):
    return 0 < st_pnt <= 160 and 0 < end_pnt <= 160

def main():

    log_time_file = open("Time_log.txt", "w")     # 'a'	открытие на дозапись, информация добавляется в конец файла.
    log_time_file.flush()
    #text_file.write("  mean_Freq,   "+str(freq_mean))
    wr_str = "start main,"+str(dt.datetime.now())+","+str(dt.datetime.now().hour)+ ","+str(dt.datetime.now().minute)+ ","+str(dt.datetime.now().second)+ ","+"\r\n"
    log_time_file.write(wr_str)

    
    debug_mode = True       # True == режим отладки - работает меню и обмен данными только с устройствами МТЕ
    #debug_mode = False       # False == режим ПСИ - автоматический перебор точек, измерения и по МТЕ и по Биному

    if debug_mode == True:
        TopMenuItems()
        set_pnts_for_PSI, ser_Counter, ser_Generator, counter_MTE, generator_MTE, parameters_MTE = init_main_MTE()
        HandleMenu(set_pnts_for_PSI, ser_Counter, ser_Generator, counter_MTE, generator_MTE, parameters_MTE,log_time_file)
    else:
        do_PSI(log_time_file)

    log_time_file.close()

 
def do_PSI(log_time_file):
    
    st_pnt = 100
    end_pnt = 115
    if not check_pnts(st_pnt, end_pnt):
        return

    cur_pnt = st_pnt
    #try:

    # Инициализация для управления МТЕ
    set_pnts_for_PSI, ser_Counter, ser_Generator, counter_MTE, generator_MTE, parameters_MTE = init_main_MTE()
    
    wr_str = "init_main_MTE,"+str(dt.datetime.now())+","+str(dt.datetime.now().hour)+ ","+str(dt.datetime.now().minute)+ ","+str(dt.datetime.now().second)+ ","+"\r\n"
    log_time_file.write(wr_str)
    #'''
    # Инициализация для получения данных с Бинома
    init_main_Binom()
    wr_str = "init_main_Binom,"+str(dt.datetime.now())+","+str(dt.datetime.now().hour)+ ","+str(dt.datetime.now().minute)+ ","+str(dt.datetime.now().second)+ ","+"\r\n"
    log_time_file.write(wr_str)
    #'''

    while cur_pnt <= end_pnt:

        #
        wr_str = "cur_pnt, "+str(cur_pnt)+"\r\n"
        log_time_file.write(wr_str)
        print(wr_str)
        #

        #1.3 - Set PSI point on Generator
        measurement.make_signal_from_csv_source(set_pnts_for_PSI, cur_pnt)    # 
        sig = measurement.measurement_storage.get_etalon_signal(cur_pnt)
        parameters_MTE.init_data(sig.get_main_freq_vector(),sig.get_frequency())

        parameters_MTE.generate_harm_cmd(sig)

        #
        wr_str = "before set_PSI_point,"+str(dt.datetime.now())+","+str(dt.datetime.now().hour)+ ","+str(dt.datetime.now().minute)+ ","+str(dt.datetime.now().second)+ ","+"\r\n"
        log_time_file.write(wr_str)
        print(wr_str)
        #

        set_PSI_pnt_flag_Generator = generator_MTE.set_PSI_point(sig,parameters_MTE, log_time_file)

        if set_PSI_pnt_flag_Generator == True:      # проверка установки точки ПСИ по генератору пройдена  
            counter_MTE.ser_port.timeout = 1
            
            counter_MTE.set_ranges_for_CNT(parameters_MTE.get_ranges_CNT())     # Установка диапазонов для Счетчика

            # 1.3.2 - Check by Counter/ - soon will be added (11:41 31.08.2020)
            # added 16:42 02.09.2020
            #set_PSI_pnt_flag_Counter = counter_MTE.check_PSI_pnt(sig, log_time_file)

            set_PSI_pnt_flag_Counter = counter_MTE.check_PSI_pnt(sig,\
                                    parameters_MTE.get_exist_harms_flag(), log_time_file)


            if set_PSI_pnt_flag_Counter == True:      # проверка установки точки ПСИ по генератору пройдена  

                #4 Read data from MTE Counter

                #
                wr_str = "start_auto_measure main,"+str(dt.datetime.now())+","+str(dt.datetime.now().hour)+ ","+str(dt.datetime.now().minute)+ ","+str(dt.datetime.now().second)+ ","+"\r\n"
                log_time_file.write(wr_str)
                print(wr_str)
                #

                counter_MTE.start_auto_measure()    # Включить режим автовыдачи результатов               
                readTime = 6
                MTE_measured_Time = 1
                counter_MTE.readByTimeT(readTime,MTE_measured_Time)
                counter_MTE.stop_auto_measure()#9 - выключить режим автовыдачи результатов после окончания интеравала записи Т

                #
                wr_str = "end_auto_measure main,"+str(dt.datetime.now())+","+str(dt.datetime.now().hour)+ ","+str(dt.datetime.now().minute)+ ","+str(dt.datetime.now().second)+ ","+"\r\n"
                log_time_file.write(wr_str)
                print(wr_str)
                #

                # получить усредненные данные 'короткой посылки' от счетчика МТЕ
                short_MTE_data_block = counter_MTE.get_mean_values()
                ####for elem in short_MTE_data_block:
                ####    print("elem "+str(elem))
                measurement.measurement_storage.set_mte_measured_signal(cur_pnt,short_MTE_data_block)
    

        #
        wr_str = "before make_psi.binom_data.read_data,"+str(dt.datetime.now())+","+str(dt.datetime.now().hour)+ ","+str(dt.datetime.now().minute)+ ","+str(dt.datetime.now().second)+ ","+"\r\n"
        #wr_str = "before make_psi.binom_data.read_data,"+str(datetime.datetime.now().time())+"\r\n"
        log_time_file.write(wr_str)
        print(wr_str)
        #
        #'''
        #for _ in range(2):
        for _ in range(1):
            make_psi.binom_data.read_data(cur_pnt)
            # time.sleep(5)
        #'''

        #
        wr_str = "after make_psi.binom_data.read_data,"+str(dt.datetime.now())+","+str(dt.datetime.now().hour)+ ","+str(dt.datetime.now().minute)+ ","+str(dt.datetime.now().second)+ ","+"\r\n"
        #wr_str = "after make_psi.binom_data.read_data,"+str(datetime.datetime.now().time())+"\r\n"
        log_time_file.write(wr_str)
        print(wr_str)
        #
        
        cur_pnt+=1

    print("Ask finished")
    # except Exception as ex:
    #    print("Exception occur:", ex)
    #finally:

    ser_Counter.close()
    ser_Generator.close()

    make_psi.deinit()

def HandleMenu(set_pnts_for_PSI, ser_Counter, ser_Generator, counter_MTE, generator_MTE,parameters_MTE,log_time_file):
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

                measurement.make_signal_from_csv_source(set_pnts_for_PSI, cur_pnt)    # 
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
                    #counter_MTE.get_all_spectrum()

                #10 передать в класс Signal усредненные значения измерений счетчика МТЕ
                #def get_mean_values(self):    
                #return self.list_I_mean, self.list_U_mean,self.list_phi_UI_mean, self.list_phi_UU_mean, self.freq_mean

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

        #except ValueError:
        #    print("\r\nSomething go wrong! main menu error exeption.")
    
    ser_Counter.close()
    ser_Generator.close()


def create_dict_test_points(csv_file_name):
    """
    Read csv line by line and create dict of points
    """
    res_dict = collections.OrderedDict()
    with(open(csv_file_name, 'r')) as csv_file:
        reader = csv.DictReader(csv_file, fieldnames = names_parameters.get_csv_parameters_names(), delimiter=";")
        for num_pnt, pnt_param in enumerate(reader):
            pnt_param = {k:v.replace(",", ".") if type(v) == str else v for k, v in pnt_param.items()}
            res_dict[num_pnt + 1] = pnt_param
    return res_dict


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