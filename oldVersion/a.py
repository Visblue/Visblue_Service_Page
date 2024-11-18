from Algo import newAlgo
from Energinet import el_prices
from Modbus import ModbusDevice
from VisblueApi import UploadAPI, WendewareAPI
from SiteInformations import siteInfo
from Database import VisblueDB
from datetime import datetime
from threading import Thread
import multiprocessing
import time
import numpy as np
import re
import pandas as pd
import os
import re
import warnings

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.expand_frame_repr', False)

warnings.filterwarnings("ignore")

"""Converts to epoch timestamp"""

DK1Priser = None
DK2Priser = None


def convertToEpoch(data):
    epoch = []
    for i in range(len(data)):
        year = int((data['Time'][i][0:4]).strip())
        month = int((data['Time'][i][5:7]).strip())
        day = int((data['Time'][i][8:10]).strip())
        hour = int((data['Time'][i][11:13]).strip())
        min = int(f"{int(str(data['Time'][i][14:16]).strip()):1d}")
        sec = int(f"{int(str(data['Time'][i][17:19]).strip()):1d}")

        epoch.append(int(datetime.timestamp(
            datetime(year, month, day, hour, min, sec))))

    return epoch


"""Used for adding 0s to SOC and Power (algoritme)"""


#def generate_soc_values(data_length, soc_value):
#    # Ensure SOC value is between 0 and 100
#    soc_value = max(0, min(soc_value, 100))
#    # Generate a list of SOC values normalized to [0, 1]
#    return [soc_value / 100] * data_length


def generate_battery_power_values(data_length):
    data = [0.0] * data_length
    return data


def get_battery_soc(battery: ModbusDevice) -> int:
    """Fetch the State of Charge (SOC) from the battery using Modbus."""
    try:
        battery.connect()
        soc = battery.get_battery_soc()
        return soc
    except Exception as e:
        print(f"Error: Failed to retrieve battery SOC. Reason: {e}")
        return 0  # Return -1 to indicate failure


def update_error(site, error):
    db_fault = VisblueDB()
   # print("HERE")
    db_fault.enter_db("Tarifstyring_kunder")
    db_fault.enter_col(site)
    fill = {'site': site}
    """existing_doc = db.col.find_one(fill)
    if existing_doc:
        print("Document exists:", existing_doc)
    else:
        print("No document found with the specified filter.")"""
    data = {"$set": {"ww_error": f"Error: {error}"}}
    db_fault.update_one(fill, data)
    db_fault.close()


def get_wendeware_forecasts(siteName, max_retries=3, delay=10):
    attempts = 0

    while attempts < max_retries:
        try:
            Wendeware = WendewareAPI(siteName)
            return Wendeware.getWendewareForecast()
        except Exception as e:
            update_error(siteName, e)
            print(
                f"main:getWendewareForecast - Attempt {attempts + 1} failed: ", siteName, " - : ", e)
            #exit()
            attempts += 1
            if attempts < max_retries:
                time.sleep(delay)
                return 100
            else:
                return f"Error: Failed to retrieve forecast after {max_retries} attempts"


""" This function is used for getting algoritme setpoints. All data from Wendeware and Energinet api and battery is used here. """


