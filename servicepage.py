
from flask import Flask, render_template, request, render_template_string, jsonify
from flask_socketio import SocketIO
from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from gevent.pywsgi import WSGIServer
from pymongo import MongoClient
import numpy as np

import os
import time
import threading
from multiprocessing import Process
from datetime import datetime, timedelta

app = Flask(__name__)
socket = SocketIO(app)
thread_lock = threading.Lock()
thread = None

"""
old = MongoClient(f"mongodb://172.20.33.151:27017")
old_db = old["Site_information"]

new = MongoClient(f"mongodb://172.20.33.163:27017")
new_db = new["Systems"]
print("STARTED")
for i in old_db.list_collection_names():
    DATA = {}
    col = old_db[i]
    data = col.find_one({},{"_id":0})
    data['PV_IP'] = data['PV_IP'][0] 
    data['PV_Slave'] = data['PV_Slave'][0]
    data['PV_Port'] = data['PV_Port'][0]
    data['PV_Type'] = data['PV_Type'][0]

    data['Grid_IP'] = data['Grid_IP'][0]
    data['Grid_Type'] = data['Grid_Type'][0]
    data['Grid_Port'] = data['Grid_Port'][0]
    
    
    
    new_col= new_db[i]
    new_col.insert_one(data)
    #print(data)
    #break
quit() 
"""



#
#DB_ERROR = MongoClient(f"mongodb://localhost:27017")
#DB_ERROR_UPDATE = DB_ERROR["TESTs"]

#Visblue_database = MongoClient(f"mongodb://172.20.33.163:27017")
#db_log = Visblue_database["Service_log"]

Alarmkoder = {"0000000000000010 ": 'CPLD_Alarm',
              "0000000000000100 ": 'DetectNoEM',
              "0000000000001000 ": 'BlockedStack',
              "0000000000010000 ": 'State Error',
              "0000000000100000 ": 'Tankpressurerelief_Alarm',
              "0000000001000000 ": 'DataValid_Alarm',
              "0000000010000000 ": 'OCVsensor_Alarm',
              "0000000100000000 ": 'IOboardComm_Alarm',
              "0000001000000000 ": 'Pressure_Alarm',
              "0000010000000000 ": 'ElectrolyteTankimbalance',
              "0000100000000000 ": 'Tankpressure',
              "0001000000000000 ": 'Emergency stop',
              "0010000000000000 ": 'Leak_Alarm',
              "0100000000000000 ": 'ElectrolyteTemp_Alarm',
              "1000000000000000 ": 'DiffPressure Alarm', }

def convertAlarmCode(Alarm_CODE):
    pos = []
    A = str(bin(Alarm_CODE)).replace("0b", "")

    for i in range(len(A)):
        if A[i] == "1":
            pos.append(i)

    res = ""
    poss = 0
    for i, x in Alarmkoder.items():        
        for g in range(len(A)):
            if i[g] == A[len(A)-1-g] and i[g] != "0":
                if res == "":
                    res += x  # + ","
                else:
                    res += "," + x + ","
                break
        poss += 1
    if res == "":
        return f"OK"
    return res





        

def decode_Uint16(regs):
    return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.BIG).decode_16bit_uint()

def decode_int16(regs):
    return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.BIG).decode_16bit_int()

def decode_int32( regs):
    return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.LITTLE).decode_32bit_int()

def decode_Carlo( regs):
    return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.LITTLE).decode_32bit_int()

def decode_float( regs):
    return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.BIG).decode_32bit_float()



class MODBUS(object):
    def __init__(self, ip, port, unit_id):
        self.IP = ip   
        self.PORT = port
        self.UNIT_ID = unit_id
        self.client = ModbusTcpClient(self.IP, self.PORT);
    

    def try_connect(self): 
        try:
            if not self.client.is_socket_open():
                self.client.connect()
            self.client.read_holding_registers(1,1,1).registers 
            self.client.close()
            return True
        except Exception as e:
            print(f"Failed : Connection {self.IP}:{self.PORT}")
            self.client.close()        
            return False             

    def siemens_ACPower(self):
            return decode_float(self.client.read_holding_registers(65,2,self.UNIT_ID).registers)
    
    def carlo_ACPower(self): 
        return decode_int32(self.client.read_holding_registers(40,3,self.UNIT_ID).registers)
        
    def server_ACPower(self): 
        return decode_int32(self.client.read_holding_registers(19026,3,self.UNIT_ID).registers)

    def fronius_eco_ACPower(self):
        return decode_int16(self.client.read_holding_registers(40083,1,self.UNIT_ID).registers)
    
    def fronius_symo_ACPower(self):
        return decode_float(self.client.read_holding_registers(40095,2,self.UNIT_ID).registers)
    

