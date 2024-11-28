import pandas as pd
import os
from datetime import datetime



def driftsikring_csv():
        folder = "/volume1/homes/admin/Downloads/"    
        #folder = "C:/Users/FarhadAnayati/VisBlue/VisBlue all - Dokumenter/Product Development/Serviceside"    
        if os.getcwd() != folder:   
            os.chdir(folder)
        try:        
            for file in os.listdir():
                if file.endswith(".csv"):
                    csv = open(file, "r")
                    data = pd.read_csv(csv)                    
                    csv.close()
                    break       
        except Exception as e:
            print("Something went wrong with getting CSV DA ", e)
        return data
               
def driftsikring(project_nr):
    DATA = {}
    data = driftsikring_csv()      
    
    csv_projetNr                   = data['Nr.']
    csv_driftsikring_aftale_nr     = data['DA nr. ']
    csv_driftsikring_aftale_Active = data['DA: Aktiv']
    csv_spotpris_aftale_nr         = data['SA nr.']
    csv_spotpris_aftale_Active     = data['SA: Aktiv']
    csv_prioritet                  = data['Prioritet']
    csv_signed                     = data['Signed']   
    try:
        for i in range(len(csv_projetNr)):    
           # print(float(csv_projetNr[i]), project_nr)
            if project_nr== float(csv_projetNr[i]):                
                split_signed_date = str(csv_signed[i]).split(" ")                
                if  len(split_signed_date) >= 2 :                                                                
                    SINGED_DATE = split_signed_date[0]     
                    
                    DATA['Signed_date'] = SINGED_DATE
                    DATA['Signed_time'] = (datetime.strptime(SINGED_DATE, "%Y-%m-%d") - datetime.now()).days
                    DATA['Site_prioritet'] = csv_prioritet[i]
                    if str(csv_prioritet[i]) == "2":
                        DATA['Site_prioritet_color'] = "red"
                if str(csv_driftsikring_aftale_Active[i]).lower()== "x":
                    DATA['DA_nr'] = csv_driftsikring_aftale_nr[i]
                if str(csv_spotpris_aftale_Active[i]).lower( )== "x":
                    DATA['SA_nr'] = csv_spotpris_aftale_nr[i]             
    except Exception as e:          
        print(f"Error getting battery data for - {e}",i)
        pass
    return DATA


""" optimeret"""

"""
import pandas as pd
import os
from datetime import datetime

def driftsikring_csv():
    folder = "/volume1/homes/admin/Downloads/"
    #folder = "C:/Users/FarhadAnayati/VisBlue/VisBlue all - Dokumenter/Product Development/Serviceside"
    if os.getcwd() != folder:
        os.chdir(folder)
    try:
        for file in os.listdir():
            if file.endswith(".csv"):
                with open(file, "r") as csv:
                    data = pd.read_csv(csv)
                break
    except Exception as e:
        print("Something went wrong with getting CSV DA ", e)
    return data

def driftsikring(project_nr):
    DATA = {}
    data = driftsikring_csv()

    csv_projetNr = data['Nr.']
    csv_driftsikring_aftale_nr = data['DA nr. ']
    csv_driftsikring_aftale_Active = data['DA: Aktiv']
    csv_spotpris_aftale_nr = data['SA nr.']
    csv_spotpris_aftale_Active = data['SA: Aktiv']
    csv_prioritet = data['Prioritet']
    csv_signed = data['Signed']

    for i in range(len(csv_projetNr)):
        try:
            if project_nr == float(csv_projetNr[i]):
                split_signed_date = str(csv_signed[i]).split(" ")
                if split_signed_date:
                    SINGED_DATE = split_signed_date[0]

                    DATA['Signed_date'] = SINGED_DATE
                    DATA['Signed_time'] = (datetime.strptime(SINGED_DATE, "%Y-%m-%d") - datetime.now()).days
                    DATA['Site_prioritet'] = csv_prioritet[i]
                    if csv_prioritet[i] == 2:
                        DATA['Site_prioritet_color'] = "red"
                    if csv_driftsikring_aftale_Active[i].lower() == "x":
                        DATA['DA_nr'] = csv_driftsikring_aftale_nr[i]
                    if csv_spotpris_aftale_Active[i].lower() == "x":
                        DATA['SA_nr'] = csv_spotpris_aftale_nr[i]
        except (ValueError, TypeError) as e:
            print(f"Error processing row {i}: {e}")
    return DATA"""