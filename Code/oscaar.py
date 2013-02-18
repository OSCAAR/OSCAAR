'''oscaar v2.0 
   Module for differential photometry
   Developed by Brett Morris, 2011-2013'''
import numpy as np
from numpy import linalg as LA
import pyfits
from matplotlib import pyplot as plt
import matplotlib.cm as cm
from scipy import ndimage, optimize
from time import sleep
import shutil
from glob import glob
from re import split
import cPickle
from shutil import copy
def paddedStr(num,pad):
    '''Return the number num padded with zero-padding of length pad'''
    strlen = len(str(num))
    lenpad = pad-strlen
    return str((lenpad*'0')+str(num))

def ut2jd(ut):
    '''
    Convert times from Universal Time (UT) to Julian Date (JD)
    
    INPUTS: ut - Time in Universial Time (UT)
    
    RETURNS: jd - Julian Date (JD)
    '''
    [date, Time] = ut.split(';')
    [year, month, day] = date.split('-')
    [hour, min, sec] = Time.split(':')
    year = int(year); month = int(month); day = int(day)
    hour = int(hour); min = int(min); sec = float(sec)
    #years = (int(year) + 4716)*365.25
    if month == 1 or month == 2: 
        month += 12
        year -= 1
    a = year/100
    b = a/4
    c = 2-a+b
    d = day
    e = np.floor(365.25*(year+4716))
    f = np.floor(30.6001*(month+1))
    years = c+d+e+f-1524.5
    fracOfDay = (hour/24.) + (min/(24*60.)) + (sec/(24*60*60.))
    jd = years + fracOfDay
    return jd

def cd(a=None):
    """Change to directory a where a is a 
       string inside of single quotes. If a
       is empty, changes to parent directory"""
    if a is None:
        os.chdir(os.pardir)
    else:
        os.chdir(str(a))

def cp(a, b):
    """Copy file a to location b where a,b are
       strings inside of single quotes"""
    copy(str(a),str(b))

def overWriteCheck(filename, checkfiles, varcheck):
    """Checks to see if a particular file should be overwritten based on whether varcheck is on or off"""
    overcheck = None
    for i in range(0, len(checkfiles)):
        if checkfiles[i]== filename and varcheck == 'on':
            overcheck = raw_input('WARNING: Overwrite /' + filename + '/ ? (Y/n): ')
            break
    if overcheck == '' or overcheck == 'Y' or overcheck == 'y':
        shutil.rmtree(filename)
        os.mkdir(filename)

def meanDarkFrame(darksPath):
    '''Return the mean dark frame calculated from each dark frame in darksPath'''
    darkFiles = glob(darksPath)
    [dim1, dim2] = np.shape(pyfits.open(darkFiles[0])[0].data)
    ## Create N-dimensional array for N dark frames, where the first 
    ##    two dimensions are the dimensions of the first image
    darks = np.zeros([len(darkFiles),dim1,dim2])
    ## Return mean of all darks
    for i in range(0,len(darkFiles)):
        darks[i,:,:] = pyfits.open(darkFiles[i])[0].data
    return np.mean(darks,axis=0)

def parseRegionsFile(regsPath):
    '''Parse the DS9 regions file (written in .txt format) which contains
       the initial guesses for the stellar centroids, in the following format:
             "circle(<y-center>,<x-center>,<radius>)"
       The reversed x,y order comes from the different directions that FITS files
       are read-in with DS9 and PyFits.
       
       INPUTS: regsPath - Path to the DS9 regions file with stellar centroid coords
       
       RETURNS: init_x_list - Inital estimates of the x-centroids
       
                init_y_list - Inital estimates of the y-centroids
       
    '''
    regionsData = open(regsPath,'r').read().splitlines()
    init_x_list = []
    init_y_list = []
    for i in range(0,len(regionsData)):
        if regionsData[i][0:6] == 'circle':
            y,x = split("\,",split("\(",regionsData[i])[1])[0:2]
            init_y_list.append(float(y))
            init_x_list.append(float(x))
    return init_x_list,init_y_list

