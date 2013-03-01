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
import IO
import other
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
        init_x_list,init_y_list = IO.parseRegionsFile(regsPath)
        zeroArray = np.zeros_like(self.imagesPaths,dtype=np.float32)
        self.times = np.zeros_like(self.imagesPaths,dtype=np.float64)
        self.keys = []
        for i in range(0,len(init_x_list)):
            self.allStarsDict[other.paddedStr(i,3)] = {'x-pos':np.copy(zeroArray), 'y-pos':np.copy(zeroArray),\
                            'rawFlux':np.copy(zeroArray), 'rawError':np.copy(zeroArray),'flag':False,\
                            'scaledFlux':np.copy(zeroArray), 'chisq':0}
            self.allStarsDict[other.paddedStr(i,3)]['x-pos'][0] = init_x_list[i]
            self.allStarsDict[other.paddedStr(i,3)]['y-pos'][0] = init_y_list[i]
            self.keys.append(other.paddedStr(i,3))    
        
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
