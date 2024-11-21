import requests
import pandas as pd
import time
import calendar
from datetime import tzinfo, datetime
from dateutil import tz
import numpy as np
import json
import os
import re

DK1Priser = None
DK2Priser = None

TarifData = {"Cerius A/S" : 0,
             "Dinel A/S" : 0,
             "NOE":     0,
             "Radius Elnet A/S" : 0,
             "Konstant Net A/S" : 0,
             "N1 A/S" : 0,
             "Midtfyns Elforsyning A.m.b.a" : 0,
             "Dinel A/S" : 0,
             "NKE-Elnet" : 0,   
             "Vores Elnet" : 0,
             'Trefor' : 0,
             'EL-NET Kongerslev A/S' : 0 ,            
             }
def WinterOrSummer():
    curTime = datetime.today()
    Vinter = [10, 11, 12, 1, 2, 3]
    Sommer = [4, 5, 6, 7, 8, 9]
    aarstid = None
    for i in range(6):
        if curTime.month == Vinter[i]:
            aarstid = 0
    for i in range(6):
        if curTime.month == Sommer[i]:
            aarstid = 1
    return aarstid


def Tarif(årstid, Tariffer, i):
    lav = round(float(Tariffer[f"{årstid}_Lav"][i]) / 100, 4)
    hoj = round(float(Tariffer[f"{årstid}_Hoj"][i]) / 100, 4)
    spids = round(float(Tariffer[f"{årstid}_Spids"][i]) / 100, 4)
    systemtarif = round(float(Tariffer["Systemtarif"][i]) / 100, 4)
    Netabonnement = round(float(Tariffer["Netabonnement"][i]) / 365 / 24, 4)
    Systemabonnement = round(float(Tariffer["Systemabonnement"][i]) / 365 / 24, 4)
    Transmissionsnettarif = round(float(Tariffer["Transmissionsnettarif"][i]) / 100, 4
    )
    #CAP = int(Tariffer["Kapacitet"][i])
   # EFF = float(Tariffer["Virkningsgrad"][i])
    T0 = int(Tariffer["LavTid"][i][0:2])
    T5 = int(Tariffer["LavTid"][i][-2:])
    T6 = int(Tariffer["HojTid"][i][0:2])
    T16 = int(Tariffer["HojTid"][i][-2:])
    T17 = int(Tariffer["SpidsTid"][i][0:2])
    T20 = int(Tariffer["SpidsTid"][i][-2:])
    T21 = int(Tariffer["HojTidEfter"][i][0:2])
    T24 = int(Tariffer["HojTidEfter"][i][-2:])
    return lav, hoj, spids, systemtarif, Netabonnement, Systemabonnement, Transmissionsnettarif,  T0, T5, T6, T16, T17, T20, T21, T24


def getTarif(Kunde, Tariffer, PriceArea, Netselskab):
    
    Elafgift = 95.13 / 100
    aarstid = WinterOrSummer()
    
    #print(aarstid)
    global TarifData

    # os.chdir("/volume1/homes/admin/Visblue/Wendeware_3")
    #os.chdir("/volume1/homes/admin/WendewareControl/WendewareControlV1")
    
    #print(Tariffer)
    
    KundeAct = False
    try:
        for name, data in TarifData.items():                
            if name.strip() == Netselskab.strip() and data != 0:                      
                return TarifData[name]       
    except:                
        return TarifData[name]       
    #TarifData[Netselskab.strip()]= 1
    
    #return
    try: 
        
        if TarifData[Netselskab] == 0:
            
            for i in range(len(Tariffer["Kunde"])): 
                #print("-->: ",Kunde[0:5], re.search( f"^{Kunde[0:6]}" ,  Tariffer["Kunde"][i].lower() ))
                if aarstid == 0:
                    if re.search( "^" + Kunde.lower()[0:5], Tariffer["Kunde"][i].lower(),  ): #Tariffer["Kunde"][i].lower() == Kunde.lower():                
                        pricearea = PriceArea              
                        
                        lav, hoj, spids, systemtarif, Netabonnement, Systemabonnement, Transmissionsnettarif, T0, T5, T6, T16, T17, T20, T21, T24 = Tarif('Vinter', Tariffer, i)
                        KundeAct = True
                if aarstid == 1:                        
                    if re.search("^" + Kunde.lower()[0:5], Tariffer["Kunde"][i].lower(),  ):# == Kunde.lower():                   
                        PriceArea = PriceArea                    
                        lav, hoj, spids, systemtarif, Netabonnement, Systemabonnement, Transmissionsnettarif,  T0, T5, T6, T16, T17, T20, T21, T24 = Tarif('Sommer', Tariffer, i)
                        KundeAct = True
            if KundeAct == False:
                return 0,0
            Priser = pd.DataFrame(columns=["Priser"], index=range(0, 24))
            for i in range(len(Priser)):
                if i >= T0 and i < T5:
                    Priser.at[i, "Priser"] = lav + Elafgift + systemtarif + Netabonnement + Systemabonnement + \
                        Transmissionsnettarif
                if i >= T6 and i < T17:
                    Priser.at[i, "Priser"] = hoj + Elafgift + systemtarif + Netabonnement + Systemabonnement + \
                        Transmissionsnettarif
                if i >= T17 and i < T21:
                    Priser.at[i, "Priser"] = spids + Elafgift + systemtarif + Netabonnement + Systemabonnement + \
                        Transmissionsnettarif
                if i >= T20 and i < T24:
                    Priser.at[i, "Priser"] = hoj + Elafgift + systemtarif + Netabonnement + Systemabonnement + \
                        Transmissionsnettarif
            if Priser.empty:
                return ValueError("None")
            TarifData[Netselskab] = Priser
            #print(TarifData[Netselskab])
            return Priser
        else:            
            return TarifData[Netselskab]

    except Exception as e:
            print(Kunde, "ERROR Elpriser", e)       
            return TarifData[Netselskab]
            


