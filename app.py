from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from flask import Flask, render_template
from flask_socketio import SocketIO
import re
from gevent.pywsgi import WSGIServer
from pymongo import MongoClient
import time
import threading
from datetime import datetime, timedelta
from routes import main_blueprint
from modbusSystems import Battery_conn, EnergyMeter_conn, PV_conn
import eventlet
from eventlet import wsgi

app = Flask(__name__)
socket = SocketIO(app)
thread_lock = threading.Lock()
thread = None


app.register_blueprint(main_blueprint)

# Use a single MongoClient instance for the entire application
visblueDBOld = MongoClient('mongodb://172.20.33.151:27017/')
db_service_notes = visblueDBOld['Actionlog']

visblueDB = MongoClient('mongodb://172.20.33.151:27018/')
db_error_log = visblueDB['ServicePage_Log']
# Get the customer info database here
db_customer_info = visblueDB['Customer_info']
# Get the service notes database here




## counters
smartFlowCounter = 0
totalSystems = 0
systemOnlineCounter = 0
systemOfflineCounter = 0

systemErrorCounter = 0
systemNoneErrorCounter = 0
CounterRefreshRate = 10
#systemCriticalErrorCounter = None

TODO = False
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
        # 0 = OK, -1 = connRefused, -2 = Used, -3=Unknown
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
                self.energymeter.client.close()
            else:
                EM_status = -2
        else:
            EM_status = -3

        self.data['Energy_meter_connection_status'] = EM_status
        self.data['Energy_meter_power'] = EM_power
      

    def PV(self):
        # 0 = OK, -1 = connRefused, -2 = Used, -3=Unknown
        PV_status = None
        PV_power = None
        
        if self.pv_ip != None:
            if self.pv_ip.lower() != 'dcc':
               # print("Here: ", self.pv_ip, self.site)
                self.pv = PV_conn(self.site, self.pv_ip, self.pv_port,
                                  self.pv_unitid, self.pv_type)
                if self.pv.try_connect():
                    PV_power = self.pv.pv_read_power()
                    PV_status = 0
                else:
                    PV_status = -1
                self.pv.client.close()
            else:
                PV_status = -2
        else:
            PV_status = -3

            if re.search("solvang", self.site.lower()) or  re.search("løse svommehal", self.site.lower()):
                PV_status = -3
        
       
        self.data['PV_connection_status'] = PV_status
        self.data['PV_power'] = PV_power
     
    def VisblueBattery(self):
        global systemOnlineCounter, systemOfflineCounter, totalSystems
        if self.plc_ip != "":
            totalSystems += 1
            self.battery = Battery_conn(
                self.site, self.plc_ip, self.plc_port, 1)
            self.bat_conn = self.battery.try_connect()
            if self.bat_conn:
                systemOnlineCounter+=1
                self.get_battery_data()
                
                return True
            else:
                systemOfflineCounter += 1
                self.data['Battery_Alarm_State'] = "Offline"
                self.data['Project_nr'] = self.project_nr
                self.driftsikring()
                return False
            
        
        self.data['Battery_Alarm_State'] = "ComingSoon"
        self.data['Project_nr'] = self.project_nr
        self.driftsikring()
        return False

    def get_battery_control(self):
        try:
            control_modes = {0: 'EM Control', 1: 'Smartflow', 2: 'Auto'}
            if re.search('vacha', self.site.lower()) or re.search('texel', self.site.lower()) or re.search('varensdorf', self.site.lower()) or re.search('bryte', self.site.lower()):
                return 'External Control'
            return control_modes.get(int(self.battery.battery_read_control_reg()), 'Unknown control')
        except Exception as e:
            return "unknown"
    def get_battery_data(self):
        global systemErrorCounter, systemNoneErrorCounter
        try:
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
            if self.battery.battery_read_alarm_state() != 0 or self.battery.battery_read_battery_state() == 0:
                systemErrorCounter += 1
            else:
                systemNoneErrorCounter += 1
                
            
        except Exception as e:
            print("Error: " , e)
        
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
        self.dbSite = None
        for i in db_error_log.list_collection_names():
            if re.search(i.lower(), self.site.lower()):
                self.col = db_error_log[i]
                col_found = True
                self.dbSite = i
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
        
        alarmStatus = "OK" if self.data.get('Battery_Alarm_State', "OK") == 0 else self.data['Battery_Alarm_State']
        db_current_data = self.col.find_one(query)
        
        if db_current_data is None:
            data_to_update = {
                "Kunde": self.site,
                "Battery_status": alarmStatus,
                'ProjectNr': self.project_nr,
                "Smartflow" : self.get_battery_control(),
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self.col.insert_one(data_to_update)
        else:
            existing_status = db_current_data.get('Battery_status')
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

            if alarmStatus == 0 or re.search("ok", alarmStatus.lower()) or re.search('ok', existing_status.lower()):
                # Sæt status til OK
             #   print("update: ", self.site, self.data.get('Battery_status'), existing_status)
                update_data = {
                                "$set": {
                                    "Battery_status": alarmStatus,  # Use the variable alarmStatus here
                                    "Time_resolved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
    }
                #drop collection
                self.col.update_one(query, update_data)  # Use update_one instead of delete_one
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

 
 

    def run(self):
        global TODO
        if not TODO:
            self.data['Todo'] = todo()
            
        #self.VisblueBattery()
        if not self.VisblueBattery():      
            if self.data['Battery_Alarm_State'] == 'ComingSoon':            
                return	
            self.update_database_error_log()
            
            return
        self.EM()
        if self.data['Battery_control'] == 'Smartflow':
            #self.data['Battery_Smartflow'] = self.battery.check_smartflow()
            self.PV()
            
        self.update_database_error_log()
        self.battery.client.close()
    
    


def todo():	 
    todoDB = visblueDB['TODO']
    col = todoDB['TODO']
    TIME = []
    TODOS = []
    for i in col.find():
        TIME.append(i['Time'])
        TODOS.append(i['Todo'])    
       # TODOS = "";
    return  TODOS

	
   
def lookup_db_for_notes(col_name):
    #col = db_service_notes.get_collection(col_name)
    found = False
    for i in db_service_notes.list_collection_names():
        if re.search(i.lower(), col_name.lower()):
            col=db_service_notes.get_collection(i)
            found = True
    if not found:
        return {}
    data = col.find_one({}, {"_id": 0}, sort=[("_id", -1)]) 
    data = {'Note_Time': data.get('Time', None), 'Note': data.get('note', None)}
	
    return data


def get_info(col_name):
    col = db_customer_info.get_collection(col_name)
    data = col.find_one({}, {"_id": 0})

    for i in data:
        site = Visblue_main(CUSTOMER=col_name, PROJECTNR=data[i].get('Project_nr', 99999), PLCIP=data[i].get('Battery_ip', None), PLCPORT=data[i].get('Battery_port', 502), EMIP=data[i].get('Em_ip', "DCC"), EMPORT=data[i].get('Em_port', 502), EMTYPE=data[i].get('Em_type', "None"),
                            PVIP=data[i].get('Pv_ip', "DCC"), PVPORT=data[i].get('Pv_port', "DCC"), PVTYPE=data[i].get('Pv_type', "None"), PVUNITID=data[i].get('PV_unit_id', 1))
        site.run()

    return i, site.data

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial

def process_collection(i, TotalData):
    try:
        site, data = get_info(i)
        datas = dict(data, **lookup_db_for_notes(i))
        
        # Thread-safe update of the shared dictionary
        with TotalData_lock:
            TotalData[site] = datas

        # Add a small delay (e.g., 10 milliseconds) after each processing
        time.sleep(0.5)  # Reduced delay (10ms)
        
        return site, datas  # Return the site and data for sending once done

    except Exception as e:
        print(f"Error processing collection {i}: {e}")
        return None, None

ShowStatus = 10
def process_collections():
    global totalSystems, systemErrorCounter, systemOnlineCounter, systemOfflineCounter, systemNoneErrorCounter,CounterRefreshRate
    global OnlyOnce
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
    with ThreadPoolExecutor(max_workers=5) as executor:  # Max workers set to 5 for better control
        # Submit each collection to be processed in a separate thread
        futures = [executor.submit(process_func, name)
                   for name in collection_names]

        # To collect completed results
        completed_results = []

        # Process results as they come in (as each thread completes)
        for future in as_completed(futures):
            site, datas = future.result()  # Get the result of the completed thread
            
            if site and datas:  # Check for successful result
                completed_results.append((site, datas))

           # print(site, datas)
           # break
            # Once we have 5 results, send them and wait
            if len(completed_results) >= 5:
                if CounterRefreshRate == 10:
                    completed_results.append(("SystemStat", {'TotalSystems' : totalSystems, "TotalError" : systemErrorCounter, "TotalNoneError" :systemNoneErrorCounter, "TotalOnline" : systemOnlineCounter, "TotalOffline" : systemOfflineCounter,  }))
                socket.emit("table", dict(completed_results))
                completed_results.clear()

                # Optional: Reduce frequency of emission or implement retry logic if network is slow
                socket.sleep(1)  # Add a small delay to throttle the communication

        # Send any remaining results
        if completed_results:
            socket.emit("table", dict(completed_results))
            completed_results.clear()
            socket.sleep(0.1)  # Add a small delay to throttle the communication
            
        OnlyOnce = False

    return TotalData


def background_threads():
    global systemOnlineCounter, systemOfflineCounter,systemErrorCounter, systemNoneErrorCounter, totalSystems, CounterRefreshRate
    while True:
        try:
            start = time.time()
            
            a = process_collections()  # Process collections
            end = time.time()
            print("TIME: ", end - start)
            print("Systems: " , systemOnlineCounter, systemOfflineCounter, systemErrorCounter , "\n")
            
            time.sleep(5)  # Delay between background task executions
            if CounterRefreshRate == 0:
                systemOnlineCounter = 0
                systemOfflineCounter= 0
                systemErrorCounter = 0
                systemNoneErrorCounter = 0
                totalSystems = 0
                CounterRefreshRate = 10
            CounterRefreshRate +=1
        except Exception as e:
            print(f"Error in background thread: {e}")
            time.sleep(5)  # Wait before retrying in case of failure


# Function to handle the processing for each collection
"""
def process_collection(i,  TotalData):

    site, data = get_info(i)
    datas = dict(data, **lookup_db_for_notes(i))

# Thread-safe update of the shared dictionary
    with TotalData_lock:
        TotalData[site] = datas

    # Add a small delay (e.g., 10 milliseconds) after each processing
    time.sleep(1) #Delay for 10 milliseconds

    return site, datas  # Return the site and data for sending once done

# Function to initialize threading


def process_collections():
    global OnlyOnce
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
    with ThreadPoolExecutor(max_workers = 5) as executor:  # Max workers set to 10
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
            if len(completed_results) == 5:
            	
                
                
                # Send/Process the batch of 10 results
                # print(f"Sending batch of 10: {completed_results[0]}")
                #print("BEFORE SENT: ", completed_results)
                # Here you can send the batch to your desired destination
                socket.emit("table", dict(completed_results))
                completed_results.clear()
              
                # Example: send_batch(completed_results)

                # Wait for 5 seconds before continuing
                socket.sleep(0.1)

                # Clear the completed results for the next batch
                completed_results.clear()

        # If there are any remaining results less than 10 after all threads are done
        if completed_results:
            
            #print("completed_results: ", completed_results)
            socket.emit("table", dict(completed_results))
            completed_results.clear()
            #time.sleep(10)
            completed_results.clear()
            OnlyOnce = False
            
            
            # print(f"Sending final batch: {completed_results}")
            # socket.emit("table", dict(completed_results))
            # Example: send_batch(completed_results)

    # Return the shared TotalData dictionary after processing is done
    return TotalData

def background_threads():
    while True:
        start = time.time()
        a = process_collections()
        #print(a)
        end = time.time()
        print("TIME: ", end-start)
        time.sleep

"""
@socket.on('note')
def save_note(msg):
    # db = visblueDB['service_page_notes']
    col = db_service_notes[msg['key'].lower()]
    res = col.insert_one({
        'Time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Site': msg['key'],
        'note': msg['value']})
    # print(res.acknowledged)

@socket.on('todo')
def save_todos(msg):
    db = visblueDB['TODO']
    col = db["TODO"]
    res = col.insert_one({
        'Time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'Todo': msg['todo']})
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
    #http_server = WSGIServer(("0.0.0.0", 5000), app)
    #server = eventlet.listen(('0.0.0.0', 5000))
    #wsgi.server(server, app)
	#run_simple("0.0.0.0", 5000, app,   use_reloader=True,  use_debugger=True, threaded=True)      # Håndter flere samtidige anmodninger

    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app )
	#socket.run(app, host="0.0.0.0", port=5000, use_reloader=False)
    #http_server.serve_forever()
