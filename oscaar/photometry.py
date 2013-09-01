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
import os
def paddedStr(num,pad):
    '''Return the number num padded with zero-padding of length pad'''
    strlen = len(str(num))
    lenpad = pad-strlen
    return str((lenpad*'0')+str(num))
  
def phot(image, xCentroid, yCentroid, apertureRadius, plottingThings, annulusOuterRadiusFactor=2.8, annulusInnerRadiusFactor=1.40, ccdGain=1, plots=False):
    '''
    Method for aperture photometry. 
    
    Parameters
    ----------
    image : numpy.ndarray
        FITS image opened with PyFITS
    
    xCentroid : float
        Stellar centroid along the x-axis (determined by trackSmooth or equivalent)
                
    yCentroid : float
        Stellar centroid along the y-axis (determined by trackSmooth or equivalent)
                
    apertureRadius : float
        Radius in pixels from centroid to use for source aperture
                     
    annulusInnerRadiusFactor : float
        Measure the background for sky background subtraction fron an annulus from a factor of 
        `annulusInnerRadiusFactor` bigger than the `apertureRadius` to one a factor `annulusOuterRadiusFactor` bigger.
    
    annulusOuterRadiusFactor : float
        Measure the background for sky background subtraction fron an annulus a factor of 
        `annulusInnerRadiusFactor` bigger than the `apertureRadius` to one a factor `annulusOuterRadiusFactor` bigger.
                          
    ccdGain : float
        Gain of your detector, used to calculate the photon noise
    
    plots : bool
            If `plots`=True, display plots showing the aperture radius and 
            annulus radii overplotted on the image of the star
                   
    Returns
    -------
    rawFlux : float
        The background-subtracted flux measured within the aperture
    
    rawError : float
        The photon noise (limiting statistical) Poisson uncertainty on the measurement of `rawFlux`
    
    errorFlag : bool
        Boolean corresponding to whether or not any error occured when running oscaar.phot(). If an error occured, the flag is
        True; otherwise False.
               
     Core developer: Brett Morris (NASA-GSFC)
    '''
    if plots:
        [fig,subplotsDimensions,photSubplotsOffset] = plottingThings
        if photSubplotsOffset == 0: plt.clf()
    annulusRadiusInner = annulusInnerRadiusFactor*apertureRadius 
    annulusRadiusOuter = annulusOuterRadiusFactor*apertureRadius

    ## From the full image, cut out just the bit around the star that we're interested in
    imageCrop = image[xCentroid-annulusRadiusOuter+1:xCentroid+annulusRadiusOuter+2,yCentroid-annulusRadiusOuter+1:yCentroid+annulusRadiusOuter+2]
    [dimy,dimx] = imageCrop.shape
    XX, YY = np.meshgrid(np.arange(dimx),np.arange(dimy))    
    x = (XX - annulusRadiusOuter)**2
    y = (YY - annulusRadiusOuter)**2
    ## Assemble arrays marking the pixels marked as either source or background pixels
    sourceIndices = x + y <= apertureRadius**2
    skyIndices = (x + y <= annulusRadiusOuter**2)*(x + y >= annulusRadiusInner**2)
    
    rawFlux = np.sum(imageCrop[sourceIndices] - np.median(imageCrop[skyIndices]))*ccdGain
    rawError = np.sqrt(np.sum(imageCrop[sourceIndices]*ccdGain) + np.median(ccdGain*imageCrop[skyIndices])) ## Poisson-uncertainty

    if plots:
        def format_coord(x, y):
            ''' Function to also give data value on mouse over with imshow. '''
            col = int(x+0.5)
            row = int(y+0.5)
            try:
                return 'x=%i, y=%i, Flux=%1.1f' % (x, y, imageCrop[row,col])
            except:
                return 'x=%i, y=%i' % (x, y)
       
        med = np.median(imageCrop)
        dsig = np.std(imageCrop)
        
        ax = fig.add_subplot(subplotsDimensions+photSubplotsOffset+1)
        ax.imshow(imageCrop, cmap=cm.gray, interpolation="nearest",vmin = med-0.5*dsig, vmax =med+2*dsig)
       
        theta = np.arange(0,360)*(np.pi/180)
        rcos = lambda r, theta: annulusRadiusOuter + r*np.cos(theta)
        rsin = lambda r, theta: annulusRadiusOuter + r*np.sin(theta)
        ax.plot(rcos(apertureRadius,theta),rsin(apertureRadius,theta),'m',linewidth=4)
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
     