def get_algos(site_name, wendeware_forecast, energinet_elprice, soc, CAP):
 
    data = energinet_elprice.reset_index(drop=True)
    data['Consumption_forecast'] = wendeware_forecast['Consumption']
    data['PV_forecast'] = wendeware_forecast['PV']
    data['Cons-PV'] = wendeware_forecast['Cons-PV']    
    consumption_forecast = []
    pv_forecast = []
    sell_price= []
    buy_price = []
    for i in range(len(data['PV_forecast'])):# /1000).values.tolist() #[i / 1000 for i in data['PV_forecast'].values.tolist()] #/ 1000  # Convert from W to kW
        consumption_forecast.append(data['Consumption_forecast'].iloc[i]/1000) 
        pv_forecast.append(data['PV_forecast'].iloc[i]/1000)
        sell_price.append(data['Sell_Price [DKK/MWh]'].iloc[i])  # No conversion needed
        buy_price.append(data['Buy_Price [DKK/MWh]'].iloc[i])   # No conversion needed
  
    capacity = CAP  # int(data['CAP'][0])    
    soc = [soc/100] * (len(data)+1)        
    print(len(soc), len(sell_price))
    battery_power = [0.0]*len(data)
    print(battery_power,)
  
    # Run the optimization algorithm
    soc_list, setpoints, cost = newAlgo(
        pv_forecast, consumption_forecast, sell_price, buy_price, soc, battery_power, capacity)

    # Convert setpoints and SOC list to proper formats
    print(soc_list)
    data['Setpoints'] = (np.array(setpoints) *
                         1000).astype(int)  # Convert kW to W
    data['SOC_at_00Min'] = np.round(soc_list[:-1], 5)  # Exclude the last SOC value

    # Shift SOC values for SOC_at_59Min
    data['SOC_at_59Min'] = np.roll(data['SOC_at_00Min'], -1)
    return data

def get_algo(site_name, wendeware_forecast, energinet_elprice, soc, CAP):
    # Reverse energinet_elprice and reset index
    data = energinet_elprice.reset_index(drop=True)

    # Add forecast data to the dataframe
    data['Consumption_forecast']    = wendeware_forecast['Consumption']
    data['PV_forecast']             = wendeware_forecast['PV']
    data['Cons-PV']                 = wendeware_forecast['Cons-PV']
    # Convert data to numpy arrays for faster computation
    sell_price = []
    buy_price = []
    pv_forecast= []
    
    consumption_forecast = []
    for i in range(len(data['PV_forecast'])):# /1000).values.tolist() #[i / 1000 for i in data['PV_forecast'].values.tolist()] #/ 1000  # Convert from W to kW
        consumption_forecast.append(data['Consumption_forecast'].iloc[i]/1000) 
        pv_forecast.append(data['PV_forecast'].iloc[i]/1000)
        sell_price.append(data['Sell_Price [DKK/MWh]'].iloc[i])  # No conversion needed
        buy_price.append(data['Buy_Price [DKK/MWh]'].iloc[i])   # No conversion needed
    
    
    soc = int(soc)    
    # Extract system parameters
    capacity = CAP  # int(data['CAP'][0])
    battery_power = [0.0] * (len(data))
    soc = [soc/100] * (len(data)+1)   
    #print(soc) 
       
    # Run the optimization algorithm
    soc_list, setpoints, cost = newAlgo(pv_forecast, consumption_forecast, sell_price, buy_price, soc, battery_power, capacity)
    
    soc_list = [np.round(i,4) for i in soc_list]
    print(soc_list, "\n")
    data['Setpoints'] = (np.array(setpoints) *1000).astype(int)  # Convert kW to W
    data['SOC_at_00Min'] = soc_list[:-1]# Exclude the last SOC value

    # Shift SOC values for SOC_at_59Min
    data['SOC_at_59Min'] = np.roll(data['SOC_at_00Min'], -1)
    return data

def checkBatteries(site_name, battery_count):
    db_for_PLC = VisblueDB()
    db_for_PLC.enter_db('Tarifstyring_kunder')
    names = []
    user = site_name.lower()[:-2]
    IPs = []
    for i in range(battery_count):
        i += 1
        for x in db_for_PLC.db.list_collection_names():

            if re.search(f"{user}_{i}".lower(), x.lower()):
                names.append(x)
                # print("USER: " , f"{user}_{i}")
                db_for_PLC.enter_col(x)
                data = db_for_PLC.read_data()
                # print(data)
                break

    print(names, IPs)
    db_for_PLC.close()


db = VisblueDB()
db.enter_db("Tarifstyring_hour_data_new_algo")

# db_35hour = VisblueDB()
# db_35hour.enter_db("tarifstyring_35hour_data")

# row['sites'], row['antal_batteier'], row['battery_ip'], row['battery_port'], row['battery_version'], row['netselskab'])


