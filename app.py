
from flask import Flask, render_template, request, render_template_string, jsonify, redirect, url_for, send_file
from flask_socketio import SocketIO

from gevent.pywsgi import WSGIServer
from pymongo import MongoClient
import pandas as pd
import os
import time
import pymongo 
import threading
from multiprocessing import Process
from datetime import datetime, timedelta
from routes import main_blueprint
from modbusSystems import Battery_conn, EnergyMeter_conn, PV_conn

app = Flask(__name__)
socket = SocketIO(app)
thread_lock = threading.Lock()
thread = None

app.register_blueprint(main_blueprint)
visblueDB = MongoClient('mongodb://172.20.33.163:27017/')


class Visblue_main():
    def __init__(self, site, project_nr,  bat_ip, em_ip, pv_ip, pv_info, em_info, smartflow):
        self.site = site
        self.project_nr = project_nr
        self.smartflow = smartflow
        self.pv_ip = pv_ip
        self.em_ip = em_ip
        self.bat_ip = bat_ip

        self.em_conn = None
        self.em_data_missing = False
        self.pv_conn = None
        self.pv_data_missing = False
        self.bat_conn = None

        self.em_power = None
        self.pv_power = None
        self.bat_power = None
        
        self.battery = Battery_conn(bat_ip, 502, 1)
        self.energymeter = EnergyMeter_conn(em_ip, 502, 1, em_info)                
        self.pv = PV_conn(pv_ip, 502, 1, pv_info)

        self.smartflow = smartflow 

        self.data = {}





    def __chk_em_connection(self):
        if self.em_ip is not None and self.em_conn != 'DCC':
            self.em_conn    = self.energymeter.try_connect()
        else:
            self.em_conn = True

    def __check_pv_connection(self):
        if self.smartflow is not None:
            if self.pv_ip is not None:
                self.pv_conn    = self.pv.try_connect()
            else:
                self.pv_data_missing = True
        else:
            self.pv_conn = True


    def connect(self):              
        self.bat_conn    = self.battery.try_connect()
        self.__chk_em_connection()
        self.__check_pv_connection()

        
#
    def gather_battery_data(self):
        self.battery.battery_read_data()
        self.data['Project_nr'] = self.project_nr
        self.data['Battery_ACPower']                        = self.battery.battery_read_ACPower()
        self.data['Battery_Charge_Setpoint']                = self.battery.battery_read_charge_setpoint()
        self.data['Battery_Discharge_Setpoint']             = self.battery.battery_read_discharge_setpoint()
        self.data['Battery_State_of_Charge']                = self.battery.battery_read_soc()
        #self.data['Battery_Alarm_State']                    = self.battery.battery_read_alarm_state()
        self.data['Battery_Temperature']                    = self.battery.battery_read_temperature()
        self.data['Battery_frozen']                         = self.battery.battery_check_frozen()
        self.data['Battery_Setpoint_error']                 = self.battery.battery_check_setpoint()
        self.data['Battery_control']                        = self.battery.battery_current_control()

        self.bat_power                                      = self.battery.battery_read_ACPower()
        self.em_power                                       = self.energymeter.em_read_power()
        self.pv_power                                       = self.pv.pv_read_power()
        self.data['Energymeter_ACPower']                    = self.em_power
        self.data['PV_ACPower']                             = self.pv_power


    def check_for_systems_errors(self):
        self.fontEnd_status_color = 'white'         
        self.__check_battery_error()
        self.__check_em_error()
        self.__check_pv_error()
        self.__check_MYP()
        self.data["Battery_Alarm_Color"] = self.fontEnd_status_color

    def __check_MYP(self):
        if self.calculate_consumption() is not None:
            if self.calculate_consumption() < 0:
                if self.data['Battery_Alarm_State'] != "":
                    self.data['Battery_Alarm_State'] += ',MYP_Cons_Error'
                self.fontEnd_status_color = "red"
        

    def __check_pv_error(self):
        if self.smartflow:
            if not self.pv_conn:
                if self.data['Battery_Alarm_State'] != "":
                    self.data['Battery_Alarm_State'] += ", DetectNoPV"                    
                self.fontEnd_status_color = "red"

    def __check_em_error(self):
        if not self.em_conn: 
            if self.data['Battery_Alarm_State'] != "":
                self.data['Battery_Alarm_State'] += ", DetectNoEM"
            self.fontEnd_status_color = "red"

    def __check_battery_error(self):
        if self.battery.battery_read_alarm_state() != 'OK':
            self.data['Battery_Alarm_State'] = self.battery.battery_read_alarm_state() 
            self.fontEnd_status_color = "red"
       
    def calculate_consumption(self):
        consumption = None
        if self.em_conn and self.pv_conn :
            return self.em_power - self.pv_power + self.bat_power          
        return consumption
        
    def driftsikring(self):
        from Driftsikring import driftsikring
        data = driftsikring(float(self.project_nr))        
        self.data = self.data | data 
               

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
                "battery_alarm_status": self.battery.battery_read_alarm_state(),                
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
        self.gather_battery_data()
        self.driftsikring()
        self.check_for_systems_errors()
        print(self.data)
        return
        self.gather_battery_data()
        self.calculate_consumption()






