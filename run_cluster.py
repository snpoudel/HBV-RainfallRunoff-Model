import pandas as pd
from dask_jobqueue import SLURMCluster #library for handling job queues on HPC
from dask.distributed import Client, as_completed #library for distributed computing with dask
from hbv_calibrate import calibNSE

#Read csv file of station ID
stationid = pd.read_csv("station_id.csv", dtype={"station_id":str})
#parameter to feed into HPC function to run in parallel
params = stationid["station_id"]

#SLURM cluster configuration
cluster = SLURMCluster(
    project='HBV_Project', #project name
    job_cpu=1, #number of cpu per job
    cores=1, #number of cores per job
    processes=1, #number of processes per job (1 process per core)
    memory='2GB',  # amount of memory per job
    walltime='00:30:00', #time to run each job
    job_extra=['--exclusive'], #to exclusively allocate a node
    local_directory='$TMPDIR', #directory for temporary file
)

# Scale the cluster to number of jobs
cluster.scale(jobs=84) #adjust to match number of tasks in slurm submission script

# Create a Dask client
client = Client(cluster)

# Submit the jobs to the cluster
client.map(calibNSE, params)