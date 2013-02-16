#import oscaar
import oscaar
import pyfits
import numpy as np
from matplotlib import pyplot as plt
from time import time

image = pyfits.open('wasp35z.fits')[0].data
est_x,est_y = [468,692]

regsPath = '../Extras/Examples/stars2.reg'

starsDictionary = oscaar.starBank(regsPath)
print starsDictionary.returnDict()

