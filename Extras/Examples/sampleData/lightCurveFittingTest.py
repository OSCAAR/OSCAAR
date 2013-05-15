
import numpy as np
import ctypes
from matplotlib import pyplot as plt
from scipy import optimize

'''
	Compile the c/transit1forLMLS.c file with:
		$ gcc -shared -o transit1forLMLS.so transit1forLMLS.c -framework Python
	in the OSCAAR/Code/c/ directory.

	Constraining inclination on 0=<i=<180 so that we're not always trapped up against the limiting case near
	i=90, but converting saved value into standard 0<=i<=90 form.

	Successor to test3e.py. Notes from that file: 

	   This set of fixed parameters may yield the most reliable measurements for
	   a/R_s, R_p/R_s, i and t_0. Produces successful fits over a wide range of 
	   noisiness in the false data.
'''

## Resources on using ctypes:
# http://docs.python.org/2/library/ctypes.html#ctypes.c_float
# http://www.scipy.org/Cookbook/Ctypes#head-0c422ad0dcf3a37f8c16d4cfd85e37e1f7290214
# http://docs.scipy.org/doc/numpy/reference/routines.ctypeslib.html


## Run parameters: 
plotFit = True		## Plot light curve fit
animatePB = False 	## Plot each prayer-bead iteration

## Set the system properties
Npoints = 200;
p = 0.1179;				## R_p/R_s
ap = 14.71;				## a/R_s
P = 1.580400; 			## Period
i = 87.0;				## Inclination (degrees)
gamma1 = 0.20;			## linear limb-darkening
gamma2 = 0.20;			## quad limb-darkening
e = 0.00;				## eccentricity
longPericenter = 0.0; 	## Longitude of pericenter
t0 = 0.003;				## midtransit time
n = Npoints;				## number of points in light curve
percentOfOrbit = 2.0;	## phase range to plot over (*100)


###################################################################################################
## Ctypes definitions from C-libraries
lib = np.ctypeslib.load_library('c/transit1forLMLS','.') 	## Loads transit1torturetest.so as a library
occultquad = lib.occultquad
occultquad.argtypes = [np.ctypeslib.ndpointer(np.float32,flags='aligned,C_CONTIGUOUS'),	#t
						  # np.ctypeslib.ndpointer(np.float32,flags='aligned,C_CONTIGUOUS'),	#phi
						   ctypes.c_float,	# p
						   ctypes.c_float,	# ap
						   ctypes.c_float,	# P
						   ctypes.c_float,	# i
						   ctypes.c_float,	# gamma1
						   ctypes.c_float,	# gamma2
						   ctypes.c_double,	# e
						   ctypes.c_double, # longPericenter
						   ctypes.c_double, # t0
						   ctypes.c_float,	# n
						   np.ctypeslib.ndpointer(np.float32,flags='aligned,C_CONTIGUOUS')]	# F
## argtypes defines what each function argument's type will be using the numpy.ctypeslib and ctypes libraries. 
## NOTE!: If vector input is going to be a vector of C-floats, use np.ctypeslib.ndpointer(np.float32,flags='aligned,C_CONTIGUOUS')
##        If vector input is going to be a vector of C-doubles, use np.ctypeslib.ndpointer(np.float64,flags='aligned,C_CONTIGUOUS')

## The arguments of occultquad are: occultquad(float *t, float *phi, float p, float ap, float P, float i, float gamma1, 
##											   float gamma2, double e, double longPericenter, double t0, float n, float *F);

occultquad.restype = None	## Put the return type of the function here. If "return void" in C func, restype=None

#################################################################
## Create simulated data to try to fit

## The "Npoints" arguement in the definition of `t` in the main() function of the .c code 
## indicates the number of points, but the equivalent argument in np.arange() is the
## increment size between points. Calculate the interval between the points
## by dividing the range of points over the number of points within the range
NpointsInT = (P*percentOfOrbit/100.0 - -1.0*P*percentOfOrbit/100.0)/Npoints	
t = np.arange(-1.0*P*percentOfOrbit/100.0,P*percentOfOrbit/100.0,NpointsInT,dtype=np.float32)

## np.require() will force the ndarrays to the right dtype as assigned in the `argtypes` list.
t = np.require(t,np.float32)
F = np.empty_like(t,dtype=np.float32)
occultquad(t, p,  ap,  P,  i,  gamma1,  gamma2, e,longPericenter, t0,  n,  F)	## Simulate fake data

simulatedUncertainty = 5e-3#5e-3
fakeData = np.copy(F) + np.random.normal(0,simulatedUncertainty,len(F))
sigmas = np.zeros_like(F) + simulatedUncertainty

# Enter Initial Parameters to vary
initParamNames = ['R_p/R_s','a/R_s','inc','t_0']
initParams = [1.0*p,  1.0*ap, 1.0*i,  -1.0*t0]
actualParams = [p, ap, i, t0]
data = fakeData

def fitfunc(p,t=t,P=P,gamma1=gamma1,gamma2=gamma2,e=e,longPericenter=longPericenter):
    '''Fixed parameters: P, gamma1, gamma2, e, longPericenter
       Constraints: 0<=inclination<=90, but to prevent the leastsq algorithm from getting penalized
       for inclinations near 90, allow it to vary over range (0,180), and if a value is submitted > 90,
       then subtract it from 180 to return a value on 0=<i<90'''
    if p[2] >= 0 and p[2] <= 180:
    	if p[2] > 90: p[2] = 180 - p[2] ## 90 - (p[2] - 90)
        occultquad(t,p[0],p[1],P,p[2],gamma1,gamma2,e,longPericenter,p[3],n,F)
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
residuals = fluxFit-fakeData


###############################################################
## Use prayer-bead method to estimate uncertainties in fit params

if animatePB:
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
	ax1.errorbar(t,fakeData,yerr=sigmas,fmt='o',label='Data')
	ax1.plot(t,fitfunc(initParams),':',linewidth=3.5,label='Init params')
	ax1.plot(t,fluxFit,linewidth=2.5,label='Fit')
	ax1.set_title("Light Curve")
	
	ax2.errorbar(t,residuals,yerr=sigmas,fmt='o')
	ax2.set_title("Residuals")
	plt.show()

