#import oscaar
import oscaar
import pyfits
import numpy as np
from matplotlib import pyplot as plt
from time import time

image = pyfits.open('wasp35z.fits')[0].data
est_x,est_y = [468,692]

print oscaar.parseRegionsFileOld('/Users/bmorris/git/OSCAAR/Extras/Examples/stars2.reg') == \
   oscaar.parseRegionsFile('/Users/bmorris/git/OSCAAR/Extras/Examples/stars2.reg')

x, y, radius = oscaar.trackSmooth(image, est_x, est_y, 2, plots=False)#True)
flux, error = oscaar.phot(image, x, y, 10, plots=False)
