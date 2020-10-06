import xlwings as xs
import time
import measurement
import names_parameters as nm_par

from math import (sqrt)

#template_file_name = ".\\Template.xlsx"                # первая версия шаблона
#template_file_name = ".\\Template_with_gen_meas.xlsx"  # шаблон с добавлением измерений генератора МТЕ
template_file_name = ".\\Template_with_meter.xlsx"      # шаблон расчетом метрол запаса


U_nom_range = "B1"
I_nom_range = "D1"

U_nom_val = 57.735
I_nom_val = 5

result_range    = "A1:AM21"
cur_col_output  = "A2"

def copy_result_fr_template(wb_src, wb_dst, cur_pnt):
    #src_sh = wb_src.sheets['Template']
    src_sh = wb_src.sheets['Template_clear']
    # wb_dst.sheets[sheet_name].activate()
    sheet_name = get_sheet_name(cur_pnt)
    dst_sh = wb_dst.sheets[sheet_name] 

    # make name from cur_pnt
    #dst_sh.sheets[current_sheet].name = get_sheet_name(cur_pnt)
    
    src_sh.range(result_range).api.copy
    dst_sh.range("A1").api.select
    dst_sh.api.paste

def get_sheet_name(cur_pnt):
    return "pnt #{}".format(cur_pnt)

def next_output_cell(wb_result):
    global cur_col_output
    cur_range = wb_result.sheets[0].range(cur_col_output).offset(12, 0)
    cur_col_output = cur_range.address.replace("$", "")

def __write_meas_result(wb_result, cur_pnt, meas_result, offset):
    '''
    template for write results to excel
    wb_result - excel book with result
    cur_pnt - current PSI point 
    meas_result - instance MeasuredSignal
    offset - typle (row, column) offset
    '''
    sheet_name = get_sheet_name(cur_pnt)
    cur_range = wb_result.sheets[sheet_name].range(cur_col_output).offset(offset[0], offset[1])
    cur_range.value = cur_pnt
    cur_range = cur_range.offset(0, 1)
    cur_range.value = list(meas_result.results.values())

def __write_meas_errors(wb_result, cur_pnt, meas_result, offset):
    '''
    template for write tolerance results
    wb_result - excel book with result
    cur_pnt - current psi point
    meas_result - MeasuredSignal from Binom or MTE
    offset - !!!! offset result must be same as in call __write_meas_result
    '''
    sheet_name = get_sheet_name(cur_pnt)
    cur_range = wb_result.sheets[sheet_name].range(cur_col_output).offset(offset[0], offset[1])
    cur_range = cur_range.offset(1, 1)

    # for num, meas_par_name in enumerate(nm_par.link_measured_params_errors.keys()):
    """
    for nm_err in ("absolute", "relative", "reduced"):
        err = [meas_result.errors[name] if type_tolerance == nm_err \
            else "-----"  for name, type_tolerance in nm_par.link_measured_params_errors.items()]
        cur_range.value = err
        cur_range = cur_range.offset(1, 0)
    """
    
def write_etalon_result(wb_result, cur_pnt):
    etalon = measurement.measurement_storage.get_etalon_signal(cur_pnt)
    __write_meas_result(wb_result, cur_pnt, etalon.meas_result, (0, 1)) 


def write_mte_CNT_result(wb_result, cur_pnt):
    mte = measurement.measurement_storage.get_mte_CNT_signal(cur_pnt)
    __write_meas_result(wb_result, cur_pnt, mte.meas_result, (2, 1))
    __write_meas_errors(wb_result, cur_pnt, mte.meas_result, (2, 1))

def write_mte_GEN_result(wb_result, cur_pnt):
    mte = measurement.measurement_storage.get_mte_GEN_signal(cur_pnt)
    __write_meas_result(wb_result, cur_pnt, mte.meas_result, (7, 1))
    __write_meas_errors(wb_result, cur_pnt, mte.meas_result, (7, 1))

def write_binom_result(wb_result, cur_pnt):
    binom_result = measurement.measurement_storage.get_binom_signal(cur_pnt)
    __write_meas_result(wb_result, cur_pnt, binom_result, (12, 1))
    __write_meas_errors(wb_result, cur_pnt, binom_result, (12, 1))
      
