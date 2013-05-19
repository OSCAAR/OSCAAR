'''
Generate a simulated transit observation to test oscaar with.
Three stars in the image from left to right are the target, 
comparison star A, and comparison star B. 

WARNING: If you want to keep the contents of the 
`OSCAAR/Extras/Examples/sampleData/images` directory, save a 
copy of it with a different name. This script will overwrite 
any directory named `images` within this directory.

From the oscaar Wiki:
    (https://github.com/OSCAAR/OSCAAR/wiki/Generating-Sample-Data)
    A transit of the target star will occur in the middle of the 
    simulated observations, and we use these data to see how our 
    differential photometry routines perform. Though the simulated 
    "stars" are exceedingly square approximations of what real 
    stellar image shapes look like in real observations, some 
    important sources of signal and noise are included in the 
    simulation in order to test oscaar in as close to battle-field 
    conditions as possible. We simulate dark current, sky background, 
    stars of different magnitudes and appropriate photon noise for 
    each of those components. We also jitter the centroids of the 
    stars around randomly in small two dimensional shifts to 
    demonstrate the capabilities of oscaar's stellar centroid 
    tracking algorithm. Below is one such simulated image with the 
    star magnitudes significantly decreased so as to portray the 
    shot noise in the background as well as in the stars in the 
    same colormapping.

    ...

    Here are some `init.par` and `observatory.par` parameters that 
    should be set to particular values to achieve successful 
    differential photometry from the simulated data sets. From 
    `init.par`:
        Smoothing Constant = 3
        Tracking Zoom = 15
        Ingress = 2013-05-15;10:06:30
        Egress = 2013-05-15;11:02:35 
    And from `observatory.par`,
        Exposure Time Keyword: JD

Requires that the C library for generating transit light curves
is compiled. If it's not, change directories to `sampleData/c`
and execute `python setup.py build_ext --inplace`. 
See the detailed instructions on the oscaar wiki: 
https://github.com/OSCAAR/OSCAAR/wiki/Generating-Sample-Data

Core developer: Brett Morris
'''

import numpy as np
import pyfits
from shutil import rmtree
from os import mkdir
from glob import glob
from matplotlib import pyplot as plt

## Import oscaar directory using relative paths
## ** This assumes that you haven't moved the 
## OSCAAR/Extras/Examples/sampleData directory
import os
import oscaar.code.oscaar as oscaarx