def multirad(image, xCentroid, yCentroid, apertureRadii, plottingThings, annulusOuterRadiusFactor=2.8, annulusInnerRadiusFactor=1.40, ccdGain=1, plots=False):
    '''
    Method for aperture photometry. 
    
    Parameters
    ----------
    image : numpy.ndarray
        FITS image opened with PyFITS
    
    xCentroid : float
        Stellar centroid along the x-axis (determined by trackSmooth or equivalent)
                
    yCentroid : float
        Stellar centroid along the y-axis (determined by trackSmooth or equivalent)
                
    apertureRadii : list
        List of aperture radii (floats) to feed to phot().
                     
    annulusInnerRadiusFactor : float
        Measure the background for sky background subtraction fron an annulus from a factor of 
        `annulusInnerRadiusFactor` bigger than the `apertureRadius` to one a factor `annulusOuterRadiusFactor` bigger.
    
    annulusOuterRadiusFactor : float
        Measure the background for sky background subtraction fron an annulus a factor of 
        `annulusInnerRadiusFactor` bigger than the `apertureRadius` to one a factor `annulusOuterRadiusFactor` bigger.
                          
    ccdGain : float
        Gain of your detector, used to calculate the photon noise
    
    plots : bool
            If `plots`=True, display plots showing the aperture radius and 
            annulus radii overplotted on the image of the star
                   
    Returns
    -------
    rawFlux : float
        The background-subtracted flux measured within the aperture
    
    rawError : float
        The photon noise (limiting statistical) Poisson uncertainty on the measurement of `rawFlux`
    
    errorFlag : bool
        Boolean corresponding to whether or not any error occured when running oscaar.phot(). If an error occured, the flag is
        True; otherwise False.
               
     Core developer: Brett Morris (NASA-GSFC)
    '''

    #[apertureRadiusMin, apertureRadiusMax, apertureRadiusStep] = apertureRadiusSettings
    #apertureRadii = np.arange(apertureRadiusMin, apertureRadiusMax, apertureRadiusStep)

    fluxes = []
    errors = []
    photFlags = []
    for apertureRadius in apertureRadii:
        flux, error, photFlag = phot(image, xCentroid, yCentroid, apertureRadius, plottingThings, annulusOuterRadiusFactor=annulusOuterRadiusFactor, annulusInnerRadiusFactor=annulusInnerRadiusFactor, ccdGain=ccdGain, plots=False)
        fluxes.append(flux)
        errors.append(error)
        photFlags.append(photFlag)
    annulusRadiusOuter = annulusOuterRadiusFactor*np.max(apertureRadii)
    imageCrop = image[xCentroid-annulusRadiusOuter+1:xCentroid+annulusRadiusOuter+2,yCentroid-annulusRadiusOuter+1:yCentroid+annulusRadiusOuter+2]
    [dimy,dimx] = imageCrop.shape

    if plots:
        [fig,subplotsDimensions,photSubplotsOffset] = plottingThings
        if photSubplotsOffset == 0: plt.clf()
        def format_coord(x, y):
            ''' Function to also give data value on mouse over with imshow. '''
            col = int(x+0.5)
            row = int(y+0.5)
            try:
                return 'x=%i, y=%i, Flux=%1.1f' % (x, y, imageCrop[row,col])
            except:
                return 'x=%i, y=%i' % (x, y)
       
        med = np.median(imageCrop)
        dsig = np.std(imageCrop)
        
        ax = fig.add_subplot(subplotsDimensions+photSubplotsOffset+1)
        ax.imshow(imageCrop, cmap=cm.gray, interpolation="nearest",vmin = med-0.5*dsig, vmax =med+2*dsig)
       
        theta = np.arange(0,360)*(np.pi/180)
        rcos = lambda r, theta: annulusRadiusOuter + r*np.cos(theta)
        rsin = lambda r, theta: annulusRadiusOuter + r*np.sin(theta)
        for apertureRadius in apertureRadii:
            ax.plot(rcos(apertureRadius,theta),rsin(apertureRadius,theta),linewidth=4)
        #ax.plot(rcos(annulusRadiusInner,theta),rsin(annulusRadiusInner,theta),'r',linewidth=4)
        #ax.plot(rcos(annulusRadiusOuter,theta),rsin(annulusRadiusOuter,theta),'r',linewidth=4)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title('Aperture')
        ax.set_xlim([-.5,dimx-.5])
        ax.set_ylim([-.5,dimy-.5])
        ax.format_coord = format_coord 
        plt.draw()            
    return fluxes, errors, photFlags