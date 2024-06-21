'''
HBV (Hydrologiska byrÂns vattenavdelning) model 
Reference:
- Seibert, Jan. "HBV light." User’s manual, Uppsala University, Institute of Earth Science, Department of Hydrology, Uppsala (1996).
- R code written by J.P. Gannon, March 2021

'''
#import libraries
import numpy as np
import math
import pyet #this package is used to calculate PET, install first
# hbv function
def hbv(pars, p, temp, latitude, routing):
    '''
    hbv function Input:
    - pars: parameter vector
    - p & temp: precipitation & temperature time series
    - latitude: centroid latitude of a watershed
    - routing: 1 = traingular routing is involved | 0 = lumped model
    
    hbv function Output:
    - q: total flow/discharge
 
    '''
    #set model parameters
    fc = pars[0] #maximum soil moisture storage, field capacity
    beta = pars[1] #shape coefficient governing fate of water input to soil moisture storage
    lp = pars[2] #soil moisture value above which actual ET reaches potential ET
    sfcf = pars[3] #snowfall correction factor
    tt = pars[4] #threshold temperature
    cfmax = pars[5] #degree-day factor
    cfr = pars[6] #usually fixed refreezing coefficient (default 0.05)
    cwh = pars[7] #usually fixed water holding capacity of snowpack (default 0.1)
    k0 = pars[8] #recession constant (upper storage, near surface)
    k1 = pars[9] #recession constant (upper storage)
    k2 = pars[10] #recession constant (lower storage)
    uzl = pars[11] #threshold parameter for upper storage, if water level higher than threshold shallow flow occurs
    perc = pars[12] #percolation constant, max flow rate from upper to lower storage
    coeff_pet = pars[13] #coefficient for potential evapotranspiration
    
    #Initialize model variables
    pet = np.zeros(len(p)) #potential evapotranspiration
    aet = np.zeros(len(p)) #actual evapotranspiration
    sf = np.zeros(len(p)) #snowfall
    r = np.zeros(len(p)) #recharge
    soil = np.zeros(len(p)) #soil storage
    swe = np.zeros(len(p)) #snow water equivalent
    w = np.zeros(len(p)) #water input = snowmelt + rainfall
    storage = np.zeros(len(p)) #total storage
    s1 = np.zeros(len(p)) #upper zone storage
    s2 = np.zeros(len(p)) #lower zone storage
    q_stz = np.zeros(len(p)) #shallow flow = saturated overland flow
    q_suz = np.zeros(len(p)) #upper zone flow = interflow
    q_slz = np.zeros(len(p)) #lower zone flow = groundwater flow
    qgen = np.zeros(len(p)) #streamflow sources not routed through channel network
    
    suz = 0 #initial storage in upper zone
    slz = 0 #initial storage in lower zone
    sp = 0 #initial snowpack
    wc = 0 #initial liquid water on snowpack
    sm = fc #initial soil moisture /storage content
    
    
    #Calculate potential evapotranspiration using Hamon's method
    #Use pyet package, Reference: https://pyet.readthedocs.io/en/latest/
    pet = pyet.hamon(temp, latitude[1], method = 2, cc = coeff_pet)
    
    ##-------Start of Time Loop-------
    for t in range(len(p)):
        
        ##Snow Routine
        '''
        Snow Routine takes temperature and precipitation as input and
        provides updated value of snow pack and water available to enter soil as output
        '''
        inc = 0 #total liquid water that can enter soil (water from snow routine available to soil routine)
    
        if (sp>0): #if ground has snowpack
            
            if(p[t] > 0): #if it is precipitating (do we really need to say this?)
                if (temp[t] > tt): #present temp > threshold temp
                    wc = wc + p[t] #add precipitation to water content present in snowpack
                else:
                    sp = sp + p[t] * sfcf #add precipitation as snow to snowpack
            
            
            if(temp[t] >tt): #warm temperature will cause melting
                melt = cfmax * (temp[t] - tt) #melting of snowpack, but not more than available snowpack
                if(melt > sp):
                    inc = sp + wc 
                    wc = 0
                    sp = 0
                else:
                    sp = sp - melt
                    wc = wc + melt #water content increased by melted snow
                    if(wc >= cwh * sp): #snowpack can only retain max of cwh*sp of water content
                        inc = wc - cwh * sp #If there is more liquid water, this goes to runoff (note:if there is no snowpack all water will go to catchment input)
                        wc = cwh * sp
            else: #freezing temperature will cause refreezing
                refreeze = cfr * cfmax * (tt - temp[t]) ##Refreezing of meltwater occurs if T < TT
                if(refreeze > wc):
                    refreeze = wc #refreeze cant be more than available liquid water
                sp = sp + refreeze
                wc = wc - refreeze
                sf[t] = p[t] * sfcf #snowfall
                
        else: #if ground doesn't have snowpack
            if(temp[t] > tt):
                inc = p[t] #if too warm, input is rain
            else:
                sp = p[t] * sfcf
        swe[t] = sp + wc #swe, snow water equivalent
        
        
        
        ##Soil Moisture Routine
        '''
        Soil moisture takes the available water to enter soil (inc) as an input from snow module, and updates
        soil moisture and recharge, the updated soil moisture is then used to calculate actual evapotranspiration
        '''
        rq = 0 #Recharge
        old_sm = sm #previous soil moisture
        if(inc > 0): #if water available to enter soil
            if(inc < 1):
                y = inc
            else:
                m = math.floor(inc) #loop through 1mm increments
                y = inc - m  
                for i in range(m): #Loop for adding input to soil 1 mm at a time to avoid instability
                    dqdp = (sm/fc) ** beta ##Partitioning betn recharge and soil moisture storage
                    if(dqdp > 1):
                        dqdp = 1 #dqdp is recharge to available water ratio,also sm to fc ratio, which shouldn't be > 1
                    else: 
                        sm = sm + 1 - dqdp #1mm is added to soil moisture but dqdp deducted as richarge(as water entering is 1mm, dqdp (recharge/water entering = recharge/1) is basically only recharge now)
                        rq = rq + dqdp 
                        
            dqdp = (sm/fc) ** beta # for the y amount of water
            if(dqdp > 1):
                dqdp = 1
            else:
                sm = sm + y - dqdp * y #soil moisture update
                rq = rq + dqdp * y #recharge
        
        
        mean_sm = (sm + old_sm)/2 #average soil moisture to estimate AET
        if(mean_sm < lp * fc): #soil moisture less than wilting point/threshold?
            aet[t] = pet[t] * mean_sm / (lp * fc)
        else:
            aet[t] = pet[t]
        
        if(sp + wc > 0):
            aet[t] = 0 #no evap if snow is present
            
        sm = sm - aet[t] #update soil moisture by reducing the evaporated water
        
        if(sm < 0):
            soil[t] = 0 #no storage in soil
            sm = 0
            
        soil[t] = sm #storage value in soil at this timestep
        r[t] = rq #recharge at this time step
        w[t] = inc #water that was available to enter soil at this timestep
        
        ##Response function/ groudwater storage
        ''' 
        This uses recharge from soil routine, partitions it on upper and lower storage 
        and provides total discharge as a summation of shallow flow, interflow & baseflow
        '''
        suz = suz + rq #recharge adds to upper zone storage
        if(suz - perc < 0): #if perc>upper storage, all water moves to lower storage
            slz = slz + suz 
            suz = 0
        else:
            slz = slz + perc
            suz = suz - perc
        
        if(suz < uzl): #if upper zone storage is less than shallow flow threshold
            q_stz[t] = 0 #no shallow flow
        else:
            q_stz[t] = (suz - uzl) * k0 #shallow flow occurs
        
        q_suz[t] = suz * k1 #flow from upper storage, interflow
        q_slz[t] = slz * k2 #flow from lower storage, baserflow
        
        suz = suz - q_suz[t] - q_stz[t] #upper zone storage reduces by interflow and shallow flow
        slz = slz - q_slz[t] #lower zone storage reduces by baseflow
        
        s1[t] = suz #upper zone storage at this timestep
        s2[t] = slz #lower zone storage at this timestep
        
        #total discharge 
        qgen[t] = q_stz[t] + q_suz[t] + q_slz[t]
        #total storage
        storage[t] = s1[t] + s2[t] + soil[t] 
        
    ##-------Start of Time Loop-------
    
    ## Routing 
    if(routing == 1):
        print("Routing is not considered now/ consideration of lumped model!!")
    else:
        qs = q_stz   #not routed shallow flow = Saturated overland flow or other rapid process
        qi = q_suz   #not routed upper zone flow = interflow
        qb = q_slz   #not routed lower zone flow = baseflow
        q  = qgen    #total flow routed to catchment outlet
    
    #return total flow as output
    return q
#End of function  