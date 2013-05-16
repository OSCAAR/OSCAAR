import numpy as np
from matplotlib import pyplot as plt

## Import oscaar directory using relative paths
import os, sys
lib_path = os.path.abspath('../../Code/')
sys.path.append(lib_path)
import oscaar

sampleData = oscaar.load('oscaarDataBase.pkl')

## Set up the figure
fig = plt.figure(figsize=(10,10))
axis1 = fig.add_subplot(221)
axis2 = fig.add_subplot(222)
axis3 = fig.add_subplot(223)
axis4 = fig.add_subplot(224)

## Plot light curve
axis1.set_title('Transit light curve')
axis1.set_xlabel('Time (JD)')
axis1.set_ylabel('Relative Flux')
axis1.plot(sampleData.times,sampleData.lightCurve,'.')	## Plot Light Curve
axis1.axvline(ymin=0,ymax=1,x=sampleData.ingress,linestyle=":")
axis1.axvline(ymin=0,ymax=1,x=sampleData.egress,linestyle=":")

## Trace (x,y) position of the target star 
starDictionary = sampleData.getDict()	## The position data is stored in a dictionary
starKeys = sampleData.keys				## There are keys for each star in the dictionary
targetX = starDictionary[starKeys[0]]['x-pos'] ## Access the position data with this dictionary look-up
targetY = starDictionary[starKeys[0]]['y-pos']
axis2.plot(targetX,targetY)
axis2.set_title('Target centroid pixel position (trace)')
axis2.set_xlabel('X')
axis2.set_ylabel('Y')

## Show the x and y position of the star over time
axis3.plot(sampleData.times,targetX,label='X')
axis3.plot(sampleData.times,targetY,label='Y')
axis3.legend()
axis3.set_title('Target centroid pixel position (over time)')
axis3.set_xlabel('Time (JD)')
axis3.set_ylabel('Pixel position of stellar centroid')

## Plot the raw fluxes of each star
for star in sampleData.keys:
	axis4.errorbar(sampleData.times,starDictionary[star]['rawFlux'],yerr=starDictionary[star]['rawError'],fmt='o',label=("Star %s" % star))
axis4.set_title('Raw flux for each star')
axis4.set_xlabel('Time (JD)')
axis4.set_ylabel('Raw flux (counts)')
#axis4.legend()

plt.subplots_adjust(hspace=0.3,wspace=0.3)
plt.show()