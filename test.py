from pymodbus.client import ModbusTcpClient
from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian

import time
def decode(regs):
    return BinaryPayloadDecoder.fromRegisters(regs, wordorder=Endian.BIG, byteorder=Endian.BIG).decode_string(16)
def uint16(regs):
    return BinaryPayloadDecoder.fromRegisters(regs,  wordorder=Endian.LITTLE, byteorder=Endian.BIG).decode_16bit_int()

def int32(regs):
    return BinaryPayloadDecoder.fromRegisters(regs,  wordorder=Endian.BIG, byteorder=Endian.BIG).decode_32bit_float()
c = ModbusTcpClient("192.168.80.3")
#print(int32(c.read_holding_registers(40154,2,1).registers))
#print(int32(c.read_holding_registers(40093,2,2).registers))
#c.close()
#quit()
#a_1s = decode(c.read_holding_registers(40052,16,1).registers)
#a_1s = str(a_1s).replace("b'", "").split("\\")[0]
#print("-->: ", a_1s)

#c.close()
#a = #
#quit()

t1=  time.time()
a_1 = int32(c.read_holding_registers(40153,2,1).registers)
a_2 = int32(c.read_holding_registers(40153,2,2).registers)
a_3 = int32(c.read_holding_registers(40153,2,3).registers)
a_4 = int32(c.read_holding_registers(40153,2,4).registers)
a_5 = int32(c.read_holding_registers(40153,2,5).registers)
a_6 = int32(c.read_holding_registers(40153,2,6).registers)
a_7 = int32(c.read_holding_registers(40153,2,7).registers)
a_8 = int32(c.read_holding_registers(40153,2,8).registers)
a_9 = int32(c.read_holding_registers(40153,2,9).registers)

a_1s =str( decode(c.read_holding_registers(40052,16,1).registers)).replace("b'", "").split("\\")[0]
a_2s =str( decode(c.read_holding_registers(40052,16,2).registers)).replace("b'", "").split("\\")[0]
a_3s =str( decode(c.read_holding_registers(40052,16,3).registers)).replace("b'", "").split("\\")[0]
a_4s =str( decode(c.read_holding_registers(40052,16,4).registers)).replace("b'", "").split("\\")[0]
a_5s =str( decode(c.read_holding_registers(40052,16,5).registers)).replace("b'", "").split("\\")[0]
a_6s =str( decode(c.read_holding_registers(40052,16,6).registers)).replace("b'", "").split("\\")[0]
a_7s =str( decode(c.read_holding_registers(40052,16,7).registers)).replace("b'", "").split("\\")[0]
a_8s =str( decode(c.read_holding_registers(40052,16,8).registers)).replace("b'", "").split("\\")[0]
a_9s =str( decode(c.read_holding_registers(40052,16,9).registers)).replace("b'", "").split("\\")[0]
print("Serial Number:" ,a_1s , " - ", a_1 , " Wh")
print("Serial Number:" ,a_2s , " - ", a_2 , " Wh")
print("Serial Number:" ,a_3s , " - ", a_3 , " Wh")
print("Serial Number:" ,a_4s , " - ", a_4 , " Wh")
print("Serial Number:" ,a_5s , " - ", a_5 , " Wh")
print("Serial Number:" ,a_6s , " - ", a_6 , " Wh")
print("Serial Number:" ,a_7s , " - ", a_7 , " Wh")
print("Serial Number:" ,a_8s , " - ", a_8 , " Wh") 
print("Serial Number:" ,a_9s , " - ", a_9 , " Wh")
print("total: ", int(int(a_1+a_2+a_3+a_4+a_5+a_6+a_7+a_8+a_9)/9)/1000)
print(time.time()-t1)
c.close()