class EnergyMeter(MODBUS):
    def __init__(self, ip_address, port, unit_id, system_info):   
        super().__init__(ip_address, port, unit_id)
        self.system_info = system_info.lower()  
        self.IP = ip_address
        self.PORT = port
        self.UNIT_ID = unit_id                                


    def em_read_power(self):
        self.power = None
        if self.system_info == "siemens":
            self.power =self.siemens_ACPower()
        if self.system_info == 'carlo':            
            self.power =self.carlo_ACPower()
        if self.system_info == 'server':
            self.power =self.server_ACPower()
        print("EM:: ", self.power)
        return self.power
   

  
class PV(MODBUS):
    def __init__(self,ip_address, port, unit_id, system_info):
        super().__init__(ip_address, port, unit_id)
        self.system_info = system_info.lower()
        self.IP = ip_address
        self.PORT = port
        self.UNIT_ID = unit_id     

    
    def pv_read_power(self):
        self.power = None
        if self.system_info == "siemens":
            self.power =  self.siemens_ACPower()
        if self.system_info == 'carlo':
            self.power= self.carlo_ACPower()
        if self.system_info == 'server':
            self.power= self.server_ACPower()
        if self.system_info == 'fronius_eco':            
            self.power= self.fronius_eco_ACPower()
        if self.system_info == 'fronius_symo':
            self.power= self.fronius_symo_ACPower()
       # print("PV: ", self.power)
        return self.power


class Battery(MODBUS):
    def __init__(self, ip_address, port, unit_id):
        super().__init__(ip_address, port, unit_id)
        self.IP = ip_address
        self.PORT = port
        self.UNIT_ID = unit_id
        self.start_time = datetime.now()
        self.frozen_timer = 0   


    def battery_read_data(self):        
        self.battery_data = self.client.read_holding_registers(0,30,1).registers 
        
    def battery_read_ACPower(self):
        decoder     =  BinaryPayloadDecoder.fromRegisters(self.client.read_holding_registers(12, 3, 1).registers, byteorder=Endian.BIG, wordorder=Endian.LITTLE)       
        return sum(decoder.decode_16bit_int() for _ in range(3))

    def battery_read_actual_charge_setpoint(self):
        return self.battery_data[22]
    
    def battery_read_actual_discharge_setpoint(self):
        return self.battery_data[23]

    def battery_read_charge_setpoint(self):
        return self.battery_data[24]
    
    def battery_read_discharge_setpoint(self):
        return self.battery_data[25]
    
    def battery_read_soc(self):
        return self.battery_data[15]
    
    def battery_read_alarm_state(self):
        return self.battery_data[1]

    def battery_read_temperature(self):
        return self.battery_data[5]

    def battery_read_control_reg(self):
        return self.battery_data[26]
    def battery_current_control(self):
        control_modes = {0: 'Energymeter', 1: 'Wendeware', 2: 'Auto'} 
        return control_modes.get(self.battery_data[26], 'Unknown')  
    
    def battery_check_frozen(self):
        if self.battery_read_ACPower() > 1000 and self.battery_read_ACPower() > -100: 
            if self.frozen_timer == 0:
                self.frozen_timer = datetime.now() 
            if (self.frozen_timer - datetime.now()).days > 3:
                return 'Battery_frozen'
        else:
            self.frozen_timer = 0

    
    def battery_check_setpoint(self):        
        if  datetime.now().replace(minute=5) >= datetime.now(): 
            if self.battery_read_charge_setpoint() != self.battery_read_actual_charge_setpoint() or self.battery_read_discharge_setpoint() != self.battery_read_actual_discharge_setpoint():
                return 'Setpoint_error'
                


