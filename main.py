from flask import Flask, render_template, request, render_template_string, jsonify
from flask_socketio import SocketIO
from pymodbus.client import ModbusTcpClient 
from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from gevent.pywsgi import WSGIServer
import pymongo
import numpy as np
from dbMongo import database
import os
import time
import threading
from multiprocessing import Process
from datetime import datetime, timedelta
from TotalList import Customers, names, AlarmCodes, BatteryStatesCodes, NewAlarmCodes
import re
from EnerginetServcePage import Elprices
import pandas as pd


app = Flask(__name__)
socket = SocketIO(app)

db_VisblueService = "VisblueService"
db_VisblusSiteLog = "VisblueLog"
db_MypowergridTimer = 'ServicePageTimer'

plc_connection_status = {}

grid_connection_status = {}
pv_connection_status = {}

Time2Set = -1
t1 = None
thread = None
thread_lock = threading.Lock()
counter = 0
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


SitesWithMoreBats = {'Kattegatcentret_2': "127.1.1.81",
                     'Kattegatcentret_1': "127.1.1.80",
                     'Vigersted_2': "127.1.1.55",
                     'Vigersted_1': "127.1.1.54",
                     "Varlose Svommehal_1": "",
                     "Varlose Svommehal_2": "",
                     "Varlose Svommehal_3": "",
                     "Varlose Svommehal_4": "",
                     "Solvangskolen_1": "",
                     "Solvangskolen_2": "",
                     "Solvangskolen_3": "",


                     }

kunde_info = {}

PVDataForMoreSites = {}
GridDataForMoreSites = {}

MypowerGridChk = 0
oldData = {}


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


MypowergridTimer = database()
MypowergridTimer.dbEnter('ServicePage_Mypowergrid_Timer')

reconnectTimer = 10

battery_mb_list = {}
get_driftsikring_projects_names = [None]
get_driftsikring_da = [None]

client = pymongo.MongoClient(f"mongodb://172.20.33.151:27017")
db_client = client["SiteErrorLog"]


# reconnect variables.
gridReconnectTimer = 5
batteryReconnectTimer = 3
PVReconnectTimer = 5


