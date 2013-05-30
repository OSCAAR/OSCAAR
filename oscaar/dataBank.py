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
import oscaar
from IO import *
from other import *
from mathMethods import *
oscaarpath = os.path.dirname(os.path.abspath(oscaar.__file__))
oscaarpathplus = os.path.join(oscaarpath,'extras')


class dataBank:
    '''
        Methods for storing information from each star in Python dictionaries.
        
        Core Developer: Brett Morris
        '''
    def __init__(self):
        '''
            Run oscaar.parseRegionsFile() to get the inital guesses for the 
            initial centroids of the stars from the DS9 regions file, create
            dictionaries in which to store all of the data collected
            for each star. Allocate the memory for these arrays wherever possible.
            Parse the init.par file to grab the paths and initial parameters for 
            the run.
            INPUTS: None.
            '''
        self.parseInit() ## parse init.par using the parseInit() method
        self.parseObservatory()
        assert len(self.imagesPaths) > 1, 'Must have at least one data image'
        print 'self.flatPath',self.flatPath
        if self.flatPath != '':
            self.masterFlat = pyfits.getdata(self.flatPath)
            self.masterFlatPath = self.flatPath
        else:
            print 'Using an isotropic ("placebo") master-flat (array of ones)'
            dim1,dim2 = np.shape(pyfits.getdata(self.imagesPaths[0]))
            self.masterFlat = np.ones([dim1,dim2])
        self.allStarsDict = {}
        init_x_list,init_y_list = parseRegionsFile(self.regsPath)        
        zeroArray = np.zeros_like(self.imagesPaths,dtype=np.float32)
        self.times = np.zeros_like(self.imagesPaths,dtype=np.float64)
        self.keys = []
        self.targetKey = '000'
        for i in range(0,len(init_x_list)):
            self.allStarsDict[paddedStr(i,3)] = {'x-pos':np.copy(zeroArray), 'y-pos':np.copy(zeroArray),\
                'rawFlux':np.copy(zeroArray), 'rawError':np.copy(zeroArray),'flag':False,\
                'scaledFlux':np.copy(zeroArray), 'scaledError':np.copy(zeroArray), 'chisq':0}
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
    
    def storeTime(self,expNumber):
        '''Store the time in JD from the FITS header.
            INPUTS: exposureNumber - Index of exposure being considered
            
            time - Time as read-in from the FITS header
            '''
        try:
            timeStamp = pyfits.getheader(self.getPaths()[expNumber])[self.timeKeyword]
        except KeyError: 
            print 'Input Error: The Exposure Time Keyword indicated in observatory.par is not a valid key: ',self.timeKeyword
        finally: 
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
                self.allStarsDict[star]['scaledFlux'], m = regressionScale(self.getFluxes(star),self.getFluxes(self.targetKey),self.getTimes(),self.ingress,self.egress,returncoeffs=True)
                print m
                self.allStarsDict[star]['scaledError'] = np.abs(m)*self.getErrors(star)
            if star == self.targetKey:	## (Keep the target star the same)
                self.allStarsDict[star]['scaledFlux'] = self.allStarsDict[star]['rawFlux']
                self.allStarsDict[star]['scaledError'] = self.allStarsDict[star]['rawError']
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
            self.allStarsDict[star]['chisq'] = chiSquared(self.getFluxes(self.targetKey),self.getFluxes(star))
        chisq = []
        for star in self.allStarsDict:
            chisq.append(self.allStarsDict[star]['chisq'])
        self.chisq = np.array(chisq)
        self.meanChisq = np.mean(chisq)
        self.stdChisq = np.std(chisq)
    
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
        for star in self.allStarsDict:
            if star != self.targetKey and (np.abs(self.meanChisq - self.allStarsDict[star]['chisq']) < 2*self.stdChisq):
                compStars[:,columnCounter] = self.getScaledFluxes(star).astype(np.float64)
                compStarsOOT[:,columnCounter] = self.getScaledFluxes(star)[self.outOfTransit()].astype(np.float64)
                compErrors[:,columnCounter] = self.getScaledErrors(star).astype(np.float64)
                acceptedCompStarKeys.append(int(star))
                columnCounter += 1
            elif star != self.targetKey and (np.abs(self.meanChisq - self.allStarsDict[star]['chisq']) > 2*self.stdChisq):
                print 'Star '+str(star)+' excluded from regression'
                columnCounter += 1
        initP = np.zeros([numCompStars])+ 1./numCompStars
        def errfunc(p,target): 
            if all(p >=0.0): return np.dot(p,compStarsOOT.T) - target ## Find only positive coefficients
        #return np.dot(p,compStarsOOT.T) - target
        
        bestFitP = optimize.leastsq(errfunc,initP[:],args=(target.astype(np.float64)),maxfev=10000000,epsfcn=np.finfo(np.float32).eps)[0]
        print '\nBest fit regression coefficients:',bestFitP
        print 'Default weight:',1./numCompStars
        
        self.comparisonStarWeights = np.vstack([acceptedCompStarKeys,bestFitP])
        self.meanComparisonStar = np.dot(bestFitP,compStars.T)
        self.meanComparisonStarError = np.sqrt(np.dot(bestFitP**2,compErrors.T**2))
        return self.meanComparisonStar, self.meanComparisonStarError  
    
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
            if line.split() > 1 and line[0] != '#':
                inline = line.split(':', 1)
                inline[0] = inline[0].strip()
                if inline[0] == 'Path to Dark Frames': 
                	if len(glob(inline[1].split('#')[0].strip())) > 0:## if glob turns up more results,
                		self.darksPath = np.sort(glob(inline[1].split('#')[0].strip()))
                	else: 
		                darkpaths = []
		                for path in str(inline[1].split('#')[0].strip()).split(','):
		                    path = os.path.join(oscaarpathplus,os.path.abspath(path))
		                    darkpaths.append(path)
		                self.darksPath = np.sort(darkpaths)
                elif inline[0] == 'Path to Master-Flat Frame': self.flatPath = str(inline[1].split('#')[0].strip())
                elif inline[0] == 'Path to data images':
                    # 					if any(np.array(glob(inline[1].split('#')[0].strip())) == inline[1].split('#')[0].strip()) == False:## if glob turns up more results,
					if len(glob(inline[1].split('#')[0].strip())) > 0:## if glob turns up more results,
                        
						self.imagesPaths = np.sort(glob(inline[1].split('#')[0].strip()))
					else: 
						impaths = []
						for path in str(inline[1].split('#')[0].strip()).split(','):
						    path = os.path.join(oscaarpathplus,os.path.abspath(path))
						    impaths.append(path)
						self.imagesPaths = np.sort(impaths)
                elif inline[0] == 'Path to regions file': self.regsPath = str(inline[1].split('#')[0].strip())
                elif inline[0] == 'Ingress':  self.ingress = oscaar.ut2jd(str(inline[1].split('#')[0].strip()))
                elif inline[0] == 'Egress':  self.egress = oscaar.ut2jd(str(inline[1].split('#')[0].strip()))
                elif inline[0] == 'Radius':   self.apertureRadius = float(inline[1].split('#')[0].strip())
                elif inline[0] == 'Tracking Zoom':   self.trackingZoom = float(inline[1].split('#')[0].strip())
                elif inline[0] == 'CCD Gain':    self.ccdGain = float(inline[1].split('#')[0].strip())
                elif inline[0] == 'GUI': self.gui = inline[1].split('#')[0].strip()
                elif inline[0] == 'Plot Tracking': self.trackPlots = True if inline[1].split('#')[0].strip() == 'on' else False
                elif inline[0] == 'Plot Photometry': self.photPlots = True if inline[1].split('#')[0].strip() == 'on' else False
                elif inline[0] == 'Smoothing Constant': self.smoothConst = float(inline[1].split('#')[0].strip())
                elif inline[0] == 'Init GUI': self.initGui = inline[1].split('#')[0].strip()
                elif inline[0] == 'Output Path': self.outputPath = inline[1].split('#')[0].strip()
        
        self.outputPath = os.path.join(oscaarpathplus,os.path.abspath(self.outputPath))
        #self.flatPath = os.path.join(os.path.abspath(self.flatPath))
        
        def wilds(self,inputString):
            if any(np.array(glob(inputString)) == inputString):
                return ','.join(glob(inputString))
            else: 
                return 
    
    def parseObservatory(self):
        '''
            Parses observatory.par
            '''
        obs = open(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'observatory.par'), 'r').read().splitlines()
        for line in obs:
            if line.split() > 1 and line[0] != '#':
                inline = line.split(':', 1)
                inline[0] = inline[0].strip()
                if inline[0] == 'Exposure Time Keyword': self.timeKeyword = str(inline[1].split('#')[0].strip())
        
        if self.timeKeyword == 'JD': self.convertToJD = lambda x: x ## If the keyword is "JD", no conversion is needed
        elif self.timeKeyword == 'DATE-OBS': self.convertToJD = ut2jdSplitAtT ## If the keyword is "DATE-OBS", converstion is needed
    ##elif inline[0] == '':
    
    def plot(self,pointsPerBin=10):
        plt.close()
        
        
        times = self.getTimes()
        meanComparisonStar, meanComparisonStarError = self.calcMeanComparison(ccdGain = self.ccdGain)
        lightCurve, lightCurveErr = self.computeLightCurve(meanComparisonStar, meanComparisonStarError)
        binnedTime, binnedFlux, binnedStd = medianBin(times,lightCurve,pointsPerBin)
        
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
    
    def plotLightCurve(self,pointsPerBin=10):
        
		binnedTime, binnedFlux, binnedStd = medianBin(self.times,self.lightCurve,pointsPerBin)
        
		fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
		fig.canvas.set_window_title('OSCAAR')
		axis = fig.add_subplot(111)
		def format_coord(x, y):
			'''Function to give data value on mouse over plot.'''
			return 'JD=%1.5f, Flux=%1.4f' % (x, y)
		axis.format_coord = format_coord 
		axis.errorbar(self.times,self.lightCurve,yerr=self.lightCurveError,fmt='k.',ecolor='gray')
		axis.errorbar(binnedTime, binnedFlux, yerr=binnedStd, fmt='rs-', linewidth=2)
		axis.axvline(ymin=0,ymax=1,x=self.ingress,color='k',ls=':')
		axis.axvline(ymin=0,ymax=1,x=self.egress,color='k',ls=':')
		axis.set_title('Light Curve')
		axis.set_xlabel('Time (JD)')
		axis.set_ylabel('Relative Flux')
		plt.ioff()
		plt.show()
    
    def plotRawFluxes(self,pointsPerBin=10):
        
		fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
		fig.canvas.set_window_title('OSCAAR')
		axis = fig.add_subplot(111)
		def format_coord(x, y):
			'''Function to give data value on mouse over plot.'''
			return 'JD=%1.5f, Flux=%1.4f' % (x, y)
		axis.format_coord = format_coord 
		for star in self.allStarsDict:
			axis.errorbar(self.times,self.allStarsDict[star]['rawFlux'],yerr=self.allStarsDict[star]['rawError'],fmt='o')
        
		axis.axvline(ymin=0,ymax=1,x=self.ingress,color='k',ls=':')
		axis.axvline(ymin=0,ymax=1,x=self.egress,color='k',ls=':')
		axis.set_title('Raw Fluxes')
		axis.set_xlabel('Time (JD)')
		axis.set_ylabel('Counts')
		plt.ioff()
		plt.show()
    
    
    def plotScaledFluxes(self,pointsPerBin=10):
        
		fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
		fig.canvas.set_window_title('OSCAAR')
		axis = fig.add_subplot(111)
		def format_coord(x, y):
			'''Function to give data value on mouse over plot.'''
			return 'JD=%1.5f, Flux=%1.4f' % (x, y)
		axis.format_coord = format_coord 
		for star in self.allStarsDict:
			axis.errorbar(self.times,self.allStarsDict[star]['scaledFlux'],yerr=self.allStarsDict[star]['scaledError'],fmt='o')
        
		axis.axvline(ymin=0,ymax=1,x=self.ingress,color='k',ls=':')
		axis.axvline(ymin=0,ymax=1,x=self.egress,color='k',ls=':')
		axis.set_title('Scaled Fluxes')
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
    
    def plotComparisonWeightings(self):
		weights = self.comparisonStarWeights
		weights = np.sort(weights,axis=1)
		print weights
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
		ax.set_title('Comparison Star Weights into the Composite Comparison Star')
		ax.axhline(xmin=0,xmax=1,y=1.0/len(indices),linestyle=':',color='k')
        
		ax.bar(indices,coefficients,width,color='w')
        
		plt.show()