def start(site_name, battery_count, site_ip, site_port, site_battery_version, CAP, site_netselskab):
    battery_port = 5502 if site_name == "Vigersted_1" else 5503 if site_name == "Vigersted_2" else 502
    # if battery_count > 1:
    #   battery_online_count = checkBatteries(site_name,int(battery_count))
    battery = ModbusDevice(site_ip, battery_port)
    soc = get_battery_soc(battery)
    wendeware_forecast = get_wendeware_forecasts(site_name)
    try:
        if wendeware_forecast.empty:
            print(f"Error: Failed to retrieve Wendeware forecast for {site_name}")
            update_error(site_name, "Failed to retrieve Wendeware forecast")
    except Exception as e:
            update_error(site_name, "Wendeware API down. Switching to emergency control")           
            print("EXITING DUE WW")
            exit()
	    # Fetch the Energinet electricity prices
    try:
        energinet = el_prices(site_name, site_netselskab)
        
        energinet_elprice = energinet.get_el_prices()
    except Exception as e:
        update_error(site_name, "Energinet API down. Switching to emergency control")
        print(f"Warning: Energinet API down. Switching to emergency control. Error: {e}")
        #battery.writeBat(26, 0)
        return

    # Run algorithm to process forecasts and pricing data    
    data = get_algo(site_name, wendeware_forecast, energinet_elprice, soc, CAP)

    # Convert price data to integer (MW -> W)
    data['Buy_Price [DKK/MWh]'] = (data['Buy_Price [DKK/MWh]']* 1000).astype(int)
    data['Sell_Price [DKK/MWh]'] = (data['Sell_Price [DKK/MWh]']* 1000).astype(int)
  

    # Prepare data for API upload
    data_to_api = pd.DataFrame(
        {'Timestamps': convertToEpoch(data), 'SetPoints': data['Setpoints']})
   
    data.insert(1, 'Name', site_name)

    global db
    # db_35hour.enter_col(site_name)
    db.enter_col(site_name)
    ## if int(battery.read_battery_register(26)) == 1:
    updateBatterySetpoint(site_name, battery, data['Setpoints'].iloc[0],
                          data['Buy_Price [DKK/MWh]'].iloc[0], data['Sell_Price [DKK/MWh]'].iloc[0])
##
    
    if len(data) > 35:
        save_35hourplan_to_csv(site_name, data)
    ##
    ## Insert data into Visblue DB
    db.insert_data(data.to_dict('records')[0])
    #db.client.close()
#
   ## # Upload data to API
    UploadAPI(data_to_api.to_dict(), site_name)
   # #
   ## # Log the latest data
    log_path = "/volume1/homes/admin/WendewareControl/Wendeware_Tarifstyring_V2/log_hour"
    save_to_csv(data, log_path, f"{site_name}_2024_Hour.csv", rows=1)
    print(data)
#
    update_error(site_name, 0)
#
    if battery.conn.is_socket_open():
       #  print("Closing battery connection")
        battery.conn.close()


def updateBatterySetpoint(site_name, battery, setpoint, buyprice, sellprice):
   # setpoint = 5000# for testing.
    if setpoint > 0:
        setpoint = int(setpoint)
    elif setpoint < 0:
        setpoint = -abs(setpoint)
    if battery.read_battery_register(26) == 1:
        battery.write_battery_register(26, 0)
    if battery.read_battery_register(26) == 0:
        #battery.write_battery_register(26, 0)
        #time.sleep(1)
        battery.write_battery_register(26, 1)
        time.sleep(0.2)
        battery.write_battery_register(29, buyprice)

    

    if setpoint > 0:
        battery.write_battery_register(24, setpoint)
        time.sleep(0.5)
        battery.write_battery_register(25, 0)
        
    elif setpoint < 0:
        battery.write_battery_register(25, abs(setpoint))
        time.sleep(0.5)
        battery.write_battery_register(24, 0)
        time.sleep(1)
    else:
        battery.write_battery_register(24, 0)
        time.sleep(0.2)
        battery.write_battery_register(25, 0)
    if setpoint > 0:
        if int(battery.read_battery_register(24)) != int(setpoint):            
            update_error(site_name, f"Setpoint is not set to discharge due register 26, setpoint: {setpoint}")
            print(site_name, " - Setpoint is not set to charge due register 26, setpoint: ", setpoint)
    elif setpoint < 0:
        if int(battery.read_battery_register(25)) != abs(int(setpoint)):            
            update_error(site_name, f"Setpoint is not set to discharge due register 26, setpoint: {setpoint}")
            print( site_name, " - Setpoint is not set to discharge due register 26, setpoint: ", setpoint)

    else:              
            update_error(site_name, 0)
    battery.write_battery_register(26, 1)
