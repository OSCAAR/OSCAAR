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

def quadraticFit(derivative,ext):
    '''
    Find an extremum in the data and use it and the points on either side, fit
    a quadratic function to the three points, and return the x-position of the 
    apex of the best-fit parabola. 
    
    Called by oscaar.trackSmooth()
    
    Parameters
    ----------
    derivative : numpy.ndarray
       The first derivative of the series of points, usually calculated by np.diff()
                    
    ext : string 
        Extremum to look find. May be either "max" or "min"
    
    Returns
    -------
    extremum : float
        The (non-integer) index where the extremum was found
       
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

def trackSmooth(image, est_x, est_y, smoothingConst, plottingThings, preCropped=False, zoom=20.0,plots=False):
    '''
    Method for tracking stellar centroids. 
    
    Parameters
    ---------- 
        image : numpy.ndarray
            FITS image read in by PyFITS
    
        est_x : float
            Inital estimate for the x-centroid of the star
        
        est_y : float
            Inital estimate for the y-centroid of the star
        
        smoothingConstant : float
            Controls the degree to which the raw stellar intensity profile will be smoothed by a Gaussian filter (0 = no smoothing)
        
        preCropped : bool
            If preCropped=False, image is assumed to be a raw image, if preCropped=True, image is assumed to be only the 
            portion of the image near the star
        
        zoom : int or float
            How many pixels in each direction away from the estimated centroid to consider when tracking the centroid. Be 
            sure to choose a large enough zoom value the stellar centroid in the next exposure will fit within the zoom
        
        plots : bool
            If plots=True, display stellar intensity profile in two axes and the centroid solution
                                
     Returns
     ------- 
         xCenter : float
             The best-fit x-centroid of the star
    
         yCenter : float
             The best-fit y-centroid of the star
         
         averageRadius : float
             Average radius of the SMOOTHED star in pixels
         
         errorFlag : bool
             Boolean corresponding to whether or not any error occured when running oscaar.trackSmooth(). If an 
             error occured, the flag is True; otherwise False.
                         
     Core developer: Brett Morris
     Modifications by: Luuk Visser, 2-12-2013
    '''
    '''If you have an interpolated grid as input, small inputs for smoothingConst
        it won't have any effect. Thus it has to be increased by the
        zoom factor you used to sub-pixel interpolate. 
        
        np.e seems to give nice smoothing results if frame is already cut out, you can 
        set preCropped to True, so the script won't cut a frame out again. '''
    try:
	    if plots:
	        [fig,subplotsDimensions,photSubplotsOffset] = plottingThings
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
	        #plt.clf(fig)
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
	        ax.axvline(ymin=0,ymax=1,x=axisAcenter+0.5,color='b',linewidth=2)
	        ax.axhline(xmin=0,xmax=1,y=axisBcenter+0.5,color='r',linewidth=2)
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
        
