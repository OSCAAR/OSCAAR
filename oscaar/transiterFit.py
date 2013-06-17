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
#Levenburg-Marquadt (sp?) algorithm. Caution should be taken to the initial
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

#Runs the initial fit using the LM least sq. algorithm. 
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
    
    #Hack for if inclination is entered as 90 degrees. This must be done so that the optimize.curve_fit tool
    #has room to find a solution. Since we have a constraint on inclination < 90.0 if we start at a number close
    #90.0 and the first guess for a new inclination is above 90.0 it may throw off the fitting algorithm.
    
    #Since eccentricity is generally not constrained well for values below a degree or so,
    #(expection of extremely high quality data) this is alright to do, though not optimal. In any case, for
    #better error estimation one should use MCMC not least square minimization.
    if incGuess == 90.0:
        incGuess=89.8
    
    RpRsGuess=np.float64(RpRsGuess)
    aRsGuess=np.float64(aRsGuess)
    perGuess=np.float64(perGuess)
    incGuess=np.float64(incGuess)
    epochGuess=np.float64(epochGuess)
    gamma1=np.float64(gamma1)
    gamma2=np.float64(gamma2)
    eccGuess=np.float64(eccGuess)
    argPerGuess=np.float64(argPerGuess)
    
    #Setting up initial guess, dependent on inclusion of limb-darkening
    if fitLimbDark == False:
        initGuess = (RpRsGuess,aRsGuess,incGuess,epochGuess)
    elif fitLimbDark == 'linear':
        initGuess = (RpRsGuess,aRsGuess,incGuess,epochGuess,gamma1)
    elif fitLimbDark == 'quadratic':
        initGuess = (RpRsGuess,aRsGuess,incGuess,epochGuess,gamma1,gamma2)
    
    def occultquadForTransiter(t,p,ap,i,t0,gamma1=gamma1,gamma2=gamma2,P=perGuess,e=eccGuess,longPericenter=0.0):
        '''Defines oscaar.occultquad differently to be compatible w/ optimize.curve_fit
        
        If a parameter goes outside physical boundries then it returns
        an array of zeros, such that the chi squared value is extremely high.
        
        Constraints:
        Limb-darkening Coeff's -- 0.0 < gamma < 1.0
        Inclination < 90 degrees
        Impact Parameter < 1 (assumes no grazing transits)
        '''
        
        b=ap*np.cos(i)
        if b > 1.0 or i > 90.0 or gamma1 < 0.0 or gamma1 > 1.0:
            return np.zeros(len(t))
        elif gamma2 < 0.0 or gamma2 > 1.0:
            return np.zeros(len(t))
        else:
            modelParams = [p,ap,P,i,gamma1,gamma2,e,longPericenter,t0]
            return oscaar.occultquad(t,modelParams)

    #Runs the initial fit
    fit,success=optimize.curve_fit(occultquadForTransiter,
                                   xdata=timeObs.astype('float64'),
                                   ydata=NormFlux.astype('float64'),
                                   p0=initGuess,
                                   sigma=0.01*flux_error.astype('float64'),
                                   maxfev=100000,
                                   xtol=np.finfo(np.float64).eps,
                                   ftol=np.finfo(np.float64).eps,
                                   #epsfcn=0.00001,
                                   #diag=(1.0,1.0,1.0,1.0,1.0,1.0),
                                   factor=0.3
                                   )

    #Check for Convergence    
    if type(success) != np.ndarray:
        print "The initial fit was not able to converge. Check to see if the input parameters are accurate."
        print ""
    
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
     
    #If Convergence is True, look at the results to double check.
    residual = modelOut - timeObs
    print "Results from the initial fit"
    params = ["Rp/Rs","a/Rs","inc","Mid-Tran Time","Gamma 1","Gamma 2"]
    for i in range(0,np.size(fit)):
        print params[i],fit[i]
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
def run_MCfit(n_iter,timeObs,NormFlux,flux_error,fit,success,perGuess,eccGuess,argPerGuess,gamma1=0.0,gamma2=0.0,plotting=False):

    
    #Sets up occultquadForTransiter to be minimized based on limb-darkening choice. 
    if len(fit)==4:
        def occultquadForTransiter(t,p,ap,i,t0,gamma1=gamma1,gamma2=gamma2,P=perGuess,e=eccGuess,longPericenter=0.0):
            b=ap*np.cos(i)
            if b > 1.0 or i > 90.0 or gamma1 < 0.0 or gamma1 > 1.0:
                return np.zeros(len(t))
            elif gamma2 < 0.0 or gamma2 > 1.0 or i < 75.0:
                return np.zeros(len(t))
            else:
                modelParams = [p,ap,P,i,gamma1,gamma2,e,longPericenter,t0]
                return oscaar.occultquad(t,modelParams)
    elif len(fit)==5:
        def occultquadForTransiter(t,p,ap,i,t0,gamma1=fit[4],gamma2=gamma2,P=perGuess,e=eccGuess,longPericenter=0.0):
            b=ap*np.cos(i)
            if b > 1.0 or i > 90.0 or gamma1 < 0.0 or gamma1 > 1.0:
                return np.zeros(len(t))
            elif gamma2 < 0.0 or gamma2 > 1.0 or i < 75.0:
                return np.zeros(len(t))
            else:
                modelParams = [p,ap,P,i,gamma1,gamma2,e,longPericenter,t0]
                return oscaar.occultquad(t,modelParams)        
    elif len(fit)==6:
        def occultquadForTransiter(t,p,ap,i,t0,gamma1=fit[4],gamma2=fit[5],P=perGuess,e=eccGuess,longPericenter=0.0):
            b=ap*np.cos(i)
            if b > 1.0 or i > 90.0 or gamma1 < 0.0 or gamma1 > 1.0:
                return np.zeros(len(t))
            elif gamma2 < 0.0 or gamma2 > 1.0 or i < 75.0:
                return np.zeros(len(t))
            else:
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
                                   #epsfcn=0.1,
                                   factor=0.3,
                                   xtol=2e-15,
                                   ftol=2e-15,
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
        
    print '''Results from bootstrap MC fit . . . . .
    
Uncertainties are calculated by standard deviation of the different fits using the bootstrap MC method.
    
    '''
    print "Planetary to Stellar Radius: ",np.mean(Rp),"+/-",np.std(Rp)
    print "Semi-major Axis to Stellar Radius: ",np.mean(aRs),"+/-",np.std(aRs)
    print "Inclination of Orbit: ",np.mean(inc),"+/-",np.std(inc)
    print "Mid-Transit Time [JD]: ",np.mean(mid),"+/-",np.std(mid)
    if len(fit) == 5 or len(fit) == 6:
        print "Gamma 1: ",np.mean(gam1),"+/-",np.std(gam1)
    if len(fit) == 6:
        print "Gamma 2: ",np.mean(gam2),"+/-",np.std(gam2)
        
    return Rp,aRs,inc,mid,gam1,gam2

def calcMidTranTime(times,flux):
    '''Estimates mid-transit time by extracting the minimum of differently binned datasets'''
    
    #For binning of sets from 5 - 15 data points calculate minimum
    midEstimate=np.zeros(10)
    for i in range(0,10):
        binnedTime,binnedFlux=oscaar.medianBin(times,flux,medianWidth=i+5)[0:2]
        idx = (abs(binnedFlux-binnedFlux.min())).argmin()
        midEstimate[i]=binnedTime[idx]
    return midEstimate.mean()
