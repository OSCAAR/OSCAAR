'''
	Open the data pickle generated after running oscaar and 
    do a L-M least-squares fit to the light curve. Calculate
    uncertainties in the extracted system parameters with the
    prayer-bead method.
'''

import numpy as np
#import ctypes
from matplotlib import pyplot as plt
from scipy import optimize

import os
import oscaar.code.oscaar as oscaarx

## Run parameters: 
plotFit = True		## Plot light curve fit
animatePB = False 	## Plot each prayer-bead iteration

dataBank = oscaarx.load(os.path.join(os.path.dirname(__file__),os.path.abspath("../../../outputs/oscaarDataBase.pkl")))
t = times = np.require(dataBank.getTimes(),dtype=np.float64)
F = dataBank.lightCurve
sigmas = dataBank.lightCurveError
Npoints = len(t)
n = Npoints

## np.require() will force the ndarrays to the right dtype as assigned in the `argtypes` list.
t = np.require(t,np.float64)
#F = np.empty_like(t,dtype=np.float32)
#occultquad(t, p,  ap,  P,  i,  gamma1,  gamma2, e,longPericenter, t0,  n,  F)	## Simulate fake data
# Enter Initial Parameters to vary
initParamNames = ['R_p/R_s','a/R_s','inc','t_0']
modelParams = np.loadtxt(os.path.join(os.path.dirname(__file__),'modelParams.txt'))
print modelParams
[p,ap,P,i,gamma1,gamma2,e,longPericenter,t0] = modelParams
initParams = actualParams = np.require([p, ap, i, t0],dtype=np.float64)
bestFitP = np.empty_like(initParams)
data = np.copy(F)

def fitfunc(p,t=t,P=P,gamma1=gamma1,gamma2=gamma2,e=e,longPericenter=longPericenter):
    '''Fixed parameters: P, gamma1, gamma2, e, longPericenter
       Constraints: 0<=inclination<=90, but to prevent the leastsq algorithm from getting penalized
       for inclinations near 90, allow it to vary over range (0,180), and if a value is submitted > 90,
       then subtract it from 180 to return a value on 0=<i<90'''
    if p[2] >= 0 and p[2] <= 180:
    	if p[2] > 90: p[2] = 180 - p[2] ## 90 - (p[2] - 90)
        #occultquad(t,p[0],p[1],P,p[2],gamma1,gamma2,e,longPericenter,p[3],n,F)
        modelParams = [p[0],p[1],P,p[2],gamma1,gamma2,e,longPericenter,p[3]]
        F = oscaarx.occultquad(times,modelParams)
        return F
    ## else: return None        #(implied without implementation)
def errfunc(p, uncertainties, y): 
    '''If the trial parameters are outside of the permitted range dictated by the limits
       in fitfunc, assign a 10% higher error value than the last one, so as to indicate a
       sharp slope in the chi^2 gradient at that limit. This will tend to reverse the 
       direction of the parameter space exploration by optimize.scipy, and keep your fitting
       on track even though you're exploring a constrained parameter space.

       Note: This isn't the most rigorous way to constrain parameter space, it's sort of a 
       hack, but it seems to work at least some of the time.'''
    global lastSuccessfulError, firstError
    #print p
    if fitfunc(p) != None:      
       # print 'success'
        error = (fitfunc(p) - y)/uncertainties
        if all(p == initParams) or all(p == bestFitP): firstError = error
        #lastSuccessfulError = error
    else: 
        error = 1.05*firstError;
        #print 'fail'
    return error

