import xlwings as xs
import time
import measurement

template_file_name = ".\\Template.xlsx"
template_range = "A1:AJ8"
result_range = "A4:AJ8"

'''
import xlwings as xw

wb = xw.Book('mybook.xlxs')
sht = wb.sheets['Sheet1']
sht2 = wb.sheets['Sheet2']

sht.range('A1:A6').api.copy
sht2.range("A1").api.select
sht2.api.paste

wb.app.api.CutCopyMode=False
'''

# class 

def create_test_report(num_point, signal_fr_csv):
    '''

    '''
    result_file = '.\\Reports\\Report_' + time.strftime("%Y_%m_%d:%H:%M:%S",time.localtime()) + ".xlsx"
    wb_template = xs.Book(template_file_name)
    
    wb = xs.Book()
    # copy template to new excel 
    # wb_template.sheets["Template"].Range(template_range).copy(wb.sheets["Result"].range(template_range))
    wb_template.sheets["Template"]

    '''
    Todo: 
    1 write copy header 
    2 write set values (from csv)
    3 wrute MTE meas values with ()
    '''


    wb.save(result_file) 


def copy_head_fr_template(wb_src, wb_dest):
    src_sh = wb_src.sheets['Template']
    dst_sh = wb_dest.sheets[0]

    src_sh.range(template_range).api.copy
    dst_sh.range("A1").api.select
    dst_sh.api.paste

    

    
def generate_report(st_pnt, end_pnt, signal_fr_csv):
    # 1. copy head from template
    # 2. copy result from csv file and MTE counter
    
    # 3. copy results part for Binom
    # 4. copy results
    res_excel_file =  '.\\Reports\\Report_' + time.strftime("%Y_%m_%d:%H:%M:%S",time.localtime()) + ".xlsx"
   # excel_app = xs.App(visible=False)
    wb_template = xs.Book(template_file_name)
    wb_result = xs.Book()
    copy_head_fr_template(wb_template, wb_result)
    wb_result.save(res_excel_file)
    pass


if __name__ == '__main__':
    #create_test_report(123, None)
    generate_report(2, 2, None)