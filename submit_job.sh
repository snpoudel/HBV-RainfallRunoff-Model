#!/bin/bash
#SBATCH --job-name=calirate_HBV          # Job name
#SBATCH --output=calirate_HBV_%j.log     # Output file name (%j expands to jobID)
#SBATCH --error=calirate_HBV_%j.log      # Error file name (%j expands to jobID)
#SBATCH --time=00:05:00                  # Time limit (HH:MM:SS)
#SBATCH --nodes=2                        # Number of nodes
#SBATCH --ntasks=84                      # Number of tasks (one for each job)
#SBATCH --cpus-per-task=1                # Number of CPU cores per task
#SBATCH --mem=2G                         # Memory per CPU core (adjust as needed)
#SBATCH --exclusive                      # Exclusive node allocation

# Load necessary modules (e.g., Python, Dask, etc.)
module load python

# Activate your virtual environment if needed
source ~/py-env/bin/activate

# Run your Python script
python run_cluster.py
