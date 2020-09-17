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
    # very slow speed below code
    '''
    for num, meas_par_name in enumerate(nm_par.link_measured_params_errors.keys()):
        type_tolerance = nm_par.link_measured_params_errors[meas_par_name]
        #  cur_range = cur_range.offset(0, num)
        for row in range(0, 3):
            if type_tolerance == "absolute" and row == 0:
                cur_range.offset(row, num).value = meas_result.errors[meas_par_name]
            elif type_tolerance == "relative" and row == 1:
                cur_range.offset(row, num).value = meas_result.errors[meas_par_name]
            elif type_tolerance == "reduced" and row == 2:
                cur_range.offset(row, num).value = meas_result.errors[meas_par_name] 
            else:
                cur_range.offset(row, num).value = "-----"
    '''
    # for num, meas_par_name in enumerate(nm_par.link_measured_params_errors.keys()):
    
    for nm_err in ("absolute", "relative", "reduced"):
        err = [meas_result.errors[name] if type_tolerance == nm_err \
            else "-----"  for name, type_tolerance in nm_par.link_measured_params_errors.items()]
        cur_range.value = err
        cur_range = cur_range.offset(1, 0)
    
    
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
    mte_CNT_res         = list(mte_CNT.meas_result.results.values())
    mte_GEN_res         = list(mte_GEN.meas_result.results.values())
    binom_result_res    = list(binom_result.results.values())

    mte_CNT_err_abs = []
    mte_CNT_err_rel = []
    mte_CNT_err_red = []

    mte_GEN_err_abs = []
    mte_GEN_err_rel = []
    mte_GEN_err_red = []

    binom_result_err_abs = []
    binom_result_err_rel = []
    binom_result_err_red = []

    list_err_res = [mte_CNT_err_abs,mte_CNT_err_rel,mte_CNT_err_red,\
                    mte_GEN_err_abs,mte_GEN_err_rel,mte_GEN_err_red,\
                    binom_result_err_abs,binom_result_err_rel,binom_result_err_red]

    list_measurement = [mte_CNT,mte_GEN,binom_result]

    list_meas = [mte_CNT_res,mte_GEN_res,binom_result_res]
    idx = 0
    idx_inner = 0

    for meas_elem in list_measurement:
        idx_inner = 0
        if idx == 2:
            for nm_err in ("absolute", "relative", "reduced"): 
                err = [meas_elem.errors[name] if type_tolerance == nm_err else "---"\
                    for name, type_tolerance in nm_par.link_measured_params_errors.items()]
                list_err_res[idx*3 + idx_inner] = err
                idx_inner += 1
        else:
            for nm_err in ("absolute", "relative", "reduced"):
                err = [meas_elem.meas_result.errors[name] if type_tolerance == nm_err else "---"\
                    for name, type_tolerance in nm_par.link_measured_params_errors.items()]
                list_err_res[idx*3 + idx_inner] = err
                idx_inner += 1

        idx += 1 

    ####

    for L_idx in range(len(list_err_res)):       # создание отступа на один столбец вправо
        list_err_res[L_idx].insert(0,"")

    for L_idx in range(len(list_meas)):          # запись номера текущей точки ПСИ
        list_meas[L_idx].insert(0,cur_pnt)
    
    empty_list = []                         # пустая строка
    for idx in range(len(list_err_res[0])):
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

#------------------------------------------------------
#------------------------------------------------------   
#------------------------------------------------------

def generate_report(st_pnt, end_pnt):
    # 1. copy head from template
    # 2. copy result from csv file and MTE counter
    
    # 3. copy results part for Binom
    # 4. copy results
    res_excel_file =  '.\\Results\\Report_' + time.strftime("%Y_%m_%d-%H-%M-%S",time.localtime()) + ".xlsx"
    
    excel_app = xs.App(visible=False)  #uncomment if visible not desired
  
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

        write_all_data_on_sheet(wb_result, cur_pnt)
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