def lookup_db_for_notes(col_name):
    db = visblueDB['service_page_notes']
    col = db.get_collection(col_name)
    data = col.find_one({}, {"_id": 0})    
    if data is None:        
        return {}
    data = {'Plan_date': data.get('Date'), 'Plan_name' : data.get('Name'), 'Plan_note': data.get('Note')}
    return data

def lookup_db_for_actions(col_name):
    db = visblueDB['Actionlog']
    col = db.get_collection(col_name)
    data = col.find_one({}, {"_id": 0})
    if data is  None:
        return {} 
    data = {'Action_date': data.get('Date'), 'Action_name' : data.get('Name'), 'Action_note': data.get('Note')}
    return data

def get_info(col_name):
    col = db.get_collection(col_name)
    data = col.find_one({}, {"_id": 0})
    PLC_ip = data.get('PLC', None)        
    pro_nr = data.get('Projekt', None)
    site = Visblue_main(col_name, pro_nr, PLC_ip,"0","0", "0", "0")
    site.run()


info = MongoClient('mongodb://172.20.33.151:27017/')
db = info['Site_information']
bat_ip = "172.20.33.12"

def background_threads():
   #while True:
     
        site = Visblue_main('col_name', 10280, bat_ip ,"0","0", "0", "0", None)
        site.run()
        
        
        socket.emit('table', {'Mollerup':site.data })
        socket.sleep(3)
    
        #print("SENT!")
  # pass
      # socket.sleep(2)        
      # total_data = {}
      # for i in db.list_collection_names():
      #     total_data[i] = get_info(i) | lookup_db_for_actions(i) | lookup_db_for_plan(i)                                            

      ##socket.emit('table', {  'A' : {"TEST" : 123},
      ##                        'B' : {"TEST" : 123},
      ##                        'C' : {"TEST" : 123,},
      ##                        'D' : {"TEST" : 123,} } )
       #                        
#ackground_threads()
#quit()                        
db_VisblueService = "VisblueService"
db_VisblusSiteLog = "VisblueLog"
db_MypowergridTimer = 'ServicePageTimer'



@socket.on('note')    
def save_note(msg):       
    db = visblueDB['service_page_notes']
    col = db[msg['key']]
    res = col.insert_one({
        'Time' : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Site' : msg['key'],
        'Note' : msg['value']})
    print(res.acknowledged)
    
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

import eventlet
if __name__ == "__main__":
   
    socket.run(app, debug=True)
    http_server = WSGIServer(("0.0.0.0", 2000), app)
    #eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 2000)), app)
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

(site_1.data)

"""
