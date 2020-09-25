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

result_range    = "A1:AM19"
cur_col_output  = "A2"

def copy_result_fr_template(wb_src, wb_dst, cur_pnt):
    src_sh = wb_src.sheets['Template']
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
def generate_value_for_write(etalon,mte_CNT,mte_GEN,binom_result,cur_pnt): 

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

    etalon_res          = list(etalon.meas_result.results.values())

    for idx in range(len(etalon_res)):
        if abs(etalon_res[idx]) < 0.00001: # 10^(-5)
            etalon_res[idx] = 0.0

    mte_CNT_res         = list(mte_CNT.meas_result.results.values())
    mte_GEN_res         = list(mte_GEN.meas_result.results.values())
    binom_result_res    = list(binom_result.results.values())

    list_err_res = [list(mte_CNT.meas_result.errors_abs.values()),
                    list(mte_CNT.meas_result.errors_rel.values()),
                    list(mte_CNT.meas_result.errors_red.values()),

                    list(mte_GEN.meas_result.errors_abs.values()),
                    list(mte_GEN.meas_result.errors_rel.values()),
                    list(mte_GEN.meas_result.errors_red.values()),

                    list(binom_result.errors_abs.values()),
                    list(binom_result.errors_rel.values()),
                    list(binom_result.errors_red.values()) ]
    
    for idx in range(len(list_err_res[0])):
        list_err_res[0][idx] = ""
        list_err_res[1][idx] = ""
        list_err_res[2][idx] = ""

    for idx in range(len(list_err_res[5])):
        if list_err_res[5][idx] == 0:
            #list_err_res[2][idx] = ""
            list_err_res[5][idx] = ""
            list_err_res[8][idx] = ""


    list_meas = [mte_CNT_res,mte_GEN_res,binom_result_res]

    ####
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
    ################################################
    ################################################

    full_list = []                          # список окончательных результатов для записи в excel за 1 заход
    #full_list.append(title_split_str)

    full_list.append(etalon_res)

    #full_list.append(empty_list)

    #full_list.append(list_meas[0])
    #full_list.append(list_err_res[0])
    #full_list.append(list_err_res[1])
    #full_list.append(list_err_res[2])

    #full_list.append(empty_list)

    full_list.append(list_meas[0])

    full_list.append(list_meas[1])
    full_list.append(list_err_res[3])
    full_list.append(list_err_res[4])
    full_list.append(list_err_res[5])

    '''
    full_list.append(empty_list)
    full_list.append(empty_list)
    full_list.append(empty_list)
    full_list.append(empty_list)
    '''

    #full_list.append(empty_list)

    full_list.append(list_meas[2])
    full_list.append(list_err_res[6])
    full_list.append(list_err_res[7])
    full_list.append(list_err_res[8])

    return full_list

    ################################################
    ################################################
    ################################################

#------------------------------------------------------
#----Запись содержимого страницы за 1 раз   
#------------------------------------------------------
def write_all_data_on_sheet(wb_result,cur_pnt):
    etalon = measurement.measurement_storage.get_etalon_signal(cur_pnt)
    mte_CNT = measurement.measurement_storage.get_mte_CNT_signal(cur_pnt)
    mte_GEN = measurement.measurement_storage.get_mte_GEN_signal(cur_pnt)
    binom_result = measurement.measurement_storage.get_binom_signal(cur_pnt)

    full_list = []
    full_list = generate_value_for_write(etalon,mte_CNT,mte_GEN,binom_result,cur_pnt)

    #exel_range = "A1:AM18" 
    exel_range_1 = "E2:AM7" 
    exel_range_2 = "E12:AM15"
    sheet_name = get_sheet_name(cur_pnt)
    cur_range = wb_result.sheets[sheet_name].range(exel_range_1)
    cur_range.value = full_list[0:6]
    cur_range = wb_result.sheets[sheet_name].range(exel_range_2)
    cur_range.value = full_list[6:10]

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
def group_meter_ranges(st_pnt, end_pnt, wb_template, wb_result):

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

    while cur_pnt <= end_pnt:
        from_meter_range = wb_result.sheets[get_sheet_name(cur_pnt)].range(from_ranges)
        dst_sh.range((10 - 1 + cur_pnt,3),(10 - 1 + cur_pnt,36)).value = from_meter_range.value

        cur_pnt += 1




#------------------------------------------------------
#------------------------------------------------------   
#------------------------------------------------------

#title_split_str = []

def generate_report(st_pnt, end_pnt):
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
    #-------------------------------------------------
    cur_pnt = st_pnt
    cnt_pnts = 0
    while cur_pnt <= end_pnt:
        measurement.measurement_storage.calc_error(cur_pnt)

        wb_result.sheets.add(get_sheet_name(cur_pnt), before=wb_result.sheets[cnt_pnts])

        copy_result_fr_template(wb_template, wb_result, cur_pnt)

        #запись всех измерений и расчетов погрешностей на страницу excel за 1 раз
        write_all_data_on_sheet(wb_result, cur_pnt)

        #установка ширины столбца по содержимому ячейки
        wb_result.sheets[get_sheet_name(cur_pnt)].range("A1:A19").columns.autofit() 

        cur_pnt += 1
        cnt_pnts += 1
    #-------------------------------------------------


    group_meter_ranges(st_pnt, end_pnt, wb_template, wb_result)

    remove_default_sheets(wb_result)

    wb_result.sheets[0].activate()
    wb_result.save(res_excel_file)


if __name__ == '__main__':
    pass