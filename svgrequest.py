'''
Create SVG requestst to binom for read data
First  stage: ping Binom on line
Second stage: ask channel names and create dict {ip_addr_1: {UID_1: name, UID_2: name, ...}, ip_addr_2: {UID_1: name, UID_2: name, ...}}
Third  stage: ask all binoms 
'''
import requests
import struct
import time
import os
import names_parameters as nm_par
import measurement as ms

import datetime

prot = "http://"
ip_addr = "192.168.99.235"

class RequestBinom():
    
    def __init__(self):
        self.http_addr = "http://" + ip_addr
        self.uid_names = dict()
        self.connect_session = False
        self.channel_open = False

        self.blob_time = datetime.datetime.now()
        
    def connect(self):
        '''
        connect to binom via http protocol
        '''       
        login = {"login" : "root", "password" : "root"}
        s = requests.Session()
        request_str = self.http_addr + '/~login'
        print("Try login to Binom3 " + request_str)

        req = s.post(request_str, params=login)
        print("Status code: " + str(req.status_code))
        if req.status_code == 302: #  code mean Found
            self.session = s
            self.connect_session = True
        # check channel names from binom
        #'''
        #out_ch = self.__ask_channel_out_names()
        self.__ask_channel_out_names()
        self.__check_received_channel_names()
        #'''

    def close_channel(self):
        if self.channel_open:
            #self.__close_channel()
            self.close_svg_channel()
            self.channel_open = False

    #def read_data(self, num_psi_pnt, cnt=1, pause=5 ):
    def read_data(self, num_psi_pnt, cnt=1, pause= 3 ):
        '''
        read_data - read data from svg channel
        num_psi_pnt - number point PSI
        cnt - number of readings, after that make update PSI mesurement results
        pause - pause between reading
        example: obj.read_data(4, cnt=2, pause=5) - PSI 4 point makes 2 reading with delay 5s between readings
        and writes result to 4 point PSI
        '''
        ####################################
        #self.__open_svg_channel()
        ####################################
        ####################################
        #self.open_svg_channel()
        ####################################

        while cnt > 0:
            ####################################
            ####################################
            ##time.sleep(pause)
            ####################################
            ####################################
            '''
            print("Request current time")
            request = "~time"
            r = self.session.get(create_request_string(request))
            cur_time = r.content.decode("utf-8")
            print("time: " + cur_time)
            '''
            #request = "~svgcurrent?name=db:PSI_data"

            #request = "~svgevent?name=db:PSI_data"

            """
            ~svgevent?name=[имя данных]
            Запрос новых данных. Используется только для чтения данных из канала вывода.
            По данному запросу будут переданы все события из канала вывода БД, произошедшие после последнего вызова запроса «~svgdata» или «~svgevent».
            """

            request = "~svgcurrent?name=db:PSI_data"
            """
            ~svgcurrent?name=[имя данных] [& shortvalue=«1»]
            Запрос текущих значений. Используется только для чтения данных из канала вывода.
            По данному запросу будут переданы текущие данные (аналогично «~svgdata»).
            При выводе значений из БД обрабатывается параметр «shortvalue». При его наличии данные будут выданы максимально упакованные – в 10 байт. Первые два байта – качество, 8 байт int или float значение. При передаче с максимальной упаковкой в заголовке ответа будет указан параметр «shortvalue» со значением «1».
            """

            r = self.session.get(self.__create_request(request))
            #print("Status code: ", r.status_code)
            print("Read data len ", len(r.content))
            self.__parse_output(r.content)
            cnt -= 1
        self.__update_result(num_psi_pnt)
        #self.__close_svg_channel()

    
    #def __close_svg_channel(self):
    def close_svg_channel(self):
        if self.channel_open == True:
            request = "~svgclose?name=db:PSI_data"
            if hasattr(self, "session"):
                r = self.session.get(self.__create_request(request))
                if r.status_code != 205:
                    raise Exception("can't close svg channel PSI_data")
                self.channel_open = False

    def close(self):
        if hasattr(self, "session"):
            self.session.close()

    def __create_request(self, request):
        return self.http_addr + "/" + request

    def __ask_channel_out_names(self):
        '''
        ask svg channel out and return dict {UID_1: nameDB, UID_2: nameDB}
        '''
        req = "~svginfo?name=db:PSI_data"
        print("Send request: " + req) 
        r = self.session.get(create_request_string(req))
        cells_names = r.content.decode("utf-8").split(";")  # format: 000000000, name, BLOB.MINMAX
        
        for el in cells_names:
            record = el.split(",")
            if len(record) > 2:
                self.uid_names[int(record[0])] = record[1][:-4]   # [:-4] clear "_rng" endings
        self.names_vals = dict().fromkeys(self.uid_names.values())
    
    def __check_received_channel_names(self):
        for names in zip(self.uid_names.values(), nm_par.names_measured_params):
            if names[0] != (names[1]):
                raise Exception("Find incorrect names in Binom out ch")

    ##def __open_svg_channel(self):
    def open_svg_channel(self):

        self.close_channel()

        request = "~svgdata?name=db:PSI_data"
        r = self.session.get(self.__create_request(request))

        #time.sleep(0.5)

        if r.status_code != 200:
            raise Exception("Can't open channel db:PSI_data")
        
        self.channel_open = True
        print("Channel PSI_data sucessfully opened!")



    def get_blob_time(self):
        return self.blob_time


    def __parse_output(self, content):
        '''
        parce answer with event from binom
        binom_answer - binary data received from binom
        uid_dict - UID: name dictionary
        '''

        time_uid_offset = 8
        # "q" == long long
        nanosec_time = struct.unpack_from("q", content, time_uid_offset)[0]
        #microsec_time = int(nanosec_time / 1000)
        mod_microsec = int(nanosec_time % (1000000000))
        #part_of_sec = mod_microsec / 1000000.0
        sec_time = int(nanosec_time / 1000000000)
        dt_time = datetime.datetime.fromtimestamp(sec_time)
        #####dt_time = dt_time + datetime.timedelta(microseconds=mod_microsec)
        self.blob_time = dt_time

        #print(str(nanosec_time)+ "   nanosec_time")
        #print(str(microsec_time)+"   microsec_time")
        print(str(dt_time)+      "   BLOB_time")

        #print(str(mod_microsec)+ "   mod_microsec")
        #print(str(part_of_sec)+  "   part_of_sec")

        offset_UID = 4
        offset_average_data = 64 + 8
        # global DBNames_value_mapping  ??? it's exactly need ???
        while offset_UID < len(content):
            uid = struct.unpack_from("I", content, offset_UID)[0]   # get uid from binom data
            value = struct.unpack_from("f", content, offset_average_data)[0]  # get average value data
            name_cell = self.uid_names.get(uid, None)
            if name_cell is not None:
                self.names_vals[name_cell] = value
            else:
                raise Exception("Received undefined UID " + str(uid))
            offset_average_data += 128
            offset_UID  += 128
            if offset_UID > len(content):
                break
        
        #self.out_measurements()
    
    def __update_result(self, num_psi_pnt):
        ms.measurement_storage.set_binom_measured_signal(num_psi_pnt, num_binom=0, **self.names_vals)

    def out_measurements(self):
        #'''
        for name, value in self.names_vals.items():
            print("{:^10s}".format(name), "=", value)
        #'''
        #pass