#------------------------------------------------------   
#----Удалить листы, созданные по умолчанию, из новой книги.
#------------------------------------------------------
def remove_default_sheets(wb_result):
    wb_result.sheets["Лист1"].delete()
    wb_result.sheets["Лист2"].delete()
    wb_result.sheets["Лист3"].delete()

#------------------------------------------------------
#----Запись содержимого страницы за 1 раз   
#------------------------------------------------------

#------------------------------------------------------
#------------------------------------------------------   
#------------------------------------------------------
def generate_value_for_write(etalon,mte_CNT,mte_GEN,binom_result,cur_pnt,st_pnt, list_of_times, P_flag, Q_flag):

################
#   ±0.01

#   abs       -     abs
#   rel, red  -     %

#   freq            -   abs - 0.01
#   Ua,b,c          -   red - 0.1
#   Ia,b,c          -   red - 0.1
#   AngUab,bc,ca    -   abs - 0.2
#   AngIab,bc,ca    -   abs - 0.5

#   cos,a,b,c       -   abs - 0.01
#   U1,2,0          -   red - 0.1
#   I1,2,0          -   red - 0.1
#   P, Pa,b,c       -   rel - 0.2 + 0.025*abs((Iном / Ia,b,c) - 1) / abs(cos,a,b,c) + 0.04*abs((Uном / Ua,b,c) - 1)
#   sin,a,b,c = sqrt( 1 - cos,a,b,c * cos,a,b,c )
#   Q, Qa,b,c       -   rel - 0.5 + 0.025*abs((Iном / Ia,b,c) - 1) / abs(sin,a,b,c) + 0.04*abs((Uном / Ua,b,c) - 1)
#   S, Sa,b,c       -   rel - 0.5 + 0.04*abs((Iном / Ia,b,c) - 1) + 0.04*abs((Uном / Ua,b,c) - 1)
##############

    etalon_res       = list(etalon.meas_result.results.values())

    for idx in range(len(etalon_res)):            # если значение параметра из файла сценария очень мало (<10^(-5)), то меняем его на нуль
        if abs(etalon_res[idx]) < 0.00001:        # 10^(-5)
            etalon_res[idx] = 0.0

    mte_CNT_res      = list(mte_CNT.meas_result.results.values())        # результаты измерения счетчика МТЕ (эталонные значения) 
    mte_GEN_res      = list(mte_GEN.meas_result.results.values())        # результаты измерения генератора МТЕ (для сравнения с чем-то)
    binom_result_res = list(binom_result.results.values())               # результаты измерения Бинома - все значения получены напрямую из BLOB-ячейки (без дорасчета)

    list_meas = [mte_CNT_res,mte_GEN_res,binom_result_res]      # список-списков - результаты измерений

    list_err_res =  [list(mte_GEN.meas_result.errors_abs.values()),     #   [0] - абсолютные ошибки измерения генератора МТЕ (относительно измерений счетчика МТЕ)
                    list(mte_GEN.meas_result.errors_rel.values()),      #   [1] - относительные ошибки измерения генератора МТЕ (относительно измерений счетчика МТЕ)
                    list(mte_GEN.meas_result.errors_red.values()),      #   [2] - приведенные ошибки измерения генератора МТЕ (относительно измерений счетчика МТЕ)

                    list(binom_result.errors_abs.values()),             #   [3] - абсолютные ошибки измерения Бинома (относительно измерений счетчика МТЕ)
                    list(binom_result.errors_rel.values()),             #   [4] - относительные ошибки измерения Бинома (относительно измерений счетчика МТЕ)
                    list(binom_result.errors_red.values()) ]            #   [5] - приведенные ошибки измерения Бинома (относительно измерений счетчика МТЕ)

    for idx in range(len(list_err_res[2])):
        if list_err_res[2][idx] == 0:           # если приведенная погрешность равна нулю, то пишем в ячейку excel файла 'ничего', вместо нуля
            list_err_res[2][idx] = ""
            list_err_res[5][idx] = ""

    ####    вставка отступов или номера точки ПСИ в первую ячейку 
    for L_idx in range(len(list_err_res)):       # создание отступа на один столбец вправо
        list_err_res[L_idx].insert(0,"")

    for L_idx in range(len(list_meas)):          # запись номера текущей точки ПСИ
        list_meas[L_idx].insert(0,cur_pnt)
    
    empty_list = []                              # пустая строка
    for _ in range(len(list_err_res[0])):
        empty_list.append("")

    etalon_res.insert(0,cur_pnt)

    ################################################
    ################################################
    #   переделать под новый шаблон

    # столбцы ячеек в которые пишутся абсолютные погрешности
    #max_abs_err_range = [6, 10,11,12, 16,17,18,19,20,21]
    # значения абсолютной погрешности
    #max_abs_err_range = [0.01, 0.2,0.2,0.2, 0.5,0.5,0.5, 0.01,0.01,0.01]

    tu_abs_err_meter = []                      #   строка со значениями макс. допустимой абсолютной погрешности
    t_idx = 0
    flag_val = 0
    for idx in range(len(list_meas[0])):
        t_idx = 5 + idx

        if t_idx == 6:
            tu_abs_err_meter.append(0.01)   # freq
            flag_val = 1

        if (10 <= t_idx) and (t_idx <= 12):
            tu_abs_err_meter.append(0.2)   # AngUxy
            flag_val = 1

        if (16 <= t_idx) and (t_idx <= 18):
            tu_abs_err_meter.append(0.5)   # AngIxy
            flag_val = 1
 
        if (19 <= t_idx) and (t_idx <= 21):
            tu_abs_err_meter.append(0.01)   # cos
            flag_val = 1

        if flag_val == 1:
            flag_val = 0
        else:
            tu_abs_err_meter.append("")

    #---------------
    tu_red_err_meter = []                   #   строка со значениями макс. допустимой приведенной погрешности
    t_idx = 0
    flag_val = 0
    for idx in range(len(list_meas[0])):
        t_idx = 5 + idx
        
        if (7 <= t_idx) and (t_idx <= 9):
            tu_red_err_meter.append(0.1)   # U
            flag_val = 1

        if (13 <= t_idx) and (t_idx <= 15):
            tu_red_err_meter.append(0.1)   # I
            flag_val = 1

        if (22 <= t_idx) and (t_idx <= 27):
            tu_red_err_meter.append(0.1)   # cos + U + I
            flag_val = 1
    
        if flag_val == 1:
            flag_val = 0
        else:
            tu_red_err_meter.append("")
            
    #---------------
    tu_rel_err_meter = []
    t_idx = 0
    for idx in range(len(list_meas[0]) - 12):   # заполняем пробелами первые пустые ячейки строки макс. допустимой относительной погрешности
        tu_rel_err_meter.append("")

    #   P, Pa,b,c       -   rel - 0.2 + 0.025*abs((Iном / Ia,b,c) - 1) / abs(cos,a,b,c) + 0.04*abs((Uном / Ua,b,c) - 1)
    #   sin,a,b,c = sqrt( 1 - cos,a,b,c * cos,a,b,c )
    #   Q, Qa,b,c       -   rel - 0.5 + 0.025*abs((Iном / Ia,b,c) - 1) / abs(sin,a,b,c) + 0.04*abs((Uном / Ua,b,c) - 1)
    #   S, Sa,b,c       -   rel - 0.5 + 0.04*abs((Iном / Ia,b,c) - 1) + 0.04*abs((Uном / Ua,b,c) - 1)

    #U_nom_val = 57.735
    #I_nom_val = 5

    full_P_rel_meter = 0.0
    full_Q_rel_meter = 0.0
    full_S_rel_meter = 0.0

    for idx in range(3):          # P abc
        t_idx = idx 
        #   rel - 0.2 + 0.025*abs((Iном / Ia,b,c) - 1) / abs(cos,a,b,c) + 0.04*abs((Uном / Ua,b,c) - 1)
    
        #   if (Ia,b,c != 0)             and (cos,a,b,c != 0)               and (Ua,b,c != 0)
        if (mte_CNT_res[8+t_idx] != 0.0) and (mte_CNT_res[14+t_idx] != 0.0) and (mte_CNT_res[2+t_idx] !=0):
            full_P_rel_meter = 0.2 + 0.025*abs((I_nom_val / mte_CNT_res[8+t_idx]) - 1) / abs(mte_CNT_res[14+t_idx]) + 0.04*abs((U_nom_val / mte_CNT_res[2+t_idx]) - 1)
            tu_rel_err_meter.append( full_P_rel_meter )
        else:
            tu_rel_err_meter.append(0)
    
    for idx in range(3):          # Q abc
        t_idx = idx  
        sin_t = sqrt(1-(mte_CNT_res[14+t_idx] ** 2))
        #   if (Ia,b,c != 0)             and (sin,a,b,c != 0)               and (Ua,b,c != 0)
        if (mte_CNT_res[8+t_idx] != 0.0) and (sin_t != 0.0) and (mte_CNT_res[2+t_idx] !=0):
            full_Q_rel_meter = 0.5 + 0.025*abs((I_nom_val / mte_CNT_res[8+t_idx]) - 1) / sin_t + 0.04*abs((U_nom_val / mte_CNT_res[2+t_idx]) - 1)
            tu_rel_err_meter.append( full_Q_rel_meter )
        else:
            tu_rel_err_meter.append(0)

    for idx in range(3):          # S abc
        t_idx = idx 
        #   if (Ia,b,c != 0)             and (cos,a,b,c != 0)               and (Ua,b,c != 0)
        if (mte_CNT_res[8+t_idx] != 0.0) and (mte_CNT_res[14+t_idx] != 0.0) and (mte_CNT_res[2+t_idx] !=0):
            full_S_rel_meter = 0.5 + 0.04*abs((I_nom_val / mte_CNT_res[8+t_idx]) - 1) + 0.04*abs((U_nom_val / mte_CNT_res[2+t_idx]) - 1)
            tu_rel_err_meter.append( full_S_rel_meter )
        else:
            tu_rel_err_meter.append(0)

    #---- full P,Q,S
    tu_rel_err_meter.append(full_P_rel_meter)
    tu_rel_err_meter.append(full_Q_rel_meter)
    tu_rel_err_meter.append(full_S_rel_meter)

    ################################################
    # метрологические запасы

    meter_range_gen = []
    meter_range_bin = []

    tu_err_list = [tu_abs_err_meter,tu_rel_err_meter,tu_red_err_meter]      # список строк со значениями технических условий
    len_tu_list = len(tu_abs_err_meter)                                     # число не пустых ячеек в строке метрол. запаса

    meter_Gen_list =    [list(mte_GEN.meas_result.errors_abs.values()),     #   [0]
                         list(mte_GEN.meas_result.errors_rel.values()),     #   [1]
                         list(mte_GEN.meas_result.errors_red.values())]     #   [2]

    meter_Binom_list =  [list(binom_result.errors_abs.values()),            #   [3]
                         list(binom_result.errors_rel.values()),            #   [4]
                         list(binom_result.errors_red.values()) ]           #   [5]

    flag_stop = 0

    for elem in meter_Binom_list:
        elem.insert(0,"")

    for elem in meter_Gen_list:
        elem.insert(0,"")

    '''
    проверка и зануление нужных ячеек с P и Q abc

    0 - занулить все фазы, abc
    1 - оставить только фазу, a
    2 - оставить только фазу, b
    3 - оставить только фазу, c

    4 - ничего не занулять

    P_flag, Q_flag

            if P_flag == 0:
    '''
    # диапазоны ячеек в которые пишутся метрол. запасы по мощностям
    P_range = [23,24,25,32]
    Q_range = [26,27,28,33]
    P_count = 0
    Q_count = 0

    err_val = 1000          # значение по умолчанию, если погрешность метрол. запас равен +бесконечности
    zer_val = ""
    #err_val = zer_val

    for m_num_idx in range(len_tu_list):        # цикл по столбцам
        if flag_stop == 1:
            flag_stop = 0

        for pogr_num in range(3):               # цикл по типам погрешностей
            if flag_stop == 1:
                break

            if tu_err_list[pogr_num][m_num_idx] != "":
                if (meter_Gen_list[pogr_num][m_num_idx] != 0) and (meter_Gen_list[pogr_num][m_num_idx] != ""):
                    meter_range_gen.append(tu_err_list[pogr_num][m_num_idx] / abs(meter_Gen_list[pogr_num][m_num_idx]))
                else:
                    meter_range_gen.append(err_val)



                if m_num_idx in P_range:
                    P_count += 1
                    if P_flag == 0:                             # 0 - занулить все фазы, abc
                        meter_range_bin.append(zer_val)
                        flag_stop = 1
                        continue
                    if (P_flag == 1) and ((P_count == 2) or (P_count == 3)):         # 1 - занулить фазу, a
                        meter_range_bin.append(zer_val)
                        flag_stop = 1
                        continue
                    if (P_flag == 2) and ((P_count == 1) or (P_count == 3)):         # 2 - занулить фазу, b
                        meter_range_bin.append(zer_val)
                        flag_stop = 1
                        continue
                    if (P_flag == 3) and ((P_count == 1) or (P_count == 2)):         # 3 - занулить фазу, c
                        meter_range_bin.append(zer_val)
                        flag_stop = 1
                        continue
                    
                if m_num_idx in Q_range:
                    Q_count += 1
                    if Q_flag == 0:                             # 0 - занулить все фазы, abc
                        meter_range_bin.append(zer_val)
                        flag_stop = 1
                        continue
                    if (Q_flag == 1) and ((Q_count == 2) or (Q_count == 3)):         # 1 - занулить фазу, a
                        meter_range_bin.append(zer_val)
                        flag_stop = 1
                        continue
                    if (Q_flag == 2) and ((Q_count == 1) or (Q_count == 3)):         # 2 - занулить фазу, b
                        meter_range_bin.append(zer_val)
                        flag_stop = 1
                        continue
                    if (Q_flag == 3) and ((Q_count == 1) or (Q_count == 2)):         # 3 - занулить фазу, c
                        meter_range_bin.append(zer_val)
                        flag_stop = 1
                        continue

                if (meter_Binom_list[pogr_num][m_num_idx] != 0) and (meter_Binom_list[pogr_num][m_num_idx] != ""):

                    # обработка случай, когда ток фазы равен нулю, а результат измерения Бинома по косинусу Фи равен 0 
                    # (устройства МТЕ в этом случае выдают косинус Фи равный 1)
                    # если текущий диапазон попадает на диапазон cos(Phi)
                    if (m_num_idx >= 14) and (m_num_idx <= 16):
                        #if ( |Iabc| <= 0.0001)                             and (cos(Phi)abc == 0):
                        if (abs(binom_result_res[m_num_idx - 6]) <= 0.0001) and (binom_result_res[m_num_idx] == 0):
                            meter_range_bin.append(err_val)
                            flag_stop = 1
                            continue

                    meter_range_bin.append(tu_err_list[pogr_num][m_num_idx] / abs(meter_Binom_list[pogr_num][m_num_idx]))
                else:
                    meter_range_bin.append(err_val)

                flag_stop = 1
                continue

    meter_range_gen.insert(0,"")
    meter_range_bin.insert(0,"")
    ################################################

    full_list = []                          # список окончательных результатов для записи в excel за 1 заход
    #full_list.append(title_split_str)

    #-------

    full_list.append(etalon_res)
    #print("etalon_res      " + str(len(etalon_res)))

    full_list.append(list_meas[0])
    #print("list_meas[0]    " + str(len(list_meas[0])))

    full_list.append(list_meas[1])
    #print("list_meas[1]    " + str(len(list_meas[1])))

    full_list.append(list_err_res[0])
    #print("list_err_res[0] " + str(len(list_err_res[0])))
    full_list.append(list_err_res[1])
    #print("list_err_res[1] " + str(len(list_err_res[1])))
    full_list.append(list_err_res[2])		
    #print("list_err_res[2] " + str(len(list_err_res[2])))											

    full_list.append(tu_err_list[0])
    #print("tu_err_list[0] " + str(len(tu_err_list[0])))
    full_list.append(tu_err_list[1])
    #print("tu_err_list[1] " + str(len(tu_err_list[1])))
    full_list.append(tu_err_list[2])	
    #print("tu_err_list[2] " + str(len(tu_err_list[2])))



    #full_list.append(empty_list)
    full_list.append(meter_range_gen)
    #print("meter_range_gen " + str(len(meter_range_gen)))




    full_list.append(list_meas[2])
    #print("list_meas[2]    " + str(len(list_meas[2])))

    full_list.append(list_err_res[3])
    #print("list_err_res[0]    " + str(len(list_err_res[0])))
    full_list.append(list_err_res[4])
    #print("list_err_res[1]    " + str(len(list_err_res[1])))
    full_list.append(list_err_res[5])
    #print("list_err_res[2]    " + str(len(list_err_res[2])))

    full_list.append(tu_err_list[0])
    #print("tu_err_list[0]     " + str(len(tu_err_list[0])))
    full_list.append(tu_err_list[1])
    #print("tu_err_list[1]     " + str(len(tu_err_list[1])))
    full_list.append(tu_err_list[2])	
    #print("tu_err_list[2]     " + str(len(tu_err_list[2])))


    #full_list.append(empty_list)
    full_list.append(meter_range_bin)
    #print("meter_range_bin    " + str(len(meter_range_bin)))

    
    full_list.append(empty_list)
    #print("empty_list    " + str(len(empty_list)))


    # строка с BLOB временем
    blob_time_str = []
    time_idx = cur_pnt - st_pnt
    #list_of_times[2][idx]
    if len(list_of_times[2]) > time_idx:
        blob_time_str.append(str(list_of_times[2][time_idx]))
    else:
        blob_time_str.append("---")

    for _ in range(len(empty_list) - 1):
        blob_time_str.append("")


    full_list.append(blob_time_str)
    #print("blob_time_str    " + str(len(blob_time_str)))


    return full_list

    ################################################
    ################################################
    ################################################

