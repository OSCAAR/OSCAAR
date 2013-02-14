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
## Set some photometry settings
from pyfits import open as pyfitsOpen, writeto
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

print "Loading and averaging dark frames..."

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
        p = np.arange(0,360)*(math.pi/180)
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
    flatImagesPath = glob('/Users/bmorris/Desktop/Exoplanets/20120616/flats/flatSky-???.fit')
    flatDarkImagesPath = glob('/Users/bmorris/Desktop/Exoplanets/20120616/flats/flatSky-???d.fit')
    masterFlatSavePath = '/Users/bmorris/Desktop/Exoplanets/20120616/flats/tmpMasterFlat'
    plots = True

    ## Create zero array with the dimensions of the first image for the flat field
    [dim1, dim2] = np.shape(pyfitsOpen(flatImagesPath[0])[0].data)
    flatSum = np.zeros([dim1, dim2])

    ## Create N-dimensional array for N dark frames, where the first 
    ##    two dimensions are the dimensions of the first image
    darks = np.zeros([len(flatDarkImagesPath),dim1,dim2])

    ## Take mean of all darks
    for i in range(0,len(flatDarkImagesPath)):
        darks[i,:,:] = pyfitsOpen(flatDarkImagesPath[i])[0].data
    dark = np.mean(darks,axis=0)

    ## Sum up all flat fields, subtract mean dark frame from each flat
    for flatImage in flatImagesPath:
        flatSum += pyfitsOpen(flatImage)[0].data - dark
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
    writeto(masterFlatSavePath+'.fits',masterFlat)
