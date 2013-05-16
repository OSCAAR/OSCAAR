'''
	Open the data pickle generated after running oscaar and 
    do a L-M least-squares fit to the light curve. Calculate
    uncertainties in the extracted system parameters with the
    prayer-bead method.
'''

import numpy as np
import ctypes
from matplotlib import pyplot as plt
from scipy import optimize

## Import oscaar directory using relative paths
import os, sys
lib_path = os.path.abspath('../../../Code/')
sys.path.append(lib_path)
import oscaar

## Run parameters: 
plotFit = True		## Plot light curve fit
animatePB = False 	## Plot each prayer-bead iteration

dataBank = oscaar.load("../../../outputs/oscaarDataBase.pkl")
t = times = dataBank.getTimes()
F = dataBank.lightCurve
Npoints = len(t)
n = Npoints

## np.require() will force the ndarrays to the right dtype as assigned in the `argtypes` list.
t = np.require(t,np.float64)
#F = np.empty_like(t,dtype=np.float32)
#occultquad(t, p,  ap,  P,  i,  gamma1,  gamma2, e,longPericenter, t0,  n,  F)	## Simulate fake data

simulatedUncertainty = 2e-3#5e-3
sigmas = np.zeros_like(F) + simulatedUncertainty

# Enter Initial Parameters to vary
initParamNames = ['R_p/R_s','a/R_s','inc','t_0']
actualParams = [0.1179,14.71,90.0,np.mean(times)]
p = 0.1179
ap = 14.71
P = 1.580400
i = 90.0
gamma1 = 0.23
gamma2 = 0.30
e = 0
longPericenter = 0.00
t_0 = np.mean(times)
initParams = [ p, ap, i, np.mean(times,dtype=np.float64)]
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
        F = oscaar.occultquad(times,modelParams)
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
    if fitfunc(p) != None:      
        error = (fitfunc(p) - y)/uncertainties
        if all(p == initParams): firstError = error
        #lastSuccessfulError = error
    else: error = 1.05*firstError;
    return error

bestFitP = optimize.leastsq(errfunc,initParams[:],args=(sigmas,data.astype(np.float64)),epsfcn=np.finfo(np.float32).eps,maxfev=100*100*(len(data)+1))[0]
if bestFitP[2] > 90: 180 - bestFitP[2]

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
		modelPlusResiduals = fluxFit + shiftedResiduals
	
	data = modelPlusResiduals 	## Add the shifted residuals to the best fit model
	PBiterationBestFitPs = optimize.leastsq(errfunc,bestFitP[:],args=(sigmas,data.astype(np.float64)),epsfcn=np.finfo(np.float32).eps,maxfev=100*100*(len(data)+1))[0]
	PBparameterTraces[i,:] = PBiterationBestFitPs	## record the best fit parameters
	shiftedResiduals = np.roll(residuals,i)		## shift the residuals over one, repeat
	shiftedSigmas = np.roll(sigmas,i)
	
	if animatePB:
		plt.clf()
		plt.title('Shifting residuals for prayer-bead analysis...')
		plt.plot(t,fluxFit,'r',linewidth=2.5)
		plt.errorbar(t,modelPlusResiduals,yerr=sigmas,fmt='bo')
		plt.draw()
if animatePB: plt.close()
uncertainties = np.std(PBparameterTraces,axis=0)	## Std of the best fits for each param is ~ the uncertainty on each param

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

