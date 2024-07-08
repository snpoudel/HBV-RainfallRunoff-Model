'''
HBV (Hydrologiska byrÂns vattenavdelning) model 
Reference:
- https://www.smhi.se/polopoly_fs/1.83592!/Menu/general/extGroup/attachmentColHold/mainCol1/file/RH_4.pdf
- https://hess.copernicus.org/articles/16/3315/2012/hess-16-3315-2012.pdf
- Matlab code by Sungwook Wi
'''
#import libraries
import numpy as np
import pandas as pd
import math
#import pyet #this package is used to calculate PET, install first
# hbv function
def hbv(pars, p, temp, date, latitude, routing):
    '''
    hbv function Input:
    - pars: parameter vector
    - p & temp: precipitation & temperature time series
    - date: date in YYYY-MM-DD
    - latitude: centroid latitude of a watershed
    - routing: 1 = traingular routing is involved | 0 = no routing
    
    hbv function Output:
    - qtotal: total flow/discharge
 
    '''
    #set model parameters
    fc = pars[0] #maximum soil moisture storage, field capacity
    beta = pars[1] #shape coefficient governing fate of water input to soil moisture storage
    pwp = pars[2] #soil permanent wilting point
    l = pars[3] #threshold parameter for upper storage, if water level higher than threshold shallow flow occurs
    ks = pars[4] #recession constant (upper storage, near surface)
    ki = pars[5] #recession constant (upper storage)
    kb = pars[6] #recession constant (lower storage)
    kperc = pars[7] #percolation constant, max flow rate from upper to lower storage
    coeff_pet = pars[8] #coefficient for potential evapotranspiration

    ddf = pars[9] #degree-day factor
    scf = pars[10] #snowfall correction factor
    ts = pars[11] #threshold temperature for snow falling
    tm = pars[12] #threshold temperature for snowmelt
    tti = pars[13] #temperature interval for mixture of snow and rain
    whc = pars[14] #usually fixed, water holding capacity of snowpack (default 0.1)
    crf = pars[15] #usually fixed, refreezing coefficient (default 0.05)
    
    maxbas = pars[16] #traingular weighting function routing parameter, it represents time taken by water to move through the catchment and reach outlet

    #Initialize model variables
    sim_snow = np.zeros(len(p)) #simulated snow
    sim_swe =np.zeros(len(p)) #simulated snow water equivalent
    sim_melt = np.zeros(len(p)) #simulated snow melt
    pr_eff = np.zeros(len(p)) #effective precip (amount of liquid water available to enter soil matrix at a time step)

    sim_et = np.zeros(len(p)) #simulated actual evapotranspiration
    sim_pexc = np.zeros(len(p)) #simulated effective rainfall
    sim_sma = np.zeros(len(p)) #simulated soil moisuture storage accounting tank
    inflow_direct = np.zeros(len(p)) #direct flow
    inflow_base = np.zeros(len(p)) #base flow

    state_upres = 0  #initial storage in upper zone/reservoir
    state_lowres = 0 #initial storage in lower zone/reservoir
    state_snow = 0 #initial state of snow storage
    state_sliq = 0 #initial state of liquid water on snowpack
    state_sma = 0 #initial state of soil moisture storage
    
    
    #Calculate potential evapotranspiration using Hamon's method
    #convert date to julian date
    date = pd.to_datetime(date) #convert first to python datetime format
    jdate = date.dt.strftime('%j').astype(int) #convert to julian date
    #calculate daylight hour
    var_theta = 0.2163108 + 2 * np.arctan(0.9671396 * np.tan(0.0086 * (jdate - 186)))
    var_pi = np.arcsin(0.39795 * np.cos(var_theta))
    daylighthr = 24 - 24 / math.pi * np.arccos((np.sin(0.8333 * math.pi / 180) + np.sin(latitude * math.pi / 180) * np.sin(var_pi)) / (np.cos(latitude * math.pi / 180) * np.cos(var_pi)))
    #now use Hamon's equation
    esat = 0.611 * np.exp(17.27 * temp/(237.3+temp))
    potevap = coeff_pet * 29.8 * daylighthr * (esat/(temp+273.2))

    
    ##-------Start of Time Loop-------
    for t in range(1, len(p)):
        
        ##Snow Routine
        '''
        Snow Routine takes temperature and precipitation as input and
        provides updated value of snow pack and water available to enter soil as output
        '''
        ct = temp[t] #temperature at current timestep
        cp = p[t] #precipitation at current timestep

        # Determine if precipitation is snow, rain, or a mixture
        if ct >= (ts + tti): #All rain, no snow
            snow = 0
            rain = cp
        elif ct <= ts:  # All snow, no rain
            snow = cp
            rain = 0
        else:  # Linear mixture of snow and rain in interval tti
            snowfrac = -1 / tti * (ct - ts) + 1
            snow = cp * snowfrac
            rain = cp * (1 - snowfrac)

        # If there is snow to melt
        if state_snow > 0:
            if ct > tm:
                melt = ddf * (ct - tm)
            else:
                melt = 0

            if melt > state_snow:
                # if melt>snow, add all snow and incoming rain to the liquid water storage in snow
                state_sliq += state_snow + rain
                state_snow = 0
            else:
                # otherwise, add melt portion and incoming rain to the liquid water storage in snow
                state_sliq += melt + rain
                state_snow -= melt

            # Calculate maximum liquid water held by the remaining snow
            liqmax = state_snow * whc

            if state_sliq > liqmax:
                pr_eff[t] = state_sliq - liqmax
                state_sliq = liqmax
            else:
                pr_eff[t] = 0
        else:
            melt = 0
            pr_eff[t] = rain

        # Calculate refreezing
        if ct < tm:
            refreeze = (tm - ct) * ddf * crf
        else:
            refreeze = 0

        if refreeze > state_sliq:
            # if refreeze >  liquid content of the snow, add entire liquid portion to current snow storage
            state_snow += state_sliq
            state_sliq = 0
        else: # if there is more liquid than will actually refreeze, add refreezing portion to the snow store
            state_snow += refreeze
            state_sliq -= refreeze

        # Final snow store for the time step by multiplying with snowfall correction factor
        state_snow += snow * scf

        sim_swe[t] = state_snow + state_sliq
        sim_snow[t] = snow
        sim_melt[t] = melt
        
        
        ##Soil Moisture Routine
        '''
        Soil moisture takes the available water to enter soil (pr_eff) as an input from snow module, and updates
        soil moisture and recharge, the updated soil moisture is then used to calculate actual evapotranspiration
        '''
        #calculate effective precipitation
        if state_sma > fc:
            peff = pr_eff[t]
        else:
            effratio = (state_sma / fc) ** beta
            remainwater = pr_eff[t] * (1 - effratio)
            if remainwater + state_sma > fc:
                peff = pr_eff[t] + state_sma - fc
                state_sma = fc
            else:
                peff = pr_eff[t] - remainwater
                state_sma += remainwater
        
        #calculate actual evapotranspiration
        if state_sma > (pwp * fc):
            pet = potevap[t]
        else:
            pet = potevap[t] * (state_sma / (pwp * fc)) #adjusted evapotranspiration
        et = min(pet, state_sma) #actual evapotranspiration
        state_sma -= et

        #calculate flow
        state_upres += peff
        qs = max(0, (state_upres - l) * ks)
        qi = min(l, state_upres) * ki
        qperc = (state_upres - qs - qi) * kperc
        state_upres = max(state_upres - qs - qi - qperc, 0)
        qq = qs + qi
        
        state_lowres += qperc
        qb = state_lowres * kb
        state_lowres -= qb

        #intermediate states
        sim_sma[t] = state_sma #simulated state of soil moisture account
        sim_et[t] = et #simulated actual evapotranspiration
        sim_pexc[t] = peff #simulated effective rainfall

        #total flow at this timestep
        inflow_direct[t] = qq
        inflow_base[t] = qb

    ##-------End of Time Loop-------
    

    ## Routing 
    if(routing == 1):
        #set integration step
        step = 0.005
        i = np.arange(0, maxbas + step, step)
        h = np.zeros(len(i))
        #define indices to construct traingular weighting function
        j = np.where(i<maxbas/2)
        h[j] = step * (i[j] *4 / maxbas ** 2)

        j = np.where(i >= maxbas/2)
        h[j] = step *(4 / maxbas - i[j] * 4 / maxbas **2)

        # Allow base of weighting function to be noninteger, adjust for extra weights for the last day
        if maxbas % 1 > 0:
            I = np.arange(1, len(i), (len(i) - 1) / maxbas)
            I = np.append(I, len(i))
        else:
            I = np.arange(1, len(i), (len(i) - 1) / maxbas)

        maxbas_w = np.zeros(len(I))

        # Integration of function
        for k in range(1, len(I)):
            maxbas_w[k] = np.sum(h[int(np.floor(I[k-1])):int(np.floor(I[k]))])

        # Ensure integration sums to unity for mass balance
        maxbas_w = maxbas_w[1:] / np.sum(maxbas_w[1:], where=~np.isnan(maxbas_w[1:]))

        # ROUTING OF DISCHARGE COMPONENTS
        qdirect = np.convolve(inflow_direct, maxbas_w, mode='full')[:len(p)]  # Routed direct flow
        qbase = np.convolve(inflow_base, maxbas_w, mode='full')[:len(p)]  # Routed base flow
        qtotal = qdirect + qbase
        
    else: #no routing
        qdirect = inflow_direct   #unrouted direct flow
        qbase = inflow_base   #unrouted base flow
        qtotal  = qdirect + qbase    #total flow 
    
    #return total flow as output
    return qtotal
#End of function  

