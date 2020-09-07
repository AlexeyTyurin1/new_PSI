""" 
MakeCmdFromCSV this module reads PSI scenariy.csv file and convert it to MTE comands
"""
import sys
import csv
import collections
import MTE_parameters
import names_parameters
import vector_signal as vs
from measurement import make_signal_from_csv_source
#import test_parsing_answer  # clear it in the future

import serial

   
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


def MenuItems():
    print("1 - Choose num point")
    print("2 - Reset MTE")
    print("3 - Exit")

def HandleMenu(pnts_for_generator):
    with open(r".\out.txt", "w") as outfile,\
    serial.Serial('COM5', 19200, timeout=1, parity=serial.PARITY_NONE, rtscts=1) as ser:
        while(True):
            try:
                menu_item = int(input())
                if menu_item == 3:
                    return
                elif menu_item == 1:
                    num_pnt = int(input("Enter point number "))
                    pnt_param = pnts_for_generator.get(num_pnt)
                    if pnt_param:
                        # res = MTE_parameters.generate_commands(pnt_param)
                        res = MTE_parameters.generate_commands_with_harm(pnt_param)
                        ser.write(res.encode(encoding="utf-8"))
                        rd_ser = ser.read(1000)
                        outfile.write(res)
                        print(rd_ser)
                    else:
                        print("No such point try again. Point starts from 1!")
                elif menu_item == 2:
                    outfile.write("R\r")
            except ValueError:
                print("Something goes wrong! input num menu item.")


def main():
    if len(sys.argv) < 3:
        print("Need more cmd arguments! 1 - name csv, 2 - number of point")
        return     
    # generator_points_dict = collections.OrderedDict()
    set_pnts_for_PSI = create_dict_test_points(sys.argv[1])
    sig = make_signal_from_csv_source(set_pnts_for_PSI, 132) 
    sig.calc_measured_param()
    
     
    Ua_from_MTE = test_parsing_answer.parse_MTE_Counter_answer()
    Ub_from_MTE = test_parsing_answer.parse_MTE_Counter_answer()
    Uc_from_MTE = test_parsing_answer.parse_MTE_Counter_answer()

     

    print(sig.calc_phase_voltage("Ua"), sig.calc_phase_voltage("Ub"), sig.calc_phase_voltage("Uc"))
    MenuItems()
    HandleMenu(set_pnts_for_PSI)

if __name__ == "__main__":
    main()