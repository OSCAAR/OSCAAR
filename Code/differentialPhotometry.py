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

outputPath = '../outputs/oscaarDataBase'

#oscaar.cd('Code')
###Parses init for settings###
init = open('init.par', 'r').read().splitlines()
for line in init:
    if line.split() > 1 and line[0] != '#':
        inline = line.split(':', 1)
        inline[0] = inline[0].strip()
        if inline[0] == 'Path to Dark Frames': darksPath = str(inline[1].split('#')[0].strip()) ##Everything after # on a line in init.par is ignored
        elif inline[0] == 'Path to Master-Flat Frame': flatPath = str(inline[1].split('#')[0].strip())
        elif inline[0] == 'Path to data images':  imagesPath = str(inline[1].split('#')[0].strip())
        elif inline[0] == 'Path to regions file': regsPath = str(inline[1].split('#')[0].strip())
        elif inline[0] == 'Ingress':  ingress = oscaar.ut2jd(str(inline[1].split('#')[0].strip()))
        elif inline[0] == 'Egress':  egress = oscaar.ut2jd(str(inline[1].split('#')[0].strip()))
        elif inline[0] == 'Radius':   apertureRadius = float(inline[1].split('#')[0].strip())
        elif inline[0] == 'Tracking Zoom':   trackingZoom = float(inline[1].split('#')[0].strip())
        elif inline[0] == 'CCD Gain':    ccdGain = float(inline[1].split('#')[0].strip())
        elif inline[0] == 'GUI': gui = inline[1].split('#')[0].strip()
        elif inline[0] == 'Plot Tracking': trackPlots = True if inline[1].split('#')[0].strip() == 'on' else False
        elif inline[0] == 'Plot Photometry': photPlots = True if inline[1].split('#')[0].strip() == 'on' else False
        elif inline[0] == 'Smoothing Constant': smoothConst = float(inline[1].split('#')[0].strip())
        elif inline[0] == 'Init GUI': initGui = inline[1].split('#')[0].strip()

data = oscaar.dataBank(imagesPath,darksPath,flatPath,regsPath,ingress,egress)  ## initalize databank for data storage
allStars = data.getDict()               ## Store initialized dictionary

## Prepare systematic corrections: dark frame, flat field

meanDarkFrame = oscaar.meanDarkFrame(data.darksPath)
masterFlat = pyfits.getdata(data.flatPath)
plottingThings,statusBarFig,statusBarAx = oscaar.plottingSettings(data.trackPlots,data.photPlots)   ## Tell oscaar what figure settings to use 

for expNumber in range(0,len(data.getPaths())):  ## For each exposure:
    print '\n'+data.getPaths()[expNumber]
    image = (pyfits.getdata(data.getPaths()[expNumber]) - meanDarkFrame)/masterFlat    ## Open image from FITS file
    data.storeTime(expNumber,pyfits.getheader(data.getPaths()[expNumber])['JD'])   ## Store time from FITS header
    if statusBarAx != None and expNumber % 15 == 0: 
        print 'plot'
        plt.cla()
        statusBarAx.set_title('oscaar2.0 is running...')
        statusBarAx.set_xlim([0,100])
        statusBarAx.set_xlabel('Percent Complete (%)')
        statusBarAx.get_yaxis().set_ticks([])
        statusBarAx.barh([0],[100.0*expNumber/len(data.getPaths())],[1],color='k')
        
meanDarkFrame = oscaar.meanDarkFrame(darksPath)
masterFlat = pyfits.open(flatPath)[0].data
print 'plottingThings'
plottingThings = oscaar.plottingSettings(trackPlots,photPlots)   ## Tell oscaar what figure settings to use 
print plottingThings
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
        x, y, radius, trackFlag = astrometry.trackSmooth(image, est_x, est_y, smoothConst, plottingThings, zoom=trackingZoom, plots=trackPlots)
        data.storeCentroid(star,expNumber,x,y)

        ## Track and store the flux and uncertainty
        flux, error, photFlag = photometry.phot(image, x, y, apertureRadius, plottingThings, ccdGain = ccdGain, plots=photPlots)
        data.storeFlux(star,expNumber,flux,error)
        if trackFlag or photFlag and (not data.getFlag()): data.setFlag(star,False) ## Store error flags

        if data.trackPlots or data.photPlots: plt.draw()   
    if statusBarAx != None and expNumber % 15 == 0: 
        print 'draw'
        #plt.draw()
        statusBarFig.canvas.draw()
plt.ioff()
#plt.clf()
plt.close()

times = data.getTimes()

#for key in data.getKeys():
#    plt.plot(times,data.returnFluxes(key))
#plt.show()

data.scaleFluxes()
data.calcChiSq()
chisq = data.getAllChiSq()

meanComparisonStar, meanComparisonStarError = data.calcMeanComparison(ccdGain = ccdGain)
lightCurve = data.lightCurve(meanComparisonStar)

binnedTime, binnedFlux, binnedStd = oscaar.medianBin(times,lightCurve,10)
photonNoise = data.photonNoise()
print np.std(lightCurve[data.outOfTransit()])
print np.mean(photonNoise[data.outOfTransit()])

#data.save(outputPath)
oscaar.save(data,outputPath)

fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
fig.canvas.set_window_title('oscaar2.0') 
print 'plotting'
plt.plot(times,lightCurve,'k.')
plt.plot(times[data.outOfTransit()],photonNoise[data.outOfTransit()]+1,'b',linewidth=2)
plt.plot(times[data.outOfTransit()],1-photonNoise[data.outOfTransit()],'b',linewidth=2)
plt.errorbar(binnedTime, binnedFlux, yerr=binnedStd, fmt='rs-', markersize=6,linewidth=2)
plt.axvline(ymin=0,ymax=1,x=ingress,color='k',ls=':')
plt.axvline(ymin=0,ymax=1,x=egress,color='k',ls=':')
plt.title('Light Curve')
plt.xlabel('Time (JD)')
plt.ylabel('Relative Flux')
print 'showing'
plt.show()

#for key in data.getKeys():
#    plt.plot(times,data.getScaledFluxes(key),'.')
#plt.show()