def quadraticFit(derivative,ext):
    '''Find an extremum in the data and use it and the points on either side, fit
       a quadratic function to the three points, and return the x-position of the 
       apex of the best-fit parabola. 
       
       Called by oscaar.trackSmooth()
       
       INPUTS: derivative - The first derivative of the series of points, usually 
                            calculated by np.diff()
                            
               ext = Extremum to look find: "max" or "min"
        
       RETURNS: extremum - the (non-integer) index where the extremum was found
       
    '''
    rangeOfFit = 1
    lenDer = len(derivative)/2
    if ext == "max":
        indExtrema = np.argmax(derivative[:lenDer])
    elif ext == "min":
        indExtrema = np.argmin(derivative[lenDer:])+lenDer

    fitPart = derivative[indExtrema-rangeOfFit:indExtrema+rangeOfFit+1]
    if len(fitPart) == 3:
        stackPolynomials = np.zeros([3,3])
        for i in range(0,len(fitPart)):
            stackPolynomials[i,:] = [i**2,i,1.0]
        estimatedCoeffs = np.dot(LA.inv(stackPolynomials),fitPart)
        d_fit = -estimatedCoeffs[1]/(2.0*estimatedCoeffs[0])            #d_fit = -b_fit/(2.*a_fit)
        extremum = d_fit+indExtrema-rangeOfFit
    else: 
        extremum = indExtrema
    return extremum

def masterFlatMaker(flatImagesPath,flatDarkImagesPath,masterFlatSavePath,plots=False):
    '''Make a master flat by taking a median of a group of flat fields
    
    INPUTS: flatImagesPath - Path to the flat field exposures
    
            flatDarkImagesPath - Path to the flat field darks
            
            masterFlatSavePath - Where to save the master flat that is created
            
            plots - Plot the master flat on completion when plots=True
    '''
    ## Create zero array with the dimensions of the first image for the flat field
    [dim1, dim2] = np.shape(pyfits.open(flatImagesPath[0])[0].data)
    flatSum = np.zeros([dim1, dim2])

    ## Create N-dimensional array for N dark frames, where the first 
    ##    two dimensions are the dimensions of the first image
    darks = np.zeros([len(flatDarkImagesPath),dim1,dim2])

    ## Take mean of all darks
    for i in range(0,len(flatDarkImagesPath)):
        darks[i,:,:] = pyfits.open(flatDarkImagesPath[i])[0].data
    dark = np.mean(darks,axis=0)

    ## Sum up all flat fields, subtract mean dark frame from each flat
    for flatImage in flatImagesPath:
        flatSum += pyfits.open(flatImage)[0].data - dark
    ## Divide the summed flat fields by their mean to obtain a flat frame
    masterFlat = flatSum/np.mean(flatSum)

    if plots:
        ## If plots == True, plot the resulting master flat
        fig = plt.figure()
        a = plt.imshow(masterFlat,interpolation='nearest')
        a.set_cmap('gray')
        plt.title('Normalized Master Flat Field')
        fig.colorbar(a)
        fig.canvas.set_window_title('oscaar2.0 - Master Flat') 
        plt.show()

    ## Write out both a Numpy pickle (.NPY) and a FITS file
    np.save(masterFlatSavePath+'.npy',masterFlat)
    pyfits.writeto(masterFlatSavePath+'.fits',masterFlat)


