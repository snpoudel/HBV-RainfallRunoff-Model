## This repo contains the following:
- data: This folder contains the data for few basins to try the HBV model
- output: This folder contains two subfolders 'nse' and 'parameter' which stores the output nse and parameter values after model calibration
- hbv_model.py: This script contains the HBV model
- hbv_calibrate.py: This scripts contains a function to calibrate the HBV model using genetic algorithm, the script then reads the data from the `data` folder and calibrates the model for each basin and stores the output in the `output` folder
- station_id.csv: This file contains the station id for few basins to try the HBV model