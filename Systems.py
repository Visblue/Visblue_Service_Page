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


import re

import pandas as pd

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




#DB_ERROR = MongoClient(f"mongodb://localhost:27017")
#DB_ERROR_UPDATE = DB_ERROR["TEST"]

DB_LOG = MongoClient(f"mongodb://172.20.33.163:27017")
DB_LOG_UPDATE = DB_LOG["Service_log"]

AlarmCodes = {0 : "OK",
              1 : "DiffPressure_Alarm",
              2 : "ElectrolyteTemp_Alarm",
              3 : "DiffPressure_Alarm, ElectrolyteTemp_Alarm",
              4 : "Leak_Alarm",
              5 : "Leak_Alarm, DiffPressure_Alarm",
              6 : "Leak_Alarm, ElectrolyteTemp_Alarm",
              7 : "Leak_Alarm, DiffPressure_Alarm, ElectrolyteTemp_Alarm ",
              8 : "Emergency stop",
              16 : "Tankpressure to high",
              32 : "ElectrolyteTankImbalance",
              64 : "Preesure_Alarm",
              128:  "IOboardComm_Alarm",
              }

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




def MYP(bat_connection, bat_power, EM_connection, EM_power,PV_connection, PV_power):        
    print("Bat: ", bat_connection, bat_power, " EM: ", EM_connection, EM_power, "  PV: ", PV_connection, PV_power)
    consumption = None
    if bat_connection is not None:
        if EM_connection != None or EM_power != False:
            if PV_connection != None or PV_power != False:  
                consumption = EM_power + abs(PV_power) + bat_power
                print("Consumption:", consumption)
                return consumption
    return consumption       
    p 
        

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




class ModbusConnection():
    def __init__(self, SITE, PROJECT_NR, IP, PORT):
        self.site_name = SITE            
        self.site_projetNr = PROJECT_NR     
        self.DATA = {}       
        if IP is None:
                return
        self.client = ModbusTcpClient(IP,PORT, timeout = 1)             

    def _update_connection_status(self, system ,status, timer, reset = None):
        self.DATA[f'{system}_connection_status'] = status                  
        if system.lower() == 'battery':                       
            self.__update_battery(status, timer, reset)
        if system.lower() == 'energymeter':                       
            self.__update_energymeter(status, timer, reset)
        if system.lower() == 'pv':     
            print("PV status updated")            
            self.__update_pv(status, timer, reset) 

    def __update_pv(self, status, timer, reset):
        self.pv_last_connection = status             
        if reset:
            self.pv_reconnection_timer = 0                        
        else:
            self.pv_reconnection_timer = timer

    def __update_energymeter(self, status, timer, reset):
        self.energymeter_last_connection = status             
        if reset:
            self.energymeter_reconnection_timer = 0                        
        else:
            self.energymeter_reconnection_timer = timer

    def __update_battery(self, status, timer, reset):
        self.battery_last_connection = status             
        if reset:
            self.battery_reconnection_timer = 0                        
        else:
            self.battery_reconnection_timer = timer              
    def _reconnection_reset_timer(self,system, last_connection, last_reconnection_timer):
        if last_connection == False and last_reconnection_timer >= 3:                       
            self._update_connection_status(system, True,0, True)
        
    def connect_to_modbus(self, system,  last_connection, last_reconnection_timer):      
    
        if last_connection == None or last_connection is True:
            try:                
                self.__check_modbus_connection(system)
            except Exception as e:   
                print("FAILED : Connection ", system)            
                last_reconnection_timer += 1
                self.client.close()
                self._update_connection_status(system,False, last_reconnection_timer)
               # self.update_db_error(system,'Connection_failed')                                           
        else:            
            last_reconnection_timer += 1
            self._update_connection_status(system,False, last_reconnection_timer)            
        self._reconnection_reset_timer(system, last_connection, last_reconnection_timer)

    def __check_modbus_connection(self, system):
        if not self.client.is_socket_open():
            self.client.connect()                

        self.client.read_holding_registers(0, 1, 1).registers
        self._update_connection_status(system,True, 0)
        #  self.update_db_error(system,'OK')
        self.client.close()
    def __update_get_collections(self):
            self.col = None
            self.add_new = False
            col_found = False
            for i in DB_ERROR_UPDATE.list_collection_names():          
                if re.search(i.lower(), self.site_name.lower()):
                    self.col = DB_ERROR_UPDATE[i]
                    col_found = True
                    break       
            if not col_found:
                self.col = DB_ERROR_UPDATE[self.site_name]            
                self.add_new = True

    def update_db_error(self, system,error):                               
        self.__update_get_collections()   
       
        query = {   
                "Kunde": self.site_name,                           
                'ProjectNr':self.site_projetNr,
        }    
        update_data = {
            "$set": {
               "Kunde": self.site_name,
                f"{system}_error":error,           
                'ProjectNr':self.site_projetNr,
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }        
        }       
        db_current_data = self.col.find_one({},query)
        if db_current_data is None:
            self.add_new = True
        if self.col is not None:
           self.col.update_one(query, update_data, upsert = self.add_new)        

