'''
Created on Jan 22, 2013
Classes and methods for photometry with oscaar2.0
Created by Brett Morris.
'''
import numpy as np
from numpy import linalg as LA
import pyfits
import math
from matplotlib import pyplot as plt
from scipy import ndimage, optimize
from time import sleep
from os import system
from glob import glob
import re
import pyfits 
import matplotlib.cm as cm
def mkdir(a, b=None):
    """Make new directory with name a where a
       is a string inside of single quotes"""
    if b is None:
        c = ''
    else:
        c = ' '+str(b)
    command = 'mkdir '+str(a)+str(c)
    system(command)

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
        system('rm -r ' + filename)
        mkdir(filename)

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
    '''Parse the DS9 regions file (.txt format) which contains
       the initial guesses for the stellar centroids'''
    system("ls "+regsPath+"> filelists/reglist.txt")

    regfile = open('filelists/reglist.txt','r').read().splitlines()[0]
    regdata = open(regfile,'r').read().splitlines()

    circle_data = []
    init_x_list = []
    init_y_list = []
    hww_list = []
    for i in range(0,len(regdata)):
        if regdata[i][0:6] == 'circle':
            circle_data.append(re.split("\(",regdata[i])[1])

    for i in range(0,len(circle_data)):
        xydata = re.split("\,",circle_data[i])
        xyhdata = re.split("\)",xydata[2])[0]
        init_y_list.append(float(xydata[0]))
        init_x_list.append(float(xydata[1]))
        hww_list.append(float(xyhdata))

    return init_x_list,init_y_list, hww_list

def quadraticFit(derivative,ext):
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

def trackSmooth(scidata,xPos,yPos,smoothConst,aprad,plots=False):
    '''Track the centroid coordinate of the star in the cropped image scidata located naer
       (init_x,init_y). Smooth out the intensity profile using a Gaussian filter from SciPy.
       Set the aperture radius through which to track the star to aprad.'''
    hww = 8
    #hww = 8

    target = scidata[xPos-hww:xPos+hww,yPos-hww:yPos+hww]   ## Cropped image of just the target star
    target = ndimage.gaussian_filter(target, sigma=smoothConst,order=0)
    ## Sum columns
    axisA = np.sum(target,axis=0)   ## Take the sums of all values in each column,
    axisB = np.sum(target,axis=1)   ## then repeat for each row

    axisADeriv = np.diff(axisA)     ## Find the differences between each pixel intensity and
    axisBDeriv = np.diff(axisB)     ## the neighboring pixel (derivative of intensity profile)

    derivMinAind = np.where(axisADeriv == min(axisADeriv[len(axisADeriv)/2:len(axisADeriv)]))[0][0] ## Minimum in the derivative
    derivMinBind = np.where(axisBDeriv == min(axisBDeriv[len(axisBDeriv)/2:len(axisBDeriv)]))[0][0] ## of the intensity plot

    derivMaxAind = np.where(axisADeriv == max(axisADeriv[0:len(axisADeriv)/2]))[0][0] ## Maximum in the derivative
    derivMaxBind = np.where(axisBDeriv == max(axisBDeriv[0:len(axisBDeriv)/2]))[0][0] ## of the intensity plot
    indMax = np.argmax(axisADeriv)

    
    extremumA = quadraticFit(axisADeriv,ext="max")
    extremumB = quadraticFit(axisADeriv,ext="min")
    extremumC = quadraticFit(axisBDeriv,ext="max")
    extremumD = quadraticFit(axisBDeriv,ext="min")

    averageRadius = (abs(derivMinAind-derivMaxAind)+abs(derivMinBind-derivMaxBind))/4. ## Average diameter / 2
    axisAcenter = (extremumA+extremumB)/2.0
    axisBcenter = (extremumC+extremumD)/2.0
    xCenter = xPos-hww+axisBcenter
    yCenter = yPos-hww+axisAcenter

    if plots:
        plt.clf()
        plt.subplot(121)
        img = plt.imshow(target)
        img.set_interpolation('nearest')
        rcos = lambda a: axisAcenter+aprad*np.cos(a)       ## Plot inner radius circle
        rsin = lambda a: axisBcenter+aprad*np.sin(a)
        p = np.arange(0,360)*(np.pi/180)
        plt.plot(rcos(p),rsin(p),'w',linewidth=2)
        plt.xlim([0,hww*2.])
        plt.ylim([hww*2.,0])
        plt.subplot(121).get_xaxis().set_ticks([])
        plt.subplot(121).get_yaxis().set_ticks([])
        plt.title('Smoothed Intensity')

        plt.subplot(122)
        plt.plot(axisA,'-b')
        plt.plot(axisB,'-r')
        plt.title('Smoothed Intensity Profile')
        plt.axvline(x=extremumA,ymin=0,ymax=1,color='b',
                linestyle=':',linewidth=1)
        plt.axvline(x=extremumB,ymin=0,ymax=1,color='b',
                linestyle=':',linewidth=1)
                
        plt.axvline(x=extremumC,ymin=0,ymax=1,color='r',
                linestyle=':',linewidth=1)
        plt.axvline(x=extremumD,ymin=0,ymax=1,color='r',
                linestyle=':',linewidth=1)
        plt.subplots_adjust(wspace = 0.5)
        plt.xlabel('Pixels')
        plt.ylabel('Counts')
        plt.draw()

    return [xCenter,yCenter,averageRadius]

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


