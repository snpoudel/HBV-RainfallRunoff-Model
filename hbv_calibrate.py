#import packages
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from hbv_model import hpv #imported from local python script
from geneticalgorithm import geneticalgorithm as ga # install package first

#read input csv file
df = pd.read_csv("C:/Cornell/HBV/hbv_model_python/data/hbv_input_01094400.csv")
#hpv model input
p = df["precip"]
temp = df["tavg"]
latitude = df["latitude"]
routing = 0 #no routing
q_obs = df["qobs"] #validation data / observed flow

##genetic algorithm for hbv model calibration
#reference: https://github.com/rmsolgi/geneticalgorithm
#write a function you want to minimize
def rmse(pars):
    q_sim = hpv(pars, p, temp, latitude, routing)
    rmse_value = np.sqrt(np.sum((q_obs - q_sim) ** 2)) 
    return rmse_value #minimize this (use negative sign if you need to maximize)

varbound = np.array([[1,5000], #fc
                     [1,7], #beta
                     [1,500], #lp
                     [1,10], #sfcf
                     [1,5], #tt
                     [0,10], #cfmax
                     [0.01,0.99], #k0
                     [0.01,0.99], #k1
                     [0.0001,0.9], #k2
                     [0.01,50], #uzl
                     [0.001,0.9], #perc
                     [0.1,10]]) #coeff_pet

algorithm_param = {'max_num_iteration':500,
                   'population_size':50,
                   'mutation_probability':0.2,
                   'elit_ratio':0.01,
                   'crossover_probability':0.5,
                   'parents_portion':0.3,
                   'crossover_type':'uniform', #one_point | two_point | uniform
                   'max_iteration_without_improv':None}

model = ga(function = rmse,
           dimension = 12, #number of parameters to be calibrated
           variable_type= 'real',
           variable_boundaries = varbound,
           algorithm_parameters = algorithm_param)

model.run()

#output of the genetic algorithm/best parameters
best_parameters = model.output_dict

param_value = best_parameters["variable"]
rmse = best_parameters["function"]