def trackSmooth(image, est_x, est_y, smoothingConst, preCropped=False, zoom=20.0, plots=False):
    '''Method for tracking stellar centroids. 
    
       INPUTS: image - Numpy array image
       
               est_x - Inital estimate for the x-centroid of the star

               est_y - Inital estimate for the y-centroid of the star

               smoothingConstant - Controls the degree to which the raw stellar intensity
                                   profile will be smoothed by a Gaussian filter 
                                   (0 = no smoothing)

               preCropped - If preCropped=False, image is assumed to be a raw image, if
                            preCropped=True, image is assumed to be only the portion of the
                            image near the star

               zoom - How many pixels in each direction away from the estimated centroid 
                      to consider when tracking the centroid. Be sure to choose a large 
                      enough zoom value the stellar centroid in the next exposure will fit
                      within the zoom

               plots - If plots=True, display stellar intensity profile in two axes
                       and the centroid solution
                                   
        RETURNS: xCenter - the best-fit x-centroid of the star
        
                 yCenter - the best-fit y-centroid of the star
                 
                 averageRadius - average radius of the SMOOTHED star in pixels
                 
                 ErrorFlag - Boolean corresponding to whether or not any error occured when 
                             running oscaar.trackSmooth(). If an error occured, the flag is
                             True; otherwise False.
                            
        Core developer: Brett Morris
        Modifications by: Luuk Visser, 2-12-2013
        '''
    '''If you have an interpolated grid as input, small inputs for smoothingConst
        it won't have any effect. Thus it has to be increased by the
        zoom factor you used to sub-pixel interpolate. 
        
        np.e seems to give nice smoothing results if frame is already cut out, you can 
        set preCropped to True, so the script won't cut a frame out again. '''
    try:
        if preCropped:
            zoom = image.shape[0]/2
            est_x, est_y = 0,0
            target = image ## Assume image is pre-cropped image of the star
        else:
            #smoothingConst *= zoom/20 
            target = image[est_x-zoom:est_x+zoom,est_y-zoom:est_y+zoom]   ## Crop image of just the target star
            
        #Save original (unsmoothed) data for plotting purposses
        if plots:
            target_orig = target.copy()
            axisA_orig = np.sum(target,axis=0)   ## Take the sums of all values in each column,
            axisB_orig = np.sum(target,axis=1)   ## then repeat for each row
        
        target = ndimage.gaussian_filter(target, sigma=smoothingConst,order=0)
        
        ## Sum columns
        axisA = np.sum(target,axis=0)   ## Take the sums of all values in each column,
        axisB = np.sum(target,axis=1)   ## then repeat for each row

        axisADeriv = np.diff(axisA)     ## Find the differences between each pixel intensity and
        axisBDeriv = np.diff(axisB)     ## the neighboring pixel (derivative of intensity profile)

        lenaxisADeriv = len(axisADeriv)
        lenaxisADeriv_2 = lenaxisADeriv/2
        lenaxisBDeriv = len(axisBDeriv)
        lenaxisBDeriv_2 = lenaxisBDeriv/2
        
        derivMinAind = np.where(axisADeriv == min(axisADeriv[lenaxisADeriv_2:lenaxisADeriv]))[0][0] ## Minimum in the derivative
        derivMinBind = np.where(axisBDeriv == min(axisBDeriv[lenaxisBDeriv_2:lenaxisBDeriv]))[0][0] ## of the intensity plot

        derivMaxAind = np.where(axisADeriv == max(axisADeriv[0:lenaxisADeriv_2]))[0][0] ## Maximum in the derivative
        derivMaxBind = np.where(axisBDeriv == max(axisBDeriv[0:lenaxisBDeriv_2]))[0][0] ## of the intensity plot

        extremumA = quadraticFit(axisADeriv,ext="max")
        extremumB = quadraticFit(axisADeriv,ext="min")
        extremumC = quadraticFit(axisBDeriv,ext="max")
        extremumD = quadraticFit(axisBDeriv,ext="min")

        averageRadius = (abs(derivMinAind-derivMaxAind)+ \
            abs(derivMinBind-derivMaxBind))/4. ## Average diameter / 2
        axisAcenter = (extremumA+extremumB)/2.
        axisBcenter = (extremumC+extremumD)/2.
        
        xCenter = est_x-zoom+axisBcenter
        yCenter = est_y-zoom+axisAcenter
        
        if plots:
            plt.clf()
            def format_coord(x, y):
                '''Function to also give data value on mouse over with imshow.'''
                col = int(x+0.5)
                row = int(y+0.5)
                try:
                    return 'x=%1.4f, y=%1.4f, z=%1.4f' % (x, y, target[row,col])
                except:
                    return 'x=%1.4f, y=%1.4f' % (x, y)
            
            dimx,dimy = target.shape
            med = np.median(target)
            dsig = np.std(target)
            
            ax = fig.add_subplot(subplotsDimensions+1)
            ax.imshow(target_orig, cmap=cm.gray, interpolation="nearest",vmin = med-0.5*dsig, vmax =med+2*dsig)
            ax.set_title('Star Center')
            rcos = lambda theta: axisAcenter+averageRadius*np.cos(theta)
            rsin = lambda theta: axisBcenter+averageRadius*np.sin(theta)
            theta = np.arange(0,360)*(np.pi/180)
            ax.plot(rcos(theta),rsin(theta),'m',linewidth=2)
            ax.plot([axisAcenter]*dimy,range(dimy),'b')
            ax.plot(range(dimx),[axisBcenter]*dimx,'r')
            ax.set_xlim([-.5,dimx-.5])
            ax.set_ylim([-.5,dimy-.5])
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.format_coord = format_coord 
            
            ax2 = fig.add_subplot(subplotsDimensions+2)
            ax2.set_title('Smoothed Intensity Profile')
            ax2.plot(axisB,'-r')
            ax2.plot(axisB_orig,'-r', alpha=0.33)
            ax2.axvline(x=extremumC,ymin=0,ymax=1,color='r',linestyle=':',linewidth=1)
            ax2.axvline(x=extremumD,ymin=0,ymax=1,color='r',linestyle=':',linewidth=1)
            ax2.axvline(x=axisBcenter,ymin=0,ymax=1,color='r',linewidth=2)
            ax2.set_xlabel('X')
            ax2.set_ylabel('Counts')

            ax3 = fig.add_subplot(subplotsDimensions+3)
            ax3.plot(axisA,'-b')
            ax3.plot(axisA_orig,'-b', alpha=0.33)
            ax3.set_title('Smoothed Intensity Profile')
            ax3.axvline(x=extremumA,ymin=0,ymax=1,color='b',linestyle=':',linewidth=1)
            ax3.axvline(x=extremumB,ymin=0,ymax=1,color='b',linestyle=':',linewidth=1)
            ax3.axvline(x=axisAcenter,ymin=0,ymax=1,color='b',linewidth=2)
            ax3.set_xlabel('Y')
            ax3.set_ylabel('Counts')
            plt.draw()
        return [xCenter,yCenter,averageRadius, False]
    except Exception:    ## If an error occurs:
        print "An error has occured in oscaar.trackSmooth(), \n\treturning inital (x,y) estimate"
        return [est_x, est_y, 1.0, True]
        
