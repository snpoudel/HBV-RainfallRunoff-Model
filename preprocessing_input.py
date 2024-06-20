'''
This script reads in input datasets and make them ready to be input into the hbv model
Specifically, we need to have these variables (precip, tavg, latitude) ready
for all the watersheds of interest for hbv rainfall runoff modeling 
'''
#import libraries
import numpy as np
import os
import re

##Extract the list of station ID from the filename
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
        id = int(match.group(1))
        station_id.append(id)
#end of loop

