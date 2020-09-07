'''
Make psi - main module. Set signals on MTE generator and fix result from Binom and MTE. 
Run as python make_psi.py PSI_Scenariy.py stPnt endPnt
'''
import sys
import measurement  
import svgrequest 
import time

binom_data = svgrequest.RequestBinom()




def init():
    
    # open Com ports 
    
    # open svg channel Binom
    # may be check opend sess and close them via simple socket connection and 23 port    
    binom_data.connect()    



def deinit():
    binom_data.close_channel()
    binom_data.close()

def check_pnts(st_pnt, end_pnt):
    return 0 < st_pnt <= 160 and 0 < end_pnt <= 160

def main():
    # parce argv
    if len(sys.argv) < 4:
        print("Need more command arguments, example Scenariy.csv stpnt endpnt")
    
    st_pnt = int(sys.argv[2]) - 1
    end_pnt = int(sys.argv[3]) - 1

    if not check_pnts(st_pnt, end_pnt):
        return


    cur_pnt = st_pnt
    try:
        init()

        while cur_pnt <= end_pnt:

        #1 Set current point on generator
        #2 pause
        #3 Read data from Generator if ok step 4 else 2
        #4 Read data from Counter MTE
        #5 Read data from Binom
        #6 pause
        
            for _ in range(2):
                binom_data.read_data(cur_pnt)
                # time.sleep(5)
            
            cur_pnt+=1

        print("Ask finished")
    except Exception as ex:
        print("Exception occur:", ex)
    finally:
        deinit()

        



if __name__ == "__main__":
    main()