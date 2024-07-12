import pandas as pd
import numpy as np
import glob
import matplotlib.pyplot as plt
import seaborn as sns
from hbv_model import hbv

########1. Check Parameters distribution
csv_files = glob.glob("output/parameter/*.csv")
file_all = []

for i in range(len(csv_files)):
    file_in = pd.read_csv(csv_files[i])
    file_all.append(file_in)
#end of loop

#columns to make histogram

final_file = pd.concat(file_all, ignore_index=True)
columns_to_plot = final_file.columns[0:-1]

# Number of subplots (rows and columns)
rows, cols = 4, 5

# Create subplots
fig, axes = plt.subplots(rows, cols, figsize=(20, 16))

# Flatten the axes array for easy iteration
axes = axes.flatten()

# Plot histograms for the selected columns
for i, column in enumerate(columns_to_plot):
    axes[i].hist(final_file[column], bins=10, alpha=0.7)
    axes[i].set_title(f'Histogram of {column}')
    axes[i].set_xlabel(column)
    axes[i].set_ylabel('Frequency')

# Turn off the remaining empty subplots
for j in range(i + 1, len(axes)):
    fig.delaxes(axes[j])

# Adjust layout
plt.tight_layout()
plt.show()




########2. Check ovs vs sim flows for any one watershed
#read in any of the input file and compare ovs vs sim flows
file_in = pd.read_csv("data/hbv_input_01094400.csv")
file_in["date"] = pd.to_datetime(file_in[["year", "month", "day"]])
#read corresponding calibrated parameters set
param_in = pd.read_csv("output/parameter/param_01094400.csv")
nse_val = pd.read_csv("output/nse/nse_01094400.csv")
nse_val #Just to have an idea of nse for this station
param_in = param_in.iloc[0, :-1]
file_in["sim_flow"] = hbv(param_in, file_in["precip"], file_in["tavg"], file_in["date"], file_in["latitude"], routing=1)

#plot for calibration period
file_in_calib = file_in[file_in["year"] <= 2005]
plt.figure(figsize=(10,6))
plt.plot(file_in_calib["date"], file_in_calib["qobs"], color = "blue", label = "OBS")
plt.plot(file_in_calib["date"], file_in_calib["sim_flow"], color = "red", label = "SIM")
plt.legend()
plt.title("Simulated vs Observed flow during calibration period")
plt.show()

#plot for validation period
file_in_valid = file_in[file_in["year"] > 2005]
plt.figure(figsize=(10,6))
plt.plot(file_in_valid["date"], file_in_valid["qobs"], color = "blue", label = "OBS")
plt.plot(file_in_valid["date"], file_in_valid["sim_flow"], color = "red", label = "SIM")
plt.legend()
plt.title("Simulated vs Observed flow during validation period")
plt.show()



########3. Check NSE
def nse(q_obs, q_sim):
    denominator = np.sum((q_obs - (np.mean(q_obs)))**2)
    numerator = np.sum((q_obs - q_sim)**2)
    nse_value = 1 - (numerator/denominator)
    return nse_value

#calculate nse values for both calibration and validation
station = pd.read_csv("station_id.csv", dtype={"station_id":str})
nse_df_calib = []
nse_df_valid = []
calib_nse_df = pd.DataFrame() #dataframe that will have params with nse for all stations
for station_id in station["station_id"]:
    #read input csv file
    df = pd.read_csv(f"data/hbv_input_{station_id}.csv")
    #read calibrated parameters
    calib_params_df = pd.read_csv(f"output/parameter/param_{station_id}.csv", dtype = {'station_id':str})
    calib_params = calib_params_df.iloc[0, :-1]
    q_obs = df["qobs"] #validation data / observed flow
    q_sim = hbv(calib_params, df["precip"], df["tavg"], df["date"], df["latitude"], routing = 1)
    df["q_sim"] = q_sim

    #split calibration and validation
    df_calibration = df[df["year"] <= 2006]
    df_validation = df[df["year"] > 2006]

    nse_calibration = nse(df_calibration["qobs"], df_calibration["q_sim"])
    nse_validation = nse(df_validation["qobs"], df_validation["q_sim"])

    #append entries into the list
    nse_df_calib.append(nse_calibration)
    nse_df_valid.append(nse_validation)

    #dataframe that binds params with nse
    calib_params_df["nse_calib"] = nse_calibration
    calib_params_df["nse_valid"] = nse_validation
    calib_nse_df = pd.concat([calib_nse_df, calib_params_df])
#End of for loop
#save the final dataframe
calib_nse_df.to_csv("output/Caliparams_nse.csv", index=False)


#make cdf plot
df_plot = calib_nse_df.dropna()
sns.kdeplot(df_plot['nse_calib'], cumulative=True, bw_adjust=0.3, color="red", label = "Calibration(1994-2005)")
sns.kdeplot(df_plot['nse_valid'], cumulative=True, bw_adjust=0.3, color="blue", label = "Validation(2006-2015)")
plt.xlabel("NSE")
plt.ylabel("CDF")
plt.xlim(0,1)
plt.legend()

