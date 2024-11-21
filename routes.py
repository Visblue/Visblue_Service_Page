
# rom app import app,render_template, request, redirect, url_for, send_file
import pymongo
import os
import pandas as pd
from flask import render_template, request, Blueprint
from pymodbus.client import ModbusTcpClient
import time
import re 
main_blueprint = Blueprint('main', __name__)
client = pymongo.MongoClient(f"mongodb://172.20.33.163:27017")
db = client["error_log"]


@main_blueprint.route('/fejloversigt', methods=['GET'])
def fejloversigt():
    global db
    sti = "/volume1/homes/admin/Downloads/"
    sti = "C:/Users/FarhadAnayati/VisBlue/VisBlue all - Dokumenter/Product Development/Serviceside"
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
        data = db[collection_name].find_one(
            sort=[("time", pymongo.DESCENDING)])
        for i in range(len(datas['Nr.'])):
            projekt_nr_item = data['ProjektNr']
            nr_datas = Projekt_Nr.iloc[i]
            prioritet = Projekt_prioritet.iloc[i]
            if str(nr_datas) == str(projekt_nr_item)+".0":
                site_info = {
                    "name":     collection_name,
                    'ProjektNr': nr_datas,
                    'Prioritet': prioritet,
                    "error":  data["error"],  # ,	 "N/A"),
                    "time":  data["time"]  # , "N/A")
                }
                all_data.append(site_info)
                break
    if request.method == "POST":
        return "Post data processed"

    return render_template("fejloversigt.html", siteErrorData=all_data)



db_sites = client['Systems']
@main_blueprint.route('/reset', methods=['POST'])
def reset_battery():
    form_data = request.form  # For POST
    query_data = request.args  # For GET
    print("form_data:", form_data)  # Debug POST data
    print("query_data:", query_data)  # Debug GET data

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

    print(f"{site} - Restarted")

    # Update restart status when the operation is completed successfully
    


    return "SUCCESS"
