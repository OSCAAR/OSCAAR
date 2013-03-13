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
## http://www.python.org/download/mac/tcltk/#activetcl-8-5-13
## http://sourceforge.net/projects/matplotlib/files/matplotlib/matplotlib-1.0.1/matplotlib-1.0.1_r0-py2.7-macosx-10.3-fat.egg/download
import matplotlib 
print matplotlib.__version__
plt.ion()
import datetime

#outputPath = '../outputs/oscaarDataBase'

data = oscaar.dataBank()#imagesPath,darksPath,flatPath,regsPath,ingress,egress)  ## initalize databank for data storage
allStars = data.getDict()               ## Store initialized dictionary
outputPath = data.outputPath

## Prepare systematic corrections: dark frame, flat field
meanDarkFrame = oscaar.meanDarkFrame(data.darksPath)
masterFlat = pyfits.open(data.flatPath)[0].data

plottingThings,statusBarFig,statusBarAx = oscaar.plottingSettings(data.trackPlots,data.photPlots)   ## Tell oscaar what figure settings to use 
print plottingThings
for expNumber in range(0,len(data.getPaths())):  ## For each exposure:
    if statusBarAx != None and expNumber % 15 == 0: 
        print 'plot'
        plt.cla()
        statusBarAx.set_title('oscaar2.0 is running...')
        statusBarAx.set_xlim([0,100])
        statusBarAx.set_xlabel('Percent Complete (%)')
        statusBarAx.get_yaxis().set_ticks([])
        statusBarAx.barh([0],[100.0*expNumber/len(data.getPaths())],[1],color='k')

    print '\n'+data.getPaths()[expNumber]
    image = (pyfits.open(data.getPaths()[expNumber])[0].data - meanDarkFrame)/masterFlat    ## Open image from FITS file
    data.storeTime(expNumber,pyfits.open(data.getPaths()[expNumber])[0].header['JD'])   ## Store time from FITS header
    for star in allStars:
        if expNumber == 0:
            est_x = allStars[star]['x-pos'][0]  ## Use DS9 regions file's estimate for the 
            est_y = allStars[star]['y-pos'][0]  ##    stellar centroid for the first exosure
        else: 
            est_x = allStars[star]['x-pos'][expNumber-1]    ## All other exposures use the
            est_y = allStars[star]['y-pos'][expNumber-1]    ##    previous exposure centroid as estimate

        ## Track and store the stellar centroid
        x, y, radius, trackFlag = astrometry.trackSmooth(image, est_x, est_y, data.smoothConst, plottingThings, zoom=data.trackingZoom, plots=data.trackPlots)
        data.storeCentroid(star,expNumber,x,y)

        ## Track and store the flux and uncertainty
        flux, error, photFlag = photometry.phot(image, x, y, data.apertureRadius, plottingThings, ccdGain = data.ccdGain, plots=data.photPlots)
        data.storeFlux(star,expNumber,flux,error)
        if trackFlag or photFlag and (not data.getFlag()): data.setFlag(star,False) ## Store error flags

        if data.trackPlots or data.photPlots: plt.draw()   
    if statusBarAx != None and expNumber % 15 == 0: 
        plt.draw()
plt.close()
plt.ioff()
#plt.clf()
#plt.close()

times = data.getTimes()

#for key in data.getKeys():
#    plt.plot(times,data.returnFluxes(key))
#plt.show()

data.scaleFluxes()
data.calcChiSq()
chisq = data.getAllChiSq()

meanComparisonStar, meanComparisonStarError = data.calcMeanComparison(ccdGain = data.ccdGain)
lightCurve = data.computeLightCurve(meanComparisonStar)

binnedTime, binnedFlux, binnedStd = oscaar.medianBin(times,lightCurve,10)
photonNoise = data.getPhotonNoise()
print np.std(lightCurve[data.outOfTransit()])
print np.mean(photonNoise[data.outOfTransit()])

#data.save(outputPath)
oscaar.save(data,outputPath)
data.plot()
if False:
    fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
    fig.canvas.set_window_title('oscaar2.0') 
    print 'plotting'
    plt.plot(times,lightCurve,'k.')
    plt.plot(times[data.outOfTransit()],photonNoise[data.outOfTransit()]+1,'b',linewidth=2)
    plt.plot(times[data.outOfTransit()],1-photonNoise[data.outOfTransit()],'b',linewidth=2)
    plt.errorbar(binnedTime, binnedFlux, yerr=binnedStd, fmt='rs-', markersize=6,linewidth=2)
    plt.axvline(ymin=0,ymax=1,x=data.ingress,color='k',ls=':')
    plt.axvline(ymin=0,ymax=1,x=data.egress,color='k',ls=':')
    plt.title('Light Curve')
    plt.xlabel('Time (JD)')
    plt.ylabel('Relative Flux')
    #fig.canvas.draw()
    #plt.draw()
    print 'showing'
    plt.show()

#for key in data.getKeys():
#    plt.plot(times,data.getScaledFluxes(key),'.')
#plt.show()