class EnergyMeter(ModbusConnection ) :
    def __init__(self,site, projet_nr , IP, PORT, system_info):
        self.system_info = system_info
        self.energymeter_power_value = None
        self.energymeter_last_connection = None
        self.energymeter_reconnect_timer = 0
        
        super().__init__(site,projet_nr, IP, PORT)        
    
    def _energymeter_power_update(self : int):
        if self.system_info == 'Carlo':
            self.energymeter_power_value = int(decode_int32(self.client.read_holding_registers(40,2,1).registers)/10)            
        if self.system_info == 'Siemens':
            self.energymeter_power_value = decode_float(self.client.read_holding_registers(65,2,1).registers)
        if self.system_info == 'server':
            self.energymeter_power_value = decode_float(self.client.read_holding_registers(19026,2,1).registers)        
        self.DATA['Energymeter_Power'] = self.energymeter_power_value

    def run(self):
        self.connect_to_modbus('energymeter', self.energymeter_last_connection, self.energymeter_reconnect_timer)
        if self.energymeter_last_connection:            
            self._energymeter_power_update()        

class PV(ModbusConnection):
    def __init__(self, site, projet_nr, IP, PORT, system_info):
        self.system_info = system_info
        self.pv_power_value = None
        self.pv_last_connection = None
        self.pv_reconnect_timer = 0        
        super().__init__(site,projet_nr,  IP, PORT)
            
    def _pv_power_update(self : int):
        if self.system_info == 'Fronius_symo':
            self.pv_power_value = decode_float(self.client.read_holding_registers(40095,2,1).registers)
        if self.system_info == 'Fronius_eco':
            self.pv_power_value = decode_int16(self.client.read_holding_registers(40083,1,1).registers)
        if self.system_info == 'Siemens':
            self.pv_power_value = decode_float(self.client.read_holding_registers(65,2,1).registers)
        if self.system_info == 'Carlo':
            self.pv_power_value = decode_int32(self.client.read_holding_registers(0,3,1).registers)             
        self.DATA['PV_Power'] = self.pv_power_value

    def run(self):
        self.connect_to_modbus('pv', self.pv_last_connection, self.pv_reconnect_timer)
        if self.pv_last_connection:
            self.pv_power_info()
            self._pv_power_update()
            

class Battery(ModbusConnection):
    def __init__(self, site, projet_nr, IP = None, PORT = None):
        self.battery_last_connection = None        
        self.battery_reconnection_timer =  0    
        self.battery_error = None            
        super().__init__(site, projet_nr, IP, PORT)

    def battery_read_data(self):        
        self.battery_data = self.client.read_holding_registers(0,30,1).registers 
        self.DATA['Battery_charge_setpoint']        =  self.battery_data[24]
        self.DATA['Battery_discharge_setpoint']     =  self.battery_data[25]   
        self.battery_temperature                    =  self.battery_data[5] 
        self.DATA['Battery_Temperature']            = self.battery_temperature 
        self.DATA['Battery_SOC']                    = self.battery_data[15]
        self.battery_alarm_value                    = self.battery_data[1]
        #print("alarmstatus:" , self.battery_aarm_value)#
        decoder     =  BinaryPayloadDecoder.fromRegisters(self.client.read_holding_registers(12, 3, 1).registers, byteorder=Endian.BIG, wordorder=Endian.LITTLE)
        self.battery_power_value    =  sum(decoder.decode_16bit_int() for _ in range(3))
        self.DATA['Battery_Power']  = self.battery_power_value
    
    def _battery_check_temperature(self):
        if self.battery_temperature >= 40:
            self.DATA['Battery_Temperature_Alarm_State'] = True
    def battery_check_alarm_state(self):
        if self.battery_alarm_value == 1:
            self.DATA['Battery_Alarm_State'] = convertAlarmCode(self.battery_alarm_value)
            self._battery_check_temperature()
        else:
            self.DATA['Battery_Alarm_State'] =  AlarmCodes.get(self.battery_alarm_value, "Unknown")
            self._battery_check_temperature()
       
    def run(self):
     
        self.connect_to_modbus('battery'  ,self.battery_last_connection, self.battery_reconnection_timer)         
        #if self.battery_last_connection:
        self.battery_read_data()
        self.battery_check_alarm_state()
        #  
         #   print(self.DATA)
    

from time import sleep

site = 'Mollerup'
em_ip = "172.20.33.15"
pv_ip = "192.168.3.196"
bat_ip = "172.20.33.12"


#site    = 'Gelsted'
#em_ip   = "172.20.32.56"
#pv_ip   = "172.20.32.58"
#bat_ip  = "172.20.32.54"



bat = Battery(site, 10240, bat_ip, 502)
#em = EnergyMeter(site, 10240, em_ip, 502, 'Carlo')
#pv = PV(site, 10240, pv_ip, 502, 'Fronius_eco')
#em.run()
bat.run()
print(bat.DATA)
"""

#em.run()
#pv.run()

#print(consumption)
#bat.save_data(em,pv)


quit()



"""
