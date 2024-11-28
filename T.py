# rom app import app,render_template, request, redirect, url_for, send_file
import pymongo
import os
import pandas as pd
from flask import render_template, request, Blueprint, jsonify
from pymodbus.client import ModbusTcpClient
import time
import re 
main_blueprint = Blueprint('main', __name__)
client = pymongo.MongoClient('mongodb://172.20.33.151:27018/') 
db = client["ServicePage_Log"]



# Global cache til at gemme data fra CSV-filer
cache = {}

def load_csv(file_path):
    if file_path in cache:
        print(f"Data hentet fra cache for filen: {file_path}")
        return cache[file_path]
    else:
        print(f"Lser filen: {file_path}")
        data = pd.read_csv(file_path)
        cache[file_path] = data
        
        return data

def get_latest_data_for_projects(datas, db):
    """Henter de nyeste data for hvert projekt fra MongoDB."""
    projekt_nr = datas['Nr.']
    prioritet = datas['Prioritet']
    all_data = []
   # print("projekt_nr: ", projekt_nr)
    for collection_name in db.list_collection_names():
      #  print("collection_name: " + collection_name)
        # Hent det nyeste dokument i samlingen
        latest_data = db[collection_name].find_one(sort=[("time", pymongo.DESCENDING)])
        print(latest_data)
        if not latest_data:
            continue
        
        for i, nr in enumerate(projekt_nr):
            latest_projectNr = latest_data.get('ProjectNr')
            latest_error = latest_data.get('Battery_Status')
            latest_Time = latest_data.get('Time')
            print("here : ", i, nr, latest_projectNr)
            if (latest_projectNr == '-'):
                continue
            if str(nr) == float(latest_projectNr):
                site_info = {
                    "Kunde": collection_name,
                    "ProjektNr": nr,
                    "Prioritet": prioritet.iloc[i],
                    "Battery_status": latest_error,
                    "Time": latest_Time,
                }
                all_data.append(site_info)
                break

    return all_data

@main_blueprint.route('/fejloversigt', methods=['GET'])
def fejloversigt():
    # Eksempel: Hent CSV-data og databaseforbindelse
    #global db
    #sti = "/volume1/homes/admin/Downloads/"
    ##sti = "C:/Users/FarhadAnayati/VisBlue/VisBlue all - Dokumenter/Product Development/Serviceside"
    #if os.getcwd != sti:
    #    os.chdir(sti)
    #for file_name in os.listdir():
    #    if file_name.endswith('.csv'):  # Kun CSV-filer
    #        file_path = os.path.join(sti, file_name)
    #        datas = load_csv(file_path)
   #
    #
    ## Hent data fra MongoDB og processér
    #site_error_data = get_latest_data_for_projects(datas, db)
#
    #if request.method == "POST":
    #    return "Post data processed"

    return render_template("Nyfejl.html")#site_error_data#render_template("fejloversigt.html", siteErrorData=site_error_data)


def fejloversigts():
    global db
    sti = "/volume1/homes/admin/Downloads/"
    #sti = "C:/Users/FarhadAnayati/VisBlue/VisBlue all - Dokumenter/Product Development/Serviceside"
    if os.getcwd != sti:
        os.chdir(sti)
    for file_name in os.listdir():
        if file_name.endswith('.csv'):  # Kun CSV-filer
            file_path = os.path.join(sti, file_name)
            datas = load_csv(file_path)
   
    csv_projectNr = datas['Nr.']
    csv_prioritet = datas["Prioritet"]
    all_data = []
    for collection_name in db.list_collection_names():
        data = db[collection_name].find_one(
            sort=[("time", pymongo.DESCENDING)])
        prioritet = csv_prioritet.iloc[i]
        latest_projectNr = data.get('ProjectNr')
        latest_error = data.get('Battery_status');
        lateste_Time = data.get('Time')
       
       # if data.get('Battery_status') == 'OK':
	        #  continue       
        #for i in range(len(datas['Nr.'])):		        	          
        if str(csv_projectNr.iloc[1]) == str(latest_projectNr)+".0":
            site_info = {
                "Kunde":     collection_name,
                'ProjectNr': csv_projectNr.iloc[1],
                'Prioritet': prioritet,
                "Battery_status":  latest_error,  # ,	 "N/A"),
                "Time":  lateste_Time  # , "N/A")
            }
            all_data.append(site_info)
          #  break
    if request.method == "POST":
        return "Post data processed"

    return all_data# render_template("Nyfejl.html")#("fejloversigt.html", siteErrorData=all_data)



db_sites = client['Systems']
@main_blueprint.route('/reset', methods=['POST'])
def reset_battery():
    form_data = request.form  # For POST
    query_data = request.args  # For GET
    #print("form_data:", form_data)  # Debug POST data
    #print("query_data:", query_data)  # Debug GET data

    site = request.form.get('site')  # Safely access form data  
    found = False
    for i in db_sites.list_collection_names():
        if re.search(site, i):
            data = db_sites[i].find_one()
            IP = data.get('PLC')
            port = data.get('Port', 502)
            found = True
            break

    if not found:
        return "Site not found"
    
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

    #print(f"{site} - Restarted")

    # Update restart status when the operation is completed successfully
    


    return "SUCCESS"

@main_blueprint.route('/get_data', methods=['POST', 'GET'])
def get_data():
	#print("HERE")
    data = fejloversigts()
    #print("DATA: ", data)
    return  jsonify(data)