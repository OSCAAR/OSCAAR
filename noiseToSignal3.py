# Descendant of the original 'differ10.2.py'
import os
import math
import numpy as np
import matplotlib.pyplot as plt
import pyfits
import diffmodule5 as dm ## Classes for "fluxArray" and "starObj"

def pstr(num,pad):
    strlen = len(str(num))
    lenpad = pad-strlen
    return str((lenpad*'0')+str(num))

def trunc(f, n):
    '''Truncates a float f to n decimal places without rounding'''
    slen = len('%.*f' % (n, f))
    return str(f)[:slen]

def mkdir(a, b=None):
    """Make new directory with name a where a
       is a string inside of single quotes"""
    if b is None:
        c = ''
    else:
        c = ' '+str(b)
    command = 'mkdir '+str(a)+str(c)
    os.system(command)

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
    os.system(command)

def noiseToSig(dir,regressCoefs,regressConst):
    lenFlx = lenFlxA                ## Identify the nod, and thus the length to expect

    dataMatrix = np.zeros([lenFlx,1])
    uncMatrix = np.zeros([lenFlx,1])
    for i in range(1,nStars):
        file = open('aper_out/phot_out_'+str(((3 - len(str(i)))*'0')+str(i))+'.log','r').read().splitlines()
        dataCol = np.zeros([len(file),1])
        uncCol = np.zeros([len(file),1])
        for j in range(0,len(file)):
            dataCol[j] = file[j].split()[0]
            uncCol[j] = file[j].split()[1]
        #plt.plot(dataCol,'o',color=(0,0,0))
        #print np.shape(dataMatrix),np.shape(dataCol)
        dataMatrix = np.hstack([dataMatrix,dataCol]) 
        uncMatrix = np.hstack([uncMatrix,uncCol]) 

    fluxMatrix = dataMatrix[:,1:nStars]
    errMatrix = uncMatrix[:,1:nStars]
    #print fluxMatrix     ## << this matrix contains columns of the flux data from each comp star
    #print errMatrix

    gain = 0.77999997138977051 # e-/ADU
    apertureRadius = 8 #pxls
    apertureArea = math.pi*apertureRadius**2
    medianBackground = 1800.0*(1+1/np.sqrt(507.5))
    apertureBackground = medianBackground*apertureArea  ## Total aperture background to add is
    #print apertureBackground                           ## the background per sq pixel times the area in pxls
    eCountsBg = (fluxMatrix+apertureBackground)*gain # signals measured in e-'s
    eCounts = (fluxMatrix)*gain # signals measured in e-'s
    errMatrix = errMatrix*gain
    
    lightCurve = diffA
    
    ScompTotal = []     ## comparison star signal
    for i in range(0,lenFlx):
        coeffWeightedSum = 0
        regressionSum = 0
        for j in range(1,nStars-1):
            regressionSum += regressCoefs[j]
            coeffWeightedSum += eCounts[i,j]
        ScompTotal.append(coeffWeightedSum)
    ScompTotal = np.array(ScompTotal)

    StargetTotal = np.array(eCounts[:,0])

    print 'mean(ScompTotal)^2',np.mean(ScompTotal**2)
    print 'regressionSum',regressionSum
    print 'mean(StargetTotal)^2',np.mean(StargetTotal**2)

    uncScompSquared = []        
    for i in range(0,lenFlx): 
        coeffWeightedSum = 0    ## sum the regression coefficients times the
        for j in range(1,nStars-1):  ##poisson noise (square root of signal) quantity squared
            coeffWeightedSum += (np.sqrt(eCountsBg[i,j]))**2
        uncScompSquared.append(coeffWeightedSum)

    uncStargetSquared = []      
    for i in range(0,lenFlx):
        #print dataMatrix
        coeffWeightedSum = 0
        for j in range(0,1):
            coeffWeightedSum += (np.sqrt(eCountsBg[i,j]))**2
        uncStargetSquared.append(coeffWeightedSum)
    #print uncStargetSquared
    print '\nlight curve \t',np.mean(lightCurve)
    print 'unc S comp \t%E' % np.mean(uncScompSquared)
    print 'S comp    \t',np.mean(ScompTotal**2)
    print 'unc S target \t%E' % np.mean(uncStargetSquared)
    print 'S target \t',np.mean(StargetTotal**2)
    N = np.sqrt(((uncScompSquared/ScompTotal**2) + (uncStargetSquared/StargetTotal**2)))
    print "N =",np.mean(N)
    #Note: N = sqrt(S)
    #Stotal = NtotalSquared
    
    #NtoS = Ntotal/Stotal 
    return N/lightCurve, StargetTotal,ScompTotal
