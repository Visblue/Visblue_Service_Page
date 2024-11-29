# rom app import app,render_template, request, redirect, url_for, send_file
import pymongo
import os
import pandas as pd
from flask import render_template, request, Blueprint, jsonify
from pymodbus.client import ModbusTcpClient, AsyncModbusTcpClient
import time
import re 
import asyncio
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
   
    Projekt_Nr = datas['Nr.']
    Projekt_prioritet = datas["Prioritet"]
    all_data = []
    for collection_name in db.list_collection_names():
        data = db[collection_name].find_one(
            sort=[("time", pymongo.DESCENDING)])
        prioritet = Projekt_prioritet.iloc[i]
        latest_projectNr = data.get('ProjectNr')
        latest_error = data.get('Battery_status');
        lateste_Time = data.get('Time')
       
       # if data.get('Battery_status') == 'OK':
	        #  continue       
        #for i in range(len(datas['Nr.'])):		        	          
        if str(Projekt_Nr.iloc[1]) == str(latest_projectNr)+".0":
            site_info = {
                "Kunde":     collection_name,
                'ProjectNr': Projekt_Nr.iloc[1],
                'Prioritet': prioritet,
                "Battery_status":  latest_error,  # ,	 "N/A"),
                "Time":  lateste_Time  # , "N/A")
            }
            all_data.append(site_info)
          #  break
    if request.method == "POST":
        return "Post data processed"

    return all_data# render_template("Nyfejl.html")#("fejloversigt.html", siteErrorData=all_data)


db_sites = client['Customer_info']

# Example route for resetting battery
@main_blueprint.route('/reset', methods=['POST'])
async def reset_battery():
    site = request.form.get('site')
    if not site:
        return jsonify({"error": "Site is required"}), 400

    db_sites = client['Customer_info']
    found = False
    # Search for the site in the database
    for collection_name in db_sites.list_collection_names():
        if site.lower() == collection_name.lower():
            data = db_sites[collection_name].find_one()
            if not data:
                return jsonify({"error": "Site data not found"}), 404
                
            data = data[site]
            IP = data.get('Battery_ip')
            port = data.get('Battery_port', 502)  # Default port 502 for Modbus
            print(data, IP , port, "\n\n")
            found = True
            break

    if not found:
        return jsonify({"error": "Site not found"}), 404
    print("found: ", IP, port)
    async def reset_sequence(ip, port):
        # Initialize the Async Modbus TCP client
        plc_client = AsyncModbusTcpClient(ip, port=port)

        # Connect to the PLC
        if not await plc_client.connect():
            return {"error": "Unable to connect to PLC"}

        try:
            # Check the status of register 26
            result = await plc_client.read_holding_registers(26, 1, 1)
            if result.registers[0] != 1:
                await plc_client.write_register(26, 1, 1)
                await asyncio.sleep(2)
            await plc_client.write_register(27, 1, 1)
            await asyncio.sleep(5)
            await plc_client.write_register(27, 0, 1)
            await plc_client.write_register(26, 0, 1)
        finally:
            # Close the connection if it's open
            if plc_client.connected:
                 plc_client.close()

    # Run the reset sequence
    await reset_sequence(IP, port)

    return jsonify({"message": "Reset instruction issued! Please wait 20 seconds before retrying."})



def fejloversigtss():
    global db
    sti = "/volume1/homes/admin/Downloads/"
    # Alternativ sti kan aktiveres, hvis nødvendigt
    # sti = "C:/Users/FarhadAnayati/VisBlue/VisBlue all - Dokumenter/Product Development/Serviceside"

    # Skift arbejdssti, hvis nødvendigt
    if os.getcwd() != sti:
        os.chdir(sti)

    # Indlæs data fra CSV-filer
    datas = None
    for file_name in os.listdir():
        if file_name.endswith('.csv'):
            file_path = os.path.join(sti, file_name)
            datas = load_csv(file_path)
            break  # Indlæs kun den første CSV-fil

    if datas is None:
        return {"error": "Ingen CSV-data fundet"}

    Projekt_Nr = datas['Nr.']
    Projekt_prioritet = datas["Prioritet"]
    all_data = []

    # Gennemgå alle MongoDB-samlinger
    for collection_name in db.list_collection_names():
        data = db[collection_name].find_one(sort=[("time", pymongo.DESCENDING)])

        if not data:
            continue  # Spring over, hvis ingen dokumenter findes i samlingen

        latest_projectNr = data.get('ProjectNr')
        latest_error = data.get('Battery_status')
        latest_time = data.get('Time')

        # Gennemgå alle projekter i datas
        for i in range(len(Projekt_Nr)):
            if str(Projekt_Nr.iloc[i]) == str(latest_projectNr) + ".0":
                site_info = {
                    "Kunde": collection_name,
                    "ProjectNr": Projekt_Nr.iloc[i],
                    "Prioritet": Projekt_prioritet.iloc[i],
                    "Battery_status": latest_error,
                    "Time": latest_time
                }
                all_data.append(site_info)
                break  # Spring til næste samling, hvis der er et match

    if request.method == "POST":
        return "Post data processed"

    # Returner data eller render en HTML-skabelon
    return all_data  # Eller: render_template("Nyfejl.html", siteErrorData=all_data)

@main_blueprint.route('/get_data', methods=['POST', 'GET'])
def get_data():
	#print("HERE")
    data = fejloversigtss()
    #print("DATA: ", data)
    return  jsonify(data)