import numpy as np
from matplotlib import pyplot as plt
import oscaar
from scipy import optimize
from numpy.random import shuffle
from oscaar.extras.knownSystemParameters import returnSystemParams

#Work below is from Nolan Matthews while relying on some of Brett Morris's
#code, particularly the transitModel.py,simulatedLightCurve.py, and
#modelLightCurve.py scripts. Additionally the light curve model used for fitting
#is Jason Eastman's occultquad function (Eastman et. al 2013) based on the analytical derivations
#from Mandel & Agol (2002) and using C implementation from Brett Morris.
#See the transitModel.py file for more info. 

#The script below allows two functionalities. There are some functions
#defined that allow the user to create a fake dataset. These were used
#to develop a random MC fitting routine which relies on the scipy
#function optimize.curve_fit. There is a tutorial on how to use the functions
#which can found at www.github.com/OSCAAR/oscaar/. The optimize.curve_fit tool uses a least square 
#Levenburg-Marquadt (sp?) algorithm. Caution should be taken to the inital
#guesses for the parameters as least sq. LM fitting typically will find
#a local minimum. One can find archival results using XXX.

#Make Fake Datasets using random number generator to test fitting function
def fake_data(stddev,RpRs,aRs,per,inc,midtrantime,gamma1,gamma2,ecc,argper):
    '''Takes in orbital and planetary parameters and simulates data using random gaussian fluctations.
    
    Parameters include,
    stddev - standard deviation of fake data.
    RpRs   - fractional planetary to stellar radius
    aRs    - semi-major axis/stellar radii
    per    - orbital period (days)
    inc    - inclination of orbital plane (degrees)
    midtrantime - mid-transit time (JD)
    gamma1 - linear limb-darkening coeff.
    gamma2 - quadrtic limb-darkening coeff
    argper - argument of pericenter
    '''
    
    #Define Times (in days) centered at mid-transit time. 
    expTime = 45./(3600*24.) #Set to be 45 sec., somewhat typical for observing.
    Nimages = 200. #Needs to be long enough to cover entire transit w/ some baseline. 
    times = np.arange(start=midtrantime-expTime*Nimages/2.,
                      stop=midtrantime+expTime*Nimages/2.,
                      step=expTime)

    #Creates Gaussian Distributed Data using numpy.random.normal function based on standard dev.
    
    #Uses alternate input parameters setup for occultquad.
    modelParams=[RpRs,aRs,per,inc,gamma1,gamma2,ecc,argper,midtrantime]
    perfect_data = oscaar.occultquad(times,modelParams)
    random_dist = np.random.normal(scale=stddev,size=np.size(times))
    fk_data = perfect_data + random_dist
    
    return times,fk_data

