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
import astrometry
import photometry
import dataBank
import systematics
import IO
import pyfits
import numpy as np
from matplotlib import pyplot as plt
plt.ion()	## Turn on interactive plots

data = dataBank.dataBank()#imagesPath,darksPath,flatPath,regsPath,ingress,egress)  ## initalize databank for data storage
allStars = data.getDict()			   ## Store initialized dictionary
outputPath = data.outputPath
N_exposures = len(data.getPaths())

## Prepare systematic corrections: dark frame, flat field
meanDarkFrame = systematics.meanDarkFrame(data.darksPath)
masterFlat = data.masterFlat

## Tell oscaar what figure settings to use 
plottingThings,statusBarFig,statusBarAx = IO.plottingSettings(data.trackPlots,data.photPlots)   

## Main loop: iterate through each exposures
for expNumber in range(0,N_exposures):  
	
	if statusBarAx != None and expNumber % 15 == 0: 
		'''Prepare some plotting settings here'''
		plt.cla()
		statusBarAx.set_title('oscaar2.0 is running...')
		statusBarAx.set_xlim([0,100])
		statusBarAx.set_xlabel('Percent Complete (%)')
		statusBarAx.get_yaxis().set_ticks([])
		statusBarAx.barh([0],[100.0*expNumber/len(data.getPaths())],[1],color='k')

	image = (pyfits.getdata(data.getPaths()[expNumber]) - meanDarkFrame)/masterFlat	## Open image from FITS file
	data.storeTime(expNumber)								   ## Store the exposure time from the FITS header
	
	## Iterate through each star in each exposure
	for star in allStars:
		est_x, est_y = data.centroidInitialGuess(expNumber,star)

		## Find the stellar centroid
		x, y, radius, trackFlag = astrometry.trackSmooth(image, est_x, est_y, data.smoothConst, plottingThings, \
														 zoom=data.trackingZoom, plots=data.trackPlots)
		data.storeCentroid(star,expNumber,x,y)			  ## Store the centroid positions

		## Measure the flux and uncertainty, centered on the previously found stellar centroid
		#flux, error, photFlag = photometry.phot(image, x, y, data.apertureRadius, plottingThings, ccdGain = data.ccdGain, \
		#										plots=data.photPlots)
		fluxes, errors, photFlags = photometry.multirad(image, x, y, data.apertureRadii, plottingThings, ccdGain = data.ccdGain, \
												plots=data.photPlots)
		photFlag = any(photFlags)
		data.storeFluxes(star,expNumber,fluxes,errors)		   ## Store the flux and uncertainty in the data object

#		data.storeFlux(star,expNumber,flux,error)		   ## Store the flux and uncertainty in the data object
		if trackFlag or photFlag and (not data.getFlag()): data.setFlag(star,False) ## Store error flags
		if data.trackPlots or data.photPlots: plt.draw()	## More plotting settings 

	if statusBarAx != None and expNumber % 15 == 0: 		## More plotting settings
		plt.draw()

plt.close()

## Compute the scaled fluxes of each comparison star
data.scaleFluxes_multirad()		

## Calculate a composite comparison star by combining all comparisons
meanComparisonStars, meanComparisonStarErrors = data.calcMeanComparison_multirad(ccdGain = data.ccdGain)
#print meanComparisonStars[0][0],meanComparisonStars[1][0],meanComparisonStars[2][0]
## Calculate the light curve
lightCurves, lightCurveErrors = data.computeLightCurve_multirad(meanComparisonStars,meanComparisonStarErrors)
#print "LightCurves:",lightCurves[0][0], lightCurves[1][0], lightCurves[2][0]
## Save the dataBank object for later use
oscaar.IO.save(data,outputPath)

## Plot the resulting light curve
data.plotLightCurve_multirad()


### Compute the scaled fluxes of each comparison star
#data.scaleFluxes()		
#
### Calculate a composite comparison star by combining all comparisons
#meanComparisonStar, meanComparisonStarError = data.calcMeanComparison(ccdGain = data.ccdGain)
#
### Calculate the light curve
#lightCurve, lightCurveError = data.computeLightCurve(meanComparisonStar,meanComparisonStarError)
#
### Save the dataBank object for later use
#IO.save(data,outputPath)
#
### Plot the resulting light curve
#data.plotLightCurve(pointsPerBin=N_exposures/20)