# may be we don't need this feature now it placed in names_parameters
# variable_names = ("P", "Ua", "Ub", "Uc", "AngUab", "AngUbc", "AngUca", "Uab", "Ubc", "Uca", "Ia", "Ib", "Ic", "AngIab", "AngIbc", "AngIca", "AngSym1")

UID_DBnames_mapping = dict()
DBNames_value_mapping = dict()

def create_request_string(req):
    return prot + ip_addr + "/" + req

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def connect_binom():
    '''
    connect_binom - connects to binom through http protocol return session obj
    '''
    login = {"login" : "root", "password" : "root"}
    s = requests.Session()
    request_str = 'http://' + ip_addr + '/~login'
    print("Try login to Binom3 " + request_str)
    req = s.post(request_str, params=login)
    print("Status code: " + str(req.status_code))
    return s

def ActionsHandler():

    #debug peace of code


    binom_session = connect_binom()
    menu_items = ("1 - send GET request","2 - ~svginfo?name=db:PSI_data" ,
                  "3 - open data", "4 - close data","5 - exit")
    work = True
    while work:
        print(*menu_items,sep='\n')
        try:
            usr_inp = int(input())
        except ValueError as ve:
            print("input number")
            continue
        if usr_inp == 1:
            print("input request")
            req = input()
            r = binom_session.get(create_request_string(req))
            print("Response len = ", len(r.content))
            txt_content = r.content.decode("utf-8").split(";")
            print("\n".join(txt_content))
        elif usr_inp == 2:
            req = "~svginfo?name=db:PSI_data"
            print("Send request: " + req)
            r = binom_session.get(create_request_string(req))
            print("Response")
            txt_content = r.content.decode("utf-8").split(";")
            print("\n".join(txt_content))
        elif usr_inp == 3:
             # ask channel output names
            UID_DBnames_mapping.update(ask_channel_out_names(binom_session))
            print(UID_DBnames_mapping)

            if len(UID_DBnames_mapping) == 0: 
                print("Can't read names from channel output")                
                continue

            code, content, len_content = read_binom_data(binom_session, True)  # open channel for read
            if code == 200:
                for _ in range(0, 10):
                    code, content, len_content = read_binom_data(binom_session)  # read channel events
                    if code == 200:
                        parce_answer_fr_binom(content)
                    elif code == 204:
                        print("no data")
                    else:
                        print("err occur")
                    time.sleep(5)
                close_binom_data(binom_session)
            else:
                print("Can't open svg channel check parametrization")
                
        elif usr_inp == 4:
            pass
        elif usr_inp == 5:
            work = False

    print("Program complete")