#Runs the intial fit using the LM least sq. algorithm. 
def run_LMfit(timeObs,NormFlux,flux_error,RpRsGuess,aRsGuess,incGuess,epochGuess,gamma1,gamma2,perGuess,eccGuess,argPerGuess,fitLimbDark=False,plotting=True):
    '''Fitting routine using the optimize.leastsq Levenburg-Marquardt least squares minimization.
    
    Input parameters include the time,flux,and uncertainty data series,
    
    timeObs: ndarray
        time data series
    NormFlux: ndarray
        flux data series
    flux_error: ndarray
        uncertainty on flux data series
    
    Type of limb-darkening law specified by the keyword argument,
    
    fitLimbDark: str or boolean
        False    - Assumes gamma1,gamma2 = 0, does not fit for limb-darkening coefficents.
        'linear' - Uses linear limb-darkening
        'quadratic'- Uses quadratic limb-darkening
        
    plotting: boolean
        Plots fit output w/ data.  
    
    Orbital and Stellar Parameters intial guesses,
    '''
    
    #Setting up inital guess, dependent on inclusion of limb-darkening
    if fitLimbDark == False:
        initGuess = (RpRsGuess,aRsGuess,incGuess,epochGuess)
    elif fitLimbDark == 'linear':
        initGuess = (RpRsGuess,aRsGuess,incGuess,epochGuess,gamma1)
    elif fitLimbDark == 'quadratic':
        initGuess = (RpRsGuess,aRsGuess,incGuess,epochGuess,gamma1,gamma2)
    
    def occultquadForTransiter(t,p,ap,i,t0,gamma1=0.0,gamma2=0.0,P=perGuess,e=eccGuess,longPericenter=0.0):
        modelParams = [p,ap,P,i,gamma1,gamma2,e,longPericenter,t0]
        return oscaar.occultquad(t,modelParams)

    #Runs the inital fit
    fit,success=optimize.curve_fit(occultquadForTransiter,
                                   xdata=timeObs,
                                   ydata=NormFlux,
                                   p0=initGuess,
                                   sigma=flux_error,
                                   maxfev=10000,
                                   xtol=2e-15,
                                   ftol=2e-16,
                                   #diag=(0.05,0.1,0.1,500.,0.1,0.1),
                                   #factor=100.
                                   )

    #Check for Convergence    
    if type(success) != np.ndarray:
        print "The inital fit was not able to converge. Check to see if the input parameters are accurate."
        print ""
        
    #If Convergence is True, look at the results to double check.
    else:
        print "Results from the inital fit w/ uncertainties based on the sq. root of the covariance matrix"
        params = ["Rp/Rs","a/Rs","inc","Mid-Tran Time","Gamma 1","Gamma 2"]
        for i in range(0,np.size(fit)):
            print params[i],fit[i],"+/-",np.sqrt(success[i][i])
        print ""
        
    #Visually check to see if it's reasonable
    if plotting == True:
        if fitLimbDark == False:
            plt.plot(timeObs,occultquadForTransiter(timeObs,fit[0],fit[1],fit[2],fit[3]))
        elif fitLimbDark == 'linear':
            plt.plot(timeObs,occultquadForTransiter(timeObs,fit[0],fit[1],fit[2],fit[3],fit[4]))            
        elif fitLimbDark == 'quadratic':
            plt.plot(timeObs,occultquadForTransiter(timeObs,fit[0],fit[1],fit[2],fit[3],fit[4],fit[5]))            
        
        plt.plot(timeObs,NormFlux,'o')
        plt.title('Result from initial LM Fit')
        plt.xlabel('JD (d)')
        plt.xlim(xmin=timeObs[0],xmax=timeObs[len(timeObs)-1])
        plt.show()
        plt.close()
    
    return fit,success
    
#Run Prayer-Bead or Random Markov Chain to estimate uncertainties.

#Shuffle Function, had to be modded for data type reasons.
def shuffle_func(x):
    shuffle(x)
    return x

