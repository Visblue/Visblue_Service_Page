from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import multiprocessing
import eventlet
from flask import Flask, render_template, request, render_template_string, jsonify, redirect, url_for, send_file
from flask_socketio import SocketIO
import re
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

# Use a single MongoClient instance for the entire application
visblueDBOld = MongoClient('mongodb://172.20.33.151:27018/')
db_error_log = visblueDBOld['ServicePage_Log']
visblueDB = MongoClient('mongodb://172.20.33.151:27018/')
# Get the customer info database here
db_customer_info = visblueDB['Customer_info']
# Get the service notes database here
db_service_notes = visblueDB['ServicePage_Log']


class Visblue_main():
    def __init__(self, CUSTOMER, PROJECTNR, PLCIP, PLCPORT, EMIP, EMPORT, EMTYPE, PVIP, PVPORT, PVTYPE, PVUNITID):
       # print(CUSTOMER, PROJECTNR, PLCIP, PLCPORT, EMIP,
       #       EMPORT, EMTYPE, PVIP, PVPORT, PVTYPE, PVUNITID)
        # return
        self.site = CUSTOMER
        self.project_nr = PROJECTNR
        self.plc_ip = PLCIP
        self.plc_port = PLCPORT
        self.em_ip = EMIP

        self.em_port = EMPORT
        self.em_type = EMTYPE
        self.pv_ip = PVIP
        self.pv_port = PVPORT
        self.pv_type = PVTYPE
        self.pv_unitid = PVUNITID
        self.em_unitid = 1

       # self.em_conn    = None
        # self.pv_conn    = None
        self.bat_conn = None
        self.em_power = None
        self.pv_power = None
        self.bat_power = None
        self.smartflow = None
        self.data = {}

    def EM(self):
        EM_power = None
        EM_status = None
        if self.em_ip != None:
            if self.em_ip.lower() != 'dcc':
                self.energymeter = EnergyMeter_conn(
                    self.site, self.em_ip, self.em_port, self.em_unitid, self.em_type)
                if self.energymeter.try_connect():
                    EM_power = self.energymeter.em_read_power()
                    EM_status = 0
                else:
                    EM_status = -1
        else:
            EM_status = 0

        self.data['Energy_meter_connection_status'] = EM_status
        self.data['Energy_meter_power'] = EM_power

    def PV(self):
        PV_status = None
        PV_power = None
        # print(self.pv_ip, self.site)
        if self.pv_ip != None:
            if self.pv_ip.lower() == 'dcc':
               # print("Here: ", self.pv_ip, self.site)
                self.pv = PV_conn(self.site, self.pv_ip, self.pv_port,
                                  self.pv_unitid, self.pv_type)
                if self.pv.try_connect():
                    PV_power = self.pv.pv_read_power()
                    PV_status = 0
                else:
                    PV_status = -1
            else:
                PV_status = True
        else:
            PV_status = 0
        self.data['PV_connection_status'] = PV_status
        self.data['PV_power'] = PV_power

    def VisblueBattery(self):

        if self.plc_ip != "":
            self.battery = Battery_conn(
                self.site, self.plc_ip, self.plc_port, 1)
            self.bat_conn = self.battery.try_connect()
            if self.bat_conn:
                self.get_battery_data()
                return True
            else:
                self.data['Battery_Alarm_State'] = "Offline"
                self.data['Project_nr'] = self.project_nr
                self.driftsikring()
                return False
        self.data['Battery_Alarm_State'] = "ComingSoon"
        self.data['Project_nr'] = self.project_nr
        self.driftsikring()
        return False

    def get_battery_control(self):
        control_modes = {0: 'EM Control', 1: 'Smartflow', 2: 'Auto'}
        if re.search('vacha', self.site.lower()) or re.search('texel', self.site.lower()) or re.search('varensdorf', self.site.lower()) or re.search('bryte', self.site.lower()):
            return 'External Control'
        return control_modes.get(int(self.battery.battery_read_control_reg()), 'Unknown control')

    def get_battery_data(self):
        control_modes = {0: 'EM Control', 1: 'Smartflow', 2: 'Auto'}
        self.battery.battery_read_data()
        self.data['Project_nr'] = self.project_nr
        self.data['Battery_ACPower'] = self.battery.battery_read_ACPower()
        self.data['Battery_Charge_Setpoint'] = self.battery.battery_read_charge_setpoint()
        self.data['Battery_Discharge_Setpoint'] = self.battery.battery_read_discharge_setpoint()
        self.data['Battery_State_of_Charge'] = self.battery.battery_read_soc()
        self.data['Battery_state'] = self.battery.battery_read_battery_state()
        self.data['Battery_Alarm_State'] = self.battery.battery_read_alarm_state()
        self.data['Battery_Temperature'] = self.battery.battery_read_temperature()
        # self.data['Battery_frozen']                         = self.battery.battery_check_frozen()
        self.data['Battery_Setpoint_error'] = self.battery.battery_check_setpoint()
        # control_modes.get(int(self.battery.battery_read_control_reg()), 'Unknown control') #self.battery_current_control(
        self.data['Battery_control'] = self.get_battery_control()
        # self.battery.battery_read_control_reg())
        self.battery_power = self.battery.battery_read_ACPower()
        self.driftsikring()

    def driftsikring(self):
        if re.search("visblue", self.site.lower()):
            return
        from Driftsikring import driftsikring
        datas = driftsikring(float(self.project_nr))
        self.data['Signed_date'] = datas.get('Signed_date', "")
        self.data['Site_prioritet'] = datas.get('Site_prioritet', 9)
        self.data['Signed_time'] = datas.get('Signed_time', 0)
        self.data['Site_prioritet_color'] = datas.get(
            'Site_prioritet_color', "white")
        self.data['DA_nr'] = datas.get('DA_nr', "")
        self.data['SA_nr'] = datas.get('SA_nr', "")
        self.smartflow = datas.get('SA_nr', False)

    def __update_get_collections(self):
        self.col = None
        self.add_new = False
        col_found = False
        for i in db_error_log.list_collection_names():
            if re.search(i.lower(), self.site.lower()):
                self.col = db_error_log[i]
                col_found = True
                break
        if not col_found:
            self.col = db_error_log[self.site]
            self.add_new = True
            


    def update_database_error_log(self):
        
        self.__update_get_collections()
        
        query = {
        "Kunde": self.site,
        'ProjectNr': self.project_nr,
    }

        alarmStatus = "OK" if self.data.get('Battery_Alarm_State', 0) == 0 else self.data['Battery_Alarm_State']
        db_current_data = self.col.find_one(query)

        if db_current_data is None:
            data_to_update = {
                "Kunde": self.site,
                "Battery_status": alarmStatus,
                'ProjectNr': self.project_nr,
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.col.insert_one(data_to_update)
        else:
            existing_status = db_current_data.get('Battery_status', '')
            existing_time = db_current_data.get('Time')

            if alarmStatus.lower() == "offline":
                # Markér som offline
                offline_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_data = {
                    "$set": {
                        "Battery_status": alarmStatus,
                        "Time": offline_time
                    }
                }
                self.col.update_one(query, update_data)
                return

            if alarmStatus.lower() == "ok":
                # Sæt status til OK
                update_data = {
                    "$set": {
                        "Battery_status": alarmStatus,
                        "Time_resolved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
                self.col.update_one(query, update_data)
                return

            if alarmStatus.lower() not in existing_status.lower():
                # Tilføj ny fejl
                existing_errors = existing_status.split(", ") if existing_status else []
                updated_status = ", ".join(existing_errors + [alarmStatus]) if alarmStatus not in existing_errors else existing_status

                data_to_update = {"Battery_status": updated_status}

                if "Time_resolved" not in db_current_data:
                    data_to_update["Time"] = existing_time

                update_data = {"$set": data_to_update}
                self.col.update_one(query, update_data)

    def update_database_error_logs(self):
        self.__update_get_collections()

        query = {
            "Kunde": self.site,
            'ProjectNr': self.project_nr,
        }

        # Bestem alarmstatus
        if self.bat_conn is None:
            alarmStatus = 'Offline'
        else:

            alarmStatus = "OK" if self.data['Battery_Alarm_State'] == 0 else self.data['Battery_Alarm_State']

        db_current_data = self.col.find_one(query)

        if db_current_data is None:
            data_to_update = {
                "Kunde": self.site,
                "Battery_status": alarmStatus,
                'ProjectNr': self.project_nr,
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.col.insert_one(data_to_update)
        else:
            if re.search("ok", alarmStatus.lower()):
                # Update existing document with new time and state
                offline_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_data = {
                    "$set": {
                        "Battery_status": alarmStatus,
                        "Time": offline_time
                    }
                }

                self.col.delete_one(query) #(query, update_data)
                # self.data['Alarm_registred'] = offline_time
                return
            if alarmStatus.lower() == 'offline':
                # Update existing document with new time and state
                offline_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_data = {
                    "$set": {
                        "Battery_status": alarmStatus,
                        "Time": offline_time
                    }
                }
                self.col.update_one(query, update_data)
                self.data['Alarm_registred'] = offline_time
                return

            # Fejlen eksisterer allerede
            existing_status = db_current_data.get('Battery_status', '')
            existing_time = db_current_data.get('Time')
            self.data['Alarm_registred'] = existing_time
            if alarmStatus.lower() not in existing_status.lower():

                # Ny fejl tilfjes til den eksisterende liste
                updated_status = f"{existing_status}, {alarmStatus}" if existing_status else alarmStatus
                data_to_update = {
                    "Battery_status": updated_status,
                }

                # Hvis der ikke er nogen rettelser endnu, behold den originale tid
                if "Time_resolved" not in db_current_data:
                    data_to_update["Time"] = existing_time
                    self.data['Alarm_registred'] = existing_time

                update_data = {
                    "$set": data_to_update
                }
                self.col.update_one(query, update_data)
            elif alarmStatus.lower() == "ok" and "Time_resolved" not in db_current_data:
                # Fejl rettet - tilfj tid for rettelse
                update_data = {
                    "$set": {
                        "Battery_status": alarmStatus,
                        "Time_resolved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
                self.col.update_one(query, update_data)

    def run(self):
        self.VisblueBattery()
        # self.EM()
        # self.PV()
        if self.data['Battery_Alarm_State'] != 'ComingSoon':            
            self.update_database_error_log()


def lookup_db_for_notes(col_name):
    col = db_error_log.get_collection(col_name)
    data = col.find_one({}, {"_id": 0}, sort=[("Time", -1)])

    if data is None:
        return {}
    data = {'Time': data.get('Time'), 'Site': data.get(
        'Site'), 'Note': data.get('Note')}

    return data


def get_info(col_name):
    col = db_customer_info.get_collection(col_name)
    data = col.find_one({}, {"_id": 0})

    for i in data:
        site = Visblue_main(CUSTOMER=col_name, PROJECTNR=data[i].get('Project_nr', 99999), PLCIP=data[i].get('Battery_ip', None), PLCPORT=data[i].get('Battery_port', 502), EMIP=data[i].get('Em_ip', "DCC"), EMPORT=data[i].get('Em_port', 502), EMTYPE=data[i].get('Em_type', "None"),
                            PVIP=data[i].get('Pv_ip', "DCC"), PVPORT=data[i].get('Pv_port', "DCC"), PVTYPE=data[i].get('Pv_type', "None"), PVUNITID=data[i].get('PV_unit_id', 1))
        site.run()

    return i, site.data


# Function to handle the processing for each collection


def process_collection(i,  TotalData):
    site, data = get_info(i)
    datas = dict(data, **lookup_db_for_notes(i))

    # Thread-safe update of the shared dictionary
    with TotalData_lock:
        TotalData[site] = datas

    # Add a small delay (e.g., 10 milliseconds) after each processing
    # time.sleep(0.2)  # Delay for 10 milliseconds

    return site, datas  # Return the site and data for sending once done

# Function to initialize threading


def process_collections():
    # Initialize a manager to handle shared data
    TotalData = {}
    # Lock to ensure thread-safe access to TotalData
    global TotalData_lock
    TotalData_lock = threading.Lock()

    # Create a partial function to pass `db` and `TotalData` to the worker function
    process_func = partial(process_collection, TotalData=TotalData)

    # Get the collection names from the database
    collection_names = db_customer_info.list_collection_names()

    # Use ThreadPoolExecutor to handle the threads
    with ThreadPoolExecutor(max_workers=5) as executor:  # Max workers set to 10
        # Submit each collection to be processed in a separate thread
        futures = [executor.submit(process_func, name)
                   for name in collection_names]

        # To collect completed results
        completed_results = []

        # Process results as they come in (as each thread completes)
        for future in as_completed(futures):
            site, datas = future.result()  # Get the result of the completed thread

            # Append result to completed_results
            completed_results.append((site, datas))

            # Once we have 10 results, send them and wait for 5 seconds
            if len(completed_results) ==20:
                # Send/Process the batch of 10 results
                # print(f"Sending batch of 10: {completed_results[0]}")
                # Here you can send the batch to your desired destination
                socket.emit("table", dict(completed_results))
                # Example: send_batch(completed_results)

                # Wait for 5 seconds before continuing
                socket.sleep(1)

                # Clear the completed results for the next batch
                completed_results.clear()

        # If there are any remaining results less than 10 after all threads are done
        if completed_results:
            pass
            # print(f"Sending final batch: {completed_results}")
            # socket.emit("table", dict(completed_results))
            # Example: send_batch(completed_results)

    # Return the shared TotalData dictionary after processing is done
    return TotalData


def background_threads():
    while True:
        start = time.time()
        process_collections()
        end = time.time()
        print("TIME: ", end-start)
        time.sleep(1)


@socket.on('note')
def save_note(msg):
    # db = visblueDB['service_page_notes']
    col = db_error_log[msg['key']]
    res = col.insert_one({
        'Time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Site': msg['key'],
        'Note': msg['value']})
    # print(res.acknowledged)


@socket.on("connect")
def connect():
    print("Client connected!!")
    global thread
    with thread_lock:
        if thread is None:
            thread = socket.start_background_task(background_threads)


@app.route('/')
def home():
    return render_template('index.html')


if __name__ == "__main__":

    # socket.run(app)
    http_server = WSGIServer(("0.0.0.0", 2000), app)
    # eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
    http_server.serve_forever()
