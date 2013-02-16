#import oscaar
import oscaar
import pyfits
import numpy as np
from matplotlib import pyplot as plt
from time import time

image = pyfits.open('wasp35z.fits')[0].data
est_x,est_y = [468,692]

init_x_list,init_y_list = oscaar.parseRegionsFile('/Users/bmorris/git/OSCAAR/Extras/Examples/stars2.reg')

starsDictionary = oscaar.starDictionary(init_x_list,init_y_list)
print starsDictionary.returnDict()

x, y, radius = oscaar.trackSmooth(image, est_x, est_y, 2, plots=False)#True)
flux, error = oscaar.phot(image, x, y, 10, plots=False)