def phot(image, xCentroid, yCentroid, apertureRadius, annulusRadiusFactor=1.5, ccdGain=1, plots=False):
    '''Method for aperture photometry. 
    
       INPUTS: image - numpy array image
       
               xCentroid - stellar centroid along the x-axis 
                           (determined by trackSmooth or equivalent)
                           
               xCentroid - stellar centroid along the y-axis 
                           (determined by trackSmooth or equivalent)
                           
               apertureRadius - radius in pixels from centroid to use 
                                for source aperture
                                
               annulusRadiusFactor - measure the background for sky background 
                                     subtraction fron an annulus a factor of 
                                     annulusRadiusFactor bigger than the apertureRadius
                                     
               ccdGain - gain of your detector, used to calculate the photon noise
               
               plots - If plots=True, display plots showing the aperture radius and 
                       annulus radii overplotted on the image of the star
                       
        RETURNS: rawFlux - the background-subtracted flux measured within the aperture
        
                 rawError - the photon noise (limiting statistical) Poisson uncertainty on the 
                            measurement of rawFlux

                 ErrorFlag - Boolean corresponding to whether or not any error occured when 
                             running oscaar.phot(). If an error occured, the flag is
                             True; otherwise False.
                            
        Core developer: Brett Morris
    '''
    try:
        annulusRadiusInner = apertureRadius 
        annulusRadiusOuter = annulusRadiusFactor*apertureRadius

        imageCrop = image[xCentroid-annulusRadiusOuter+1:xCentroid+annulusRadiusOuter+2,yCentroid-annulusRadiusOuter+1:yCentroid+annulusRadiusOuter+2]
        [dimx,dimy] = imageCrop.shape
        XX, YY = np.meshgrid(np.arange(dimx),np.arange(dimy))
        x = (XX - annulusRadiusOuter)**2
        y = (YY - annulusRadiusOuter)**2
        sourceIndices = x + y <= apertureRadius**2
        skyIndices = (x + y <= annulusRadiusOuter**2)*(x + y >= annulusRadiusInner**2)
        rawFlux = np.sum(imageCrop[sourceIndices] - np.median(imageCrop[skyIndices]))
        rawError = np.sum(np.sqrt(imageCrop[sourceIndices]*ccdGain)) ## Poisson-uncertainty

        if plots:
            def format_coord(x, y):
                ''' Function to also give data value on mouse over with imshow. '''
                col = int(x+0.5)
                row = int(y+0.5)
                try:
                    return 'x=%1.4f, y=%1.4f, z=%1.4f' % (x, y, imageCrop[row,col])
                except:
                    return 'x=%1.4f, y=%1.4f' % (x, y)
           
            med = np.median(imageCrop)
            dsig = np.std(imageCrop)
            
            ax = fig.add_subplot(subplotsDimensions+photSubplotsOffset+1)
            ax.imshow(imageCrop, cmap=cm.gray, interpolation="nearest",vmin = med-0.5*dsig, vmax =med+2*dsig)
           
            theta = np.arange(0,360)*(np.pi/180)
            rcos = lambda r, theta: annulusRadiusOuter + r*np.cos(theta)
            rsin = lambda r, theta: annulusRadiusOuter + r*np.sin(theta)
            ax.plot(rcos(annulusRadiusInner,theta),rsin(annulusRadiusInner,theta),'r',linewidth=4)
            ax.plot(rcos(annulusRadiusOuter,theta),rsin(annulusRadiusOuter,theta),'r',linewidth=4)
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_title('Aperture')
            ax.set_xlim([-.5,dimx-.5])
            ax.set_ylim([-.5,dimy-.5])
            ax.format_coord = format_coord 
            plt.draw()
        return [rawFlux, rawError, False]
    except Exception:    ## If an error occurs:
        print "An error has occured in oscaar.phot(), \n\tReturning flux = 1"
        return [1.0, 1.0, True]        