#------------------------------------------------------
#----Запись содержимого страницы за 1 раз   
#------------------------------------------------------
def write_all_data_on_sheet(wb_result,cur_pnt, st_pnt, list_of_times, P_flag, Q_flag):
    etalon = measurement.measurement_storage.get_etalon_signal(cur_pnt)
    mte_CNT = measurement.measurement_storage.get_mte_CNT_signal(cur_pnt)
    mte_GEN = measurement.measurement_storage.get_mte_GEN_signal(cur_pnt)
    binom_result = measurement.measurement_storage.get_binom_signal(cur_pnt)

    full_list = []
    full_list = generate_value_for_write(etalon,mte_CNT,mte_GEN,binom_result,cur_pnt,st_pnt, list_of_times, P_flag, Q_flag)

    exel_range = "E2:AM21" 
    sheet_name = get_sheet_name(cur_pnt)
    cur_range = wb_result.sheets[sheet_name].range(exel_range)
    cur_range.value = full_list

    '''
    exel_range_1 = "E2:AM7" 
    exel_range_2 = "E12:AM15"
    sheet_name = get_sheet_name(cur_pnt)
    cur_range = wb_result.sheets[sheet_name].range(exel_range_1)
    cur_range.value = full_list[0:6]
    cur_range = wb_result.sheets[sheet_name].range(exel_range_2)
    cur_range.value = full_list[6:10]
    '''

    #make_color_sell_diff(wb_result,cur_pnt,full_list)

