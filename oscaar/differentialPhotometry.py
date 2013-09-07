"""
OSCAAR/Code/differentialPhotometry.py

Load in the images and analysis parameters set in the Code/init.par
file, loop through each star within each image, for all images, and
measure the stellar centroid positions and fluxes. Save these data
to the oscaar.dataBank() object, and save that out to a binary
"pickle".


Core developer: Brett Morris
"""

from matplotlib import pyplot as plt

import oscaar
import astrometry
import photometry
import dataBank
import systematics
import IO
import pyfits

# Turn on interactive plots
plt.ion()

# initalize databank for data storage
data = dataBank.dataBank()
# Store initialized dictionary
allStars = data.getDict()
outputPath = data.outputPath
N_exposures = len(data.getPaths())

# Prepare systematic corrections: dark frame, flat field
meanDarkFrame = systematics.meanDarkFrame(data.darksPath)
masterFlat = data.masterFlat

# Tell oscaar what figure settings to use
plottingThings, statusBarFig, statusBarAx = \
    IO.plottingSettings(data.trackPlots, data.photPlots)

# Main loop: iterate through each exposures
for expNumber in xrange(N_exposures):
    if statusBarAx is not None and expNumber % 15 == 0:
        # Prepare some plotting settings here
        plt.cla()
        statusBarAx.set_title('oscaar2.0 is running...')
        statusBarAx.set_xlim([0, 100])
        statusBarAx.set_xlabel('Percent Complete (%)')
        statusBarAx.get_yaxis().set_ticks([])
        statusBarAx.barh([0], [100.0*expNumber/len(data.getPaths())],
                         [1], color='k')

    # Open image from FITS file
    image = (pyfits.getdata(data.getPaths()[expNumber]) - meanDarkFrame) \
        / masterFlat
    # Store the exposure time from the FITS header
    data.storeTime(expNumber)

    # Iterate through each star in each exposure
    for star in allStars:
        est_x, est_y = data.centroidInitialGuess(expNumber, star)
        # Find the stellar centroid
        x, y, radius, trackFlag = astrometry.trackSmooth(image, est_x, est_y,
                                                         data.smoothConst,
                                                         plottingThings,
                                                         zoom=data.trackingZoom,
                                                         plots=data.trackPlots)
        # Store the centroid positions
        data.storeCentroid(star, expNumber, x, y)
        # Measure the flux and uncertainty, centered on the previously found
        # stellar centroid
        fluxes, errors, photFlags = photometry.multirad(image, x, y,
                                                        data.apertureRadii,
                                                        plottingThings,
                                                        ccdGain=data.ccdGain,
                                                        plots=data.photPlots)
        photFlag = any(photFlags)
        # Store the flux and uncertainty in the data object
        data.storeFluxes(star, expNumber, fluxes, errors)

        if trackFlag or photFlag and not data.getFlag():
            # Store error flags
            data.setFlag(star, False)
        if data.trackPlots or data.photPlots:
            # More plotting settings
            plt.draw()

    if statusBarAx is not None and expNumber % 15 == 0:
        # More plotting settings
        plt.draw()

plt.close()

# Compute the scaled fluxes of each comparison star
data.scaleFluxes_multirad()

# Calculate a composite comparison star by combining all comparisons
meanComparisonStars, meanComparisonStarErrors = \
    data.calcMeanComparison_multirad(ccdGain=data.ccdGain)

# Calculate the light curve
lightCurves, lightCurveErrors = \
    data.computeLightCurve_multirad(meanComparisonStars,
                                    meanComparisonStarErrors)

# Save the dataBank object for later use
oscaar.IO.save(data, outputPath)

# Plot the resulting light curve
data.plotLightCurve_multirad()