class Visblue_main():
    def __init__(self, site, project_nr,  bat_ip, em_ip, pv_ip, pv_info, em_info):
        self.site = site
        self.project_nr = project_nr
        self.em_conn = None
        self.pv_conn = None
        self.bat_conn = None

        self.em_power = None
        self.pv_power = None
        self.bat_power = None

        self.battery = Battery(bat_ip, 502, 1)
        self.energymeter = EnergyMeter(em_ip, 502, 1, em_info)        
        
        self.pv = PV(pv_ip, 502, 1, pv_info)
        self.data = {}

    def connect(self):
        self.em_conn    = self.energymeter.try_connect()
        self.pv_conn    = self.pv.try_connect()
        self.bat_conn   = self.battery.try_connect()
        self.data['Em_connection_status']       = self.em_conn
        self.data['Pv_connection_status']       = self.pv_conn
        self.data['Battery_connection_status']  = self.bat_conn

    def gather_battery_data(self):
        self.battery.battery_read_data()
        self.data['Battery_ACPower']                    = self.battery.battery_read_ACPower()
        self.data['Battery_Charge_Setpoint']            = self.battery.battery_read_charge_setpoint()
        self.data['Battery_Discharge_Setpoint']         = self.battery.battery_read_discharge_setpoint()
        self.data['Battery_State_of_Charge']            = self.battery.battery_read_soc()
        self.data['Battery_Alarm_State']                = self.battery.battery_read_alarm_state()
        self.data['Battery_Temperature']                = self.battery.battery_read_temperature()
        self.data['Battery_frozen']                     = self.battery.battery_check_frozen()
        self.data['Battery_Setpoint_error']             = self.battery.battery_check_setpoint()
        
        self.bat_power = self.battery.battery_read_ACPower()
        self.em_power = self.energymeter.em_read_power()
        self.pv_power = self.pv.pv_read_power()
        self.data['Energymeter_ACPower'] = self.em_power
        self.data['PV_ACPower']         = self.pv_power

       
    def calculate_consumption(self):
        consumption = None
        if self.em_conn and self.pv_conn :
            consumption= self.em_power - self.pv_power + self.bat_power
        else:
            return        
        self.data['Consumption'] = consumption
        
    def driftsikring(self):
        from Driftsikring import driftsikring
        data = driftsikring(float(self.project_nr))
        print(data.keys())
        self.data = self.data | data 

        print(self.data)
        

    def update_database_error_log(self):        
        self.__update_get_collections()   
       
        query = {   
                "Kunde": self.site,                           
                'ProjectNr':self.project_nr,
        }    
        update_data = {
            "$set": {
               "Kunde": self.site,
                "Em_connection_status": self.em_conn,
                "Pv_connection_status": self.pv_conn,
                "battery_connection_status": self.bat_conn,
                "battery_alarm_status": self.bat_alarm,                
                'ProjectNr':self.project_nr,
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }        
        }       
        db_current_data = self.col.find_one({},query)
        if db_current_data is None:
            self.add_new = True
        if self.col is not None:
           self.col.update_one(query, update_data, upsert = self.add_new)   

    def run(self):
       
        self.connect()   
        self.driftsikring()
        return
        self.gather_battery_data()
        self.calculate_consumption()


def background_threads():
        
   # site = 'Mollerup'
   # em_ip = "172.20.33.195"
   # pv_ip = "192.168.3.196"
   # pv_info = 'Fronius_Eco'
   # em_info = 'Carlo'
   # bat_ip = "172.20.33.12"
#
#
   # #site    = 'Gelsted'
   # #em_ip   = "172.20.32.56"
   # #pv_ip   = "172.20.32.58"
   # #bat_ip  = "172.20.32.54"
#
   # site_1 = Visblue_main("Mollerup", 10680,  bat_ip, em_ip, pv_ip, pv_info, em_info)
#
   # site_1.run()
    socket.emit('table', "site_1.data")


@socket.on("connect")
def connect():
    print("Client connected")
    global thread
    with thread_lock:
        if thread is None:
            thread = socket.start_background_task(background_threads)

    

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == "__main__":
   socket.run(app, debug=True)
   #http_server = WSGIServer(("0.0.0.0", 5000), app)
   #http_server.serve_forever()


"""
from time import sleep

site = 'Mollerup'
em_ip = "172.20.33.195"
pv_ip = "192.168.3.196"
pv_info = 'Fronius_Eco'
em_info = 'Carlo'
bat_ip = "172.20.33.12"


#site    = 'Gelsted'
#em_ip   = "172.20.32.56"
#pv_ip   = "172.20.32.58"
#bat_ip  = "172.20.32.54"

site_1 = Visblue_main("Mollerup", 10680,  bat_ip, em_ip, pv_ip, pv_info, em_info)

site_1.run()
print(site_1.data)

"""