def energinet_SpotPriser(pricearea="DK1", Kunde = None):
    global DK1Priser,DK2Priser
    
    curTime = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    try:
        if pricearea == 'DK1' and DK1Priser != None:        
            
            return DK1Priser
    except:            
        return DK1Priser
    
    try:
        if pricearea == 'DK2' and DK2Priser != None:    
            return DK2Priser
    except:                    
        return DK2Priser    
    
    try:
        
        Today = EnerginetReqSpotprice(pricearea, curTime)                    
    except:
        return 0
    
    return Today

def EnerginetReqSpotprice(pricearea, curTime):
    global DK1Priser, DK2Priser       
    Api_URL = f'https://api.energidataservice.dk/dataset/Elspotprices?&columns=PriceArea,SpotPriceDKK,HourDK&filter={{"PriceArea":"{pricearea}"}}&'
    
    data = requests.get(Api_URL)
    if data.status_code != 200:
        return 0
    data = pd.DataFrame(json.loads(data.text)['records'][0:35])
    data = data[::-1]             
    
    for i in range(len(data)):
        data.at[i, 'HourDK'] = data['HourDK'][i].replace('T', ' ')
    data.sort_values('HourDK', inplace=True)
    Time = []

    Price = []
    for i in range(len(data)):
        if data['HourDK'][i][0:10] == curTime[0:10]:
            if data['HourDK'][i][11:13] >= curTime[11:13]:
                Time.append(data['HourDK'][i])
                Price.append(data['SpotPriceDKK'][i]/1000)
        if data['HourDK'][i][0:10] > curTime[0:10]:
            Time.append(data['HourDK'][i])
            Price.append(data['SpotPriceDKK'][i]/1000)

    Today = pd.DataFrame({'Time': Time, 'Spot_Price': Price, })
    if pricearea == 'DK1': 
        DK1Priser = Today
    else:
        DK2Priser = Today
    return Today


def Elprices(Kunde,):  
  #  os.chdir("/volume1/web/ServicePage/TestVersion/Test")
    if re.search('Værløse Svømmehal', Kunde):        
        Kunde = "Værløse Svømmehal_1"
    if re.search('Bosei', Kunde):
        Kunde = "Bosei_1"
    if re.search('Birkerød Idrætscenter', Kunde):
            Kunde = "Birkerød Idrætscenter_1"
    if re.search('Vigersted', Kunde):
            Kunde = "Vigersted Skole_1"
    if re.search('Lille Birkholm', Kunde):
            Kunde = "Lille Birkholm_1_rum1"
    if re.search('KIE', Kunde):
            Kunde = "KIE_1"

    if re.search('Solvangskolen', Kunde):
            Kunde = "Solvangskolen_1"     

    if re.search('AlmenBo afd.', Kunde):
        Kunde = "AlmenBo afd. 15_2_blok20"   

    
    if re.search('Ringe Kostskole', Kunde):
        Kunde = "Ringe Kostskole_1"
    if re.search('Kattegatcentret', Kunde):
        Kunde = "Kattegatcentret_1"
    data = open("KundeInfoTarif.csv", 'r', encoding='utf-8')
    Tariffer = pd.read_csv(data)
    data.close()
    
    #Tariffer = pd.read_csv("KundeInfoTarif.csv")
    
    global TarifData
    PriceArea = ""
    Netselskab = ""
    for i in range(len(Tariffer)): 
        #print(Tariffer['Kunde'][i],Kunde)
        if (Tariffer['Kunde'][i] == Kunde):
            PriceArea = Tariffer['Lokation'][i]
            Netselskab = Tariffer['Netselskab'][i]
            
            break
           # print(Netselskab)
           
    
    #( TarifData[Netselskab] , TarifData)
   
   
    LastPerioder = getTarif(Kunde, Tariffer, PriceArea, Netselskab)
   # return
    Spotprices = energinet_SpotPriser(PriceArea, Kunde)       

    try:
        if Spotprices == 0:
            return 0
    except:
        pass

    
    add_Last = 0
    curTime = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    Time = []
    BuyPrice = []
    SpotPrice = []
    sellPrice = []
    
    
    for i in range(len(Spotprices)):
        if Spotprices['Time'][i][0:13] >= curTime[0:13]:
            for x in range(len(LastPerioder)):
                if x == int(Spotprices['Time'][i][11:13]):
                    add_Last = LastPerioder['Priser'][x]

            Time.append(Spotprices['Time'][i])
            sellPrice.append(round(Spotprices['Spot_Price'][i]*1.25 + 0.12, 2))
            SpotPrice.append(round(Spotprices['Spot_Price'][i]*1.25 + 0.12, 2))
            BuyPrice.append(round(round(Spotprices['Spot_Price'][i]*1.25, 2)+round(add_Last, 2),2))

    Today = pd.DataFrame({'Time': Time, 'Spot_Price [kW]': SpotPrice,
                         "Buy_Price [kW]": BuyPrice, 'Sell_Price [kW]': sellPrice})
    
    #print("ADSD")
    return Today

