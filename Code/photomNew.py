import oscaar
import pyfits
import numpy as np
from matplotlib import pyplot as plt
from time import time

image = pyfits.open('wasp35z.fits')[0].data
est_x,est_y = [468,692]

## Inputs to paths, to be replaced with init.par parser
regsPath = '../Extras/Examples/20120616/stars2.reg'
imagesPath = '../Extras/Examples/20120616/tres1-???.fit'
darksPath = '../Extras/Examples/20120616/tres1-???d.fit'
flatPath = '../Extras/Examples/20120616/masterFlat.fits'
trackPlots = False#True
photPlots = False

ingress = '2012-06-17;02:59:00'
egress = '2012-06-17;05:29:00'

data = oscaar.dataBank(imagesPath,darksPath,flatPath,regsPath,ingress,egress)  ## initalize databank for data storage
allStars = data.returnDict()               ## Store initialized dictionary

oscaar.plottingSettings(trackPlots,photPlots)   ## Tell oscaar what figure settings to use 
for expNumber in range(0,len(data.getPaths())):  ## For each exposure:
    print '\n'+data.getPaths()[expNumber]
    image = pyfits.open(data.getPaths()[expNumber])[0].data     ## Open image from FITS file
    data.storeTime(expNumber,pyfits.open(data.getPaths()[expNumber])[0].header['JD'])   ## Store time from FITS header
    for star in allStars:
        if expNumber == 0:
            est_x = allStars[star]['x-pos'][0]  ## Use DS9 regions file's estimate for the 
            est_y = allStars[star]['y-pos'][0]  ##    stellar centroid for the first exosure
        else: 
            est_x = allStars[star]['x-pos'][expNumber-1]    ## All other exposures use the
            est_y = allStars[star]['y-pos'][expNumber-1]    ##    previous exposure centroid as estimate

        ## Track and store the stellar centroid
        x, y, radius, trackFlag = oscaar.trackSmooth(image, est_x, est_y, 3, zoom=10, plots=trackPlots)
        data.storeCentroid(star,expNumber,x,y)

        ## Tracl and store the flux and uncertainty
        flux, error, photFlag = oscaar.phot(image, x, y, 10, plots=photPlots)
        data.storeFlux(star,expNumber,flux,error)
        if trackFlag or photFlag and (not data.getFlag()): data.setFlag(False) ## Store error flags

times = data.timeJD()
print data.getAllFlags()
for key in data.getKeys():
    plt.plot(times,data.returnFluxes(key))
plt.show()