#------------------------------------------------------
#----Сделать цветовую градуировку ячеек  
#------------------------------------------------------
def make_color_sell_diff(wb_result,cur_pnt,full_list):

    '''
    красный фон  =   (255,0,0)     - большое значение погрешности
    серый        =   (128,128,128)     - не используемое в "метрологическом отчете" значение погрешности
    светло серый =   (192,192,192)    - расчетные величины
    '''
    red_color = (255,0,0)
    
    # цикл по столбцам 
    #   цикл по строке  (только строки с погрешностями)
    #       если значение из списка full_list > 'порогового значения'
    #           выделить эту ячейку красным цветом
    #---------------------------------------
    abs_max_diff = 0.2
    rel_max_diff = 0.1
    red_max_diff = 0.1
    max_err_list = [abs_max_diff,rel_max_diff,red_max_diff]
    temp_idx = 0

    for idx in range(3):
        for idx_err in range(3):
            elem_num = 0
            t_full_list_idx = 3 + temp_idx + idx_err + idx*3
            for elem_list in full_list[t_full_list_idx]:
                if elem_num == 0:   # пропустить первый элемент (столбец) строки: пустую ячейку или номер точки ПСИ
                    elem_num += 1
                    continue
                if (elem_list != "") and (elem_list > max_err_list[idx_err]):
                    col_val = 2 + t_full_list_idx
                    row_val = elem_num + 2
                    wb_result.sheets[get_sheet_name(cur_pnt)].range((col_val, row_val)).color = red_color

                elem_num += 1   # перейти на следующую строку
        temp_idx += 2           # пропустить пустую строку