def plottingSettings(trackPlots,photPlots):
    global fig, subplotsDimensions, photSubplotsOffset
    if trackPlots or photPlots: plt.ion()
    if trackPlots and photPlots:
        fig = plt.figure(num=None, figsize=(18, 3), facecolor='w',edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        subplotsDimensions = 140
        photSubplotsOffset = 3
        fig.canvas.set_window_title('oscaar2.0') 
    elif photPlots and not trackPlots:
        fig = plt.figure(num=None, figsize=(5, 5), facecolor='w',edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        subplotsDimensions = 110
        photSubplotsOffset = 0
        fig.canvas.set_window_title('oscaar2.0') 
    elif trackPlots and not photPlots:
        fig = plt.figure(num=None, figsize=(14, 4), facecolor='w',edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        subplotsDimensions = 130
        photSubplotsOffset = 0
        fig.canvas.set_window_title('oscaar2.0') 

def regressionScale(comparisonFlux,targetFlux,time,ingress,egress):
	'''
    Use a least-squares regression to stretch and offset a comparison star fluxes
    to scale them to the relative intensity of the target star. Only do this regression
    considering the out-of-transit portions of the light curve.
    
    INPUTS: comparisonFlux - Flux of a comparison star
    
            targetFlux - Flux of the target star
            
            time - List of times for each flux measurement in JD
            
            ingress - Time of ingress (JD, assuming time list is in JD)
            
            egress - Time of egress (JD, assuming time list is in JD)
            
    RETURNS: scaledVector - rescaled version of the comparisonFlux vector using the
                            above described process
    '''
	outOfTransit = (time < ingress) + (time > egress)
	regressMatrix = np.vstack([comparisonFlux[outOfTransit], np.ones_like(targetFlux[outOfTransit])]).T
	m,c = LA.lstsq(regressMatrix,targetFlux[outOfTransit])[0]
	scaledVector = m*comparisonFlux + c
	return scaledVector

def chiSquared(vector1,vector2):
    '''Return chi-squared of two vectors'''
    return np.sum(np.power(vector1-vector2,2))

def medianBin(time,flux,medianWidth):
    numberBins = len(time)/medianWidth
    binnedTime = np.arange(numberBins,dtype=float)
    binnedFlux = np.arange(numberBins,dtype=float)
    binnedStd = np.arange(numberBins,dtype=float)
    for i in range(0,numberBins):
        fluxInBin = flux[i*medianWidth:(i+1)*medianWidth+1]
        binnedTime[i] = np.median(time[i*medianWidth:(i+1)*medianWidth+1])
        binnedFlux[i] = np.median(fluxInBin)
        binnedStd[i] = np.std(fluxInBin)
    return binnedTime, binnedFlux, binnedStd    

class dataBank:
    '''
        Methods for storing information from each star in Python dictionaries.
        
        Core Developer: Brett Morris
    '''
    def __init__(self,imagesPath,darksPath,flatPath,regsPath,ingress,egress,loading=False):
        '''
        Run oscaar.parseRegionsFile() to get the inital guesses for the 
        initial centroids of the stars from the DS9 regions file, create
        dictionaries in which to store all of the data collected
        for each star. Allocate the memory for these arrays wherever possible.
        INPUTS: imagesPath - Path to the data images
        
                darksPath - Path to the dark frames
                
                flatPath - Path to the master flat field
                
                regsPath - Path to the DS9 regions file
                
                ingress - Time of ingress in JD
                
                egress - Time of egress in JD
                
                loading - if loading=True, load data from a previously saved
                          oscaar dataBank object
        '''
        self.imagesPaths = glob(imagesPath)
        self.darksPaths = glob(darksPath)
        self.masterFlat = pyfits.open(flatPath)[0].data
        self.masterFlatPath = flatPath
        self.ingress = ingress
        self.egress = egress
        self.allStarsDict = {}
        init_x_list,init_y_list = parseRegionsFile(regsPath)
        zeroArray = np.zeros_like(self.imagesPaths,dtype=np.float32)
        self.times = np.zeros_like(self.imagesPaths,dtype=np.float64)
        self.keys = []
        for i in range(0,len(init_x_list)):
            self.allStarsDict[paddedStr(i,3)] = {'x-pos':np.copy(zeroArray), 'y-pos':np.copy(zeroArray),\
                            'rawFlux':np.copy(zeroArray), 'rawError':np.copy(zeroArray),'flag':False,\
                            'scaledFlux':np.copy(zeroArray), 'chisq':0}
            self.allStarsDict[paddedStr(i,3)]['x-pos'][0] = init_x_list[i]
            self.allStarsDict[paddedStr(i,3)]['y-pos'][0] = init_y_list[i]
            self.keys.append(paddedStr(i,3))    
        
    def getDict(self):
        '''Return master dictionary of all star data'''
        return self.allStarsDict
        
    def storeCentroid(self,star,exposureNumber,xCentroid,yCentroid):
        '''Store the centroid data collected by oscaar.trackSmooth()
           INPUTS: star - Key for the star for which the centroid has been measured
           
                   exposureNumber - Index of exposure being considered
                   
                   xCentroid - x-centroid of the star
                   
                   yCentroid - y-centroid of the star
        '''
        self.allStarsDict[star]['x-pos'][exposureNumber] = xCentroid
        self.allStarsDict[star]['y-pos'][exposureNumber] = yCentroid   
        
    def storeFlux(self,star,exposureNumber,rawFlux,rawError):
        '''Store the flux and error data collected by oscaar.phot()
           INPUTS: star - Key for the star for which the centroid has been measured
           
                   exposureNumber - Index of exposure being considered
                   
                   rawFlux - flux measured, to be stored
                   
                   rawError - photon noise measured, to be stored
        '''
        self.allStarsDict[star]['rawFlux'][exposureNumber] = rawFlux
        self.allStarsDict[star]['rawError'][exposureNumber] = rawError
        
    def getPaths(self):
        '''Return the paths to the raw images used'''
        return self.imagesPaths
        
    def getFluxes(self,star):
        '''Return the fluxes for one star, where the star parameter is the key for the
              star of interest.'''
        return self.allStarsDict[star]['rawFlux']

    def getErrors(self,star):
        '''Return the errors for one star, where the star parameter is the key for the
              star of interest.'''
        return self.allStarsDict[star]['rawError']
        
    def storeTime(self,expNumber,time):
        '''Store the time in JD from the FITS header.
           INPUTS: exposureNumber - Index of exposure being considered
           
                   time - Time as read-in from the FITS header
        '''
        self.times[expNumber] = time
        
    def getTimes(self):
        '''Return all times collected with dataBank.storeTime()'''
        return self.times
        
    def getFlag(self,star):
        '''Return the flag for the star with key "star" '''
        return self.allStarsDict[star]['flag']
        
    def getAllFlags(self):
        '''Return flags for all stars'''
        flags = []
        for star in self.allStarsDict:
            flags.append(self.allStarsDict[star]['flag'])
        self.flags = flags
        return flags
        
    def setFlag(self,star,setting):
        '''Set flag for star with key <star> to <setting> where 
           setting is a Boolean'''
        self.allStarsDict[star]['flag'] = setting
        
    def getKeys(self):
        '''Return the keys for all of the stars'''
        return self.keys
        
    def scaleFluxes(self):
        '''
        When all fluxes have been collected, run this to re-scale the fluxes of each
        comparison star to the flux of the target star. 
        '''
        for star in self.allStarsDict:
            self.allStarsDict[star]['scaledFlux'] = regressionScale(self.getFluxes(star),self.getFluxes('000'),self.getTimes(),self.ingress,self.egress)

    def getScaledFluxes(self,star):
        '''Return the scaled fluxes for one star, where the star parameter is the 
           key for the star of interest.'''
        return np.array(self.allStarsDict[star]['scaledFlux'])
        
    def calcChiSq(self):
        for star in self.allStarsDict:
            self.allStarsDict[star]['chisq'] = chiSquared(self.getFluxes('000'),self.getFluxes(star))
    
    def getAllChiSq(self):
        '''Return chi-squared's for all stars'''
        chisq = []
        for star in self.allStarsDict:
            chisq.append(self.allStarsDict[star]['chisq'])
        self.chisq = chisq
        return self.chisq

    def outOfTransit(self):
        return (self.getTimes() < self.ingress) + (self.getTimes() > self.egress)

    def calcMeanComparison(self,ccdGain=12):
        '''
        Take the regression-weighted mean of all of the comparison stars
        to produce one comparison star flux to compare to the target to
        produce a light curve.
        '''
        numCompStars =  len(self.allStarsDict) - 1
        targetFullLength = len(self.getScaledFluxes('000'))
        target = self.getScaledFluxes('000')[self.outOfTransit()]
        compStars = np.zeros([targetFullLength,numCompStars])
        compStarsOOT = np.zeros([len(target),numCompStars])
        compErrors = np.copy(compStars)
        columnCounter = 0
        for star in self.allStarsDict:
            if star != '000':
                compStars[:,columnCounter] = self.getScaledFluxes(star).astype(np.float64)
                compStarsOOT[:,columnCounter] = self.getScaledFluxes(star)[self.outOfTransit()].astype(np.float64)
                compErrors[:,columnCounter] = self.getErrors(star).astype(np.float64)
                columnCounter += 1
        initP = np.zeros([numCompStars])+ 1./numCompStars
        def errfunc(p,target): ## Find only positive coefficients
            if all(p >=0.0): return np.dot(p,compStarsOOT.T) - target
            #return np.dot(p,compStarsOOT.T) - target

        bestFitP = optimize.leastsq(errfunc,initP[:],args=(target.astype(np.float64)),maxfev=10000000,epsfcn=np.finfo(np.float32).eps)[0]
        print '\nBest fit regression coefficients:',bestFitP
        #return np.dot(bestFitP,compStars.T), np.sqrt(np.dot((bestFitP/ccdGain)**2,(compErrors.T/compStars.T)**2))#np.sqrt(np.dot(np.ones([columnCounter],dtype=float),(compErrors.T/compStars.T)**2))
        self.meanComparisonStar = np.dot(bestFitP,compStars.T)
        self.meanComparisonStarError = np.sqrt(np.dot((bestFitP/ccdGain)**2,((1/np.sqrt(compStars.T*ccdGain))**2))) 
        return self.meanComparisonStar, self.meanComparisonStarError  

    def lightCurve(self,meanComparisonStar):
        '''
        Divide the target star flux by the mean comparison star to yield a light curve,
        save the light curve into the dataBank object.
        
        INPUTS: meanComparisonStar - The fluxes of the (one) mean comparison star
        
        RETURNS: self.lightCurve - The target star divided by the mean comparison 
                                   star, i.e., the light curve.
        '''
        self.lightCurve = self.getFluxes('000')/meanComparisonStar
        return self.lightCurve

    def photonNoise(self):
        '''
        Calculate photon noise using the lightCurve and the meanComparisonStar
        
        RETURNS: self.photonNoise - The estimated photon noise limit
        '''
        self.photonNoise = self.lightCurve*self.meanComparisonStarError
        return self.photonNoise

def save(data,outputPath):
    '''
    Save everything in oscaar.dataBank object <data> to a python pickle using cPickle.
    
    INPUTS: data - oscaar.dataBank() object to save
    
            outputPath - Path for the saved numpy-pickle.
    '''
    if glob(outputPath) > 0 or glob(outputPath+'/oscaarDataBase.pkl') > 0 or glob(outputPath+'.pkl') > 0: ## Over-write check
        print 'WARNING: overwriting the most recent oscaarDataBase.pkl'
    
    if outputPath[len(outputPath)-4:len(outputPath)] == '.pkl':
        outputName = outputPath
    elif outputPath[-1] == '/': 
        outputName = outputPath+'oscaarDataBase.pkl'
    else: 
        outputName = outputPath+'.pkl'
    
    output = open(outputName,'wb')
    cPickle.dump(data,output)
    output.close()

def load(inputPath):
    '''
    Load everything from a oscaar.dataBank() object in a python pickle using cPickle.
    
    INPUTS: data - oscaar.dataBank() object to save
    
            outputPath - Path for the saved numpy-pickle.
    '''
    inputFile = open(inputPath,'rb')
    data = cPickle.load(inputFile)
    inputFile.close()
    return data