#import oscaar
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
trackPlots = True#False
photPlots = True#True

data = oscaar.dataBank(imagesPath,darksPath,flatPath,regsPath)
starDictionary = data.returnDict()
image = pyfits.open(data.paths()[0])[0].data

oscaar.setFigureSettings(trackPlots,photPlots)

for star in starDictionary:
    est_x = dictionary[star]['x-pos'][0]
    est_y = dictionary[star]['y-pos'][0]
    x, y, radius = oscaar.trackSmooth(image, est_x, est_y, 2, zoom=15, plots=trackPlots)
    flux, error = oscaar.phot(image, x, y, 10, plots=photPlots)