def main():
    #################################################################
    ## Tweak these parameters, if you like!
    NdataImages = 200        ## Number of data images to generate
    NdarkImages = 3          ## Number of dark frames to generate
    NflatImages = 3          ## Number of flat fields to generate
    flatFieldCounts = 20000  ## Approx counts per pixel in flat field
    imageDimensionX = 120    ## Pixel dimensions of each image
    imageDimensionY = 40
    starDimensions = 4       ## Pixel dimensions of the stars
    skyBackground = 500      ## Background counts from sky brightness
    darkBackground = 100     ## Background counts from detector
    targetFluxOOT = 10000    ## Flux (in counts) from each pixel of the unocculted target star (out-of-transit)
    relativeFluxCompA = 0.85 ## Flux from comp A relative to target
    relativeFluxCompB = 0.95 ## Flux from comp B relative to target
    plotModel = False        ## Plot the injected transit light curve
    createMasterFlatNow = True  ## Use oscaar to create a master flat from the freshly generated flat frames
    ## Isn't it nice to control the signal to noise?
    #################################################################
    
    ## Delete `images` directory, if there is one, and
    ##      make a fresh one.
    if len(glob(os.path.join(os.path.dirname(__file__),'images'))) > 0: rmtree(os.path.join(os.path.dirname(__file__),'images'))
    mkdir(os.path.join(os.path.dirname(__file__),'images'))
    
    ## Pixel positions of the stars (x,y)
    targetX = [20-starDimensions/2,20+starDimensions/2]
    compAX = [60-starDimensions/2,60+starDimensions/2]
    compBX = [100-starDimensions/2,100+starDimensions/2]
    starsY = [imageDimensionY/2-starDimensions/2,imageDimensionY/2+starDimensions/2]
    
    ## Set ingress/egress times, transiting system parameters 
    ## In GD: Ingress = 2013-05-15;10:06:30; egress = 2013-05-15;11:02:35
    jd0 = 2456427.88890 
    exposureTime = 45/(60*60*24.) ## Convert s -> hr
    times = np.arange(jd0,jd0+exposureTime*NdataImages,exposureTime)
    # [p,ap,P,i,gamma1,gamma2,e,longPericenter,t0]
    modelParams = [ 0.1179, 14.71, 1.580400, 90.0, 0.23, \
                    0.30, 0.00, 0.0, np.mean(times,dtype=np.float64)]
    np.savetxt(os.path.join(os.path.dirname(__file__),'modelParams.txt'),modelParams)
    modelLightCurve = oscaarx.occultquad(times,modelParams)
    if plotModel: 
    	fig = plt.figure()
    	ax1 = fig.add_subplot(111)
    	def format_coord(x, y):
    		'''Function to also give data value on mouse over with imshow.'''
    		return 'JD=%1.6f, Flux=%1.6f' % (x, y)
    	ax1.set_xlabel('Time (JD)')
    	ax1.set_ylabel('Relative Flux')
    	ax1.set_title('Injected Light Curve')
    	ax1.plot(times,modelLightCurve)
    	ax1.format_coord = format_coord
    	plt.show()
    
    ## For producing random arrays, initialize reference arrays with the proper shapes
    imageShapedMatrix = np.zeros([imageDimensionY,imageDimensionX])
    starShapedMatrix = np.zeros([starDimensions,starDimensions])
    
    ## Simulate dark frames with shot noise
    for i in range(NdarkImages):
        darkFrame = darkBackground + np.random.normal(imageShapedMatrix,np.sqrt(darkBackground))
        darkFrame = np.require(darkFrame,dtype=int)   ## Require integer counts
        pyfits.writeto(os.path.join(os.path.dirname(__file__),'images/simulatedImg-'+str(i).zfill(3)+'d.fits'),darkFrame)
    
    ## Simulate ideal flat frames (perfectly flat)
    for i in range(NflatImages):
        ## Flats will be completely flat -- ie, we're pretending that we have a 
        ##      perfect optical path with no spatial flux variations.
        flatField = np.zeros([imageDimensionY,imageDimensionX]) +  flatFieldCounts
        flatField = np.require(flatField,dtype=int)## Require integer counts
        pyfits.writeto(os.path.join(os.path.dirname(__file__),'images/simulatedImg-'+str(i).zfill(3)+'f.fits'),flatField)
    
    
    ## Create master flat now using oscaar's standard flat maker
    if createMasterFlatNow:
        flatPaths = glob(os.path.join(os.path.dirname(__file__),'images/simulatedImg-???f.fits'))
        flatDarkPaths = glob(os.path.join(os.path.dirname(__file__),'images/simulatedImg-???d.fits'))   ## Use the same darks
        masterFlatSavePath = os.path.join(os.path.dirname(__file__),'images/masterFlat.fits')   ## Where to save the master
        oscaarx.standardFlatMaker(flatPaths,flatDarkPaths,masterFlatSavePath,plots=False)
    
    
    ## Create data images
    for i in range(NdataImages):
        ## Produce image with sky and dark background with simulated photon noise for each source
        simulatedImage = darkBackground + skyBackground +\
            np.random.normal(imageShapedMatrix,np.sqrt(darkBackground)) +\
            np.random.normal(imageShapedMatrix,np.sqrt(skyBackground))
        
        ## Create two box-shaped stars with simulated photon noise
        targetBrightness = targetFluxOOT*modelLightCurve[i]  ## Scale brightness with the light curve
        target = targetBrightness + np.random.normal(starShapedMatrix,np.sqrt(targetBrightness))
        
        compBrightnessA = targetFluxOOT*relativeFluxCompA
        compBrightnessB = targetFluxOOT*relativeFluxCompB
        compA = compBrightnessA + np.random.normal(starShapedMatrix,np.sqrt(compBrightnessA))
        compB = compBrightnessB + np.random.normal(starShapedMatrix,np.sqrt(compBrightnessB))
        
        ## Add stars onto the simulated image with some position jitter
        randomPositionJitterX = np.sign(np.random.uniform(-1,1))	## +/- 1 pixel stellar centroid position jitter
        randomPositionJitterY = np.sign(np.random.uniform(-1,1))	## +/- 1 pixel stellar centroid position jitter
        simulatedImage[starsY[0]+randomPositionJitterY:starsY[1]+randomPositionJitterY,targetX[0]+randomPositionJitterX:targetX[1]+randomPositionJitterX] += target
        simulatedImage[starsY[0]+randomPositionJitterY:starsY[1]+randomPositionJitterY,compAX[0]+randomPositionJitterX:compAX[1]+randomPositionJitterX] += compA
        simulatedImage[starsY[0]+randomPositionJitterY:starsY[1]+randomPositionJitterY,compBX[0]+randomPositionJitterX:compBX[1]+randomPositionJitterX] += compB
    
        ## Force counts to integers, save.
        simulatedImage = np.require(simulatedImage,dtype=int)   ## Require integer counts before save
    
        header = pyfits.Header()
        header.append(('JD',times[i],'Simulated Time (Julian Date)'))
        pyfits.writeto(os.path.join(os.path.dirname(__file__),'images/simulatedImg-'+str(i).zfill(3)+'r.fits'),simulatedImage,header=header)
        
if __name__ == '__main__':
    main()