#Function that allows one to determine model uncertainties using a random
#Monte Carlo method. 
def run_MCfit(n_iter,timeObs,NormFlux,flux_error,fit,success,perGuess,eccGuess,argPerGuess,plotting=False):

    def occultquadForTransiter(t,p,ap,i,t0,gamma1=0.0,gamma2=0.0,P=perGuess,e=eccGuess,longPericenter=argPerGuess):
        modelParams = [p,ap,P,i,gamma1,gamma2,e,longPericenter,t0]
        return oscaar.occultquad(t,modelParams)
    
    RpFit,aRsFit,incFit,epochFit = fit[0],fit[1],fit[2],fit[3]
    
    #Create model, dependent on inclusion of limb-darkening
    if len(fit) == 4:
        modelOut  = occultquadForTransiter(timeObs,fit[0],fit[1],fit[2],fit[3])
        initGuess = (fit[0],fit[1],fit[2],fit[3])
    elif len(fit) == 5:
        modelOut  = occultquadForTransiter(timeObs,fit[0],fit[1],fit[2],fit[3],fit[4])
        initGuess = (fit[0],fit[1],fit[2],fit[3],fit[4])
        gam1Fit = fit[4]
    elif len(fit) == 6:
        modelOut  = occultquadForTransiter(timeObs,fit[0],fit[1],fit[2],fit[3],fit[4],fit[5])
        initGuess = (fit[0],fit[1],fit[2],fit[3],fit[4],fit[5])
        gam1Fit,gam2Fit = fit[4],fit[5]
    
    residuals = NormFlux - modelOut
    
    #Generate random datasets based on residuals from inital fit. 
    n_sets = n_iter
    Rp,aRs,inc,mid,gam1,gam2=[],[],[],[],[],[]
    for i in range(0,n_sets):
    
        #Randomly shuffling both data/uncertainties together 
        MCset,randSet,SigSet = [],[],[]
        index_shuf = range(len(residuals))
        shuffle(index_shuf)
        for i in index_shuf:
            MCset.append(residuals[i])
            SigSet.append(flux_error[i])
        
        #Generate random dataset and fit to the function.
        randSet = MCset + modelOut
        fit,success=optimize.curve_fit(occultquadForTransiter,
                                    xdata=timeObs,
                                   ydata=randSet,
                                   p0=initGuess,
                                   maxfev=100000,
                                   sigma=SigSet,
                                   #diag=(0.1,0.1,0.1,1.0,0.1,0.1),
                                   #factor=100.,
                                   xtol=2e-15,
                                   ftol=2e-16,
                                   )
        
        #Save output parameters from fit
        Rp.append(fit[0])
        aRs.append(fit[1])
        inc.append(fit[2])
        mid.append(fit[3])
        if len(fit) == 5 or len(fit) == 6:
            gam1.append(fit[4])
        if len(fit) == 6:
            gam2.append(fit[5])
            
        if plotting == True:
            if len(fit) == 4:
                plt.plot(timeObs,occultquadForTransiter(timeObs,fit[0],fit[1],fit[2],fit[3]))
            elif len(fit) == 5:
                plt.plot(timeObs,occultquadForTransiter(timeObs,fit[0],fit[1],fit[2],fit[3],fit[4]))
            elif len(fit) == 6:
                plt.plot(timeObs,occultquadForTransiter(timeObs,fit[0],fit[1],fit[2],fit[3],fit[4],fit[5]))

    #Visually compare MC fits to inital fit and observational data.
    if plotting == True:
        plt.errorbar(timeObs,NormFlux,yerr=flux_error,linestyle='None',marker='.',label="Data")
        
        if len(fit) == 4:
            plt.plot(timeObs,occultquadForTransiter(timeObs,RpFit,aRsFit,incFit,epochFit),
                     lw=2.0,color='k',label="Inital Fit")
        elif len(fit) == 5:
            plt.plot(timeObs,occultquadForTransiter(timeObs,RpFit,aRsFit,incFit,epochFit,gam1Fit),
                     lw=2.0,color='k',label="Inital Fit")
        elif len(fit) == 6:
            plt.plot(timeObs,occultquadForTransiter(timeObs,RpFit,aRsFit,incFit,epochFit,gam1Fit,gam2Fit),
                     lw=2.0,color='k',label="Inital Fit")
        plt.title('Results from Random MC Fits')
        plt.xlabel('JD (days)')
        plt.ylabel('Normalized Flux')
        plt.xlim(xmin=timeObs[0],xmax=timeObs[len(timeObs)-1])
        plt.legend(loc=7)
        plt.show()
        plt.close()
        plt.clf()
        
    print "Results from random MC fit . . . . . "     
    print "Planetary to Stellar Radius: ",np.mean(Rp),"+/-",np.std(Rp)
    print "Semi-major Axis to Stellar Radius: ",np.mean(aRs),"+/-",np.std(aRs)
    print "Inclination of Orbit: ",np.mean(inc),"+/-",np.std(inc)
    print "Mid-Transit Time [JD]: ",np.mean(mid),"+/-",np.std(mid)
    if len(fit) == 5 or len(fit) == 6:
        print "Gamma 1: ",np.mean(gam1),"+/-",np.std(gam1)
    if len(fit) == 6:
        print "Gamma 2: ",np.mean(gam2),"+/-",np.std(gam2)
        
    return Rp,aRs,inc,mid,gam1,gam2