def testing_new_master_control(battery, data):
    cur_data_time = data['Time'].iloc[0]
    battery_setpoint = data['Setpoints'].iloc[0]
    el_price_current_hour = data['Buy_Price [DKK/MW]'].iloc[0]
    # print(battery.conn.is_socket_open(), cur_data_time, el_price_current_hour, battery_setpoint)
    battery.write_battery_register(30, battery_setpoint)
    battery.write_battery_register(29, el_price_current_hour)

    # check if setpoint is sent to the battery.
    time.sleep(1)
    if battery.read_battery_register(30) != battery_setpoint:
        raise BrokenPipeError('Battery has not received setpoitns!')


def save_35hourplan_to_csv(site_name, data):
    log_path = "/volume1/homes/admin/WendewareControl/Wendeware_Tarifstyring_V2/log_35hour"
    # db_35hour.insert_data(data.to_dict()[0])
    # db_35hour.client.close()
    save_to_csv(data, log_path, f"{site_name}_2024_35Hour.csv", rows=25)


def save_to_csv(data, directory, filename, rows=1):
    """Helper function to save data to CSV."""
    os.chdir(directory)
    file_path = os.path.join(directory, filename)
    # Only add header if file doesn't exist
    header = not os.path.exists(file_path)
    data.iloc[:rows].to_csv(file_path, mode='a',
                            decimal=',', sep=';', header=header)


def main():
    # Load site information from CSV
    site_info = siteInfo()
    # List to keep track of running threads
    # print("HERE")
   # quit()
    # quit()
    thread_counter = []
    start_time = time.time()
    for index, row in site_info.iterrows():
        if row['tarifstyring'] == 1:
            # Start a new process for each customer site
            #print(row['site'])
            # return
            # AlmenboB20
            listOfSites = ['almenbob19'.lower(), 'almenbob20'.lower(),'Kongerslev_1'.lower(), 'Espergarde_1'.lower()]
            if row['site'].lower() in listOfSites:
                #print(True, row['site'])
                continue
            # or  re.search('Vigersted'.lower() ,row['site'].lower()) :# or csv['Customer'][i] != 'Kattegatcentret_1':
            if not re.search('Gelstedskole'.lower(), row['site'].lower()):
            #   print(row['site'])
                continue
            # or csv['Customer'][i] != 'Kattegatcentret_1':
            if re.search('Kattegatcent'.lower(), row['site'].lower()) or re.search('Vigersted'.lower(), row['site'].lower()) or re.search('Varlose'.lower(), row['site'].lower()) or re.search('Solvang'.lower(), row['site'].lower()):
                #print("Skip: ", row['site'] )
                continue
            #

           # print("START")
            process = multiprocessing.Process(target=start, args=(
                row['site'], row['battery_count'], row['battery_ip'], row['battery_port'], row['battery_version'], row['capacity'], row['netselskab']))

            # print(row['site'])
            process.start()
            thread_counter.append(process)
            # Optional: Sleep to avoid overwhelming the system
            time.sleep(1)
        else:
        # print("Tarifstyring is not enabled ", row['site'])
            pass
    # Wait for all processes to finish
    for thread in thread_counter:
        thread.join()

    print("Total execution time: {:.2f} seconds".format(
        time.time() - start_time))


if __name__ == "__main__":
    main()