#------------------------------------------------------
#------------------------------------------------------   
#------------------------------------------------------

# функция копирует строку с метрологическим запасом  со всех листов (об одиночной точке)
# и созраняет на странице meter_result_by_pnt
# Алгоритм работы:
# выделить фрагмент со страницы с заполненным результатом (метрологического запаса)
# скопировать на страницу результата в нужную строку
# 
def group_meter_ranges(st_pnt, end_pnt, wb_template, wb_result, list_of_times):

    cur_pnt = st_pnt
    cnt_pnts = 0

    dest_sheet_name = "meter_result"

    from_ranges = "F19:AM19"

    #--------- Копирование итогового шаблона в отчет о ПСИ
    wb_result.sheets.add(dest_sheet_name, before=wb_result.sheets[cnt_pnts])

    src_sh = wb_template.sheets['Template_meter_result']
    dst_sh = wb_result.sheets[dest_sheet_name] 

    res_meter_range = "A1:AM167"

    src_sh.range(res_meter_range).api.copy
    dst_sh.range("A1").api.select
    dst_sh.api.paste
    #--------- 

    start_col_to = 5
    end_col_to   = start_col_to + 34

    num_row_to = 10 - 1 + cur_pnt

    ########################################
    #list_of_times
    #[0] - delta_mte_time
    #[1] - end_automeas_mte_time
    #[2] - BLOB-e Binom time
    idx = 0
    ########################################

    while cur_pnt <= end_pnt:

        #write times
        if len(list_of_times[0]) > idx:
            dst_sh.range((num_row_to,2),(num_row_to,4)).value =[str(list_of_times[0][idx]), 
                                                                str(list_of_times[1][idx]),
                                                                str(list_of_times[2][idx])   ]                                 
        idx += 1
        ##

        from_meter_range = wb_result.sheets[get_sheet_name(cur_pnt)].range(from_ranges)
        dst_sh.range((num_row_to,start_col_to),(num_row_to,end_col_to)).value = from_meter_range.value

        num_row_to += 1
        cur_pnt += 1


