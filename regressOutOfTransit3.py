import os
import math
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import scipy.stats as stats
from time import sleep
import diffmodule5 as dm ## Classes for "fluxArray" and "starObj"

## differcalc3.py adapted for "regression" a la Drake

def pstr(num,pad):
    strlen = len(str(num))
    lenpad = pad-strlen
    return str((lenpad*'0')+str(num))

def trunc(f, n):
    '''Truncates a float f to n decimal places without rounding'''
    slen = len('%.*f' % (n, f))
    return str(f)[:slen]

def ut2jd(utshut):
    [date, Time] = utshut.split(';')
    [year, month, day] = date.split('-')
    [hour, min, sec] = Time.split(':')
    year = int(year); month = int(month); day = int(day)
    hour = int(hour); min = int(min); sec = float(sec)
    #years = (int(year) + 4716)*365.25
    if month == 1 or month == 2: 
        month += 12
        year -= 1
    a = year/100
    b = a/4
    c = 2-a+b
    d = day
    e = math.floor(365.25*(year+4716))
    f = math.floor(30.6001*(month+1))
    years = c+d+e+f-1524.5
    fracOfDay = (hour/24.) + (min/(24*60.)) + (sec/(24*60*60.))
    jd = years + fracOfDay
    return jd

mkdir('reducedOut/')

ingress = ut2jd(ingressUt)
egress = ut2jd(egressUt)


for nod in range(0,1):
    ## Load time
    timeFile = open('time_out/time.log','r').read().splitlines()
    timeComplete = np.transpose(np.array([map(float,timeFile)]))     ## column vector

    numlist = range(1,nStars+1)
    targetNumber = 1

    #numlist = [1, 3, 4, 5, 6, 7]
    #numlist = [1,2,4,6,9]
    flxfiles = numlist
    compStars = []
    targetComplete = dm.starObj(pstr(targetNumber,3)).flux()
    target = []
    timeOOT = []
    for i in range(0,len(targetComplete)):
        print timeComplete[i], ingress
        if timeComplete[i] < ingress or timeComplete[i] > egress:
            target.append(float(targetComplete[i]))     ## Column vector
            timeOOT.append(timeComplete[i])

    hstack = target     ## Initialize the 'hstack' matrix with (first column)=(target fluxes)

    hstackComplete = np.transpose(targetComplete)

    for i in range(0,len(numlist)):
        if numlist[i] != targetNumber:
            comparisonComplete = dm.starObj(pstr(numlist[i],3)).flux()
            comp = []
            for j in range(0,len(comparisonComplete)):
                if timeComplete[j] < ingress or timeComplete[j] > egress:
                    comp.append(float(comparisonComplete[j]))## Column vector
            #print hstack, comp
            #print np.shape(np.transpose(hstackComplete)),np.shape(comparisonComplete)
            #print np.shape(hstack), np.shape(comp)
            hstack = np.vstack([hstack,comp])
            hstackComplete = np.vstack([hstackComplete,np.transpose(comparisonComplete)])
    ##print np.shape(np.transpose(hstack)),np.shape(timeOOT)
    hstack = np.transpose(hstack)
    #print np.shape(timeOOT), np.shape(hstack)
    hstack = np.hstack([timeOOT,hstack])

    hstackFiltered = hstack

    hstackComplete = np.transpose(hstackComplete)
    #print np.shape(timeComplete),np.shape(hstackComplete)
    hstackComplete = np.hstack([timeComplete,hstackComplete])

    target = hstackFiltered[:,1]
    time = hstackFiltered[:,0]
    #################################
    ## Now from regressionCalc.py:

    #print np.shape(LDDmatrix),np.shape(target)
    #LDDmatrix = hstackFiltered[:,2:np.shape(hstackFiltered)[1]]     ## cut out the time column and the column of the target star from hstack
    #print 'np.shape(hstackFiltered)',np.shape(hstackFiltered)
    LDDmatrix = hstackFiltered[:,2:]     ## cut out the time column and the column of the target star from hstack
    #print 'shape(LDDmatrix)',np.shape(LDDmatrix)
    
    #print 'shape(ones)',np.shape(np.ones([np.shape(LDDmatrix)[0],1]))
    #LDDmatrix = np.hstack([LDDmatrix, np.ones([np.shape(LDDmatrix)[0],1])])
    #print 'LDDmatrix',LDDmatrix

    #print 'regression output',np.linalg.lstsq(LDDmatrix,target)
    #coeffs = np.array(np.linalg.lstsq(LDDmatrix,target)[0])
    #coeff = np.zeros([len(coeffs),1])
    #for i in range(0,len(coeff)): coeff[i] = coeffs[i]
    
    coeff = []
    const = []
    for i in range(0,LDDmatrix.shape[1]):
        regressMatrix = np.vstack([LDDmatrix[:,i], np.ones_like(LDDmatrix[:,i])]).T
        m,c = np.linalg.lstsq(regressMatrix,target)[0]
        coeff.append(m)
        const.append(c)
    
    regressCoeffs = np.append(1,coeff)
    regressConst = np.append(0,const)
    if nod == 0:
        regressCoeffsA = regressCoeffs
        regressConstA = regressConst
    else:
        regressCoeffsB = regressCoeffs
        regressConstB = regressConst
    
    coeffWeightedSum = np.dot(LDDmatrix[:,:np.shape(LDDmatrix)[1]],coeff)#+regressConst ## changed coeff->coeffList[0]: Use only first coefficients list
    regNormCompStars = hstackComplete[:,2:]*np.array(coeff).T#+regressConst ## changed coeff->coeffList[0]: Use only first coefficients list
    
    for i in range(0,nStars-1):
        regNormCompStars[:,i] = regNormCompStars[:,i]+const[i]

    print regNormCompStars.shape
