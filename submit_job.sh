#!/bin/bash
#SBATCH --job-name=calirate_HBV          # Job name
#SBATCH --output=calibrate_HBV_%j.log     # Output file name (%j expands to jobID)
#SBATCH --error=calibrate_HBV_%j.log      # Error file name (%j expands to jobID)
#SBATCH --time=00:05:00                  # Time limit (HH:MM:SS)
#SBATCH --nodes=1                        # Number of nodes
#SBATCH --ntasks=84                      # Number of tasks (one for each job), if you don't know numner of tasks beforehand there are ways to make this input dynamic as well
#SBATCH --cpus-per-task=1                # Number of CPU cores per task
#SBATCH --mem=2G                         # Memory per CPU core (adjust as needed)
#SBATCH --exclusive                      # Exclusive node allocation

# Load necessary modules
module load mpi4py
# Activate your virtual environment if needed
source ~/py-env/bin/activate

# Run your Python script
python run_cluster.py