#------------------------------------------------------
#------------------------------------------------------   
#------------------------------------------------------

#title_split_str = []

def generate_report(st_pnt, end_pnt, list_of_times):
    # 1. copy head from template
    # 2. copy result from csv file and MTE counter
    
    # 3. copy results part for Binom
    # 4. copy results
    res_excel_file =  '.\\Results\\Report_' + time.strftime("%Y_%m_%d-%H-%M-%S",time.localtime()) + ".xlsx"
    
    #excel_app = xs.App(visible=False)  #uncomment if visible not desired
  
    wb_template = xs.Book(template_file_name)
    wb_result = xs.Book()
    #copy_head_fr_template(wb_template, wb_result)
    '''
        #title_str = "Uном, В" + str(U_nom_val)	+	"Iном, А"		№ точки	freq	Ua	Ub	Uc	AngUab	AngUbc	AngUca	Ia	Ib	Ic	AngIab	AngIbc	AngIca	cosPhi_A	cosPhi_B	cosPhi_C	U1	U2	U0	I1	I2	I0	Pa	Pb	Pc	Qa	Qb	Qc	Sa	Sb	Sc	P	Q	S"
    title_str = "Uном, В;Iном, А;№ точки;freq;Ua;Ub;Uc;AngUab;AngUbc;AngUca;Ia;Ib;Ic;AngIab;AngIbc;AngIca;" + 
                "cosPhi_A;cosPhi_B;cosPhi_C;U1;U2;U0;I1;I2;I0;Pa;Pb;Pc;Qa;Qb;Qc;Sa;Sb;Sc;P;Q;S"
    title_split_str = title_str.split(";")
    title_split_str.insert(1,str(U_nom_val))
    title_split_str.insert(3,str(I_nom_val))
    '''

    #-----Заполнить списки того, как заполнять значения для активной и реактивной мощности
    list_P_flag, list_Q_flag = init_P_Q_dict(st_pnt, end_pnt)
    flag_list_idx = 0


    #-------------------------------------------------
    cur_pnt = st_pnt
    cnt_pnts = 0
    while cur_pnt <= end_pnt:
        measurement.measurement_storage.calc_error(cur_pnt)

        wb_result.sheets.add(get_sheet_name(cur_pnt), before=wb_result.sheets[cnt_pnts])

        copy_result_fr_template(wb_template, wb_result, cur_pnt)

        #запись всех измерений и расчетов погрешностей на страницу excel за 1 раз
        #write_all_data_on_sheet(wb_result, cur_pnt, st_pnt, list_of_times)
        write_all_data_on_sheet(wb_result, cur_pnt, st_pnt, list_of_times, list_P_flag[flag_list_idx], list_Q_flag[flag_list_idx])
        flag_list_idx += 1

        #установка ширины столбца по содержимому ячейки
        #wb_result.sheets[get_sheet_name(cur_pnt)].range("A1:A21").columns.autofit()

        #wb_result.sheets[get_sheet_name(cur_pnt)].range("E1:E21").columns.autofit() 

        cur_pnt += 1
        cnt_pnts += 1
    #-------------------------------------------------


    group_meter_ranges(st_pnt, end_pnt, wb_template, wb_result, list_of_times)
    wb_result.sheets[0].range("B1:D200").columns.autofit() 

    remove_default_sheets(wb_result)

    wb_result.sheets[0].activate()
    wb_result.save(res_excel_file)


    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#
    #-----Заполнить списки того, как заполнять значения для активной и реактивной мощности
    #-----------------------------------------------------------------------------------#
    #-----------------------------------------------------------------------------------#

