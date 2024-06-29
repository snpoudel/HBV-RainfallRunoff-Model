#import packages
import numpy as np
import pandas as pd
import os
from hbv_model import hbv #imported from local python script
from geneticalgorithm import geneticalgorithm as ga # install package first

#read stationID
#stationid = pd.read_csv("station_id.csv", dtype={"station_id":str})

#function that reads station ID, takes input for that ID and outputs calibrated parameters and nse values
def calibNSE(station_id):
    #read input csv file
    df = pd.read_csv(f"data/hbv_input_{station_id}.csv")
    #only used data upto 2005 for calibration
    df = df[df["year"] < 2006]
    #hbv model input
    p = df["precip"]
    temp = df["tavg"]
    latitude = df["latitude"]
    routing = 0 #no routing
    q_obs = df["qobs"] #validation data / observed flow

    ##genetic algorithm for hbv model calibration
    #reference: https://github.com/rmsolgi/geneticalgorithm
    #write a function you want to minimize
    def nse(pars):
        q_sim = hbv(pars, p, temp, latitude, routing)
        denominator = np.sum((q_obs - (np.mean(q_obs)))**2)
        numerator = np.sum((q_obs - q_sim)**2)
        nse_value = 1 - (numerator/denominator)
        return -nse_value #minimize this (use negative sign if you need to maximize)

    varbound = np.array([[1,1000], #fc
                        [1,7], #beta
                        [0.01,1], #lp
                        [1,3], #sfcf
                        [-1,4], #tt
                        [0.1,15], #cfmax
                        [0.005, 0.5], #cfr
                        [0.01, 0.2], #cwh
                        [0.01,0.99], #k0
                        [0.01,0.99], #k1
                        [0.0001,0.99], #k2
                        [0.01,500], #uzl
                        [0.001,0.99], #perc
                        [0.1,10]]) #coeff_pet

    algorithm_param = {
        'max_num_iteration': 1000,                # Generations, higher is better, but requires more computational time
        'max_iteration_without_improv': None,   # Stopping criterion for lack of improvement
        'population_size': 1000,                  # Number of parameter-sets in a single iteration/generation(to start with population 10 times the number of parameters should be fine!)
        'parents_portion': 0.2,                 # Portion of new generation population filled by previous population
        'elit_ratio': 0.01,                     # Portion of the best individuals preserved unchanged
        'crossover_probability': 0.5,           # Chance of existing solution passing its characteristics to new trial solution
        'crossover_type': 'uniform',            # Create offspring by combining the parameters of selected parents
        'mutation_probability': 0.1             # Introduce random changes to the offspring’s parameters (0.1 is 10%)
    }

    model = ga(function = nse,
            dimension = 14, #number of parameters to be calibrated
            variable_type= 'real',
            variable_boundaries = varbound,
            algorithm_parameters = algorithm_param)

    model.run()

    #output of the genetic algorithm/best parameters
    best_parameters = model.output_dict
    param_value = best_parameters["variable"]
    nse_value = best_parameters["function"]
    nse_value = -nse_value #nse function gives -ve values, which is now reversed here to get true nse
    #convert into a dataframe
    df_param = pd.DataFrame(param_value).transpose()
    df_param = df_param.rename(columns={0:"fc", 1:"beta", 2:"lp", 3:"sfcf", 4:"tt", 5:"cfmax",
                             6:"cfr", 7:"cwh",  8:"k0", 9:"k1", 10:"k2", 11:"uzl", 12:"perc", 13:"coeff_pet"})
    df_param["station_id"] = str(station_id)
    df_nse = pd.DataFrame([nse_value], columns=["nse"])
    df_nse["station_id"] = str(station_id)
    #save as a csv file
    df_param.to_csv(f"output/parameter/param_{station_id}.csv", index = False)
    df_nse.to_csv(f"output/nse/nse_{station_id}.csv", index = False)
    #End of function

#call the function