class datahandler(Process):
    t1 = 0

    def __init__(self, Kunde, ip, port, KundeData):
        global system_status
        Process.__init__(self)
        self.plc_client = ModbusTcpClient(ip, port, )
        self.plc_ip = ip

        self.Kunde = Kunde
        self.battery_ReconnectCounter = 0
        self.battery_lastConnection = None
        self.battery_status = None
        self.battery_last_status = None
        self.battery_offline_counter = None
        self.status_timer = None
        self.retry_counter = 5

        self.battery_power_frozen = None

        self.battery_alarm_detected_time = None
        self.battery_connectionIssue_detected_time = None
        self.pv_alarm_detected_time = None
        self.grid_alarm_detected_time = None
        self.system_offline_detected_time = None
        self.grid_ReconnectCounter = 0
        self.grid_lastConnection = None
        self.grid_last_status = None
        self.pv_ReconnectCounter = 0
        self.pv_lastConnection = None
        self.pv_last_status = None
        self.pv_status = None
        self.kunde_data = KundeData
        self.lastCheckForPlan = 0
        self.lastCheckForNote = 0
        self.data_to_site = {
            "ProjektNr": KundeData["Projekt"],
            "Kunde": self.Kunde,
            "battery_connection": [""],
            "battery_status": [""],
            "battery_power": [""],
            "battery_soc": [""],
            "battery_temp": [""],
            'battery_offline_counter': self.battery_offline_counter,
            "battery_control": [""],
            'status_timer': self.status_timer,
            'grid_connection': [""],
            'grid_status': [""],
            'grid_power': [""],
            'battery_alarm_detected': "",
            'battery_notCharging': 0,
            'pv_alarm_detected': "",
            'grid_alarm_detected': "",
            'system_offline_detected': "",
            'pv_connection': [""],
            'pv_status': [""],
            'pv_power': [""],
            'total_consumption': [""],
            "tarifstyring_version": KundeData["TarifstyringVersion"],
            "drift": "",
            "sa": "",
            "lokation": KundeData["Lokation"],
            "google": KundeData["google"],
            "kunde_site": KundeData["Page"],
            "deadline": KundeData["Deadline"],
            'plan': {},
            'note': {},
            "prioritet": "",
            "days_left" : "",
        }
        self.offline_data_to_site = {
            "ProjektNr": KundeData["Projekt"],
            "Kunde": self.Kunde,
            "battery_connection": [""],
            "battery_status": [""],
            "battery_power": [""],
            "battery_soc": [""],
            "battery_temp": [""],
            'battery_offline_counter': self.battery_offline_counter,
            'status_timer': self.status_timer,
            'grid_connection': [""],
            'grid_status': [""],
            'grid_power': [""],
            'pv_connection': [""],
            'battery_alarm_detected': "",
            'pv_alarm_detected': "",
            'grid_alarm_detected': "",
            'system_offline_detected': "",
            'pv_status': [""],
            'pv_power': [""],
            'total_consumption': [""],
            "tarifstyring_version": KundeData["TarifstyringVersion"],
            "drift": "",
            "sa": "",
            "lokation": KundeData["Lokation"],
            "google": KundeData["google"],
            "kunde_site": KundeData["Page"],
            "deadline": KundeData["Deadline"],
            'plan': {},
            'note': {},
            "prioritet": "",
            "days_left" : "",
        }

    def check_control(self):
        # 0 = EM, 1 = Tarif, 2 = AUTO
        control = ""
        control_reg = self.plc_client.read_holding_registers(
            30, 1, 1).registers
        if control_reg == 0:
            control = "EM control"
        elif control_reg == 1:
            control = 'Wendeware control'
        else:
            control = 'Auto'
        self.data_to_site.update({'battery_control': control})

    #def battery_insert_or_update_db_error(self):
    #    from datetime import datetime


    def battery_insert_or_update_db_error(self):
        
        """
        global db_client
        col = db_client[self.Kunde]

        # Definer 5-dages grnsen
        five_days_ago = datetime.now() - timedelta(days=5)

        # Slet dokumenter ldre end 5 dage baseret p 'time' eller 'time_lst'
        col.delete_many({
            "$or": [
                {"time": {"$lt": five_days_ago.strftime("%d-%m-%Y %H:%M")}},
                {"time_lst": {"$lt": five_days_ago.strftime("%d-%m-%Y %H:%M")}}
            ]
        })

        if self.BatteryAlarmData > 0:
            localtime = datetime.today().strftime("%d-%m-%Y %H:%M")

            # Find det nyeste dokument baseret p 'time' (fejl der allerede eksisterer)
            latest_record = col.find_one({}, {'time': 1}, sort=[('time', -1)])

            if latest_record and latest_record.get('time'):
                self.data_to_site.update({"battery_alarm_detected": latest_record['time']})
            else:
                self.data_to_site.update({"battery_alarm_detected": ""})

            # Opret ny post for batterifejl (uden opdatering af eksisterende)
            new_entry = {
                "Kunde": self.Kunde,
                "ProjektNr": self.kunde_data['Projekt'],
                "error": self.data_to_site['battery_status'],
                "time": localtime,
                "last_update": localtime
            }

            col.insert_one(new_entry)

        else:
            try:
                # Hvis fejlen er lst, registrer tidspunktet for lsningen
                localtime = datetime.today().strftime("%d-%m-%Y %H:%M")
                solution_entry = {
                    "Kunde": self.Kunde,
                    "ProjektNr": self.kunde_data['Projekt'],
                    "time_lst": localtime,  # Tidspunkt for, hvornr fejlen blev lst
                    "last_update": localtime
                }

                col.insert_one(solution_entry)
            except:
                pass

    
        """    
        global db_client
        col = db_client[self.Kunde]

        if self.BatteryAlarmData > 0:

            localtime = datetime.today().strftime("%d-%m-%Y %H:%M")
           # col = db_client[self.Kunde]

            for i in col.find({}, {'time': 1}):
                if i.get('time'):
                    self.data_to_site.update(
                        {"battery_alarm_detected": i['time']})
                    break
            else:
                self.data_to_site.update({"battery_alarm_detected": ""})

            query = {
                "Kunde": self.Kunde,
                "ProjektNr": self.kunde_data['Projekt'],
                "error": self.data_to_site['battery_status'],
            }

            update_data = {
                "$set": {
                    "Kunde": self.Kunde,
                    'ProjektNr': self.kunde_data['Projekt'],
                    "error": self.data_to_site['battery_status'],
                    "last_update": localtime

                }
            }
        
           
            existing_document = col.find_one(query)
            if existing_document is None:
                update_data["$set"]["time"] = localtime
            else:
                if self.data_to_site['battery_status'] == "OK":
                    last_update_time = datetime.strptime(existing_document['time'], "%d-%m-%Y %H:%M")
                    if datetime.now() - last_update_time > timedelta(minutes=1):
                        col.delete_one(query)
                    else:
                        update_data["$set"]["time"] = localtime
            col.update_one(query, update_data, upsert=True)
        else:
            try:
                # for i in col.find({},{'error':1}):
                # if i['error'] == 'OK':
                dataLength = col.estimated_document_count() - 1

                if dataLength < 0:
                    pass
                else:

                    col.drop()
            except:
                pass
  

    def battery_connect(self):
        """
        try:
            # Start batteritimer
            self.battery_chk_timer()

            # Kontrollr, om vi skal forsge en ny forbindelse baseret p rekonstruktionstller
            if not self.battery_lastConnection and self.battery_ReconnectCounter == batteryReconnectTimer:
                self.battery_lastConnection = True

            # Hvis der allerede er forbindelse eller vi prver frste gang
            if self.battery_lastConnection or self.battery_lastConnection is None:
                try:
                    # Kontroller om PLC-klienten stadig er aktiv
                    if not self.plc_client.is_active():
                        self.plc_client.connect()

                    # Test forbindelse ved at lse registrer
                    self.plc_client.read_holding_registers(0, 1, 1).registers
                    self.data_to_site['battery_connection'] = True
                    self.battery_lastConnection = True

                except Exception as e:
                    print(f"Bat_error - {self.Kunde}: {e}")
                    # Luk klienten hvis der opstod en fejl og marker forbindelsen som tabt
                    self.plc_client.close()
                    self.data_to_site['battery_connection'] = False
                    self.battery_lastConnection = False
            else:
                # Hvis der ikke er forbindelse, opdater forbindelsesstatus og g tlleren
                self.data_to_site.update({'battery_connection': False})
                self.battery_ReconnectCounter += 1

        except Exception as e:
            print(f"battery_connect error {self.Kunde}: {e}")

    """     
        global batteryReconnectTimer
        try:
            global reconnectTimer
            self.battery_chk_timer()
            if self.battery_lastConnection == False and self.battery_ReconnectCounter == batteryReconnectTimer:
                self.battery_lastConnection = True
            if self.battery_lastConnection or self.battery_lastConnection is None:
                try:
                    socket_open = self.plc_client.is_active()
                    if not socket_open:
                        self.plc_client.connect()

                    self.plc_client.read_holding_registers(0, 1, 1).registers
                    self.data_to_site['battery_connection'] = True                   
                    self.battery_lastConnection = True
                except Exception as e:
                    print("Bat_error - ", self.Kunde, ": ", e)

                    self.plc_client.close()
                    self.data_to_site['battery_connection'] = False
                    self.battery_lastConnection = False
            else:
                self.data_to_site.update({'battery_connection': False})
                self.battery_ReconnectCounter += 1
        except Exception as e:
            print("battery_connect error ", self.Kunde, ": ", e)

    def battery_chk_timer(self):
        if self.battery_ReconnectCounter == reconnectTimer:
            self.battery_lastConnection = True
            self.battery_ReconnectCounter = 0

    def battery_power_not_changing(self):
        timer = 0

        if self.battery_power_frozen is None and 0 < abs(self.battery_power) < 1000:
            # Hvis self.battery_power_frozen ikke er sat, så sæt den til den nuværende tid
            self.battery_power_frozen = time.time()
            return

        if self.battery_power_frozen is not None:
            # Beregn tiden der er gået
            timer = int(round(time.time() - self.battery_power_frozen))

            # Tjek om timeren er indenfor et rimeligt interval, nulstil hvis for lang tid
            if timer > 122132:  # Bruges kun pga time.time() laver en under stor tal når det startes forste gang.
                timer = 0

            # Hvis 480 minutter (8 timer) er gået, opdater data
            if timer // 60 == 480:
                self.data_to_site.update({'battery_notCharging': timer // 60})
        else:
            self.battery_power_frozen = None

        """timer = 0
        if self.battery_power_frozen == None and abs(self.battery_power) > 0 and abs(self.battery_power) < 1000:
            if self.battery_power_frozen == None:
                self.battery_power_frozen = time.time()
                return
            else:
                timer = int(round(self.battery_power_frozen - time.time()))

                if timer > 122132:
                    timer = 0
                if (timer/60) == 480:
                    self.data_to_site.update(
                        {'battery_notCharging': (timer/60)})
        else:
            self.battery_power_frozen = None"""

    def battery_read_data(self):
        try:
            self.plcdata = self.plc_client.read_holding_registers(
                0, 31, 1).registers
            self.ChargeSetpointData = self.plcdata[24]
            self.DischargeSetpointData = self.plcdata[25]
            self.ActChargeSetpointData = self.plcdata[24]
            self.ActDischargeSetpointData = self.plcdata[25]
            self.SOCData = self.plcdata[15]
            self.BatteryStateData = self.plcdata[0]
            self.BatteryAlarmData = self.plcdata[1]
            self.BatTempData = self.plcdata[5]
            decoder = BinaryPayloadDecoder.fromRegisters(self.plc_client.read_holding_registers(
                12, 3, 1).registers, byteorder=Endian.BIG, wordorder=Endian.LITTLE)
            self.battery_power = sum(decoder.decode_16bit_int()
                                     for _ in range(3))
            self.data_to_site.update({'battery_power': self.battery_power, 'battery_soc': self.SOCData,
                                     'battery_temp': self.BatTempData, 'battery_temp': self.BatTempData})
        except Exception as e:
            print("battery_read_data error ", self.Kunde, ": ", e)
        return True

    def get_driftsikring_data(self, offline=False):  
        try:     
            sti = "/volume1/homes/admin/Downloads/"
            if os.getcwd() != sti:
                os.chdir(sti)
            for i in os.listdir():
                csv = open(i, "r")
                data = pd.read_csv(csv)
                csv.close()
            get_driftsikring_projects_nr    = data['Nr.']
            get_driftsikring_da             = data['DA nr. ']            
            get_driftsikring_sa             = data['SA nr.']
            get_driftsikring_prioritet      = data['Prioritet']
            get_driftsikring_signed         = data['Signed']
        except Exception as e:
            print("Something went wrong with getting CSV DA ", e)
        try:
            for i in range(len(get_driftsikring_projects_nr)):
                if get_driftsikring_projects_nr[i] == float(self.kunde_data['Projekt']):
                    
                    # Beregn nedtællingen til signed-datoen
                    signed_date_str = get_driftsikring_signed[i].split(' ')[0]
                    signed_date = datetime.strptime(signed_date_str, "%Y-%m-%d")
                    today = datetime.today()
                    days_left = (signed_date - today).days
                    
                    
                    if offline:
                        if int(get_driftsikring_prioritet[i]): # Tilføj data til offline_data_to_site
                            self.offline_data_to_site.update({'prioritet': get_driftsikring_prioritet[i]})
                            self.offline_data_to_site.update({'drift': get_driftsikring_da[i][0:6] if str(
                                get_driftsikring_da[i][0:6]).isalnum() else ""})
                            self.offline_data_to_site.update({'sa': get_driftsikring_sa[i][0:6] if str(
                                get_driftsikring_sa[i][0:6]).isalnum() else ""})
                            self.offline_data_to_site.update({'deadline': signed_date_str})
                            self.offline_data_to_site.update({'days_left': days_left})
                    else:
                        if int(get_driftsikring_prioritet[i]): # Tilføj data til data_to_site
                            self.data_to_site.update({'prioritet': get_driftsikring_prioritet[i]})
                        self.data_to_site.update({'drift': get_driftsikring_da[i][0:6] if str(
                            get_driftsikring_da[i][0:6]).isalnum() else ""})
                        self.data_to_site.update({'sa': get_driftsikring_sa[i][0:6] if str(
                            get_driftsikring_sa[i][0:6]).isalnum() else ""})
                        self.data_to_site.update({'deadline': signed_date_str})
                        self.data_to_site.update({'days_left': days_left})
                    break            

        except Exception as e:
            self.data_to_site.update({'drift': ""})
            self.data_to_site.update({'days_left': ""})

    def battery_alarm_status(self):
        try:
            alarm = None
            # Hvis battery er visflow 10
            if self.kunde_data['SW'] == 1:
                alarm = convertAlarmCode(int(self.BatteryAlarmData))
            else:
                # hvis battery er visflow 8
                alarm = AlarmCodes.get(int(self.BatteryAlarmData))
                if alarm == None:
                    alarm = "Unknown code"
            self.data_to_site.update({'battery_status': alarm})
        except Exception as e:
            print("battery_alarm_status error ", self.Kunde, ": ", e)

        self.battery_insert_or_update_db_error()
       # print("ALARM: ", self.data_to_site['battery_alarm_detected'])
        # self.insert_or_update_db_error(system="Battery")

    def chkSetpoint(self):
        local_time = datetime.today()
        if local_time.minute < 5:
            self.data_to_site['ActSetpoint'] = 'Waiting'
            return
        charge_diff = self.ActChargeSetpoint - self.BatPower
        discharge_diff = self.ActDischargeSetpoint - abs(self.BatPower)
        if 0 <= charge_diff <= 100:
            self.data_to_site['ActSetpoint'] = 'OK'
        elif 0 <= discharge_diff <= 100:
            self.data_to_site['ActSetpoint'] = 'OK'
        else:
            self.data_to_site['ActSetpoint'] = 'Error'

    def system_offline(self):
        self.offline_data_to_site.update(
            {'battery_status': 'Offline', 'grid_status': '', 'pv_status': "", 'system_offline_detected': ""})
        socket.emit("table", self.offline_data_to_site)

    def _decode_Uint16(self, regs):
        return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.BIG).decode_16bit_uint()

    def _decode_int16(self, regs):
        return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.BIG).decode_16bit_int()

    def _decode_int32(self, regs):
        return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.BIG).decode_32bit_int()

    def _decode_Carlo(self, regs):
        return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.LITTLE).decode_32bit_int()

    def _decode_float(self, regs):
        return BinaryPayloadDecoder.fromRegisters(regs, byteorder=Endian.BIG, wordorder=Endian.BIG).decode_32bit_float()

    def insert_or_update_db_error(self, system):
        systemTimer = None
        systemStatus = ""
        lastStatus = None
        active = None

        if system == 'PV':
            systemTimer = "pv_alarm_detected"
            systemStatus = "pv_status"
            lastStatus = self.pv_lastConnection

        if system == 'Grid':
            systemTimer = "grid_alarm_detected"
            systemStatus = "grid_status"
            lastStatus = self.grid_lastConnection

        if system == 'Battery':
            systemTimer = "battery_alarm_detected"
            systemStatus = "battery_status"
            lastStatus = self.battery_lastConnection

        global db_client
        if system == 'Battery':
            col = db_client[self.Kunde]
        else:
            col = db_client[self.Kunde+f"_{system}"]

        if lastStatus == False:

            localtime = datetime.today().strftime("%d-%m-%Y %H:%M")
            for i in col.find({}, {'time': 1}):
                if i.get('time'):
                    self.data_to_site.update({systemTimer: i['time']})
                    break
            else:
                self.data_to_site.update({systemTimer: ""})

            query = {"Kunde": self.Kunde,
                     'ProjektNr': self.kunde_data['Projekt'],  "error": self.data_to_site[systemStatus], }

            update_data = {"$set": {
                "Kunde": self.Kunde, 'ProjektNr': self.kunde_data['Projekt'],   "error": self.data_to_site[systemStatus], "last_update": localtime}}

            existing_document = col.find_one(query)
            if existing_document is None:
                update_data["$set"]["time"] = localtime
            else:
                if self.data_to_site[systemStatus] == "OK":
                    last_update_time = datetime.strptime(
                        existing_document['time'], "%d-%m-%Y %H:%M")
                    if datetime.now() - last_update_time > timedelta(minutes=1):
                        col.delete_one(query)
                    else:
                        update_data["$set"]["time"] = localtime

            col.update_one(query, update_data, upsert=True)
        else:
            try:
                dataLength = col.estimated_document_count() - 1
                if dataLength < 0:
                    pass
                else:
                    col.drop()
            except:
                pass

    def pv_main(self):
        global PVReconnectTimer
        # getting pv data
       # print("PV: ", self.pv_ReconnectCounter, self.pv_lastConnection, PVReconnectTimer)
        try:
            self.__pv_kunde_data()
            if self.pv_ip[0] == 'DCC':
                self.data_to_site.update({'pv_status': 'OK'})
                self.data_to_site.update({'pv_alarm_detected': ""})
                return

            if self.pv_ip[0] == None or self.pv_ip[0] == "":
                if int(self.kunde_data['Projekt'] == 10490):
                    self.data_to_site.update({'pv_status': 'OK'})

                    return
                self.data_to_site.update({'pv_status': 'Data_missing'})
                return
            if self.pv_lastConnection == False and self.pv_ReconnectCounter == PVReconnectTimer:
                self.pv_lastConnection = True
                # PVReconnectTimer += 5
                # if PVReconnectTimer >= 30:
                #    PVReconnectTimer = 30

            if self.pv_lastConnection == None or self.pv_lastConnection:

                for i in range(len(self.pv_ip)):
                    port = self.pv_port[i] if self.pv_port[i] else self.default_port
                    unit_id = self.pv_unit_id[i] if self.pv_unit_id[i] else self.default_unit_id
                    try:
                        self.pv_client = ModbusTcpClient(self.pv_ip[i], port)

                        if self.pv_client.connect():
                            self.__pv_read_data(self.pv_type[i], unit_id)
                            self.pv_client.close()
                            self.pv_last_status = 'OK'
                            self.pv_lastConnection = True
                            # print("PV Power: ", self.pv_power)
                            self.data_to_site['pv_status'] = self.pv_last_status
                            # self.PV_insert_or_update_db_error()
                            self.insert_or_update_db_error(system="PV")
                            self.pv_ReconnectCounter = 0
                            

                        else:
                            self.pv_client.close()
                            self.pv_lastConnection = False
                            self.pv_last_status = "Connection_error"
                            self.data_to_site['pv_status'] = self.pv_last_status

                            self.data_to_site.update(
                                {'pv_alarm_detected': self.pv_alarm_detected_time})
                            # self.PV_insert_or_update_db_error()
                            self.insert_or_update_db_error(system="PV")
                            return

                    except Exception as e:
                        print("PV_error - ", self.Kunde, ":", e)
                        self.pv_client.close()
                        self.pv_lastConnection = False
                        self.pv_last_status = "Connection_error"
                        self.data_to_site.update(
                            {'pv_status': self.pv_last_status})
                       # self.PV_insert_or_update_db_error()
                        self.insert_or_update_db_error(system="PV")
            else:
                # if connection not ok - get last status and count
                # self.data_to_site.update({'pv_alarm_detected': self.pv_alarm_detected_time})
                self.data_to_site['pv_status'] = self.pv_last_status
                self.pv_ReconnectCounter += 1
        except Exception as e:
            print("PV_main error ", self.Kunde, ": ", e)
    # self.PV_insert_or_update_db_error()

    def __pv_kunde_data(self):
        self.pv_port = self.kunde_data['PV_Port']
        self.pv_type = self.kunde_data['PV_Type']
        self.pv_ip = self.kunde_data['PV_IP']
        self.pv_unit_id = self.kunde_data['PV_Slave']
        self.default_port = 502
        self.default_unit_id = 1
        self.pv_power = 0

    def __pv_read_data(self, pv_type, unitid):
        unitid = int(unitid)
        if pv_type.strip() == 'Carlo':
            self.pv_power = self._decode_Carlo(
                self.pv_client.read_holding_registers(41-1, 2, unitid).registers)/10
        if pv_type.strip() == 'Siemens':
            self.pv_power += int(self._decode_float(
                self.pv_client.read_holding_registers(65, 2, unitid).registers))
        if pv_type.strip() == 'Nas':
            if self.Kunde == 'Kongerslev Skole_1':
                # print("Here kongerrslev - ", self.pv_client.read_holding_registers(19026, 2, unitid).registers)
                self.pv_power += int(self._decode_float(
                    self.pv_client.read_holding_registers(19026, 2, unitid).registers))
        if pv_type.strip() == 'Smartlogger':
            self.pv_power += int(self._decode_int32(
                self.pv_client.read_holding_registers(20, 2, 1).registers))

        if pv_type.strip() == 'Fronius':
            self.pv_power += int(self._decode_float(
                self.pv_client.read_holding_registers(40095, 2, unitid).registers))
        self.pv_power = abs(self.pv_power)

    def grid_get_kunde_data(self):
        self.grid_port = self.kunde_data['Grid_Port']
        self.grid_ip = self.kunde_data['Grid_IP']
        self.grid_date_type = self.kunde_data['Grid_Type']
        self.grid_power = 0

    def grid_read_data(self, grid_date_type):
        if grid_date_type.strip() == 'Carlo':

            # else:
            self.grid_power += self._decode_Carlo(
                self.grid_client.read_holding_registers(41-1, 2, 1).registers)/10
        if grid_date_type.strip().lower() == 'Siemens'.lower():

            if re.search('Vigersted'.lower(), self.Kunde.lower()):
                # print("HERE")
                self.grid_power += int(self._decode_float(
                    self.grid_client.read_holding_registers(19026, 2, 1).registers))
                # print("GRID: ", self.grid_power, self.grid_client.read_holding_registers(19026, 2, 1).registers, self.Kunde)
                return
            if re.search('KIE'.lower(), self.Kunde.lower()):
                # print("HERE")
                self.grid_power += int(self._decode_float(self.grid_client.read_holding_registers(10, 2, 1).registers))                
            if self.Kunde == 'KEA_1':
                self.grid_power = int(self._decode_float(
                    self.grid_client.read_holding_registers(19026, 2, 1).registers))
                return

            self.grid_power = int(self._decode_float(
                self.grid_client.read_holding_registers(65, 2, 1).registers))

    def grid_main(self):
        global gridReconnectTimer   
        try:
            self.grid_get_kunde_data()
            #print(self.Kunde) 
            if str(self.grid_ip[0]).strip().lower() == 'DCC'.lower():
                self.data_to_site.update({'grid_status': 'OK'})
                self.data_to_site.update({'grid_alarm_detected': ""})
                return

            if self.grid_lastConnection == False and self.grid_ReconnectCounter == gridReconnectTimer:
                # gridReconnectTimer += 5
                # p#rint("HERE ", gridReconnectTimer)
                self.grid_lastConnection = True
                # if gridReconnectTimer >= 30:
                #   gridReconnectTimer = 30

            if self.grid_ip[0] == None or self.grid_ip[0] == "":
                self.data_to_site.update({'grid_status': 'Data_missing'})
                return

            if self.grid_lastConnection or self.grid_lastConnection == None:

                try:
                    for i in range(len(self.grid_ip)):
                        port = self.grid_port[0] if self.grid_port[0] else 502
                        self.grid_client = ModbusTcpClient(
                            self.grid_ip[i], port)
                        if self.grid_client.connect():

                            self.grid_read_data(self.grid_date_type[i])
                            self.grid_client.close()
                            self.grid_lastConnection = True

                            self.data_to_site['grid_status'] = "OK"
                            # self.Grid_insert_or_update_db_error()
                            self.insert_or_update_db_error(system="Grid")
                            self.grid_ReconnectCounter = 0

                        else:
                            self.grid_client.close()

                            self.grid_lastConnection = False
                            self.grid_last_status = 'Connection_error'
                            self.data_to_site['grid_status'] = self.grid_last_status
                            # self.Grid_insert_or_update_db_error()
                            self.insert_or_update_db_error(system="Grid")
                            return

                except Exception as e:
                    print("Grid_error - ", self.Kunde, ":", e)
                    self.grid_client.close()
                    self.grid_lastConnection = False
                    self.grid_last_status = "Connection_error"
                    self.data_to_site.update(
                        {'grid_status':  self.grid_last_status})

                    # self.Grid_insert_or_update_db_error()
                    self.insert_or_update_db_error(system="Grid")

            else:

                self.data_to_site.update(
                    {'grid_status': self.grid_last_status})

                self.grid_ReconnectCounter += 1
        except Exception as e:
            print("grid_main error ", self.Kunde, ": ", e)      

    def consumption_chk(self):
        if self.pv_lastConnection and self.grid_lastConnection:
            # if re.search('Vigersted'.lower(), self.Kunde.lower()):
            #  self.grid_power = -self.grid_power
            # print("GRID: ", self.grid_power)
            self.consumption = self.grid_power + \
                abs(self.pv_power) - self.battery_power
           # print(self.consumption)

            if self.consumption < 0:
                self.data_to_site.update(
                    {'total_consumption': 'ConsumptionError'})
                return
            self.data_to_site.update({'total_consumption': 'OK'})
        else:
            self.data_to_site.update({'total_consumption': 'OK'})

    def Elpriser(self):
        if re.search('Vacha', self.Kunde) or re.search('Te', self.Kunde) or re.search('Varensdorf', self.Kunde) or re.search('Ter Steege_1', self.Kunde):
            self.data_to_site.update({"Elpriser": "-"})
            return
        try:
            TodayPrices = Elprices(self.Kunde)
            try:
                if TodayPrices == 0 or TodayPrices == None:
                    self.data_to_site.update({"Elpriser": "-"})
            except Exception as e:
                self.data_to_site.update(
                    {"Elpriser": TodayPrices['Buy_Price [kW]'].iloc[-1]})
        except:
            self.data_to_site.update({"Elpriser": ""})

    def check_for_plan(self):
        global ServiceDb
        try:
            ServiceDb.colEnter(self.Kunde)  # msg['name'])
            date, sname, note = ServiceDb.read()
            
            self.data_to_site.update(
                {"plan": {"site": self.Kunde, "date": date, "sName": sname, "note": note}})
            self.offline_data_to_site.update(
                {"plan": {"site": self.Kunde, "date": date, "sName": sname, "note": note}})
        except Exception as e:
            print("chkForPlan: ", e)
            pass

    def check_for_notes(self):
        global ActionLog
        try:
            ActionLog.colEnter(self.Kunde.lower())
            data = ActionLog.readAll()
            self.offline_data_to_site.update(
                {"note": {"site": self.Kunde, "note": data['note']}})
            self.data_to_site.update(
                {"note": {"site": self.Kunde, "note": data['note']}})
        except Exception as e:
            pass

    def chk_setpoints(self):
        pass

    def status_alarm_timer(self):
        if self.battery_status == 'Offline':
            return

        if self.status_timer == None:
            if self.data_to_site['tarifstyring_version'] == 'Wendeware control':
                if self.data_to_site['battery_status'] != "OK" or self.data_to_site['grid_status'] != "OK" or self.data_to_site['pv_status'] != "OK":
                    self.status_timer = time.time()

            else:
                if self.data_to_site['battery_status'] != "OK" or self.data_to_site['grid_status'] != "OK":
                    self.status_timer = time.time()
        else:
            if self.data_to_site['tarifstyring_version'] == 'Wendeware control':
                if self.data_to_site['battery_status'] == "OK" or self.data_to_site['grid_status'] == "OK" or self.data_to_site['pv_status'] == "OK":
                    self.status_timer = None

                if self.data_to_site['battery_status'] != "OK" and self.data_to_site['grid_status'] != "OK" and self.data_to_site['pv_status'] != "OK":
                    timer = int(time.time() - self.status_timer)
                    if timer > 178239:
                        timer = 0
                    timer = secs = int(
                        (round(time.time() - self.status_timer))/60)
                    self.data_to_site.update({'status_timer': f"{timer:02d}"})

            else:
                if self.data_to_site['battery_status'] != "OK" or self.data_to_site['grid_status'] != "OK":
                    timer = int(time.time() - self.status_timer)
                    if timer > 178239:
                        timer = 0
                    timer = secs = int(
                        (round(time.time() - self.status_timer))/60)
                    self.data_to_site.update({'status_timer': f"{timer:02d}"})
                if self.data_to_site['battery_status'] == "OK" and self.data_to_site['grid_status'] == "OK":
                    self.status_timer = None

    def run(self):

        # self.data_to_site.update({'battery_ip': self.plc_ip})
        #local_t = datetime.today()
       # self.get_driftsikring_data()
       # print("START")
        #return
        self.check_for_plan()
        self.check_for_notes()
        self.get_driftsikring_data()
        # with semaphore:
        try:
            if self.kunde_data['PLC'] != "":
                self.battery_connect()
                if self.battery_lastConnection or self.battery_lastConnection == None:
                    # Battery
                    self.battery_read_data()
                    self.battery_alarm_status()
                    # if local_t.minute > 4 and local_t < 6:
                    self.battery_power_not_changing()
