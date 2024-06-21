'''
This script reads in input datasets and make them ready to be input into the hbv model
Specifically, we need to have these variables (precip, tavg, latitude) ready
for all the watersheds of interest for hbv rainfall runoff modeling 
'''
#import libraries
import numpy as np
import pandas as pd
import os
import re

##Step 1: Extract the list of station ID from the filename
#path where csv files are present
csv_path = 'C:/Cornell/HBV/from_sungwook/input data/lstm_input'
#initialize empy list to store station ID
station_id = []
#define regular expression patter to extract station id from file name
pattern = re.compile(r'lstm_input_(\d+)\.csv')
#loop through csv files in the folder and extract stationID
for filename in os.listdir(csv_path):
    match = pattern.search(filename)
    if match:
        id = match.group(1)
        station_id.append(id)
#end of loop
df_stationID = pd.DataFrame(station_id, columns=["station_id"])
df_stationID.to_csv("station_id.csv", index=False)
##Step2: Loop through each station ID and generate new sets of csv files that only has precip & tavg
lat_in = pd.read_csv('C:/Cornell/HBV/from_sungwook/input data/stnID_withLatLon.csv')

for station in station_id:  
    file_in = pd.read_csv(f"C:/Cornell/HBV/from_sungwook/input data/lstm_input/lstm_input_{station}.csv")
    precip = file_in["pr"]
    qobs = file_in["q"]
    tmax = file_in["tmax"]
    tmin = file_in["tmin"]
    tavg = tmax/2 + tmin/2
    year = file_in["Year"]
    month = file_in["Month"]
    day = file_in["Day"]
    id = station
    latitude = lat_in["LAT_CENT"][lat_in["STAID"] == int(station)].values[0]
    #create a dictionary for these variables 
    dictionary = { "id":id, "year":year, "month":month, "day":day,
                  "tavg":tavg, "precip": precip, "qobs":qobs, "latitude":latitude }
    #create dataframe from dictionary
    df = pd.DataFrame(dictionary)
    #save dataframe as a csv file
    df.to_csv(f"C:/Cornell/HBV/from_sungwook/input data/hbv_input/hbv_input_{station}.csv", index = False)
#end of loop
