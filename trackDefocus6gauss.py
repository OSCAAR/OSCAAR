## Find the maximum and MINIMUM of the intensity plot without
## the absolute value used in trackDefocus1.py, making it more general

## Adapted to replace trackstars2 in oscaar for NIRoscaar

import pyfits
import os
import numpy as np
import math
from matplotlib import pyplot as plt

###Editted to allow for gaussian stars by not looking at each half for the
###max/min

def trackDefocus6(scidata,init_x, init_y, hww,plots=trackplot):
    #print 'Centering file: '+str(files[i])
    #hdulist = pyfits.open(files[i])
    #scidata = hdulist[0].data

    xPos = init_x#415
    yPos = init_y#700
    #hww = 8

    target = scidata[xPos-hww:xPos+hww,yPos-hww:yPos+hww]   ## Cropped image of just the target star

    ## Sum columns
    axisA = np.sum(target,axis=0)   ## Take the sums of all values in each column,
    axisB = np.sum(target,axis=1)   ## then repeat for each row

    axisADeriv = np.diff(axisA)     ## Find the differences between each pixel intensity and
    axisBDeriv = np.diff(axisB)     ## the neighboring pixel (derivative of intensity profile)

    #print len(axisADeriv)
    derivMinAind = np.where(axisADeriv == min(axisADeriv[len(axisADeriv)/2:len(axisADeriv)]))[0][0] ## Minimum in the derivative
    derivMinBind = np.where(axisBDeriv == min(axisBDeriv[len(axisBDeriv)/2:len(axisBDeriv)]))[0][0] ## of the intensity plot

    derivMaxAind = np.where(axisADeriv == max(axisADeriv[0:len(axisADeriv)/2]))[0][0] ## Maximum in the derivative
    derivMaxBind = np.where(axisBDeriv == max(axisBDeriv[0:len(axisBDeriv)/2]))[0][0] ## of the intensity plot

    #print "First axis min:",axisADeriv[derivMinAind],derivMinAind
    #print "First axis max:",axisADeriv[derivMaxAind],derivMaxAind
    #print "Second axis min:",axisBDeriv[derivMinBind],derivMinBind
    #print "Second axis max:",axisBDeriv[derivMaxBind],derivMaxBind

    indMax = np.argmax(axisADeriv)
    fitPlots = 'off'
    def quadraticFit(derivative,ext):
        rangeOfFit = 1
        lenDer = len(derivative)/2
        #if ext == "max":
        #    indExtrema = np.argmax(derivative[:lenDer])
        #if ext == "min":
        #    indExtrema = np.argmin(derivative[lenDer:])+lenDer
   
        if ext == "max":
            indExtrema = np.argmax(derivative)
        if ext == "min":
            indExtrema = np.argmin(derivative)
        fitPart = derivative[indExtrema-rangeOfFit:indExtrema+rangeOfFit+1]
        #print 'indExtrema',indExtrema
        #print 'len(derivative)',len(derivative)
        #print 'len(fitPart)',len(fitPart)
        #def quadfunc(x, a, b, c):
        if len(fitPart) == 3:
            stackPolynomials = [0,0,0]
            for i in range(0,len(fitPart)):
                vector = [i**2,i,1]
                stackPolynomials = np.vstack([stackPolynomials,vector])
            xMatrix = stackPolynomials[1:,:]
            from numpy import linalg as LA
            xMatrixInv = LA.inv(xMatrix)

            estimatedCoeffs = np.dot(xMatrixInv,fitPart)
            #print estimatedCoeffs

            a_fit = estimatedCoeffs[0]#-0.05
            b_fit = estimatedCoeffs[1]#0.5
            c_fit = estimatedCoeffs[2]#0.1
            d_fit = -b_fit/(2.*a_fit)

            #print "Fit found:",d_fit
            extremum = d_fit+indExtrema-rangeOfFit
            
            if fitPlots == 'on':
                fitVals = []
                for i in range(0,len(fitPart)):
                    fitVals.append(quadfunc(i,a_fit,b_fit,c_fit,d_fit))
                plt.clf()
                #plt.plot(axisBDeriv,'-b')
                #plt.plot(axisBDeriv,'-g')
                plt.plot(fitPart,'-b')    
                plt.plot(fitVals,'r')
                plt.show()
        else: 
            extremum = indExtrema
        return extremum
    
    extremumA = quadraticFit(axisADeriv,ext="max")
    extremumB = quadraticFit(axisADeriv,ext="min")
    extremumC = quadraticFit(axisBDeriv,ext="max")
    extremumD = quadraticFit(axisBDeriv,ext="min")

    averageRadius = (abs(derivMinAind-derivMaxAind)+abs(derivMinBind-derivMaxBind))/4. ## Average diameter / 2
    #print "Average Radius",averageRadius

    #axisAcenterInd = abs(derivMaxAind+derivMinAind)/2
    #axisBcenterInd = abs(derivMaxBind+derivMinBind)/2
    #print "Star center in axis a,b:",axisAcenterInd, axisBcenterInd

    #xCenter = xPos-hww+axisBcenterInd+1
    #yCenter = yPos-hww+axisAcenterInd+1
    #print np.mean(target)

    axisAcenter = (extremumA+extremumB)/2.
    axisBcenter = (extremumC+extremumD)/2.

    xCenter = xPos-hww+axisBcenter
    yCenter = yPos-hww+axisAcenter

#    print "axisAcenter",axisAcenter,"axisBcenter",axisBcenter
#    print "Center (x,y): ",xCenter,yCenter

    #fig = plt.figure()

    if plots == 'on':

        plt.clf()
        plt.subplot(212)
        plt.plot(axisA,'-b')
        plt.plot(axisB,'-g')
        #plt.plot(axisADeriv,'-')
        #plt.plot(axisBDeriv,'-')
        plt.title('Intensity profile in two axes')
        plt.axvline(x=extremumA,ymin=0,ymax=1,color='b',
                linestyle=':',linewidth=1)
        plt.axvline(x=extremumB,ymin=0,ymax=1,color='b',
                linestyle=':',linewidth=1)
                
        plt.axvline(x=extremumC,ymin=0,ymax=1,color='g',
                linestyle=':',linewidth=1)
        plt.axvline(x=extremumD,ymin=0,ymax=1,color='g',
                linestyle=':',linewidth=1)
        #plt.axvline(x=yCenter+11,ymin=0,ymax=1,color='r',
        #        linestyle=':',linewidth=1)            
        plt.draw()
    
        #targetRecentered = scidata[xCenter-hww:xCenter+hww,yCenter-hww:yCenter+hww]
        #img = plt.imshow(targetRecentered)
        #plt.grid()
        #img.set_clim([0,10000])
        #img.set_interpolation('nearest')
        #plt.draw()

    return [xCenter,yCenter,averageRadius]