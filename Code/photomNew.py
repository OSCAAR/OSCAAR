import oscaar
import pyfits
import numpy as np
from matplotlib import pyplot as plt
from time import time

## Inputs to paths, to be replaced with init.par parser
regsPath = '../Extras/Examples/20120616/stars2.reg'
imagesPath = '../Extras/Examples/20120616/tres1-???.fit'
darksPath = '../Extras/Examples/20120616/tres1-???d.fit'
flatPath = '../Extras/Examples/20120616/masterFlat.fits'
trackPlots = False#True
photPlots = False

ingress = oscaar.ut2jd('2012-06-17;02:59:00') ## Enter ingress and egress in JD
egress = oscaar.ut2jd('2012-06-17;05:29:00')

data = oscaar.dataBank(imagesPath,darksPath,flatPath,regsPath,ingress,egress)  ## initalize databank for data storage
allStars = data.getDict()               ## Store initialized dictionary

## Prepare systematic corrections: dark frame, flat field
meanDarkFrame = oscaar.meanDarkFrame(darksPath)
masterFlat = pyfits.open(flatPath)[0].data

oscaar.plottingSettings(trackPlots,photPlots)   ## Tell oscaar what figure settings to use 
for expNumber in range(0,len(data.getPaths())):  ## For each exposure:
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
        x, y, radius, trackFlag = oscaar.trackSmooth(image, est_x, est_y, 3, zoom=10,plots=trackPlots)
        data.storeCentroid(star,expNumber,x,y)

        ## Tracl and store the flux and uncertainty
        #apertureRadius = 4; rms out-of-transit scatter: 0.012478066561
        #apertureRadius = 4.5; rms out-of-transit scatter: 0.00831816981609 << best aperture
        #apertureRadius = 5; rms out-of-transit scatter: 0.00919495508291
        #apertureRadius = 6; rms out-of-transit scatter: 0.00961801849049
        flux, error, photFlag = oscaar.phot(image, x, y, 4.5, ccdGain = 0.77999997138977051, plots=photPlots)
        data.storeFlux(star,expNumber,flux,error)
        if trackFlag or photFlag and (not data.getFlag()): data.setFlag(star,False) ## Store error flags

times = data.getTimes()

#for key in data.getKeys():
#    plt.plot(times,data.returnFluxes(key))
#plt.show()

data.scaleFluxes()
data.calcChiSq()
chisq = data.getAllChiSq()

meanComp, meanCompError = data.calcMeanComparison(ccdGain = 0.77999997138977051)
target = data.getScaledFluxes('000')
lightCurve = target/meanComp
binnedTime, binnedFlux, binnedStd = oscaar.medianBin(times,lightCurve,10)
photonNoise = meanCompError*lightCurve
print np.std(lightCurve[data.outOfTransit()])
print np.mean(photonNoise[data.outOfTransit()])

plt.plot(times,lightCurve,'k.')
plt.plot(times[data.outOfTransit()],photonNoise[data.outOfTransit()]+1,'b',linewidth=2)
plt.plot(times[data.outOfTransit()],1-photonNoise[data.outOfTransit()],'b',linewidth=2)
plt.errorbar(binnedTime, binnedFlux, yerr=binnedStd, fmt='rs-', markersize=6,linewidth=2)
plt.axvline(ymin=0,ymax=1,x=ingress,color='k',ls=':')
plt.axvline(ymin=0,ymax=1,x=egress,color='k',ls=':')
plt.title('Light Curve')
plt.xlabel('Time (JD)')
plt.ylabel('Relative Flux')
plt.show()

#for key in data.getKeys():
#    plt.plot(times,data.getScaledFluxes(key),'.')
#plt.show()