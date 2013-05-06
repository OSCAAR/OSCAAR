'''
OSCAAR/Code/differentialPhotometry.py

Load in the images and analysis parameters set in the Code/init.par
file, loop through each star within each image, for all images, and 
measure the stellar centroid positions and fluxes. Save these data
to the oscaar.dataBank() object, and save that out to a binary 
"pickle".


Core developer: Brett Morris
'''

import oscaar
from oscaar import astrometry
from oscaar import photometry
import pyfits
import numpy as np
from matplotlib import pyplot as plt
plt.ion()
import datetime

data = oscaar.dataBank()#imagesPath,darksPath,flatPath,regsPath,ingress,egress)  ## initalize databank for data storage
allStars = data.getDict()               ## Store initialized dictionary
outputPath = data.outputPath

## Prepare systematic corrections: dark frame, flat field
meanDarkFrame = oscaar.meanDarkFrame(data.darksPath)
masterFlat = data.masterFlat

## Tell oscaar what figure settings to use 
plottingThings,statusBarFig,statusBarAx = oscaar.plottingSettings(data.trackPlots,data.photPlots)   

## MAIN LOOP FOR PHOTOMETRY
for expNumber in range(0,len(data.getPaths())):  ## For each exposure:
    if statusBarAx != None and expNumber % 15 == 0: 
        plt.cla()
        statusBarAx.set_title('oscaar2.0 is running...')
        statusBarAx.set_xlim([0,100])
        statusBarAx.set_xlabel('Percent Complete (%)')
        statusBarAx.get_yaxis().set_ticks([])
        statusBarAx.barh([0],[100.0*expNumber/len(data.getPaths())],[1],color='k')

    print '\n'+'Loading file: '+data.getPaths()[expNumber]
    image = (pyfits.getdata(data.getPaths()[expNumber]) - meanDarkFrame)/masterFlat    ## Open image from FITS file
    data.storeTime(expNumber)                                               ## Get the exposure time from the header
    
    for star in allStars:
        if expNumber == 0:
            est_x = allStars[star]['x-pos'][0]  ## Use DS9 regions file's estimate for the 
            est_y = allStars[star]['y-pos'][0]  ##    stellar centroid for the first exosure
        else: 
            est_x = allStars[star]['x-pos'][expNumber-1]    ## All other exposures use the
            est_y = allStars[star]['y-pos'][expNumber-1]    ##    previous exposure centroid as estimate

        ## Find the stellar centroid
        x, y, radius, trackFlag = astrometry.trackSmooth(image, est_x, est_y, data.smoothConst, plottingThings, \
                                                         zoom=data.trackingZoom, plots=data.trackPlots)
        data.storeCentroid(star,expNumber,x,y)              ## Store the centroid positions

        ## Measure the flux and uncertainty, assuming the previously found stellar centroid
        flux, error, photFlag = photometry.phot(image, x, y, data.apertureRadius, plottingThings, ccdGain = data.ccdGain, \
                                                plots=data.photPlots)
        
        data.storeFlux(star,expNumber,flux,error)           ## Store the flux and uncertainty
        if trackFlag or photFlag and (not data.getFlag()): data.setFlag(star,False) ## Store error flags
        if data.trackPlots or data.photPlots: plt.draw()   
    if statusBarAx != None and expNumber % 15 == 0: 
        plt.draw()
plt.close()
#plt.ioff()

times = data.getTimes()
data.scaleFluxes()
meanComparisonStar, meanComparisonStarError = data.calcMeanComparison(ccdGain = data.ccdGain)
#chisq = data.getAllChiSq()
lightCurve = data.computeLightCurve(meanComparisonStar)

binnedTime, binnedFlux, binnedStd = oscaar.medianBin(times,lightCurve,10)
photonNoise = data.getPhotonNoise()
print np.std(lightCurve[data.outOfTransit()])
print np.mean(photonNoise[data.outOfTransit()])


oscaar.save(data,outputPath)
#data.plot(pointsPerBin=20)

#execfile('plotPickle.py')
