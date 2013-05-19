import numpy as np
from matplotlib import pyplot as plt

## Import oscaar directory using relative paths
import os, sys
lib_path = os.path.abspath('../../Code/')
sys.path.append(lib_path)
import oscaar

## Define system parameters for planet HAT-P-7 b. 
## Citation: Morris et al. 2013 (http://arxiv.org/abs/1301.4503)
RpOverRs = 0.07759				## R_p/R_s = ratio of planetary radius to stellar radius
aOverRs = 4.0					## a/R_s = ratio of semimajor axis to stellar radius
period = 2.204737				## Period [days]
inclination = 83.111			## Inclination [degrees]
gamma1 = 0.3525					## Linear limb-darkening coefficient
gamma2 = 0.168					## Quadratic limb-darkening coefficient
eccentricity = 0.0				## Eccentricity
longPericenter = 0.0			## Longitude of pericenter
epoch = 2454954.357463			## Mid transit time [Julian date]

## Generate times at which to calculate the flux
durationOfObservation = 6./24	## Elapsed time [days]
times = np.arange(epoch-durationOfObservation/2,epoch+durationOfObservation/2,1e-5)

modelParams = [RpOverRs,aOverRs,period,inclination,gamma1,gamma2,eccentricity,longPericenter,epoch]

## Generate light curve
flux = oscaar.occultquad(times,modelParams)

## Plot light curve
plt.plot(times,flux,linewidth=2)
plt.title('Transit light curve for HAT-P-7 b')
plt.ylabel('Relative Flux')
plt.xlabel('Time (JD)')
plt.show()