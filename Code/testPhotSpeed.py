#import oscaar
import oscaar
import pyfits
import numpy as np
from matplotlib import pyplot as plt
from time import time

image = pyfits.open('wasp35z.fits')[0].data
est_x,est_y = [468,692]

x, y, radius = oscaar.trackSmooth(image, est_x, est_y, 2, plots=False)#True)

Ntrials = 1000
oldTimes = np.zeros([Ntrials])
newTimes = np.zeros([Ntrials])
oldCounter = -1
newCounter = -1
for i in range(0,2*Ntrials):
    if i % 2 == 0:
        oldCounter += 1
        startTime = time() 
        flux, error = oscaar.phot(image, x, y, 10, plots=False)
        newTimes[oldCounter] = time() - startTime
    elif i % 2 != 0:
        newCounter += 1
        startTime = time()
        flux, error = oscaar.photOld(image, x, y, 10, plots=False)
        oldTimes[newCounter] = time() - startTime
plt.plot(oldTimes,label='Old')
plt.plot(newTimes,label='Compact')
ratio = np.mean(newTimes)/np.mean(oldTimes)
plt.title('Improvement: '+str(ratio)[:4])
plt.legend()
plt.show()