#plt.errorbar(times,data,yerr=sigmas,fmt='.')
#plt.plot(times,fitfunc(initParams))
#plt.show()
#<<<<<<< HEAD
bestFitP = optimize.leastsq(errfunc,initParams[:],args=(sigmas,data.astype(np.float64)),epsfcn=10*np.finfo(np.float64).eps,xtol=np.finfo(np.float64).eps,maxfev=100*100*(len(data)+1))[0]
#=======
bestFitP = optimize.leastsq(errfunc,initParams[:],args=(sigmas,data.astype(np.float64)),xtol=np.finfo(np.float64).eps,epsfcn=10*np.finfo(np.float64).eps,maxfev=100*(len(data)+1))[0]
#>>>>>>> 4ea13351c2cdb376c1132d08a75b082f840b0d23
if bestFitP[2] > 90: 180 - bestFitP[2]
print 'bestFitP:',bestFitP
fluxFit = np.copy(fitfunc(bestFitP)) ## THIS WORKS ONLY IF USING NP.COPY, OTHERWISE COMPUTE fitfunc(bestFitP) EACH TIME
residuals = fluxFit-data

###############################################################
## Use prayer-bead method to estimate uncertainties in fit params

if animatePB:   ## Show plot for each iteration in the prayer-bead algorithm?
	plt.ion()
	fig = plt.figure()

PBparameterTraces = np.zeros([len(fluxFit),len(bestFitP)])
for i in range(0,len(fluxFit)):
    if i == 0: 
        modelPlusResiduals = fluxFit + residuals
        shiftedSigmas = sigmas
    else: 
        modelPlusResiduals = fluxFit + shiftedResiduals # undifined name?!?!

    data = np.copy(modelPlusResiduals) 	## Add the shifted residuals to the best fit model
    bestFitP =  (1.0*np.array(bestFitP,dtype=np.float64)).tolist()
#<<<<<<< HEAD
    PBiterationBestFitPs = optimize.leastsq(errfunc,bestFitP[:],args=(shiftedSigmas,data.astype(np.float64)),epsfcn=10*np.finfo(np.float64).eps,xtol=np.finfo(np.float64).eps,maxfev=100*100*(len(data)+1))[0]
#=======
    PBiterationBestFitPs = optimize.leastsq(errfunc,bestFitP[:],args=(shiftedSigmas,data.astype(np.float64)),xtol=np.finfo(np.float64).eps,epsfcn=10*np.finfo(np.float64).eps,maxfev=100*(len(data)+1))[0]
#>>>>>>> 4ea13351c2cdb376c1132d08a75b082f840b0d23

    PBparameterTraces[i,:] = PBiterationBestFitPs	## record the best fit parameters
    shiftedResiduals = np.roll(residuals,i)		## shift the residuals over one, repeat
    shiftedSigmas = np.roll(sigmas,i)
    if animatePB:
        plt.clf()
        plt.title('Shifting residuals for prayer-bead analysis...')
        plt.plot(t,fluxFit,'r',linewidth=2.5)
        plt.errorbar(t,modelPlusResiduals,yerr=sigmas,fmt='bo')
        plt.plot(t,fitfunc(PBiterationBestFitPs),'g',linewidth=2.5)
        #plt.plot(fluxFit-fitfunc(PBiterationBestFitPs),linewidth=2)
        plt.draw()
if animatePB: plt.close()
uncertainties = np.std(PBparameterTraces,axis=0)	## Std of the best fits for each param is ~ the uncertainty on each param
plt.plot(PBparameterTraces[:,3])
plt.show()

print "\nLevenberg-Marquardt Least-Squares Fit:"
Nsigmas = np.abs(bestFitP - actualParams) / uncertainties
for i in range(len(bestFitP)):
	print "%s = %.4f +/- %.4f (True Value=%.4f; i.e. measured within %f sigma)" % (initParamNames[i],bestFitP[i],uncertainties[i],actualParams[i],Nsigmas[i])

#################################################################
## Plot the results

if plotFit:
	fig = plt.figure(figsize=(8,10))
	ax1 = fig.add_subplot(211)
	ax2 = fig.add_subplot(212,sharex=ax1)
	ax1.errorbar(t,data,yerr=sigmas,fmt='o',label='Data')
	ax1.plot(t,fitfunc(initParams),':',linewidth=3.5,label='Init params')
	ax1.plot(t,fluxFit,linewidth=2.5,label='Fit')
	ax1.set_title("Light Curve")
	
	ax2.errorbar(t,residuals,yerr=sigmas,fmt='o')
	ax2.set_title("Residuals")
	plt.show()

