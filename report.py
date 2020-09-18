import xlwings as xs
import time
import measurement
import names_parameters as nm_par

#template_file_name = ".\\Template.xlsx"
template_file_name = ".\\Template_with_gen_meas.xlsx"

# head_range = "A1:AJ1"
# result_range = "A2:AJ13"

result_range = "A1:AJ18"

cur_col_output = "A2"

'''
def copy_head_fr_template(wb_src, wb_dest):
    src_sh = wb_src.sheets['Template']
    dst_sh = wb_dest.sheets[0]

    src_sh.range(head_range).api.copy
    dst_sh.range("A1").api.select
    dst_sh.api.paste

def copy_result_field_fr_template(wb_src, wb_dest, cur_pnt):
    src_sh = wb_src.sheets['Template']
    dst_sh = wb_dest.sheets[0]

    src_sh.range(result_range).api.copy
    dst_sh.range(cur_col_output).api.select
    dst_sh.api.paste
'''

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

    etalon_res          = list(etalon.meas_result.results.values())

    for idx in range(len(etalon_res)):
        if etalon_res[idx] < 0.000001: # 10^(-6)
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
    
    empty_list = []                         # пустая строка
    for _ in range(len(list_err_res[0])):
        empty_list.append("")

    etalon_res.insert(0,cur_pnt)
    ####
    full_list = []                          # список окончательных результатов для записи в excel за 1 заход

    full_list.append(etalon_res)

    full_list.append(empty_list)

    full_list.append(list_meas[0])
    full_list.append(list_err_res[0])
    full_list.append(list_err_res[1])
    full_list.append(list_err_res[2])

    full_list.append(empty_list)

    full_list.append(list_meas[1])
    full_list.append(list_err_res[3])
    full_list.append(list_err_res[4])
    full_list.append(list_err_res[5])

    full_list.append(empty_list)

    full_list.append(list_meas[2])
    full_list.append(list_err_res[6])
    full_list.append(list_err_res[7])
    full_list.append(list_err_res[8])

    return full_list

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

    exel_range = "B2:AJ18" 
    sheet_name = get_sheet_name(cur_pnt)
    cur_range = wb_result.sheets[sheet_name].range(exel_range)
    cur_range.value = full_list

    make_color_sell_diff(wb_result,cur_pnt,full_list)

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
    '''
    abs_max_diff = 0.005
    rel_max_diff = 1
    red_max_diff = 1

    temp_idx = 0

    for idx in range(3):
        for inner_idx in range(len(full_list[0]) - 1):
            
            if full_list[temp_idx + 3 + idx*3][inner_idx] > abs_max_diff:
                wb_result.sheets[get_sheet_name(cur_pnt)].range((temp_idx + 1 + 3 + idx*3, inner_idx + 1)).color = red_color
            
            if full_list[temp_idx + 3 + 1 + idx*3][inner_idx] > rel_max_diff:
                wb_result.sheets[get_sheet_name(cur_pnt)].range((temp_idx + 1 + 3 + idx*3, inner_idx + 1)).color = red_color
            
            if full_list[temp_idx + 3 + 2 + idx*3][inner_idx] > red_max_diff:
                wb_result.sheets[get_sheet_name(cur_pnt)].range((temp_idx + 1 + 3 + idx*3, inner_idx + 1)).color = red_color

        temp_idx += 1
    '''


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
                if elem_num == 0:
                    elem_num += 1
                    continue

                if (elem_list != "") and (elem_list > max_err_list[idx_err]):

                    #t_elem_val = elem_list
                    #t_max_err_val = max_err_list[idx_err]

                    col_val = 2 + t_full_list_idx
                    row_val = elem_num + 2
                    wb_result.sheets[get_sheet_name(cur_pnt)].range((col_val, row_val)).color = red_color

                    #t = 0

                elem_num += 1
        temp_idx += 2



    

#------------------------------------------------------
#------------------------------------------------------   
#------------------------------------------------------

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

    #-------------------------------------------------
    cur_pnt = st_pnt
    cnt_pnts = 0
    while cur_pnt <= end_pnt:
        measurement.measurement_storage.calc_error(cur_pnt)

        #copy_result_field_fr_template(wb_template, wb_result)

        wb_result.sheets.add(get_sheet_name(cur_pnt), before=wb_result.sheets[cnt_pnts])
        # wb_result.sheets[sheet_name].activate()

        copy_result_fr_template(wb_template, wb_result, cur_pnt)

        

        #запись всех измерений и расчетов погрешностей на страницу excel
        write_all_data_on_sheet(wb_result, cur_pnt)

        #установка ширины столбца по содержимому ячейки
        wb_result.sheets[get_sheet_name(cur_pnt)].range("A1:A18").columns.autofit() 
        '''
        write_etalon_result(wb_result, cur_pnt)
        write_mte_CNT_result(wb_result, cur_pnt) 
        write_mte_GEN_result(wb_result, cur_pnt) 
        write_binom_result(wb_result, cur_pnt)
        '''

        # next_output_cell(wb_result)
        cur_pnt += 1
        cnt_pnts += 1
        
    #-------------------------------------------------
    remove_default_sheets(wb_result)

    wb_result.sheets[0].activate()
    wb_result.save(res_excel_file)


if __name__ == '__main__':
    pass