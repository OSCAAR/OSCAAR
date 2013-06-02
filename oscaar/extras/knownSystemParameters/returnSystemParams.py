import numpy as np
import os
import oscaar

'''
System parameters for occultquad: 
p   = Rp/Rs     = planet radius/stellar radius
ap  = a/Rs      = semimajor axis/stellar radius
P   = period
i   = inclination
gamma1  = limb darkening, linear
gamma2  = limb darkening, quadratic
e       = eccentricity
longPericenter = logitude of pericenter
t0      =   mid-transit time
'''
global exoplanetDB

def period(planet):
    '''Units:  days'''
    return np.float64(exoplanetDB[planet]['PER'])

def epoch(planet):
    '''Tc at mid-transit. Units:  days'''
    if exoplanetDB[planet]['TT'] == '': return 0.0
    else: return np.float64(exoplanetDB[planet]['TT'])

def aOverRs(planet):
    '''Returns semimajor axis over stellar radius (a/Rs)'''
    return float(exoplanetDB[planet]['AR'])

def depth(planet):
    '''Transit depth = (Rp/Rs)^2 '''
    if exoplanetDB[planet]['DEPTH'] == '': return 0.0
    else: return float(exoplanetDB[planet]['DEPTH'])
        
def RpOverRs(planet):
    '''Ratio of planet radius to stellar radius, derived from transit depth since depth=(Rp/Rs)^2'''
    return np.sqrt(depth(planet))

def inclination(planet):
    return float(exoplanetDB[planet]['I'])

def eccentricity(planet):
    if float(exoplanetDB[planet]['ECC']) == '': return 0.0
    else: return float(exoplanetDB[planet]['ECC'])
    
def transiterParams(planet):
    '''Return accepted values for the fitting routine'''

    ## Load latest data from exoplanets.org
    from getLatestParams import downloadAndPickle
    global exoplanetDB
    exoplanetDB = downloadAndPickle()
    return [RpOverRs(planet),aOverRs(planet),period(planet),inclination(planet),eccentricity(planet)]

