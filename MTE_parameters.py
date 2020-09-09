"""
MTE_parameters classes for generator parameters
"""


class C_MTE_parameters():
    def __init__(self):
        
        # Строки с командами для управления МТЕ
        self.base_param_cmd = ""
        self.harm_voltage_cmd = ""
        self.harm_current_cmd = ""

        self.exist_harms_in_signal = False

        # Диапазоны СЧЕТЧИКА
        self.range_U_CNT = []
        self.range_I_CNT = []

        # Диапазоны СЧЕТЧИКА (U)
        self.U_CNT_max_ranges_dict = {  1   : 0.4, 
                                        2   : 5.0,
                                        3   : 65.0,
                                        4   : 130.0,
                                        5   : 260.0,
                                        6   : 520.0  }
        # Диапазоны СЧЕТЧИКА (I)
        self.I_CNT_max_ranges_dict = {  1   : 0.004, 
                                        2   : 0.012,
                                        3   : 0.04,
                                        4   : 0.12,
                                        5   : 0.4,
                                        6   : 1.2,
                                        7   : 4.0,
                                        8   : 12.0    }
        # Диапазоны ГЕНЕРАТОРА 
        self.range_U_GEN = []
        self.range_I_GEN = []  

        self.U_GEN_max_ranges_dict = {  2   : 75,
                                        3   : 150     }
                                              
        self.U_GEN_TRUE_dict = {        2   : 3,
                                        3   : 2     } 
                                            
        self.I_GEN_max_ranges_dict = {  1   : 0.012,
                                        2   : 0.12,
                                        3   : 1.2,
                                        4   : 12.0    } 
                                          
        self.I_GEN_TRUE_dict = {        1   : 4,
                                        2   : 3,
                                        3   : 2,
                                        4   : 1    }                       

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Получить команду генерации основных параметров
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_base_param_cmd(self):
        return self.base_param_cmd

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Получить команду генерации гармоник напряжения
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_harm_voltage_cmd(self):
        return self.harm_voltage_cmd

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Получить команду генерации гармоник тока
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_harm_current_cmd(self):
        return self.harm_current_cmd

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Сгенерировать команду для установки сигнала основной частоты на счетчике МТЕ, 
    #-----а также определить диапазоны измерений генератора и счетчика МТЕ
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def init_data(self,vec_par,main_freq):
        '''
        generate_base_signal_commands for MTE generator: set FREQ, U, I, phase U, phase between U and I
        '''
        ########################################################################
        Ua = vec_par.get_ampl("Ua")
        Ub = vec_par.get_ampl("Ub")
        Uc = vec_par.get_ampl("Uc")

        Ia = vec_par.get_ampl("Ia")
        Ib = vec_par.get_ampl("Ib")
        Ic = vec_par.get_ampl("Ic")

        ph_U_a = vec_par.get_phase("Ua") * (-1)
        ph_U_b = vec_par.get_phase("Ub") * (-1)
        ph_U_c = vec_par.get_phase("Uc") * (-1)

        ph_I_a = (vec_par.get_phase("Ia") - vec_par.get_phase("Ua")) * (-1)
        ph_I_b = (vec_par.get_phase("Ib") - vec_par.get_phase("Ub")) * (-1)
        ph_I_c = (vec_par.get_phase("Ic") - vec_par.get_phase("Uc")) * (-1)
        ########################################################################
        # найти максимальный элемент U и I -> выбрать нужный верхний диапазон -> установить команду на счетчик МТЕ
        self.range_U_CNT = []
        self.range_I_CNT = []
        self.find_ranges_CNT(Ua,Ub,Uc,self.range_U_CNT,self.U_CNT_max_ranges_dict)
        self.find_ranges_CNT(Ia,Ib,Ic,self.range_I_CNT,self.I_CNT_max_ranges_dict)

        self.range_U_GEN = []
        self.range_I_GEN = []
        self.find_ranges_GEN(Ua,Ub,Uc,self.range_U_GEN,self.U_GEN_max_ranges_dict,self.U_GEN_TRUE_dict)
        self.find_ranges_GEN(Ia,Ib,Ic,self.range_I_GEN,self.I_GEN_max_ranges_dict,self.I_GEN_TRUE_dict)

        ########################################################################
        self.base_param_cmd = "FRQ,"+str(main_freq)+";"

        self.base_param_cmd +=  "U1,"+ str(Ua)+";"+ "U2,"+ str(Ub)+";"+ "U3,"+ str(Uc)+";"+\
                "PH1,"+str(ph_U_a)+";"+"PH2,"+str(ph_U_b)+";"+"PH3,"+str(ph_U_c)+";"

        self.base_param_cmd +=  "I1,"+ str(Ia)+";"+ "I2,"+ str(Ib)+";"+ "I3,"+ str(Ic)+";"+\
                    "W1,"+str(ph_I_a)+";"+ "W2,"+str(ph_I_b)+";"+ "W3,"+str(ph_I_c) #+";"

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Сгенерировать команду для установки гармоник в сигнал
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def generate_harm_cmd(self,h_signal):
        vol_harm_zero = True
        cur_harm_zero = True
        t_U_ampl = 0.0
        t_I_ampl = 0.0
        keys_vect_dict = ["Ua", "Ub", "Uc", "Ia", "Ib", "Ic"]
        cmd_harm_prefix = ["OWU","OWI"]
        cmd_phase_prefix = ["1","2","3"]

        self.harm_voltage_cmd = ""
        self.harm_current_cmd = ""
        main_harm_ampl = []
        main_harm = h_signal.get_main_freq_vector()

        for idx_phase in keys_vect_dict:                        # амплитуда гармоники сигнала основной частоты,
            main_harm_ampl.append(main_harm.get_ampl(idx_phase))# необходима для установки гармоник на генераторе МТЕ в "% от основной частоты"

        for idx_harm_num in range(2, 32):   # цикл по всем гармоникам
            cur_harm_signal = h_signal.get_vector_harm(idx_harm_num)    # текущий объект Vector_values с параметрами idx_harm_num гармоники

            for idx_phase in range(3):              # цикл по фазам

                # проверка на неравенство нулю амплитуды гармоники основной частоты
                if main_harm_ampl[idx_phase] != 0.0: 
                    t_U_ampl = round(100.0*cur_harm_signal.get(keys_vect_dict[idx_phase])[0] / main_harm_ampl[idx_phase],3)
                else: t_U_ampl = 0.0

                if main_harm_ampl[idx_phase+3] != 0.0: 
                    t_I_ampl = round(100.0*cur_harm_signal.get(keys_vect_dict[idx_phase+3])[0] / main_harm_ampl[idx_phase+3],3)
                else: t_I_ampl = 0.0

                if t_U_ampl != 0.0: vol_harm_zero = False
                if t_I_ampl != 0.0: cur_harm_zero = False

                self.harm_voltage_cmd += cmd_harm_prefix[0] + cmd_phase_prefix[idx_phase] + "," \
                                                            + str(idx_harm_num) + "," \
                                                            + str(t_U_ampl) + "," \
                                                            + str(cur_harm_signal.get(keys_vect_dict[idx_phase])[1]) + ";"

                self.harm_current_cmd += cmd_harm_prefix[1] + cmd_phase_prefix[idx_phase] + "," \
                                                            + str(idx_harm_num) + "," \
                                                            + str(t_I_ampl) + "," \
                                                            + str(cur_harm_signal.get(keys_vect_dict[idx_phase+3])[1]) + ";"

        self.exist_harms_in_signal = True
        if vol_harm_zero == True: 
            self.harm_voltage_cmd = ""
        if cur_harm_zero == True: 
            self.harm_current_cmd = ""

        if (cur_harm_zero == True) and (vol_harm_zero == True):
            self.exist_harms_in_signal = False

        #return cmd_voltage, cmd_current

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Получить флаг наличия гармоник в этой точке ПСИ
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_exist_harms_flag(self):
        return self.exist_harms_in_signal
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Получить команду для установки диапазона измерений Счетчика МТЕ
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_ranges_CNT(self):

        if (len(self.range_U_CNT) != 3) or (len(self.range_I_CNT) != 3):
            print("Error in 'get_ranges_CNT'. Length of ranges_CNT[] not equal 3")
            self.range_I_CNT = [4,4,4]   # Если ошибка, то выставляем максимальные диапазоны измерений
            self.range_U_CNT = [4,4,4]   # Если ошибка, то выставляем максимальные диапазоны измерений

        ranges_CNT = ""
        ranges_CNT = "U"+str(self.range_U_CNT[0])+","+str(self.range_U_CNT[1])+","+str(self.range_U_CNT[2])+";" 
        ranges_CNT = ranges_CNT + "I"+str(self.range_I_CNT[0])+","+str(self.range_I_CNT[1])+","+str(self.range_I_CNT[2])+"\r"  
            
        return ranges_CNT

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Получить команду для установки диапазона измерений Генератора МТЕ
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def get_ranges_GEN(self):
        
        if (len(self.range_U_GEN) != 3) or (len(self.range_I_GEN) != 3):
            print("Error in 'get_ranges_GEN'. Length of ranges_GEN[] not equal 3")
            self.range_I_GEN = [8,8,8]   # Если ошибка, то выставляем максимальные диапазоны измерений
            self.range_U_GEN = [6,6,6]   # Если ошибка, то выставляем максимальные диапазоны измерений

        ranges_GEN = ""
        ranges_GEN = "BU1,"+str(self.range_U_GEN[0])+";BU2,"+str(self.range_U_GEN[1])+";BU3,"+str(self.range_U_GEN[2])+";" 
        ranges_GEN = ranges_GEN + "BI1,"+str(self.range_I_GEN[0])+";BI2,"+str(self.range_I_GEN[1])+";BI3,"+str(self.range_I_GEN[2])+"\r"
        return ranges_GEN 

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Найти и сохранить диапазоны измерений Счетчика МТЕ
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def find_ranges_CNT(self,val_a,val_b,val_c,res_list,max_ranges_dict):
        list_vals = [val_a,val_b,val_c]
        #res_list = []
        for key_list_vals in list_vals:
            for key_dict in max_ranges_dict:
                if key_list_vals < max_ranges_dict[key_dict] * 0.95:
                    res_list.append(key_dict)
                    #print("val " + str(key_list_vals)+" key_dict find max range: "+ str(GEN_TRUE_dict[key_dict])+"  max_ranges_dict[key_dict]  " + str(max_ranges_dict[key_dict]))
                    break

    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Найти и сохранить диапазоны измерений Генератора МТЕ
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    def find_ranges_GEN(self,val_a,val_b,val_c,res_list,max_ranges_dict,GEN_TRUE_dict):
        list_vals = [val_a,val_b,val_c]
        #res_list = []
        for key_list_vals in list_vals:
            for key_dict in max_ranges_dict:
                if key_list_vals < max_ranges_dict[key_dict]:
                    res_list.append(GEN_TRUE_dict[key_dict])
                    #print("val " + str(key_list_vals)+" key_dict find max range: "+ str(GEN_TRUE_dict[key_dict])+"  max_ranges_dict[key_dict]  " + str(max_ranges_dict[key_dict]))
                    break
 

if __name__ == "__main__":
    pass



        