#                   
                    self.pv_main()
                    self.grid_main()
                    self.consumption_chk()
                    self.status_alarm_timer()
                    if self.plc_client.is_socket_open():
                        self.plc_client.close()
               
                    #self.get_driftsikring_data()
                    socket.emit("table", self.data_to_site)
                    return
                else:
                	
                    self.get_driftsikring_data(offline=True)
                    
                    self.system_offline()
                    return
            else:
                self.data_to_site.update({"battery_status": "Coming soon"})
                socket.emit("table", self.data_to_site)
                return

        except Exception as e:
            print(self.Kunde, "ERROR Run: ", e)
            self.plc_client.close()


###############################################################################################################


ServiceDb = database()
ServiceDb.dbEnter(db_VisblueService)

siteDb = database()
siteDb.dbEnter(db_VisblusSiteLog)

ActionLog = database()
ActionLog.dbEnter('Actionlog')


@socket.on('resetPlan')
def plans(msg):
    global ServiceDb
    ServiceDb.colEnter(msg['site'])
    ServiceDb.delete()


@socket.on('saveNote')
def LastStats(msg):
    global ActionLog
    local_time = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    ActionLog.colEnter(msg['site'].lower())
    data = {'Time': local_time, 'note': msg['note']}
    ActionLog.insertdata(data)


