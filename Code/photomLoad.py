import oscaar
import pyfits
import numpy as np
from matplotlib import pyplot as plt
from time import time

## Inputs to paths, to be replaced with init.par parser
inputPath = 'outputs/oscaarDataBase.pkl'
data = oscaar.load(inputPath)

#plt.plot(data.getTimes(),data.lightCurve)
#plt.show()
allStars = data.getDict()
for star in allStars:
    plt.plot(data.getTimes(),allStars[star]['rawFlux'],'.')
plt.show()