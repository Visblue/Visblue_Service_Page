from pymodbus.client import ModbusTcpClient 
from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian


def decode_int16( regs):
    return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.BIG).decode_16bit_int()
def decode_int32( regs):
    return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.LITTLE).decode_32bit_int()
def decode_float( regs):
    return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.LITTLE).decode_32bit_float()
"""
a = ModbusTcpClient("172.20.33.195")
#a = ModbusTcpClient("172.16.68.183")
a.connect()
regs = a.read_holding_registers(40, 2,1).registers
print(regs)
print(decode_int32(regs))


a.close()
"""

#Sites = {'Mollerup' : {'Battery_ip' : "127.1.1.26", 'Battery_port' : 502, 'Smartflow' : True, 'Energymeter_ip': "127.1.1.94", }}

import pymongo 

client = pymongo.MongoClient(f"mongodb://172.20.33.151:27017")

new_client = pymongo.MongoClient(f"mongodb://172.20.33.151:27018")
new_db = new_client['Customer_info']
import re
db = client['Site_information']
from Driftsikring import driftsikring
for i in db.list_collection_names():
#    print(i)
 #   if re.search('KEA'.lower(),i.lower()):
        name = i
        col = db.get_collection(name)
        data = col.find_one({},{"_id":0})
        #print(data)
        PLC_ip      = data['PLC']
        PLC_Port    = data.get('Port', 502)
        PLC_V       = data['BatVersion']
        EM_IP       = data['Grid_IP'][0]
        EM_Port     = data.get('Grid_Port'[0], 502)
        EM_type     = data['Grid_Type'][0]
        PV_IP       = data['PV_IP'][0]
        PV_Type     = data['PV_Type'][0]
        PV_port     = data.get('PV_Port'[0], 502)
        PV_unit_id  = data.get('PV_Slave'[0], 1) 
        #print(PV_unit_id)
        #break
        
        data = {name : {"Customer" : "" ,'Project_nr' : data.get('Projekt', 99999),  "Battery_ip" : PLC_ip, "Battery_port" : PLC_Port, "Battery_version" : PLC_V, "Em_ip" : EM_IP, "Em_port" : EM_Port, "Em_type" : EM_type, "Pv_ip" : PV_IP,  "Pv_port" : PV_port , "Pv_type" : PV_Type, "Pv_unit_id" :PV_unit_id}}
        new_col = new_db[name]
        new_col.insert_one(data)
#        print(data)
 #       break
        
    

