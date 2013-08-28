'''oscaar v2.0 
    Module for differential photometry
    Developed by Brett Morris, 2011-2013 & minor modifications by Luuk Visser 
    '''
import numpy as np
import pyfits
from matplotlib import pyplot as plt
from scipy import optimize
from glob import glob

import os
import re
import oscaar
import mathMethods
import IO
import sys
oscaarpath = os.path.dirname(os.path.abspath(oscaar.__file__))
oscaarpathplus = os.path.join(oscaarpath,'extras')

class dataBank:
    '''
    Methods for easily storing and accessing information from the entire 
    differential photometry process with OSCAAR.
    
    Core Developer: Brett Morris
    '''
    def __init__(self):
        """
        Get the inital guesses for the initial centroids of the stars from the DS9 regions file, 
        create dictionaries in which to store all of the data collected for each star, and for each 
        aperture radius. Allocate the memory for these arrays wherever possible. Parse the init.par 
        file to grab the paths and initial parameters for the run.
        
        Parameters
        ----------
            None
            
        Returns
        -------
            Instance of the ``dataBank`` object.
        
        """

        self.dict = {}
        self.parseInit()
        
        self.flatPath = self.dict["flatPath"]
        self.rawRegionsList = self.dict["regPaths"]
        self.ingress = self.dict["ingress"]
        self.egress = self.dict["egress"]
        self.apertureRadii = self.dict["apertureRadius"]
        self.trackingZoom = self.dict["trackingZoom"]
        self.ccdGain = self.dict["ccdGain"]
        self.trackPlots = self.dict["trackPlots"]
        self.photPlots = self.dict["photPlots"]
        self.smoothConst = self.dict ["smoothConst"]
        self.darksPath = self.dict["darksPath"]
        self.imagesPaths = self.dict["imagesPaths"]
        self.timeKeyword = self.dict["timeKeyword"]
        
        if self.timeKeyword == 'JD': 
            self.convertToJD = lambda x: x
        elif self.timeKeyword == 'DATE-OBS':
            self.convertToJD = mathMethods.ut2jdSplitAtT
        if not hasattr(sys, 'real_prefix'):
            assert len(self.imagesPaths) > 1, 'Must have at least two data images'
        if self.flatPath != '':
            self.masterFlat = pyfits.getdata(self.flatPath)
            self.masterFlatPath = self.flatPath
        else:
            if not hasattr(sys, 'real_prefix'):
                print 'Using an isotropic ("placebo") master-flat (array of ones)'
                dim1,dim2 = np.shape(pyfits.getdata(self.imagesPaths[0]))
                self.masterFlat = np.ones([dim1,dim2])
        self.allStarsDict = {}
        
        self.regionsFileList, self.regionsFITSrefsList = self.parseRawRegionsList(self.rawRegionsList)
        init_x_list,init_y_list = self.parseRegionsFile(self.regionsFileList[0])
        zeroArray = np.zeros_like(self.imagesPaths,dtype=np.float32)
        self.times = np.zeros_like(self.imagesPaths,dtype=np.float64)
        self.keys = []
        self.targetKey = '000'

        Nradii = len(self.apertureRadii)
        
        for i in range(0,len(init_x_list)):

            self.allStarsDict[str(i).zfill(3)] = {'x-pos':np.copy(zeroArray), 'y-pos':np.copy(zeroArray),\
                'rawFlux':[np.copy(zeroArray) for j in range(Nradii)], 'rawError':[np.copy(zeroArray) for j in range(Nradii)],'flag':False,\
                'scaledFlux':[np.copy(zeroArray) for j in range(Nradii)], 'scaledError':[np.copy(zeroArray) for j in range(Nradii)], 'chisq':np.zeros_like(self.apertureRadii)}
            self.allStarsDict[str(i).zfill(3)]['x-pos'][0] = init_x_list[i]
            self.allStarsDict[str(i).zfill(3)]['y-pos'][0] = init_y_list[i]
            self.keys.append(str(i).zfill(3))   
    def getDict(self):
        '''Return dictionary of all star data called ``allStarsDict`.'''
        return self.allStarsDict
    
    def centroidInitialGuess(self,expNumber,star):
        '''
        Gets called for each exposure. If called on the first exposure, it will return
        the intial centroid guesses input by the DS9 regions file. If any other image
        and only one regions file has been submitted, it will return the previous centroid
        as the initial guess for subsequent exposures. If multiple regions files have been
        submitted, it will return the initial guesses in those regions files when the image path
        with index ``expNumber`` is equivalent to the path stored for that regions file's 
        "Reference FITS image".
        
        Parameters
        ----------
        expNumber : int
            The index of the exposure currently being analyzed. The image gets called
            by its index from the list of image paths returned by getPaths().
        star : str
            The key from ``allStarsDict`` that corresponds to the star for which you'd
            like a centroid initial guess.
    
        Returns
        -------
        est_x : float
            Estimated centroid position of the star ``star`` along the *x*-axis of pixels for
            exposure index ``expNumber``
        
        est_y : float
            Estimated centroid position of the star ``star`` along the *y*-axis of pixels for
            exposure index ``expNumber``
        '''
        if expNumber == 0:
            est_x = self.allStarsDict[star]['x-pos'][0]  ## Use DS9 regions file's estimate for the 
            est_y = self.allStarsDict[star]['y-pos'][0]  ##    stellar centroid for the first exposure
        elif self.imagesPaths[expNumber] in self.regionsFITSrefsList:
            refIndex = self.regionsFITSrefsList.index(self.imagesPaths[expNumber])
            init_x_list, init_y_list = self.parseRegionsFile(self.regionsFileList[refIndex])
            est_x = init_x_list[int(star)]
            est_y = init_y_list[int(star)]
        else: 
            est_x = self.allStarsDict[star]['x-pos'][expNumber-1]    ## All other exposures use the
            est_y = self.allStarsDict[star]['y-pos'][expNumber-1]    ##    previous exposure centroid as estimate
        return est_x, est_y
    
    def storeCentroid(self,star,exposureNumber,xCentroid,yCentroid):
        '''Store the centroid data collected by oscaar.trackSmooth()
            Parameters
            ----------
            star : str
                Key for the star for which the centroid has been measured
            
            exposureNumber : int
                Index of exposure being considered
            
            xCentroid : float
                *x*-centroid of the star
            
            yCentroid : float
                *y*-centroid of the star
            '''
        self.allStarsDict[star]['x-pos'][exposureNumber] = xCentroid
        self.allStarsDict[star]['y-pos'][exposureNumber] = yCentroid   
    
    def storeFlux(self,star,exposureNumber,rawFlux,rawError):
        '''Store the flux and error data collected by oscaar.phot()
            Parameters
            ----------
            star : str
                Key for the star from the ``allStarsDict`` dictionary
            
            exposureNumber : int
                Index of exposure being considered
            
            rawFlux : float
                flux measured, to be stored
            
            rawError : 
                photon noise measured, to be stored
            '''
        self.allStarsDict[star]['rawFlux'][exposureNumber] = rawFlux
        self.allStarsDict[star]['rawError'][exposureNumber] = rawError
    def storeFluxes(self,star,exposureNumber,rawFluxes,rawErrors):
        '''
        Store the flux and error data collected by oscaar.phot()
        Parameters
        ----------
        star : str
            Key for the star from the ``allStarsDict`` dictionary
        
        exposureNumber : int
            Index of exposure being considered
        
        rawFluxes : list of floats
            flux measured, to be stored
        
        rawErrors : list of floats
            photon noise measured, to be stored
        '''
        for apertureRadiusIndex in range(len(self.apertureRadii)):
            self.allStarsDict[star]['rawFlux'][apertureRadiusIndex][exposureNumber] = rawFluxes[apertureRadiusIndex]
            self.allStarsDict[star]['rawError'][apertureRadiusIndex][exposureNumber] = rawErrors[apertureRadiusIndex]
    
    def getPaths(self):
        '''Return the paths to the raw images to be used'''
        return self.imagesPaths
    
    def getFluxes(self,star):
        '''
        Return list of fluxes for the star with key ``star``
        
        Parameters
        ----------
        star : str
            Key for the star from the ``allStarsDict`` dictionary
        
        Returns
        _______
        fluxes : list
            List of fluxes for each aperture radius
        '''
        return self.allStarsDict[star]['rawFlux']
    
    def getErrors(self,star):
        '''Return the errors for one star, where the star parameter is the key for the
            star of interest.'''
        return self.allStarsDict[star]['rawError']
    
    def storeTime(self,expNumber):
        '''
        Store the time in JD from the FITS header.
        INPUTS: exposureNumber - Index of exposure being considered
        
        time - Time as read-in from the FITS header
        '''
        #try:
        timeStamp = pyfits.getheader(self.getPaths()[expNumber])[self.timeKeyword]
        #except KeyError: 
        #    print 'Input Error: The Exposure Time Keyword indicated in observatory.par is not a valid key: ',self.timeKeyword
        #finally: 
        self.times[expNumber] = self.convertToJD(timeStamp)
    
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
        comparison star to the flux of the target star. Do the same transformation on the errors.
        '''
        for star in self.allStarsDict:
            if star != self.targetKey:
                self.allStarsDict[star]['scaledFlux'], m = mathMethods.regressionScale(self.getFluxes(star),self.getFluxes(self.targetKey),self.getTimes(),self.ingress,self.egress,returncoeffs=True)
                print m
                self.allStarsDict[star]['scaledError'] = np.abs(m)*self.getErrors(star)
            if star == self.targetKey:    ## (Keep the target star the same)
                self.allStarsDict[star]['scaledFlux'] = self.allStarsDict[star]['rawFlux']
                self.allStarsDict[star]['scaledError'] = self.allStarsDict[star]['rawError']

    
    def getFluxes_multirad(self,star,apertureRadiusIndex):
        '''Return the fluxes for one star, where the star parameter is the key for the
            star of interest.'''
        return self.allStarsDict[star]['rawFlux'][apertureRadiusIndex]
    
    def getErrors_multirad(self,star,apertureRadiusIndex):
        '''Return the errors for one star, where the star parameter is the key for the
            star of interest.'''
        return self.allStarsDict[star]['rawError'][apertureRadiusIndex]

    def scaleFluxes_multirad(self):
        '''
            When all fluxes have been collected, run this to re-scale the fluxes of each
            comparison star to the flux of the target star. Do the same transformation on the errors.
            '''
        for star in self.allStarsDict:
            for apertureRadiusIndex in range(len(self.apertureRadii)):    
                if star != self.targetKey:
                    print self.getFluxes_multirad(star,apertureRadiusIndex)[0]
                    self.allStarsDict[star]['scaledFlux'][apertureRadiusIndex], m = mathMethods.regressionScale(self.getFluxes_multirad(star,apertureRadiusIndex),self.getFluxes_multirad(self.targetKey,apertureRadiusIndex),self.getTimes(),self.ingress,self.egress,returncoeffs=True)
                    #print m
                    self.allStarsDict[star]['scaledError'][apertureRadiusIndex] = np.abs(m)*self.getErrors_multirad(star,apertureRadiusIndex)
                if star == self.targetKey:    ## (Keep the target star the same)
                    self.allStarsDict[star]['scaledFlux'][apertureRadiusIndex] = self.allStarsDict[star]['rawFlux'][apertureRadiusIndex]
                    self.allStarsDict[star]['scaledError'][apertureRadiusIndex] = self.allStarsDict[star]['rawError'][apertureRadiusIndex]
    
    
    def getScaledFluxes(self,star):
        '''Return the scaled fluxes for one star, where the star parameter is the 
            key for the star of interest.'''
        return np.array(self.allStarsDict[star]['scaledFlux'])
    
    def getScaledErrors(self,star):
        '''Return the scaled fluxes for one star, where the star parameter is the 
            key for the star of interest.'''
        return np.array(self.allStarsDict[star]['scaledError'])

    def getScaledFluxes_multirad(self,star,apertureRadiusIndex):
        '''Return the scaled fluxes for one star, where the star parameter is the 
            key for the star of interest.'''
        return np.array(self.allStarsDict[star]['scaledFlux'][apertureRadiusIndex])
    
    def getScaledErrors_multirad(self,star,apertureRadiusIndex):
        '''Return the scaled fluxes for one star, where the star parameter is the 
            key for the star of interest.'''
        return np.array(self.allStarsDict[star]['scaledError'][apertureRadiusIndex])
    
    def getScaledFluxes(self,star):
        '''Return the scaled fluxes for one star, where the star parameter is the 
            key for the star of interest.'''
        return np.array(self.allStarsDict[star]['scaledFlux'])
    
    def getScaledErrors(self,star):
        '''Return the scaled fluxes for one star, where the star parameter is the 
            key for the star of interest.'''
        return np.array(self.allStarsDict[star]['scaledError'])
    
    def calcChiSq(self):
        for star in self.allStarsDict:
            self.allStarsDict[star]['chisq'] = mathMethods.chiSquared(self.getFluxes(self.targetKey),self.getFluxes(star))
        chisq = []
        for star in self.allStarsDict:
            chisq.append(self.allStarsDict[star]['chisq'])
        self.chisq = np.array(chisq)
        self.meanChisq = np.mean(chisq)
        self.stdChisq = np.std(chisq)

    def calcChiSq_multirad(self,apertureRadiusIndex):
        for star in self.allStarsDict:
            print self.getFluxes_multirad(self.targetKey,apertureRadiusIndex),self.getFluxes_multirad(star,apertureRadiusIndex)
            self.allStarsDict[star]['chisq'][apertureRadiusIndex] = mathMethods.chiSquared(self.getFluxes_multirad(self.targetKey,apertureRadiusIndex),self.getFluxes_multirad(star,apertureRadiusIndex))
        chisq = []
        for star in self.allStarsDict:
            chisq.append(self.allStarsDict[star]['chisq'][apertureRadiusIndex])
        self.chisq = np.array(chisq)
        self.meanChisq = np.mean(chisq)
        self.stdChisq = np.std(chisq)

    def calcMeanComparison_multirad(self,ccdGain=1):
        '''
            Take the regression-weighted mean of some of the comparison stars
            to produce one comparison star flux to compare to the target to
            produce a light curve.
            
            The comparison stars used are those whose chi-squareds calculated by
            self.calcChiSq() are less than 2*sigma away from the other chi-squareds.
            This condition removes outliers.
            '''
        self.meanComparisonStars = []
        self.meanComparisonStarErrors = []
        self.comparisonStarWeights = []
        
        for apertureRadiusIndex in range(len(self.apertureRadii)):
            ## Check whether chi-squared has been calculated already. If not, compute it.
            chisq = []
            for star in self.allStarsDict: chisq.append(self.allStarsDict[star]['chisq'])
            chisq = np.array(chisq)
            #if all(chisq == 0): self.calcChiSq_multirad(apertureRadiusIndex)
            if (chisq==0).all(): self.calcChiSq_multirad(apertureRadiusIndex)
            ## Begin regression technique
            numCompStars =  len(self.allStarsDict) - 1
            targetFullLength = len(self.getScaledFluxes_multirad(self.targetKey,apertureRadiusIndex))    
            print "Aperture rad:", apertureRadiusIndex
            print "Target raw flux:",self.getFluxes_multirad(self.targetKey,apertureRadiusIndex)
            print "Target scaled flux:",self.getScaledFluxes_multirad(self.targetKey,apertureRadiusIndex)
            target = self.getFluxes_multirad(self.targetKey,apertureRadiusIndex)[self.outOfTransit()]
            compStars = np.zeros([targetFullLength,numCompStars])
            compStarsOOT = np.zeros([len(target),numCompStars])
            compErrors = np.copy(compStars)
            columnCounter = 0
            acceptedCompStarKeys = []
            compStarKeys = []
            for star in self.allStarsDict:
                if star != self.targetKey and (np.abs(self.meanChisq - self.allStarsDict[star]['chisq']) < 2*self.stdChisq).any():
                    compStars[:,columnCounter] = self.getScaledFluxes_multirad(star,apertureRadiusIndex).astype(np.float64)
                    compStarsOOT[:,columnCounter] = self.getScaledFluxes_multirad(star,apertureRadiusIndex)[self.outOfTransit()].astype(np.float64)
                    compErrors[:,columnCounter] = self.getScaledErrors_multirad(star,apertureRadiusIndex).astype(np.float64)
                    compStarKeys.append(int(star))
                    columnCounter += 1
                elif star != self.targetKey and (np.abs(self.meanChisq - self.allStarsDict[star]['chisq']) > 2*self.stdChisq):
                    print 'Star '+str(star)+' excluded from regression'
                    compStarKeys.append(int(star))
                    columnCounter += 1
            initP = np.zeros([numCompStars])+ 1./numCompStars
            def errfunc(p,target): 
                if all(p >=0.0): return np.dot(p,compStarsOOT.T) - target ## Find only positive coefficients
            #return np.dot(p,compStarsOOT.T) - target
            
            bestFitP = optimize.leastsq(errfunc,initP[:],args=(target.astype(np.float64)),maxfev=10000000,epsfcn=np.finfo(np.float32).eps)[0]
            print '\nBest fit regression coefficients:',bestFitP
            print 'Default weight:',1./numCompStars
            
            self.comparisonStarWeights_i = np.vstack([compStarKeys,bestFitP])
            self.meanComparisonStar = np.dot(bestFitP,compStars.T)
            self.meanComparisonStarError = np.sqrt(np.dot(bestFitP**2,compErrors.T**2))
            self.meanComparisonStars.append(self.meanComparisonStar)
            self.meanComparisonStarErrors.append(self.meanComparisonStarError)
            self.comparisonStarWeights.append(self.comparisonStarWeights_i)      
        return self.meanComparisonStars, self.meanComparisonStarErrors

   
    def getAllChiSq(self):
        '''Return chi-squared's for all stars'''
        return self.chisq
    
    def outOfTransit(self):
        '''Boolean array where True are the times in data.getTimes() that are
            before ingress or after egress.'''
        return (self.getTimes() < self.ingress) + (self.getTimes() > self.egress)
    
    def calcMeanComparison(self,ccdGain=1):
        '''
            Take the regression-weighted mean of some of the comparison stars
            to produce one comparison star flux to compare to the target to
            produce a light curve.
            
            The comparison stars used are those whose chi-squareds calculated by
            self.calcChiSq() are less than 2*sigma away from the other chi-squareds.
            This condition removes outliers.
            '''
        
        ## Check whether chi-squared has been calculated already. If not, compute it.
        chisq = []
        for star in self.allStarsDict: chisq.append(self.allStarsDict[star]['chisq'])
        chisq = np.array(chisq)
        if all(chisq == 0): self.calcChiSq()
        
        ## Begin regression technique
        numCompStars =  len(self.allStarsDict) - 1
        targetFullLength = len(self.getScaledFluxes(self.targetKey))
        target = self.getFluxes(self.targetKey)[self.outOfTransit()]
        compStars = np.zeros([targetFullLength,numCompStars])
        compStarsOOT = np.zeros([len(target),numCompStars])
        compErrors = np.copy(compStars)
        columnCounter = 0
        acceptedCompStarKeys = []
        compStarKeys = []
        for star in self.allStarsDict:
            if star != self.targetKey and (np.abs(self.meanChisq - self.allStarsDict[star]['chisq']) < 2*self.stdChisq):
                compStars[:,columnCounter] = self.getScaledFluxes(star).astype(np.float64)
                compStarsOOT[:,columnCounter] = self.getScaledFluxes(star)[self.outOfTransit()].astype(np.float64)
                compErrors[:,columnCounter] = self.getScaledErrors(star).astype(np.float64)
                compStarKeys.append(int(star))
                columnCounter += 1
            elif star != self.targetKey and (np.abs(self.meanChisq - self.allStarsDict[star]['chisq']) > 2*self.stdChisq):
                print 'Star '+str(star)+' excluded from regression'
                compStarKeys.append(int(star))
                columnCounter += 1
        initP = np.zeros([numCompStars])+ 1./numCompStars
        def errfunc(p,target): 
            if all(p >=0.0): return np.dot(p,compStarsOOT.T) - target ## Find only positive coefficients
        #return np.dot(p,compStarsOOT.T) - target
        
        bestFitP = optimize.leastsq(errfunc,initP[:],args=(target.astype(np.float64)),maxfev=10000000,epsfcn=np.finfo(np.float32).eps)[0]
        print '\nBest fit regression coefficients:',bestFitP
        print 'Default weight:',1./numCompStars
        
        self.comparisonStarWeights = np.vstack([compStarKeys,bestFitP])
        self.meanComparisonStar = np.dot(bestFitP,compStars.T)
        self.meanComparisonStarError = np.sqrt(np.dot(bestFitP**2,compErrors.T**2))
        return self.meanComparisonStar, self.meanComparisonStarError  

    def calcMeanComparison_multirad(self,ccdGain=1):
        '''
            Take the regression-weighted mean of some of the comparison stars
            to produce one comparison star flux to compare to the target to
            produce a light curve.
            
            The comparison stars used are those whose chi-squareds calculated by
            self.calcChiSq() are less than 2*sigma away from the other chi-squareds.
            This condition removes outliers.
            '''
        self.meanComparisonStars = []
        self.meanComparisonStarErrors = []
        self.comparisonStarWeights = []
        
        for apertureRadiusIndex in range(len(self.apertureRadii)):
            ## Check whether chi-squared has been calculated already. If not, compute it.
            chisq = []
            for star in self.allStarsDict: chisq.append(self.allStarsDict[star]['chisq'])
            chisq = np.array(chisq)
            #if all(chisq == 0): self.calcChiSq_multirad(apertureRadiusIndex)
            if (chisq==0).all(): self.calcChiSq_multirad(apertureRadiusIndex)
            ## Begin regression technique
            numCompStars =  len(self.allStarsDict) - 1
            targetFullLength = len(self.getScaledFluxes_multirad(self.targetKey,apertureRadiusIndex))    
            print "Aperture rad:", apertureRadiusIndex
            print "Target raw flux:",self.getFluxes_multirad(self.targetKey,apertureRadiusIndex)
            print "Target scaled flux:",self.getScaledFluxes_multirad(self.targetKey,apertureRadiusIndex)
            target = self.getFluxes_multirad(self.targetKey,apertureRadiusIndex)[self.outOfTransit()]
            compStars = np.zeros([targetFullLength,numCompStars])
            compStarsOOT = np.zeros([len(target),numCompStars])
            compErrors = np.copy(compStars)
            columnCounter = 0
            acceptedCompStarKeys = []
            compStarKeys = []
            for star in self.allStarsDict:
                if star != self.targetKey and (np.abs(self.meanChisq - self.allStarsDict[star]['chisq']) < 2*self.stdChisq).any():
                    compStars[:,columnCounter] = self.getScaledFluxes_multirad(star,apertureRadiusIndex).astype(np.float64)
                    compStarsOOT[:,columnCounter] = self.getScaledFluxes_multirad(star,apertureRadiusIndex)[self.outOfTransit()].astype(np.float64)
                    compErrors[:,columnCounter] = self.getScaledErrors_multirad(star,apertureRadiusIndex).astype(np.float64)
                    compStarKeys.append(int(star))
                    columnCounter += 1
                elif star != self.targetKey and (np.abs(self.meanChisq - self.allStarsDict[star]['chisq']) > 2*self.stdChisq):
                    print 'Star '+str(star)+' excluded from regression'
                    compStarKeys.append(int(star))
                    columnCounter += 1
            initP = np.zeros([numCompStars])+ 1./numCompStars
            def errfunc(p,target): 
                if all(p >=0.0): return np.dot(p,compStarsOOT.T) - target ## Find only positive coefficients
            #return np.dot(p,compStarsOOT.T) - target
            
            bestFitP = optimize.leastsq(errfunc,initP[:],args=(target.astype(np.float64)),maxfev=10000000,epsfcn=np.finfo(np.float32).eps)[0]
            print '\nBest fit regression coefficients:',bestFitP
            print 'Default weight:',1./numCompStars
            
            self.comparisonStarWeights_i = np.vstack([compStarKeys,bestFitP])
            self.meanComparisonStar = np.dot(bestFitP,compStars.T)
            self.meanComparisonStarError = np.sqrt(np.dot(bestFitP**2,compErrors.T**2))
            self.meanComparisonStars.append(self.meanComparisonStar)
            self.meanComparisonStarErrors.append(self.meanComparisonStarError)
            self.comparisonStarWeights.append(self.comparisonStarWeights_i)      
        return self.meanComparisonStars, self.meanComparisonStarErrors

    def computeLightCurve(self,meanComparisonStar,meanComparisonStarError):
        '''
            Divide the target star flux by the mean comparison star to yield a light curve,
            save the light curve into the dataBank object.
            
            INPUTS: meanComparisonStar - The fluxes of the (one) mean comparison star
            
            RETURNS: self.lightCurve - The target star divided by the mean comparison 
            star, i.e., the light curve.
            '''
        self.lightCurve = self.getFluxes(self.targetKey)/meanComparisonStar
        self.lightCurveError = np.sqrt(self.lightCurve**2 * ( (self.getErrors(self.targetKey)/self.getFluxes(self.targetKey))**2 + (meanComparisonStarError/meanComparisonStar)**2 ))
        return self.lightCurve, self.lightCurveError
    
    def computeLightCurve_multirad(self,meanComparisonStars,meanComparisonStarErrors):
        '''
            Divide the target star flux by the mean comparison star to yield a light curve,
            save the light curve into the dataBank object.
            
            INPUTS: meanComparisonStar - The fluxes of the (one) mean comparison star
            
            RETURNS: self.lightCurve - The target star divided by the mean comparison 
            star, i.e., the light curve.
            '''
        self.lightCurves = []
        self.lightCurveErrors = []
        for apertureRadiusIndex in range(len(self.apertureRadii)):
            lightCurve = self.getFluxes_multirad(self.targetKey,apertureRadiusIndex)/meanComparisonStars[apertureRadiusIndex]
            self.lightCurves.append(lightCurve)
            self.lightCurveErrors.append(np.sqrt(lightCurve**2 * ( (self.getErrors_multirad(self.targetKey,apertureRadiusIndex)/self.getFluxes_multirad(self.targetKey,apertureRadiusIndex))**2 +\
                                         (meanComparisonStarErrors[apertureRadiusIndex]/meanComparisonStars[apertureRadiusIndex])**2 )))
        return self.lightCurves, self.lightCurveErrors

    def getPhotonNoise(self):
        '''
            Calculate photon noise using the lightCurve and the meanComparisonStar
            
            RETURNS: self.photonNoise - The estimated photon noise limit
            '''
        self.photonNoise = self.lightCurve*self.meanComparisonStarError
        return self.photonNoise
    
    def parseInit(self):
        '''
            Parses init.par
            '''        
        init = open(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'init.par'), 'r').read().splitlines()
        for line in init:
            if len(line.split()) > 1:
                inline = line.split(':', 1)
                name = inline[0].strip()
                value = str(inline[1].strip())
                list = [("Path to Master-Flat Frame", "flatPath"),
                        ("Path to regions file", "regPaths"),
                        ("Ingress", "ingress"), ("Egress", "egress"),
                        ("Radius", "apertureRadius"), ("Tracking Zoom", "trackingZoom"),
                        ("CCD Gain", "ccdGain"), ("Plot Tracking", "trackPlots"),
                        ("Plot Photometry", "photPlots"), ("Smoothing Constant", "smoothConst"),
                        ("Output Path","outputPath"), ("Path to Dark Frames", "darksPath"),
                        ("Path to data images", "imagesPaths"), ("Exposure Time Keyword", "timeKeyword")]
                
                for string,save in list:
                    if string == name:
                        #if name == "Smoothing Constant" or name == "Radius" or name == "Tracking Zoom" or name == "CCD Gain":
                        if name == "Smoothing Constant" or name == "Tracking Zoom" or name == "CCD Gain":
                            self.dict[save] = float(value)
                        elif name == "Ingress" or name == "Egress":
                            self.dict[save] = oscaar.mathMethods.ut2jd(value)
                        elif name == "Plot Photometry" or name == "Plot Tracking":
                            if value == "on":
                                self.dict[save] = True
                            else:
                                self.dict[save] = False
                        elif name == "Path to Dark Frames" or name == "Path to data images":
                            value = inline[1].strip()
                            if len(glob(value)) > 0:
                                self.dict[save] = np.sort(glob(value))
                            else:
                                tempArr = []
                                for path in str(inline[1]).split(','):
                                    path = path.strip()
                                    path = os.path.join(oscaarpathplus,os.path.abspath(path))
                                    tempArr.append(path)
                                self.dict[save] = np.sort(tempArr)
                                
                        elif name == "Radius":
                            if len(value.split(',')) == 3:
                                ## If multiple aperture radii are requested by dictating the range, enumerate the range:
                                apertureRadiusMin, apertureRadiusMax, apertureRadiusStep = map(float,value.split(','))
                                
                                if (apertureRadiusMax-apertureRadiusMin) % apertureRadiusStep == 0:
                                    apertureRadii = np.arange(apertureRadiusMin, apertureRadiusMax+apertureRadiusStep, apertureRadiusStep)
                                else: 
                                    apertureRadii = np.arange(apertureRadiusMin, apertureRadiusMax, apertureRadiusStep)

                                self.dict[save] = apertureRadii
                            elif len(value.split(',')) == 1:
                                ## If only one aperture radius is requested, make a list with only that one element
                                self.dict[save] = [float(value)]
                            else:
                                self.dict[save] = [float(i) for i in value.split(',')]                                    

                        elif name == "Output Path":
                            self.outputPath = os.path.join(oscaarpathplus,os.path.abspath(value))
                        else:
                            self.dict[save] = value

    def parseRegionsFile(self,regPath):
        regionsData = open(regPath,'r').read().splitlines()
        init_x_list = []
        init_y_list = []
        for i in range(0,len(regionsData)):
            if regionsData[i][0:6] == 'circle':
                y,x = re.split("\,",re.split("\(",regionsData[i])[1])[0:2]
                init_y_list.append(float(y))
                init_x_list.append(float(x))
        return init_x_list,init_y_list

    def parseRawRegionsList(self,rawRegionsList):
        '''Split up the "rawRegionsList", which should be in the format: 
        
           <first regions file>,<reference FITS file for the first regs file>;<second> regions file>,
           <reference FITS file for the first regs file>;....
           
           into a list of regions files and a list of FITS reference files.
        '''
        regionsFiles = []
        refFITSFiles = []
        
        for pair in rawRegionsList.split(';'):
            if len(pair.split(",")) == 2:
                regionsFile, refFITSFile = pair.split(',')
                regionsFiles.append(regionsFile)
                refFITSFiles.append(refFITSFile)

        return regionsFiles, refFITSFiles
        
    
    def plot(self,pointsPerBin=10):
        plt.close()
        times = self.getTimes()
        meanComparisonStar, meanComparisonStarError = self.calcMeanComparison(ccdGain = self.ccdGain)
        lightCurve, lightCurveErr = self.computeLightCurve(meanComparisonStar, meanComparisonStarError)
        binnedTime, binnedFlux, binnedStd = mathMethods.medianBin(times,lightCurve,pointsPerBin)
        
        fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
        fig.canvas.set_window_title('OSCAAR')
        axis = fig.add_subplot(111)
        def format_coord(x, y):
            '''Function to give data value on mouse over plot.'''
            return 'JD=%1.5f, Flux=%1.4f' % (x, y)
        axis.format_coord = format_coord 
        axis.errorbar(times,lightCurve,yerr=lightCurveErr,fmt='k.',ecolor='gray')
        axis.errorbar(binnedTime, binnedFlux, yerr=binnedStd, fmt='rs-', linewidth=2)
        axis.axvline(ymin=0,ymax=1,x=self.ingress,color='k',ls=':')
        axis.axvline(ymin=0,ymax=1,x=self.egress,color='k',ls=':')
        axis.set_title('Light Curve')
        axis.set_xlabel('Time (JD)')
        axis.set_ylabel('Relative Flux')
        plt.ioff()
        plt.show()
    
    def plotLightCurve(self,pointsPerBin=10,apertureRadiusIndex=0):
        binnedTime, binnedFlux, binnedStd = mathMethods.medianBin(self.times,self.lightCurves[apertureRadiusIndex],pointsPerBin)
        
        fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
        fig.canvas.set_window_title('OSCAAR')
        axis = fig.add_subplot(111)
        def format_coord(x, y):
            '''Function to give data value on mouse over plot.'''
            return 'JD=%1.5f, Flux=%1.4f' % (x, y)
        axis.format_coord = format_coord 
        axis.errorbar(self.times,self.lightCurves[apertureRadiusIndex],yerr=self.lightCurveErrors[apertureRadiusIndex],fmt='k.',ecolor='gray')
        axis.errorbar(binnedTime, binnedFlux, yerr=binnedStd, fmt='rs-', linewidth=2)
        axis.axvline(ymin=0,ymax=1,x=self.ingress,color='k',ls=':')
        axis.axvline(ymin=0,ymax=1,x=self.egress,color='k',ls=':')
        axis.set_title(('Light curve for aperture radius %s' % self.apertureRadii[apertureRadiusIndex]))
        axis.set_xlabel('Time (JD)')
        axis.set_ylabel('Relative Flux')
        plt.ioff()
        plt.show()
    
    def plotRawFluxes(self,apertureRadiusIndex=0,pointsPerBin=10):
        plt.ion()
        fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
        fig.canvas.set_window_title('OSCAAR')
        axis = fig.add_subplot(111)
        def format_coord(x, y):
            '''Function to give data value on mouse over plot.'''
            return 'JD=%1.5f, Flux=%1.4f' % (x, y)
        axis.format_coord = format_coord 
        for star in self.allStarsDict:
            axis.errorbar(self.times,self.allStarsDict[star]['rawFlux'][apertureRadiusIndex],yerr=self.allStarsDict[star]['rawError'][apertureRadiusIndex],fmt='o')
        
        axis.axvline(ymin=0,ymax=1,x=self.ingress,color='k',ls=':')
        axis.axvline(ymin=0,ymax=1,x=self.egress,color='k',ls=':')
        axis.set_title(('Raw fluxes for aperture radius %s' % self.apertureRadii[apertureRadiusIndex]))
        axis.set_xlabel('Time (JD)')
        axis.set_ylabel('Counts')
        plt.ioff()
        plt.show()
    
    
    def plotScaledFluxes(self,apertureRadiusIndex=0,pointsPerBin=10):
        plt.ion()
        fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
        fig.canvas.set_window_title('OSCAAR')
        axis = fig.add_subplot(111)
        def format_coord(x, y):
            '''Function to give data value on mouse over plot.'''
            return 'JD=%1.5f, Flux=%1.4f' % (x, y)
        axis.format_coord = format_coord 
        for star in self.allStarsDict:
            axis.errorbar(self.times,self.allStarsDict[star]['scaledFlux'][apertureRadiusIndex],yerr=self.allStarsDict[star]['scaledError'][apertureRadiusIndex],fmt='o')
        
        axis.axvline(ymin=0,ymax=1,x=self.ingress,color='k',ls=':')
        axis.axvline(ymin=0,ymax=1,x=self.egress,color='k',ls=':')
        axis.set_title(('Scaled fluxes for aperture radius: %s' % self.apertureRadii[apertureRadiusIndex]))
        axis.set_xlabel('Time (JD)')
        axis.set_ylabel('Counts')
        plt.ioff()
        plt.show()

    def plotCentroidsTrace(self,pointsPerBin=10):
        
        fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
        fig.canvas.set_window_title('OSCAAR')
        axis = fig.add_subplot(111)
        def format_coord(x, y):
            '''Function to give data value on mouse over plot.'''
            return 'JD=%1.5f, Flux=%1.4f' % (x, y)
        axis.format_coord = format_coord 
        for star in self.allStarsDict:
            axis.plot(self.allStarsDict[star]['y-pos'],self.allStarsDict[star]['x-pos'])
        
        axis.set_title('Tracing Stellar Centroids')
        axis.set_xlabel('X')
        axis.set_ylabel('Y')
        plt.ioff()
        plt.show()
    
    def plotComparisonWeightings(self, apertureRadiusIndex=0):
        plt.ion()
        weights = self.comparisonStarWeights[apertureRadiusIndex]
        weights = np.sort(weights,axis=1)
        width = 0.5
        indices = weights[0,:]
        coefficients = weights[1,:]
        ind = np.arange(len(indices))
        fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
        fig.canvas.set_window_title('OSCAAR')
        ax = fig.add_subplot(111)
        ax.set_xlim([0,len(indices)+1])
        ax.set_xticks(indices+width/2)
        ax.set_xticklabels(["Star "+str(i) for i in range(len(indices))])
        ax.set_xlabel('Comparison Star')
        ax.set_ylabel('Normalized Weighting')
        ax.set_title('Comparison Star Weights into the Composite Comparison Star for aperture radius %s' \
                     % self.apertureRadii[apertureRadiusIndex])
        ax.axhline(xmin=0,xmax=1,y=1.0/len(indices),linestyle=':',color='k')
        ax.bar(indices,coefficients,width,color='w')
        plt.ioff()
        plt.show()

    def updateMCMC(self,bestp,allparams,acceptanceRate,dataBankPath,uncertainties):
        self.MCMC_bestp = bestp
        self.MCMC_allparams = allparams
        self.MCMC_acceptanceRate = acceptanceRate
        self.dataBankPath = dataBankPath
        self.MCMC_uncertainties = uncertainties

    def uncertaintyString(self):
        savestring = 'MCMC Best Fit Parameters And One-Sigma Uncertainties\n----------------------------------------------------\n\n'
        labels = ['Rp/Rs','a/Rs','Inclination','Mid-transit time']
        for i in range(len(labels)):
            savestring += '%s:\t%s\t +%s / -%s \n' % (labels[i],self.MCMC_bestp[i],self.MCMC_uncertainties[i][0],self.MCMC_uncertainties[i][1])
        return savestring

    def plotMCMC(self):
        bestp = self.MCMC_bestp
        allparams = self.MCMC_allparams
        acceptanceRate = self.MCMC_acceptanceRate
        x = self.times
        y = self.lightCurve
        sigma_y = self.lightCurveError
    
        ##############################
        # Prepare figures
        fig = plt.figure()
        ax1 = fig.add_subplot(331)
        ax2 = fig.add_subplot(332)
        ax3 = fig.add_subplot(333)
        ax4 = fig.add_subplot(334)
        ax5 = fig.add_subplot(335)
        ax6 = fig.add_subplot(336)
        ax7 = fig.add_subplot(337)
        ax8 = fig.add_subplot(338)
        ax9 = fig.add_subplot(339)
        yfit = occult4params(x,bestp)
        ax1.errorbar(x,y,yerr=sigma_y,fmt='o-')
        ax1.plot(x,yfit,'r')
        ax1.set_title("Fit with MCMC")

        ##############################
        # Plot traces and histograms of mcmc params
        p = allparams[0,:]
        ap = allparams[1,:]
        i = allparams[2,:]
        t0 = allparams[3,:]
        abscissa = np.arange(len(allparams[0,:]))   ## Make x-axis for trace plots
        burnFraction = 0.20     ## "burn" or ignore the first 20% of the chains

        ax2.plot(abscissa,p,'k.')
        ax2.set_title('p trace')
        ax2.axvline(ymin=0,ymax=1,x=burnFraction*len(abscissa),linestyle=':')

        ax3.plot(abscissa,ap,'k.')
        ax3.set_title('ap trace')
        ax3.axvline(ymin=0,ymax=1,x=burnFraction*len(abscissa),linestyle=':')

        ax4.plot(abscissa,i,'k.')
        ax4.set_title('i trace')
        ax4.axvline(ymin=0,ymax=1,x=burnFraction*len(abscissa),linestyle=':')

        ax5.plot(abscissa,t0,'k.')
        ax5.set_title('t0 trace')
        ax5.axvline(ymin=0,ymax=1,x=burnFraction*len(abscissa),linestyle=':')

        def histplot(parameter,axis,title,bestFitParameter):
            postburn = parameter[burnFraction*len(parameter):len(parameter)]    ## Burn beginning of chain
            Nbins = 15              ## Plot histograms with 15 bins
            n, bins, patches = axis.hist(postburn, Nbins, normed=0, facecolor='white')  ## Generate histogram
            plus,minus = oscaar.mcmc.get_uncertainties(postburn,bestFitParameter)   ## Calculate uncertainties on best fit parameter
            axis.axvline(ymin=0,ymax=1,x=bestFitParameter+plus,ls=':',color='r')    ## Plot vertical lines representing uncertainties
            axis.axvline(ymin=0,ymax=1,x=bestFitParameter-minus,ls=':',color='r')        
            axis.set_title(title)
        ## Plot the histograms
        histplot(p,ax6,'p',bestp[0])
        histplot(ap,ax7,'ap',bestp[1])
        histplot(i,ax8,'i',bestp[2])
        histplot(t0,ax9,'t0',bestp[3])

        plt.savefig("mcmc_results.png",bbox_inches='tight')     ## Save plot
        plt.show()

    def plotLightCurve_multirad(self,pointsPerBin=10):
        for apertureRadiusIndex in range(len(self.apertureRadii)):
            
            meanTimeInt = int(np.rint(np.mean(self.times)))
            offsetTimes = self.times - meanTimeInt
            binnedTime, binnedFlux, binnedStd = mathMethods.medianBin(offsetTimes,self.lightCurves[apertureRadiusIndex],pointsPerBin)
            fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
            fig.canvas.set_window_title('OSCAAR')
            axis = fig.add_subplot(111)
            def format_coord(x, y):
                '''Function to give data value on mouse over plot.'''
                return 'JD=%1.5f, Flux=%1.4f' % (meanTimeInt+x, y)
            axis.format_coord = format_coord 
            axis.errorbar(offsetTimes,self.lightCurves[apertureRadiusIndex],yerr=self.lightCurveErrors[apertureRadiusIndex],fmt='k.',ecolor='gray')
            axis.errorbar(binnedTime, binnedFlux, yerr=binnedStd, fmt='rs-', linewidth=2)
            axis.axvline(ymin=0,ymax=1,x=self.ingress-meanTimeInt,color='k',ls=':')
            axis.axvline(ymin=0,ymax=1,x=self.egress-meanTimeInt,color='k',ls=':')
            axis.set_title('Light curve for aperture radius: %s' % self.apertureRadii[apertureRadiusIndex])
            axis.set_xlabel(('Time - %i (JD)' % meanTimeInt))
            axis.set_ylabel('Relative Flux')
        plt.ioff()
        plt.show()