@socket.on('plan')
def plan(msg):
    try:
        global ServiceDb
        ServiceDb.colEnter(msg['name'])
        data = {'Date': msg['date'], 'Name': msg['Sname'], 'Note': msg['Note']}
        ServiceDb.insertdata(data)
    except Exception as e:
        print("socket plan ", e)


def start_service_page(site):
   # with semaphore:

    #if re.search('Solvang'.lower(), site.lower()):
        battery_mb_list[site].run()
    # print(site)


MAX_THREADS = 35
semaphore = threading.Semaphore(MAX_THREADS)


def background_thread():
    db = database()
    global battery_mb_list
    readDb = True
    try:
        while True:
            local_time = datetime.today()
            if readDb:

                db.dbEnter('Site_information')
                sites = db.read_site_name()
                for name in sites:
                    db.colEnter(name)
                    data = db.readAll()
                    IP = data['PLC']
                    port = data['Port']
                    battery_mb_list[name] = datahandler(name, IP, port, data)
                readDb = False
            if local_time.minute % 20 == 0 and local_time.second > 0 and local_time.second < 30 and not readDb:
                readDb = True
            
            ThrCounter = []
            count = 0
            t1 = time.time()
            for i in sites:
                Thrd = threading.Thread(target=start_service_page, args=(i,))
                Thrd.start()
                ThrCounter.append(Thrd)
                socket.sleep(0.2)
                count += 1
            print("Timer: ", t1-time.time())
            for thread in ThrCounter:
                thread.join()

    except Exception as e:
        print(e)


