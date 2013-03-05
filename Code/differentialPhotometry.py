import oscaar
from oscaar import astrometry
from oscaar import photometry
import pyfits
import numpy as np
from matplotlib import pyplot as plt
import os
plt.ion()
outputPath = '../outputs/oscaarDataBase'

data = oscaar.dataBank()  ## initalize databank for data storage, parse init.par
allStars = data.getDict()               ## Store initialized dictionary

## Prepare systematic corrections: dark frame, flat field
meanDarkFrame = oscaar.meanDarkFrame(data.darksPath)
masterFlat = pyfits.getdata(data.flatPath)
plottingThings,statusBarAx = oscaar.plottingSettings(data.trackPlots,data.photPlots)   ## Tell oscaar what figure settings to use 

for expNumber in range(0,len(data.getPaths())):  ## For each exposure:
    print '\n'+data.getPaths()[expNumber]
    image = (pyfits.getdata(data.getPaths()[expNumber]) - meanDarkFrame)/masterFlat    ## Open image from FITS file
    data.storeTime(expNumber,pyfits.getheader(data.getPaths()[expNumber])['JD'])   ## Store time from FITS header
    if statusBarAx != None and expNumber % 15 == 0: 
        plt.cla()
        statusBarAx.set_title('oscaar2.0 is running...')
        statusBarAx.set_xlim([0,100])
        statusBarAx.set_xlabel('Percent Complete (%)')
        statusBarAx.get_yaxis().set_ticks([])
        statusBarAx.barh([0],[100.0*expNumber/len(data.getPaths())],[1],color='k')
        
    for star in allStars:
        if statusBarAx == None: plt.clf()
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
    if statusBarAx != None and expNumber % 15 == 0: plt.draw()
plt.close()
plt.ioff()
fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
fig.canvas.set_window_title('oscaar2.0') 

times = data.getTimes()

#for key in data.getKeys():
#    plt.plot(times,data.returnFluxes(key))
#plt.show()

data.scaleFluxes()
data.calcChiSq()
chisq = data.getAllChiSq()

meanComparisonStar, meanComparisonStarError = data.calcMeanComparison(ccdGain = data.ccdGain)
lightCurve = data.lightCurve(meanComparisonStar)

binnedTime, binnedFlux, binnedStd = oscaar.medianBin(times,lightCurve,10)
photonNoise = data.photonNoise()
print np.std(lightCurve[data.outOfTransit()])
print np.mean(photonNoise[data.outOfTransit()])

#data.save(outputPath)
oscaar.save(data,outputPath)
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

#for key in data.getKeys():
#    plt.plot(times,data.getScaledFluxes(key),'.')
#plt.show()