from mpi4py import MPI #Package for parallel processing with MPI
from hbv_calibrate import calibNSE #local package
comm = MPI.COMM_WORLD #Get the default communicator object
rank = comm.Get_rank() #Get the rank of the current process
size = comm.Get_size() #Get the total number of processes

#read stationID
stationid = pd.read_csv("station_id.csv", dtype={"station_id":str})
number_of_tasks = len(stationid["station_id"]) #Need to run in parallel for this number of tasks

#parallelize 
if rank < number_of_tasks:
    calibNSE(station_id=stationid["station_id"][rank]) 
    '''
    this fuction takes in one station_id at a time from input csv file,
    calibrates model for corresponding station, and outputs calibrated parameters in specified folder'''
#end of loop