client = pymongo.MongoClient(f"mongodb://172.20.33.151:27017")
db = client["SiteErrorLog"]

restart_status = {}


def resetPLC(IP, site, port=502):
    global restart_status
    try:
        plc_client = ModbusTcpClient(str(IP), port=port)
        if not plc_client.is_socket_open():
            plc_client.connect()
            if plc_client.read_holding_registers(26, 1, 1).registers != 1:
                plc_client.write_register(26, 1, 1)
            time.sleep(2)
            plc_client.write_register(27, 1, 1)
            time.sleep(5)
            plc_client.write_register(27, 0, 1)
            plc_client.write_register(26, 0, 1)

        if plc_client.is_socket_open():
            plc_client.close()
        print(f"{site} - Restarted")

        restart_status[site] = "Restart completed"
        return
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"{site} - Something went wrong")
        restart_status[site] = f"Failed - {str(e)}"
        


def resetbattery_background(IP, site, port):
    reset_thread = threading.Thread(target=resetPLC, args=(IP, site, port))
    reset_thread.start()
    return

import threading

# Create a global dictionary to store the busy status for each site
busy_status = {}
from flask import jsonify, request

# Create global dictionaries to store the busy status and restart status for each site
busy_status = {}
restart_status = {}

def resetPLC(IP, site, port=502):
    global restart_status
    try:
        plc_client = ModbusTcpClient(str(IP), port=port)
        if not plc_client.is_socket_open():
            plc_client.connect()
        
        # Perform PLC reset sequence
        if plc_client.read_holding_registers(26, 1, 1).registers != 1:
            plc_client.write_register(26, 1, 1)
        time.sleep(2)
        plc_client.write_register(27, 1, 1)
        time.sleep(5)
        plc_client.write_register(27, 0, 1)
        plc_client.write_register(26, 0, 1)

        if plc_client.is_socket_open():
            plc_client.close()

        print(f"{site} - Restarted")

        # Update restart status when the operation is completed successfully
        restart_status[site] = "Restart completed"
        
    except Exception as e:
        print(f"Error: {str(e)}")
        # Update restart status when the operation fails
        restart_status[site] = f"Failed - {str(e)}"
    #finally:
        # Mark the site as no longer busy after the operation is done
       # busy_status[site] = False


