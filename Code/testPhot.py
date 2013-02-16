import photPack
import pyfits
import numpy as np
from matplotlib import pyplot as plt

image = pyfits.open('wasp35z.fits')[0].data
est_x,est_y = [468,692]#[692,468]
#star = image[est_x-20:est_x+20,est_y-20:est_y+20]

x, y, radius = photPack.trackSmooth(image, est_x, est_y, 2, plots=False)#True)
print x,y
flux, error, maximumValue = photPack.phot(image, x, y, 10, plots=True)
print flux, error

#plt.imshow(star,interpolation='nearest')