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

outputPath = 'outputs'+os.sep+'oscaarDataBase.pkl'
data = oscaar.load(outputPath)

fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
fig.canvas.set_window_title('oscaar2.0') 
print 'plotting'
times = data.getTimes()
meanComparisonStar, meanComparisonStarError = data.calcMeanComparison(ccdGain = 1.0)
lightCurve, lightCurveError = data.computeLightCurve(meanComparisonStar,meanComparisonStarError)
binnedTime, binnedFlux, binnedStd = oscaar.medianBin(times,lightCurve,10)
photonNoise = data.getPhotonNoise()

print times.shape,lightCurve.shape

ax1 = fig.add_subplot(111)
def format_coord(x, y):
	'''Function to also give data value on mouse over with imshow.'''
	col = int(x+0.5)
	row = int(y+0.5)
	return 'x=%1.8f, y=%1.8f' % (x, y)

ax1.plot(times,lightCurve,'k.')
#ax1.plot(times[data.outOfTransit()],photonNoise[data.outOfTransit()]+1,'b',linewidth=2)
#ax1.plot(times[data.outOfTransit()],1-photonNoise[data.outOfTransit()],'b',linewidth=2)
ax1.errorbar(binnedTime, binnedFlux, yerr=binnedStd, fmt='rs-', markersize=6,linewidth=2)
ax1.axvline(ymin=0,ymax=1,x=data.ingress,color='k',ls=':')
ax1.axvline(ymin=0,ymax=1,x=data.egress,color='k',ls=':')
ax1.set_title('Light Curve')
ax1.set_xlabel('Time (JD)')
ax1.set_ylabel('Relative Flux')
ax1.format_coord = format_coord 
plt.show()