#cd()
hstackA = hstackFiltered
hstackCompleteA = hstackComplete
regNormCompStarsA = regNormCompStars

timeA = hstackA[:,0]
#timeB = hstackB[:,0]
targetA = hstackA[:,1]
#targetB = hstackB[:,1]
timeAc = hstackCompleteA[:,0]
targetAc = hstackCompleteA[:,1]
#timeBc = hstackCompleteB[:,0]
#targetBc = hstackCompleteB[:,1]

regNormCompStarsOOTA = []

regNormCompStarsOOTA = regNormCompStarsA[0,:]

for i in range(1,len(regNormCompStarsA)):
    if timeAc[i] < ingress or timeAc[i] > egress:
        regNormCompStarsOOTA = np.vstack([regNormCompStarsOOTA,regNormCompStarsA[i,:]])     ## Column vector

starNum = 1#11
##########################################
## Plot comp star 1 normalized w regression coeff

comp1A = hstackA[:,2]*regressCoeffsA[1]+regressConstA[1]        ## <<<**** THIS!!

pedanticPlots = 'on'
if pedanticPlots == 'on':
    for i in range(0,nStars-1):
        plt.plot(hstackCompleteA[:,0],regNormCompStarsA[:,i],'.')#+regressConstA[1]
    plt.xlabel('JD')
    plt.ylabel('Regression Normalized Flux')
    plt.plot(timeA,targetA,'bo')
    
    plt.plot()
    if initGui == None:
        plt.show()
    else:
        plt.savefig('plots/jdRNF.png', fmt = '.png')

##########################################
## Calculate cross correlation coefficients

def correlationCoeff(target,comp):
    return np.sum(np.abs(np.array(target)-np.array(comp)))

#corrCoeffsA = []
#for i in range(0,nStars-1):
#    corrCoeffsA.append(correlationCoeff(targetA,hstackA[:,2+i]))
#corrCoeffsB = []
#for i in range(0,nStars-1):
#    corrCoeffsB.append(correlationCoeff(targetB,hstackB[:,2+i]))
corrCoeffsA = []
for i in range(0,nStars-1):
    print np.shape(targetA),np.shape(regNormCompStarsOOTA)
    corrCoeffsA.append(correlationCoeff(targetA,regNormCompStarsOOTA[:,i]))

print corrCoeffsA/np.min(corrCoeffsA)

plotGoodness = True
if plotGoodness == True:
    plt.plot(range(0,nStars-1),corrCoeffsA,'o')
    plt.title('Goodness of fit')
    plt.xlabel('Comp star index')
    plt.ylabel('Cross-correlation')
    plt.xlim([-1,nStars-1])
    #plt.ylim([0,2.5e7])
    plt.savefig('plots/goodnessOfFit.png',fmt='png')
    if initGui == None:
        plt.show()
##########################################

goodnessCoeff = (corrCoeffsA/np.min(corrCoeffsA))**-1
goodnessCoeff = goodnessCoeff/np.sum(goodnessCoeff)

useOne = False
useSum = True

if useOne == False:
    sumCompA = regNormCompStarsA[:,3]
