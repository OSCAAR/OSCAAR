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
from os import system
import shutil
from glob import glob
from re import split

def paddedStr(num,pad):
    '''Return the number num padded with zero-padding of length pad'''
    strlen = len(str(num))
    lenpad = pad-strlen
    return str((lenpad*'0')+str(num))

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
    command = 'cp '+str(a)+' '+str(b)
    system(command)

def overWriteCheck(filename, checkfiles, varcheck):
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
                
    #        fig = plt.figure(num=None, figsize=(14, 4), facecolor='w', \
    #            edgecolor='k')
    #        fig.subplots_adjust(wspace = 0.5)
            
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
            #plt.show()
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
        
                 rawError - the photon noise (limiting statistical) uncertainty on the 
                            measurement of rawFlux
                            
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
        rawError = np.sum(np.sqrt(imageCrop[sourceIndices]*ccdGain))

        if plots:
            def format_coord(x, y):
                ''' Function to also give data value on mouse over with imshow. '''
                col = int(x+0.5)
                row = int(y+0.5)
                try:
                    return 'x=%1.4f, y=%1.4f, z=%1.4f' % (x, y, imageCrop[row,col])
                except:
                    return 'x=%1.4f, y=%1.4f' % (x, y)
            #fig = plt.figure(num=None, facecolor='w', edgecolor='k')
            #fig.subplots_adjust(wspace = 0.5)
            
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
            ax.set_xlim([-.5,dimx-.5])
            ax.set_ylim([-.5,dimy-.5])
            ax.format_coord = format_coord 
            plt.draw()
            #plt.show()
        return [rawFlux, rawError, False]
    except Exception:    ## If an error occurs:
        print "An error has occured in oscaar.phot(), \n\tReturning flux = 1"
        return [1.0, 1.0, True]        

def figureSettings(trackPlots,photPlots):
    global fig, subplotsDimensions, photSubplotsOffset
    if trackPlots or photPlots: plt.ion()
    if trackPlots and photPlots:
        fig = plt.figure(num=None, figsize=(18, 3), facecolor='w',edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        subplotsDimensions = 140
        photSubplotsOffset = 3
    elif photPlots and not trackPlots:
        fig = plt.figure(num=None, figsize=(5, 5), facecolor='w',edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        subplotsDimensions = 110
        photSubplotsOffset = 0
    elif trackPlots and not photPlots:
        fig = plt.figure(num=None, figsize=(14, 4), facecolor='w',edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        subplotsDimensions = 130
        photSubplotsOffset = 0

class dataBank:
    '''
        Methods for storing information from each star in Python dictionaries.
    '''
    def __init__(self,imagesPath,darksPath,flatPath,regsPath,ingress,egress):
        '''Run oscaar.parseRegionsFile() to get the inital guesses for the 
           initial centroids of the stars from the DS9 regions file, create
           dictionaries for each star, with x and y position lists'''
        self.imagesPaths = glob(imagesPath)
        self.darksPaths = glob(darksPath)
        self.masterFlat = pyfits.open(flatPath)[0].data
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
                            'scaledFlux':np.copy(zeroArray)}
            self.allStarsDict[paddedStr(i,3)]['x-pos'][0] = init_x_list[i]
            self.allStarsDict[paddedStr(i,3)]['y-pos'][0] = init_y_list[i]
            self.keys.append(paddedStr(i,3))
       # self.starDict['init_x_list'] = np.array(init_x_list,type=np.float32)
        #self.starDict['init_y_list'] = np.array(init_y_list,type=np.float32)        
    def returnDict(self):
        return self.allStarsDict
    def storeCentroid(self,star,exposureNumber,xCentroid,yCentroid):
        self.allStarsDict[star]['x-pos'][exposureNumber] = xCentroid
        self.allStarsDict[star]['y-pos'][exposureNumber] = yCentroid   
    def storeFlux(self,star,exposureNumber,rawFlux,rawError):
        self.allStarsDict[star]['rawFlux'][exposureNumber] = rawFlux
        self.allStarsDict[star]['rawError'][exposureNumber] = rawError
    def paths(self):
        return self.imagesPaths
    def returnFluxes(self,star):
        return self.allStarsDict[star]['rawFlux']
    def storeTime(self,expNumber,time):
        self.times[expNumber] = time
    def timeJD(self):
        return self.times
    def getFlag(self,star):
        return self.allStarsDict[star]['flag']
    def getAllFlags(self):
        flags = []
        for star in self.allStarsDict:
            flags.append(self.allStarsDict[star]['flag'])
        return flags
    def setFlag(self,star,setting):
        self.allStarsDict[star]['flag'] = setting
    def getKeys(self):
        return self.keys