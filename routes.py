
#rom app import app,render_template, request, redirect, url_for, send_file
import pymongo 
import os 
import pandas as pd
from flask import render_template, request, Blueprint




main_blueprint = Blueprint('main', __name__)
client = pymongo.MongoClient(f"mongodb://172.20.33.151:27017")
db = client["SiteErrorLog"]



@main_blueprint.route('/fejloversigt', methods=['GET'])  
def fejloversigt():       
        global db    
        sti = "/volume1/homes/admin/Downloads/"
        sti= "C:/Users/FarhadAnayati/VisBlue/VisBlue all - Dokumenter/Product Development/Serviceside"
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
            data = db[collection_name].find_one(sort=[("time", pymongo.DESCENDING)])
            for i in range(len(datas['Nr.'])):
                projekt_nr_item = data['ProjektNr']
                nr_datas = Projekt_Nr.iloc[i]
                prioritet = Projekt_prioritet.iloc[i]
                if str(nr_datas) == str(projekt_nr_item)+".0":                                              
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
        
        return render_template("fejloversigt.html", siteErrorData=all_data)
    