@app.route("/resetBattery", methods=["GET", "POST"])
def resetbattery():
    form_data = request.form.to_dict()
    site = None
    for name, i in form_data.items():
        site = name
        break

    print("SITE : ", site)
    code = form_data.get('code')

    # Check if the site is busy
    if busy_status.get(site, False):
        return jsonify({site: "Busy - please wait until the previous reset completes."})

    if code == "Visblue2022":
        client = pymongo.MongoClient(f"mongodb://172.20.33.151:27017")
        db_client = client["Site_information"]

        IP = None
        port = 502
        foundIP = False

        # Search for the site in the database
        for collection_name in db_client.list_collection_names():
            if re.search(site.lower(), collection_name.lower()):
                print("COL: ", collection_name)
                col = db_client[collection_name]
                for document in col.find({}, {}):
                    if document.get('PLC'):
                        IP = document['PLC']
                        foundIP = True
                        if document.get('Port'):
                            port = document['Port']
                        break

        if not foundIP:
            return jsonify({site: "No PLC found for the site."})

        # Mark the site as busy before starting the operation
        busy_status[site] = True

        # Set initial status indicating the reset operation has started
        restart_status[site] = "Reset operation started. You can check the status later."

        # Run resetPLC in a separate thread
        threading.Thread(target=resetPLC, args=(IP, site, port)).start()

        # Wait 5 seconds before fetching the updated status
        c= 0
        while restart_status.get(site) != "Restart completed":
            time.sleep(1)
          #  print("waiting: ", restart_status)
            if c == 25:
                #print("TIMES UP!")
                break
            c+=1
        # Check the status (simulate internal call to `/resetStatus`)
        busy_status[site] = False
        if restart_status.get(site) == "Restart completed":
            current_status = f"Status: {restart_status.get(site)}"
        else:
            current_status = restart_status.get("Status", "No recent reset status available.")

        # Return the current status after 5 seconds
        return jsonify({site: current_status})
    
    return jsonify({site: "Wrong password - try again."})


