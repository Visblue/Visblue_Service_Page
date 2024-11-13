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

a = ModbusTcpClient("172.20.33.195")
#a = ModbusTcpClient("172.16.68.183")
a.connect()
regs = a.read_holding_registers(40, 2,1).registers
print(regs)
print(decode_int32(regs))


a.close()
