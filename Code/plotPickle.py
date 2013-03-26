#import matplotlib
#matplotlib.use('MacOSX')

import oscaar
from oscaar import astrometry
from oscaar import photometry
import pyfits
import numpy as np
from matplotlib import pyplot as plt
from time import time
import os
import matplotlib 
print matplotlib.__version__
#plt.ion()
import datetime

outputPath = './outputs/oscaarDataBase.pkl'
data = oscaar.load(outputPath)

fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
fig.canvas.set_window_title('oscaar2.0') 
print 'plotting'
times = data.getTimes()
meanComparisonStar, meanComparisonStarError = data.calcMeanComparison(ccdGain = 1.0)
lightCurve = data.computeLightCurve(meanComparisonStar)
binnedTime, binnedFlux, binnedStd = oscaar.medianBin(times,lightCurve,10)
photonNoise = data.getPhotonNoise()

plt.plot(times,lightCurve,'k.')
plt.plot(times[data.outOfTransit()],photonNoise[data.outOfTransit()]+1,'b',linewidth=2)
plt.plot(times[data.outOfTransit()],1-photonNoise[data.outOfTransit()],'b',linewidth=2)
plt.errorbar(binnedTime, binnedFlux, yerr=binnedStd, fmt='rs-', markersize=6,linewidth=2)
plt.axvline(ymin=0,ymax=1,x=data.ingress,color='k',ls=':')
plt.axvline(ymin=0,ymax=1,x=data.egress,color='k',ls=':')
plt.title('Light Curve')
plt.xlabel('Time (JD)')
plt.ylabel('Relative Flux')
plt.show()