if useSum == True:
    sumCompA = np.zeros_like(regNormCompStarsA[:,0])
    numTot = 0
    for i in [0,1,2,3,5,6,7,13,15,16]: #[1,2,3,6,13]#range(0,nStars-1):
        numTot += 1
        sumCompA +=  regNormCompStarsA[:,i]
    sumCompA = sumCompA/numTot#/(nStars-1)

fig = plt.figure()
ax2 = fig.add_subplot(211)
ax2.set_ylim([np.mean(targetAc/sumCompA)-2*np.std(targetAc/sumCompA),np.mean(targetAc/sumCompA)+2*np.std(targetAc/sumCompA)])
ax2.set_title('Target/Comparison')
ax2.set_ylabel('Normalized flux')

global lenFlxA, diffA
diffA = targetAc/sumCompA
lenFlxA = len(diffA)

## Fit and subtract linear trend
subtractTrend = False

if subtractTrend == True:
    ## compile out of transit LC points
    diffAOOT = []
    for i in range(0,len(timeAc)):
        if timeAc[i] < ingress or timeAc[i] > egress:
            diffAOOT.append(diffA[i])
    diffAOOT = np.array(diffAOOT)
    
    LCregressMatrix = np.hstack([timeOOT, np.ones_like(timeOOT)])
    print LCregressMatrix.shape, diffAOOT.shape
    m,c = np.linalg.lstsq(LCregressMatrix,diffAOOT)[0]
    print 'Linear trend removed: y =',m,'*x +',c
    diffALin = np.ones_like(diffA)
    for i in range(0,len(timeAc)):
        diffALin[i] = diffA[i] - (m*timeAc[i] + c) + 1
 
    combinedStack = np.zeros([len(timeAc),2])
    for i in range(0,len(timeAc)):
        combinedStack[i,0] = timeAc[i]
        combinedStack[i,1] = diffALin[i]

    combinedStackSorted = combinedStack[np.lexsort((combinedStack[:,1],combinedStack[:,0]))]

    ax2.plot(combinedStackSorted[:,0],combinedStackSorted[:,1],'ko')
    
    diffArr = dm.diffArr(combinedStackSorted[:,1],combinedStackSorted[:,1])
    diffArr.calcMedian(16,combinedStackSorted[:,0])
    ax2.plot(diffArr.medianx(),diffArr.mediany(),'r',linewidth=3)
    ax2.set_xlim([min(combinedStackSorted[:,0]),max(combinedStackSorted[:,0])])
    ax2.axvline(x=ingress,ymin=0,ymax=1,color='k',
        linestyle=':',linewidth=1)
    ax2.axvline(x=egress,ymin=0,ymax=1,color='k',
        linestyle=':',linewidth=1)

    lightCurveOutA = open('reducedOut/lightCurveOutA.txt','w')
    for i in diffALin:
        lightCurveOutA.write(str(i)+'\n')
        
else:
    combinedStack = np.zeros([len(timeAc),2])
    for i in range(0,len(timeAc)):
        combinedStack[i,0] = timeAc[i]
        combinedStack[i,1] = diffA[i]

    combinedStackSorted = combinedStack[np.lexsort((combinedStack[:,1],combinedStack[:,0]))]
    #phaseTime = open('phaseTime.txt','wa')
    #for i in range(0,len(combinedStackSorted[:,0])):
    #    phaseTime.write(str(combinedStackSorted[:,0][i])+'\n')
    #phaseTime.close()
    ax2.plot(combinedStackSorted[:,0],combinedStackSorted[:,1],'ko')
    diffArr = dm.diffArr(combinedStackSorted[:,1],combinedStackSorted[:,1])
    diffArr.calcMedian(10,combinedStackSorted[:,0])
    #medianBinned = open('medianBinned.txt','wa')
    #for i in range(0,len(diffArr.medianx())):
    #    print 'writing'
    #    medianBinned.write(str(diffArr.medianx()[i])+' '+str(diffArr.mediany()[i])+' '+str('0.002')+'\n')
    #medianBinned.close()
    ax2.plot(diffArr.medianx(),diffArr.mediany(),'r',linewidth=3)
    ax2.set_xlim([min(combinedStackSorted[:,0]),max(combinedStackSorted[:,0])])
    ax2.axvline(x=ingress,ymin=0,ymax=1,color='k',
        linestyle=':',linewidth=1)
    ax2.axvline(x=egress,ymin=0,ymax=1,color='k',
        linestyle=':',linewidth=1)

    lightCurveOutA = open('reducedOut/lightCurveOutA.txt','w')
    for i in diffA:
        lightCurveOutA.write(str(i)+'\n')