# Route to check the reset status for the site
@app.route("/resetStatus", methods=["GET"])
def reset_status():
    site = request.args.get('site')

    if not site:
        return jsonify({"error": "Site parameter is missing."})

    # Check if the site is still busy
    if busy_status.get(site, False):
        return jsonify({"Status": "Reset operation in progress."})

    # Return the restart status if the site is no longer busy
    return jsonify({site: restart_status.get("Status", "No recent reset status available.")})



@app.route("/showError", methods=["GET", "POST"])
def errors():
    global db    
    sti = "/volume1/homes/admin/Downloads/"
    if os.getcwd != sti:
        os.chdir(sti)
    for i in os.listdir():
        csv = open(i, "r")
        datas = pd.read_csv(csv)
        csv.close()
    Projekt_Nr = datas['Nr.']
    Projekt_prioritet = datas["Prioritet"]
    all_data = []
    for collection_name in db.list_collection_names():            
        #data = db[collection_name].find_one() #collection.find()       
        data = db[collection_name].find_one(sort=[("time", pymongo.DESCENDING)])
       # for item in data:
        
        for i in range(len(datas['Nr.'])):
                projekt_nr_item = data['ProjektNr']
              #  print(projekt_nr_item)
                nr_datas = Projekt_Nr.iloc[i]
                prioritet = Projekt_prioritet.iloc[i]
                if str(nr_datas) == str(projekt_nr_item)+".0":                          
                    #if str(prioritet) in ["1.0", "2.0", "3.0", "1", "2", "3"]:                          
                        site_info = {
                                "name":     collection_name,
                                'ProjektNr'	: nr_datas,
                                'Prioritet' : prioritet,
                                "error"		:  data["error"],	#,	 "N/A"),
                                "time"		:  data["time"]#	, "N/A")

                            }                           
                        all_data.append(site_info)
                        break  
    if request.method == "POST":
        return "Post data processed"

    return render_template("showlist.html", siteErrorData=all_data)


@app.route("/")
def index():
    db = database()
    db.dbEnter('Site_information')
    sites = db.read_site_name()
    return render_template("indexa.html", customer=sites)


@socket.on("connect")
def connect():
    print("Client connected")
    global thread
    with thread_lock:
        if thread is None:
            thread = socket.start_background_task(background_thread)


if __name__ == "__main__":
    http_server = WSGIServer(("", 5000), app)
    http_server.serve_forever()