def ask_channel_out_names(binom_sess):
    '''
    ask svg channel out and return dict {UID_1: nameDB, UID_2: nameDB}
    '''
    req = "~svginfo?name=db:PSI_data"
    print("Send request: " + req) 
    r = binom_sess.get(create_request_string(req))
    cells_names = r.content.decode("utf-8").split(";")  # format: 000000000, name, BLOB.MINMAX
    res = dict()
    for el in cells_names:
        record = el.split(",")
        if len(record) > 2:
            res[int(record[0])] = record[1]
    return res


def read_binom_data(binom_sess, open=False):
    print("Request current time")
    request = "~time"
    r = binom_sess.get(create_request_string(request))
    time = r.content.decode("utf-8")
    print("time: " + time)
    request = "~svgdata?name=db:PSI_data" if open else "~svgevent?name=db:PSI_data"
    print("Send request: " + request)
    r = binom_sess.get(create_request_string(request))
    print("Status code: ", r.status_code)
    print("Read data len ", len(r.content))
    return r.status_code, r.content, len(r.content)


def close_binom_data(binom_sess):
    print("close svg channel")
    request = "svgclose?name=db:Ua"
    print("Send request: " + request)
    r = binom_sess.get(create_request_string(request))
    print("Status code: ", r.status_code)
    print(r.content)
    


def parce_answer_fr_binom(binom_answer):
    '''
    parce answer with event from binom
    binom_answer - binary data received from binom
    uid_dict - UID: name dictionary
    '''
    offset_UID = 4
    offset_average_data = 64 + 8
    # global DBNames_value_mapping  ??? it's exactly need ???
    for _ in range(0, len(nm_par.names_measured_params)):
        uid = struct.unpack_from("I", binom_answer, offset_UID)[0]   # get uid from binom data
        value = struct.unpack_from("f", binom_answer, offset_average_data)[0]  # get average value data
        name_cell = UID_DBnames_mapping.get(uid, None)
        if name_cell is not None:
            DBNames_value_mapping[name_cell] = value
        else:
            raise Exception("Received undefined UID " + str(uid))
        
        offset_average_data += 128
        offset_UID  += 128
    
    for name, value in DBNames_value_mapping.items():
        print("{:^10s}".format(name), "=", value)

if __name__ == "__main__":
   # parce_answer_fr_binom(rcv_binary_str)  # it's only for debug
    ActionsHandler()