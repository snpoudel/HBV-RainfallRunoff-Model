import pandas as pd
import glob
import matplotlib.pyplot as plt
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
rows, cols = 4, 4

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




########3. Check ovs vs sim flows
#read in any of the input file and compare ovs vs sim flows
file_in = pd.read_csv("data/hbv_input_01094400.csv")
file_in["date"] = pd.to_datetime(file_in[["year", "month", "day"]])
#read corresponding calibrated parameters set
param_in = pd.read_csv("output/parameter/param_01094400.csv")
nse_val = pd.read_csv("output/nse/nse_01094400.csv")
nse_val #Just to have an idea of nse for this station
param_in = param_in.iloc[0, :-1]
sim_flow = hbv(param_in, file_in["precip"], file_in["tavg"], file_in["latitude"], routing=0)

#plot for calibration period
#calibration is upto 2005

plt.figure(figsize=(10,6))
plt.plot(file_in["date"], file_in["qobs"], color = "blue", label = "OBS")
plt.plot(file_in["date"], sim_flow, color = "red", label = "SIM")
plt.legend()
plt.title("Simulated vs Obseved flow ")
plt.show()



########2. Check NSE
#NSE for calibration period
csv_files = glob.glob("output/nse/*.csv")
file_all = []

for i in range(len(csv_files)):
    file_in = pd.read_csv(csv_files[i])
    file_all.append(file_in)
#end of loop
final_file = pd.concat(file_all, ignore_index=True)

#make plot
#histogram
plt.hist(final_file["nse"])
plt.xlabel("NSE")
plt.ylabel("Frequency")
plt.title("Histogram")