def init_P_Q_dict(st_pnt, end_pnt):

    Pabc_null_dict = {  range(50,53)    : 1,
                        range(53,59)    : 3,
                        range(59,62)    : 1,
                        range(62,68)    : 2,
                        range(81,87)    : 0,
                        range(101,107)    : 0,
                        range(107,110)    : 1,
                        range(110,113)    : 3,
                        range(113,116)    : 0,
                        range(116,119)    : 2,
                        range(125,127)    : 0  }

    Qabc_null_dict = {      range(1,2)    : 0,
                            range(3,4)    : 0,
                            range(4,5)    : 0,
                            range(6,7)    : 0,
                            range(12,17)    : 1,
                            range(23,36)    : 0,
                            range(50,56)    : 0,
                            range(56,59)    : 3,
                            range(59,62)    : 1,
                            range(62,65)    : 0,
                            range(65,68)    : 1,
                            range(101,104)    : 1,
                            range(104,107)    : 3,
                            range(107,110)    : 1,
                            range(110,113)    : 3,
                            range(113,119)    : 2,
                            range(119,127)    : 0,
                            range(135,139)    : 0,
                            range(142,145)    : 0,
                            range(147,148)    : 0,
                            range(150,157)    : 0  }

    list_P_flag = []

    # цикл по номерам точек от "start point" до "end point"
    #   если элемент в списке зануления, то выставить флаг 0,1,2,3
    #   если нет элемента, то пишем 4

    for idx in range(st_pnt, end_pnt + 1):
        for Pabc_keys in Pabc_null_dict.keys():
            if idx in Pabc_keys:
                list_P_flag.append(Pabc_null_dict[Pabc_keys])
                break
        else:
            list_P_flag.append( 4 )

    """
    for i in range(len(list_P_flag)):
        print("pnt   "+str(i+1)+"   "+str(list_P_flag[i]))
    """
    
    list_Q_flag = []

    for idx in range(st_pnt, end_pnt + 1):
        for Qabc_keys in Qabc_null_dict.keys():
            if idx in Qabc_keys:
                list_Q_flag.append(Qabc_null_dict[Qabc_keys])
                break
        else:
            list_Q_flag.append( 4 )

    """
    for i in range(len(list_Q_flag)):
        print("pnt   "+str(i+1)+"   "+str(list_Q_flag[i]))
    """

    return list_P_flag, list_Q_flag


if __name__ == '__main__':
    pass