def trackSmooth(image, est_x, est_y, smoothingConst, plots=False, precut=False, zoom=1.0):
    '''Track the centroid coordinate of the star in the image located naer
       (est_x,est_y). Smooth out the intensity profile using a Gaussian filter from SciPy.
       Set the aperture radius through which to track the star to aprad.'''
       
    """ You can have an interpolated grid as input. If smoothingConst is then 
        small, it won't have any effect. So it has to be increased by the
        zoom factor you used to sub-pixel interpolate. 
        
        e seems to give nice smoothing results
        
        Core developer: Brett Morris.
        Modifications by Luuk Visser, Leiden University & Delft University 
        of Technology - 2-12-2013"""
    smoothingConst = zoom*np.e
    
    """ If frame is already cut out, you can set precut to True, so the script
        won't cut a frame out again. """
    if precut == False:
        hww = zoom*20
        target = image[est_x-hww:est_x+hww,est_y-hww:est_y+hww]   ## Cropped image of just the target star
    else:
        hww = 0
        est_x, est_y = 0,0
        target = image ## Use pre-cropped image of the star
        
    """  Save original (unsmoothed) data for plotting purposses """
    if plots:
        target_orig = target.copy()
        ## Sum columns of original data
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
#    indMax = np.argmax(axisADeriv)

    extremumA = quadraticFit(axisADeriv,ext="max")
    extremumB = quadraticFit(axisADeriv,ext="min")
    extremumC = quadraticFit(axisBDeriv,ext="max")
    extremumD = quadraticFit(axisBDeriv,ext="min")

    averageRadius = (abs(derivMinAind-derivMaxAind)+ \
        abs(derivMinBind-derivMaxBind))/4. ## Average diameter / 2
    axisAcenter = (extremumA+extremumB)/2.
    axisBcenter = (extremumC+extremumD)/2.
    
    xCenter = est_x-hww+axisBcenter
    yCenter = est_y-hww+axisAcenter
    
    if plots:
        def format_coord(x, y):
            """ Function to also give data value on mouse over with imshow. """
            col = int(x+0.5)
            row = int(y+0.5)
            try:
                return 'x=%1.4f, y=%1.4f, z=%1.4f' % (x, y, target[row,col])
            except:
                return 'x=%1.4f, y=%1.4f' % (x, y)
            
        fig = plt.figure(num=None, figsize=(14, 4), facecolor='w', \
            edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        
        dimx,dimy = target.shape
        med = np.median(target)
        dsig = np.std(target)
        
        ax = fig.add_subplot(131)
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
        
        ax2 = fig.add_subplot(132)
        ax2.set_title('Smoothed Intensity Profile')
        ax2.plot(axisB,'-r')
        ax2.plot(axisB_orig,'-r', alpha=0.33)
        ax2.axvline(x=extremumC,ymin=0,ymax=1,color='r',linestyle=':',linewidth=1)
        ax2.axvline(x=extremumD,ymin=0,ymax=1,color='r',linestyle=':',linewidth=1)
        ax2.axvline(x=axisBcenter,ymin=0,ymax=1,color='r',linewidth=1)
        ax2.set_xlabel('X')
        ax2.set_ylabel('Counts')

        ax3 = fig.add_subplot(133)
        ax3.plot(axisA,'-b')
        ax3.plot(axisA_orig,'-b', alpha=0.33)
        ax3.set_title('Smoothed Intensity Profile')
        ax3.axvline(x=extremumA,ymin=0,ymax=1,color='b',linestyle=':',linewidth=1)
        ax3.axvline(x=extremumB,ymin=0,ymax=1,color='b',linestyle=':',linewidth=1)
        ax3.axvline(x=axisAcenter,ymin=0,ymax=1,color='b',linewidth=1)
        ax3.set_xlabel('Y')
        ax3.set_ylabel('Counts')
        plt.show()
    return [xCenter,yCenter,averageRadius]
    
def phot(image, x, y, apertureRadius, Kccd=1, plots=False):
    ## *******<from gauss4.py>**********

    rad = apertureRadius
    annulusRadiusInner = apertureRadius                         ## (same as above) ...inner radius
    annulusRadiusOuter = 1.5*apertureRadius                      ##                 ...outer radius

    row = x
    col = y
    imagecrop = image[row-annulusRadiusOuter+1:row+annulusRadiusOuter+2,col-annulusRadiusOuter+1:col+annulusRadiusOuter+2]
    [dimx,dimy] = imagecrop.shape

    rowcrop = colcrop = annulusRadiusOuter                    ## Expected center of the star
                                                    ## in the cropped coordinates
    [dimx,dimy] = imagecrop.shape 

    ixsrc = np.zeros([dimx,dimy])                   ## Pull out array of pixels
    ixsrc_vals = []                                 ## in the 'source' region
    for a in range(0,dimy):                         ## (where the star is)
        for b in range(0,dimx):
            if ((a-colcrop)**2 + (b-rowcrop)**2) <= rad**2:
                ixsrc[b,a] = 1
                ixsrc_vals.append(imagecrop[b,a])

    ixsky = np.zeros([dimx,dimy])                   ## Pull out array of pixels
    ixsky_vals = []                                 ## in the 'sky' region
    for a in range(0,dimy):                         ## (background sky, no stars)
        for b in range(0,dimx):
            if ((a-colcrop)**2 + (b-rowcrop)**2) <= annulusRadiusOuter**2 and (
                (a-colcrop)**2 + (b-rowcrop)**2) >= annulusRadiusInner**2:
                ixsky[b,a] = 1
                ixsky_vals.append(imagecrop[b,a])
    maxval = max(ixsrc_vals)
    sky = np.median(ixsky_vals)                     ## Take the source-background 
    pix = np.array(ixsrc_vals) - sky                ## sum and divide by CCD gain
    sig = np.sqrt(np.abs(np.array(ixsrc_vals))/Kccd)**2        ## to get ADU counts
    sig = math.sqrt(np.sum(sig))
    ssig = np.std(np.array(ixsky_vals)/Kccd)*math.sqrt(len(ixsky_vals))
    flx = np.sum(pix)/Kccd
    err = math.sqrt(sig**2 + ssig**2)
    if math.isnan(flx) == True:
        flx = 1.0
    if math.isnan(err) == True:
        err = 1.0
    if plots:
        def format_coord(x, y):
            """ Function to also give data value on mouse over with imshow. """
            col = int(x+0.5)
            row = int(y+0.5)
            try:
                return 'x=%1.4f, y=%1.4f, z=%1.4f' % (x, y, imagecrop[row,col])
            except:
                return 'x=%1.4f, y=%1.4f' % (x, y)
        fig = plt.figure(num=None, facecolor='w', edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        
        dimx,dimy = imagecrop.shape
        med = np.median(imagecrop)
        dsig = np.std(imagecrop)
        ax = fig.add_subplot(111)
        ax.imshow(imagecrop, cmap=cm.gray, interpolation="nearest",vmin = med-0.5*dsig, vmax =med+2*dsig)
       
        theta = np.arange(0,360)*(np.pi/180)
        rcos = lambda r, theta: annulusRadiusOuter + r*np.cos(theta)#col+annulusRadiusInner*math.cos(theta)       ## Plot inner radius circle
        rsin = lambda r, theta: annulusRadiusOuter + r*np.sin(theta)#row+annulusRadiusInner*math.sin(theta)
        ax.plot(rcos(annulusRadiusInner,theta),rsin(annulusRadiusInner,theta),'r',linewidth=4)
        ax.plot(rcos(annulusRadiusOuter,theta),rsin(annulusRadiusOuter,theta),'r',linewidth=4)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_xlim([-.5,dimx-.5])
        ax.set_ylim([-.5,dimy-.5])
        ax.format_coord = format_coord 

        plt.show()
    return [flx, err, maxval]

    
def photOld(image, x, y, apertureRadius, Kccd=1, plots=False):
    ## *******<from gauss4.py>**********

    rad = apertureRadius
    annulusRadiusInner = apertureRadius                         ## (same as above) ...inner radius
    annulusRadiusOuter = 1.5*apertureRadius                      ##                 ...outer radius

    row = x
    col = y
    imagecrop = image[row-annulusRadiusOuter+1:row+annulusRadiusOuter+2,col-annulusRadiusOuter+1:col+annulusRadiusOuter+2]
    [dimx,dimy] = imagecrop.shape

    rowcrop = colcrop = annulusRadiusOuter                    ## Expected center of the star
                                                    ## in the cropped coordinates
    [dimx,dimy] = imagecrop.shape 

    ixsrc = np.zeros([dimx,dimy])                   ## Pull out array of pixels
    ixsrc_vals = []                                 ## in the 'source' region
    for a in range(0,dimy):                         ## (where the star is)
        for b in range(0,dimx):
            if ((a-colcrop)**2 + (b-rowcrop)**2) <= rad**2:
                ixsrc[b,a] = 1
                ixsrc_vals.append(imagecrop[b,a])

    ixsky = np.zeros([dimx,dimy])                   ## Pull out array of pixels
    ixsky_vals = []                                 ## in the 'sky' region
    for a in range(0,dimy):                         ## (background sky, no stars)
        for b in range(0,dimx):
            if ((a-colcrop)**2 + (b-rowcrop)**2) <= annulusRadiusOuter**2 and (
                (a-colcrop)**2 + (b-rowcrop)**2) >= annulusRadiusInner**2:
                ixsky[b,a] = 1
                ixsky_vals.append(imagecrop[b,a])
    maxval = max(ixsrc_vals)
    sky = np.median(ixsky_vals)                     ## Take the source-background 
    pix = np.array(ixsrc_vals) - sky                ## sum and divide by CCD gain
    sig = np.sqrt(np.abs(np.array(ixsrc_vals))/Kccd)**2        ## to get ADU counts
    sig = math.sqrt(np.sum(sig))
    ssig = np.std(np.array(ixsky_vals)/Kccd)*math.sqrt(len(ixsky_vals))
    flx = np.sum(pix)/Kccd
    err = math.sqrt(sig**2 + ssig**2)
    if math.isnan(flx) == True:
        flx = 1.0
    if math.isnan(err) == True:
        err = 1.0
    if plots:
        def format_coord(x, y):
            """ Function to also give data value on mouse over with imshow. """
            col = int(x+0.5)
            row = int(y+0.5)
            try:
                return 'x=%1.4f, y=%1.4f, z=%1.4f' % (x, y, imagecrop[row,col])
            except:
                return 'x=%1.4f, y=%1.4f' % (x, y)
        fig = plt.figure(num=None, facecolor='w', edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        
        dimx,dimy = imagecrop.shape
        med = np.median(imagecrop)
        dsig = np.std(imagecrop)
        ax = fig.add_subplot(111)
        ax.imshow(imagecrop, cmap=cm.gray, interpolation="nearest",vmin = med-0.5*dsig, vmax =med+2*dsig)
       
        theta = np.arange(0,360)*(np.pi/180)
        rcos = lambda r, theta: annulusRadiusOuter + r*np.cos(theta)#col+annulusRadiusInner*math.cos(theta)       ## Plot inner radius circle
        rsin = lambda r, theta: annulusRadiusOuter + r*np.sin(theta)#row+annulusRadiusInner*math.sin(theta)
        ax.plot(rcos(annulusRadiusInner,theta),rsin(annulusRadiusInner,theta),'r',linewidth=4)
        ax.plot(rcos(annulusRadiusOuter,theta),rsin(annulusRadiusOuter,theta),'r',linewidth=4)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_xlim([-.5,dimx-.5])
        ax.set_ylim([-.5,dimy-.5])
        ax.format_coord = format_coord 

        plt.show()
    return [flx, err, maxval]