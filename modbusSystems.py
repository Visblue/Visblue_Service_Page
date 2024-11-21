from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from datetime import datetime 

Alarmkoder = {"0000000000000010 ": 'CPLD',
              "0000000000000100 ": 'DetectNoEM',
              "0000000000001000 ": 'BlockedStack',
              "0000000000010000 ": 'State Error',
              "0000000000100000 ": 'Tankpressurerelief',
              "0000000001000000 ": 'DataValid',
              "0000000010000000 ": 'OCVsensor',
              "0000000100000000 ": 'IOboardComm',
              "0000001000000000 ": 'Pressure',
              "0000010000000000 ": 'ElectrolyteTankimbalance',
              "0000100000000000 ": 'Tankpressure',
              "0001000000000000 ": 'Emergency stop',
              "0010000000000000 ": 'Leak_Alarm',
              "0100000000000000 ": 'ElectrolyteTemp',
              "1000000000000000 ": 'DiffPressure', }

def convertAlarmCode(Alarm_CODE):
    pos = []
    A = str(bin(Alarm_CODE)).replace("0b", "")

    for i in range(len(A)):
        if A[i] == "1":
            pos.append(i)

    res = None
    poss = 0
    for i, x in Alarmkoder.items():        
        for g in range(len(A)):
            if i[g] == A[len(A)-1-g] and i[g] != "0":
                if res == None:
                    res = x  # + ","
                else:
                    res += "," + x 
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
    def __init__(self,site,  ip, port, unit_id):
        
        self.IP = ip   
        self.PORT = port
        self.UNIT_ID = unit_id
        self.site = site


        try:
            self.client = ModbusTcpClient(host=ip,port=port,timeout=1.5)
        except Exception as e:
            print(f"Error initializing Modbus client: {e}") 
            raise
        #self.client = ModbusTcpClient(self.IP, self.PORT)
        
    

    def try_connect(self): 
        
        try:
            if not self.client.is_socket_open():
                self.client.connect()
            self.client.read_holding_registers(1,1,1).registers 
            self.client.close()
            return True
        except Exception as e:
            print(f"Failed : Connection {self.site}")
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
    
    def smartlogger_ACPower(self):
        return decode_float(self.client.read_holding_registers(20,2,self.UNIT_ID).registers)

class EnergyMeter_conn(MODBUS):
    def __init__(self, site,  ip_address, port, unit_id, system_info):   
        super().__init__(site,ip_address, port, unit_id)
        self.system_info = system_info.lower()  
        self.IP = ip_address
        self.PORT = port
        self.UNIT_ID = unit_id                                


    def em_read_power(self):
        try:
            self.power = None
            if self.system_info == "siemens":
                self.power =self.siemens_ACPower()
            if self.system_info == 'carlo':            
                self.power =self.carlo_ACPower()
            if self.system_info == 'server':
                self.power =self.server_ACPower()            
            return self.power
    
        except Exception as e:
            print(f"Error reading Energy Meter data: {e}")
            return "error"

  
class PV_conn(MODBUS):
    def __init__(self,site, ip_address, port, unit_id, system_info):
        super().__init__(site, ip_address, port, unit_id)
        self.system_info = system_info.lower()
        self.IP = ip_address
        self.PORT = port
        self.UNIT_ID = unit_id     

    
    def pv_read_power(self):
        try:
            print("PV systeminfo:", self.system_info)
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
            if self.system_info.lower() == 'smartlogger':
                self.power= self.smartlogger_ACPower()       
            return self.power
        except Exception as e:
            print(f"Error reading PV data: {e}")
            return "error"

class Battery_conn(MODBUS):
    def __init__(self, site,  ip, port, unit_id):
        super().__init__(site, ip,port,1)

        self.IP = ip
        self.PORT = port
        self.UNIT_ID = unit_id
        self.start_time = datetime.now()
        self.frozen_timer = 0   


    def battery_read_data(self):        
        try:
            self.battery_data = self.client.read_holding_registers(0,30,1).registers 
        except Exception as e:
            print(f"Error reading battery data: {e}")
            return "error"
        
    def battery_read_ACPower(self):
        try:
            decoder     =  BinaryPayloadDecoder.fromRegisters(self.client.read_holding_registers(12, 3, 1).registers, byteorder=Endian.BIG, wordorder=Endian.LITTLE)       
            return sum(decoder.decode_16bit_int() for _ in range(3))
        except Exception as e:
            print(f"Error reading battery ACPower: {e}")
            return "error"

    def battery_read_actual_charge_setpoint(self):
        return self.battery_data[22]
    
    def battery_read_actual_discharge_setpoint(self):
        return self.battery_data[23]
    
    def battery_read_battery_state(self):
        return self.battery_data[0]

    def battery_read_charge_setpoint(self):
        return int(self.battery_data[24])
    
    def battery_read_discharge_setpoint(self):
        return int(self.battery_data[25])
    
    def battery_read_soc(self):
        return int(self.battery_data[15])
    
    def battery_read_alarm_state(self):
        if self.battery_data[1] > 0:
            return convertAlarmCode(self.battery_data[1])
        return 0
        #return self.battery_data[1]

    def battery_read_temperature(self):
        return self.battery_data[5]

    def battery_read_control_reg(self):
        return self.battery_data[26]
    def battery_current_control(self):
        print("CONTROL: ", int(self.battery_read_control_reg()), self.IP, self.battery_read_ACPower())
        control_modes = {0: 'EM Control', 1: 'Smartflow', 2: 'Auto'} 
        return control_modes.get(int(self.battery_read_control_reg()), 'Unknown control')  
    
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
                
