'''
Markov Chain Monte Carlo fitting routine for transit light curve
fitting and uncertainty analysis as laid out by Ford (2005).

Created by Brett Morris, with inspiration from Evan Sinukoff
'''
import os
import numpy as np
from matplotlib import pyplot as plt
from scipy import optimize
import oscaar

def fitLinearTrend(xVector,yVector):
	'''Fit a line to the set {xVectorCropped,yVectorCropped}, then remove that linear trend
	   from the full set {xVector,yVector}'''
	print 'linearTrend'
	initP = [0.0,0.0]
	fitfunc = lambda p, x: p[0]*x + p[1]
	errfunc = lambda p, x, y: (fitfunc(p,x) - y)
	
	bestFitP = optimize.leastsq(errfunc,initP[:],args=(xVector,yVector))[0]
	return bestFitP

def linearFunc(xVector,params):
	return xVector*params[0] + params[1]

    
def mcmc(t,flux,sigma,initParams,func,Nsteps,beta,saveInterval,verbose=False):
    '''
        Markov Chain Monte Carlo for a set of fluxes `flux` at times `t`
        with uncertainties `sigma`. Input fitting function `func` is fed
        initial parameters `initParams` and iterated through the chains
        a total of `Nsteps` times, randomly sampled from normal distributions
        with widths `beta`, and every `saveInterval`-th state in the chain 
        is saved for later analysis.

       :INPUTS: 
            t 		-- time (vector)
            flux 	-- fluxes (vector)
            sigma 	-- uncertainties in fluxes (vector)
            initParams	-- initial parameter estimates, `x_0` in Ford 2005 (vector)
            func	-- fitting function (function)
            Nsteps	-- number of iterations (int)
            beta	-- widths of normal distribution to randomly sample for each parameter (vector)
            saveInterval 	-- number of steps between "saves" (int)
            
        :OUTPUTS:
            bestp 		-- parameters at minimum chi^2
            x_0toN	-- trace of each parameter at each save step

        :Notes:
         * Developed by Brett Morris (NASA-GSFC/UMD)	
         * Based on the theory codified by Ford 2005 in The Astronomical Journal, 129:1706-1717
         * Code implementation partly influenced by Ian Crossfield's routines: 
                http://www.mpia-hd.mpg.de/homes/ianc/python/transit.html
    
    '''
    
    Nsteps = int(Nsteps)			## Type cast where necessary
    saveInterval = int(saveInterval)
    assert Nsteps % saveInterval == 0, ("Must choose integer number of `saveInterval`s in `Nsteps`. "+\
                 "Currently: Nsteps %% saveInterval = %.2f (should be zero)" % (Nsteps % saveInterval))
    acceptedStates = 0
    nout = Nsteps/saveInterval
    
    ## Metropolis-Hastings algorithm...
    x_n = initParams ## initial trial state, **Step 1 in Ford 2005**, n=0
    weights = 1./sigma**2
    x_0toN = np.zeros([len(x_n),nout],dtype=float)
    allchi = np.zeros(nout,dtype=float)
    bestp = None
    
    ## Compute chi^2 using initial params
    trialModel = func(t,x_n)
    chisq_n = np.sum(((trialModel-flux)**2)*weights)
    chisq_min = 1e10#chisq_n
    for n in range(Nsteps):
        ## Generate trial step in parameters, **Step 2 in Ford 2005**
        x_nplus1 = np.random.normal(x_n,beta) 	
            ## ^^^ Sample gaussians with widths `beta` randomly centered 
            ##        about each parameter in `params`
            
        ## Should hold fixed constants and ensure pos-def here (not implementing)
        trialModel = func(t,x_nplus1)
        
        ## Calculate chisq for current step **Step 3 in Ford 2005**
        chisq_nplus1 = np.sum(((trialModel-flux)**2)*weights)	
        
        ## Ratio of probability distributions, Eq. 9 of Ford 2005;  **Step 4 in Ford 2005**
        ratioOfProbDist = np.exp((chisq_n - chisq_nplus1)/2.0)	
        alpha = np.min([ratioOfProbDist,1])## Eq. 11 in Ford 2005
        
        u = np.random.uniform(0,1)		## Draw random number on (0,1), **Step 5 in Ford 2005**
        if u <= alpha:					## If u<=alpha, accept this state
            x_n = np.copy(x_nplus1)
            chisq_n = chisq_nplus1
            acceptedStates += 1
        #elif u > alpha: x_nplus1 = x_n	## Implicit, commented out
        
        if chisq_nplus1 < chisq_min:	## If this chisq is minimum, record it
            bestp = np.copy(x_n)
            chisq_min = chisq_n
            
        if n % saveInterval == 0: 		## Every `saveInterval`-th state, save it
            if verbose: print "Step",n,"of",Nsteps
            x_0toN[:,n/saveInterval] = np.copy(x_n)
            allchi[n/saveInterval] = chisq_n

    ## Calculate acceptance rate, should ideally be ~0.44 (Ford 2005)
    acceptanceRate = float(acceptedStates)/Nsteps	

    assert bestp is not None, "No best-fit found, chi^2 minimizing state not found"
    return bestp, x_0toN, acceptanceRate


def mcmc_iterate(t,flux,sigma,initParams,func,Nsteps,beta,saveInterval,verbose=False):
    '''
        MCMC routine specifically for optimizing the beta parameters with 
        optimizeBetas(). Will randomly perturb individual initial parameters
        within certain physical limits and calculate acceptance rates of each
        trial beta parameter. optimizeBetas() then uses these rates to determine
        if the next trial beta should be larger or smaller in order to make the
        acceptance rates for each parameter tend towards the ideal range between
        0.25 and 0.55, or near ~0.44, as codified by Ford 2005.
    
        Description of MCMC from mcmc(): 
        Markov Chain Monte Carlo for a set of fluxes `flux` at times `t`
        with uncertainties `sigma`. Input fitting function `func` is fed
        initial parameters `initParams` and iterated through the chains
        a total of `Nsteps` times, randomly sampled from normal distributions
        with widths `beta`, and every `saveInterval`-th state in the chain 
        is saved for later analysis.

       :INPUTS: 
            t 		-- time (vector)
            flux 	-- fluxes (vector)
            sigma 	-- uncertainties in fluxes (vector)
            initParams	-- initial parameter estimates, `x_0` in Ford 2005 (vector)
            func	-- fitting function (function)
            Nsteps	-- number of iterations (int)
            beta	-- widths of normal distribution to randomly sample for each parameter (vector)
            saveInterval 	-- number of steps between "saves" (int)
            
        :OUTPUTS:
            acceptanceRateArray	-- Array of acceptance rates for each beta_mu

        :Notes:
         * Developed by Brett Morris (NASA-GSFC/UMD)	
         * Based on the theory codified by Ford 2005 in The Astronomical Journal, 129:1706-1717
         * Code implementation partly influenced by Ian Crossfield's routines: 
                http://www.mpia-hd.mpg.de/homes/ianc/python/transit.html
    
    '''
    Niterations = 5*len(initParams)#20 ##40000	## Hard coded in Evan's code as 4e4

    
    ## Change one of the initial parameters at random per each iteration
    randomInitParamIndex = np.floor(np.random.uniform(0,len(initParams),Niterations))	## array of random indices of initParams
    NacceptancesPerParameter = np.zeros(len(initParams))	## initialize arrays
    #NstepsPerParameter = np.zeros(len(initParams)) + Nsteps*Niterations
    NstepsPerParameter = np.zeros(len(initParams))
    originalInitParams = np.copy(initParams)
    for i in range(Niterations):
        initParams = originalInitParams
        #print "Iteration",i,"of",Niterations
        testParamIndex = randomInitParamIndex[i]	## This initParam index will be tested
        
        ## Only use physically valid parameters, for this example, make up validity rules:
        ## Keep slope between -0.2<m<0.2 and int between 0.0<intercept<1.0
        continueTag = True
        #while initParams[0] > 0.2 or initParams[0] < -0.2 or initParams[1] > 1.0 or initParams[1] < 0.0 or continueTag:
        #	initParams[testParamIndex] += np.random.normal(0,1)*beta[testParamIndex]			## np.random.normal(0,1) is equivalent to the IDL: randomn(seed,1)
        #	continueTag = False
        initParams[testParamIndex] += np.random.normal(0,1)*beta[testParamIndex]
        
        Nsteps = int(Nsteps)			## Type cast where necessary
        saveInterval = int(saveInterval)
        assert Nsteps % saveInterval == 0, ("Must choose integer number of `saveInterval`s in `Nsteps`. "+\
                     "Currently: Nsteps %% saveInterval = %.2f (should be zero)" % (Nsteps % saveInterval))
        acceptedStates = 0
        nout = Nsteps/saveInterval
        
        ## Metropolis-Hastings algorithm...
        x_n = initParams ## initial trial state, **Step 1 in Ford 2005**, n=0
        weights = 1./sigma**2
        x_0toN = np.zeros([len(x_n),nout],dtype=float)
        allchi = np.zeros(nout,dtype=float)
        bestp = None
        
        ## Compute chi^2 using initial params
        trialModel = func(t,x_n)
        chisq_n = np.sum(((trialModel-flux)**2)*weights)
        chisq_min = 1e10#chisq_n
        for n in range(Nsteps):
            ## Generate trial step in parameters, **Step 2 in Ford 2005**
            x_nplus1 = np.random.normal(x_n,beta) 	
                ## ^^^ Sample gaussians with widths `beta` randomly centered 
                ##        about each parameter in `params`
                
            ## Should hold fixed constants and ensure pos-def here (not implementing)
            trialModel = func(t,x_nplus1)
            
            ## Calculate chisq for current step **Step 3 in Ford 2005**
            chisq_nplus1 = np.sum(((trialModel-flux)**2)*weights)	
            
            ## Ratio of probability distributions, Eq. 9 of Ford 2005;  **Step 4 in Ford 2005**
            ratioOfProbDist = np.exp((chisq_n - chisq_nplus1)/2.0)	
            alpha = np.min([ratioOfProbDist,1])## Eq. 11 in Ford 2005
            
            u = np.random.uniform(0,1)		## Draw random number on (0,1), **Step 5 in Ford 2005**
            if u <= alpha:					## If u<=alpha, accept this state
                x_n = np.copy(x_nplus1)
                chisq_n = chisq_nplus1
                acceptedStates += 1
                NacceptancesPerParameter[testParamIndex] += 1
            NstepsPerParameter[testParamIndex] += 1
            #elif u > alpha: x_nplus1 = x_n	## Implicit, commented out
            
            if chisq_nplus1 < chisq_min:	## If this chisq is minimum, record it
                bestp = np.copy(x_n)
                chisq_min = chisq_n
                
            if n % saveInterval == 0: 		## Every `saveInterval`-th state, save it
                if verbose: print "Step",n,"of",Nsteps
                x_0toN[:,n/saveInterval] = np.copy(x_n)
                allchi[n/saveInterval] = chisq_n
    
        ## Calculate acceptance rate, should ideally be ~0.44 (Ford 2005)
        acceptanceRate = float(acceptedStates)/Nsteps	
    
        assert bestp is not None, "No best-fit found, chi^2 minimizing state not found"
        #return bestp, x_0toN, acceptanceRate
    acceptanceRateArray = NacceptancesPerParameter/NstepsPerParameter 
    return acceptanceRateArray


def optimizeBeta(t,flux,sigma,initParams,func,beta):
    '''
        The `beta` input parameters for the MCMC function determine the 
        acceptance rate of the Metropolis-Hastings algorithm. According
        to Ford 2005, the ideal acceptance rate is ~0.25 - ~0.44. This routine
        will generate optimized `beta` parameters that will produce
        good acceptance rates.
    
       :INPUTS: 
            t 		-- time (vector)
            flux 	-- fluxes (vector)
            sigma 	-- uncertainties in fluxes (vector)
            initParams	-- initial parameter estimates, `x_0` in Ford 2005 (vector)
            func	-- fitting function (function)
            Nsteps	-- number of iterations (int)
            beta	-- widths of normal distribution to randomly sample for each parameter (vector)
            saveInterval 	-- number of steps between "saves" (int)
            
        :OUTPUTS:
            bestp 		-- parameters at minimum chi^2
            x_0toN	-- trace of each parameter at each save step

        :Notes:
         * Developed by Brett Morris (NASA-GSFC/UMD)	
         * Based on the theory codified by Ford 2005 in The Astronomical Journal, 129:1706-1717
         * Code implementation partly influenced by Evan Sinukoff's MCMC_Evan_Master_v3_new22.pro
    '''
    
    Nsteps = len(initParams)*100.0      ## do N iterations per parameter
    saveInterval = 50.0					## Save every Nth step
    acceptanceRateArray = mcmc_iterate(t,flux,sigma,initParams,func,Nsteps,beta,saveInterval,verbose=False)

    idealAcceptanceRate = 0.25			## Good rates according to Ford 2005: 0.25 - 0.44
    
    for paramIndex in range(0,len(initParams)):	## For each random parameter to be changed,
        iterationCounter = 0		## Count how many times the while loop has been run
        while any(acceptanceRateArray > 1.1*idealAcceptanceRate) or any(acceptanceRateArray < 0.9*idealAcceptanceRate):	## While the acceptance rate is unacceptable (Ford 2005), 
            assert iterationCounter<1e4,"After 10000 trials, the input beta parameters can not be optimized"

            ## Calculate the acceptance rates for each individual beta parameter
            acceptanceRateArray = mcmc_iterate(t,flux,sigma,initParams,func,Nsteps,beta,saveInterval,verbose=False)


            ## If the acceptance rate is too high, the normal distributions sampled about each input parameter
            ## are not wide enough, so try increasing the beta_mu term by raising (acceptanceRate/idealAcceptanceRate)
            ## to a positive power `phi`, so that betaFactor = (acceptanceRate/idealAcceptanceRate)^phi > 1 and therefore
            ## beta_mu * betaFactor > beta_mu, i.e., the next beta_mu will be larger.
            ##
            ## If the acceptance rate is too low, take betaFactor < 1, and if the acceptance rate is good, take
            ## phi to be zero, i.e., betaFactor = 1.0, or "make no change in beta_mu on this step"
            phi = np.zeros(len(acceptanceRateArray)) ## Initialize `phi` array
            
            phi[acceptanceRateArray > 1.1*idealAcceptanceRate] = 1	
            phi[acceptanceRateArray < 0.9*idealAcceptanceRate] = 1
            #phi[acceptanceRateArray > 1.4*idealAcceptanceRate] = 3			## If very far from within the limits, use higher power
            #phi[acceptanceRateArray < 0.6*idealAcceptanceRate] = 3			
            phi[(acceptanceRateArray <= 1.1*idealAcceptanceRate)*(acceptanceRateArray >= 0.9*idealAcceptanceRate)] = 0
            betaFactor = np.power(acceptanceRateArray/idealAcceptanceRate,phi) ## Change beta by a factor of `betaFactor
            betaFactor[betaFactor < 0.01] = 0.01        ## If betaFactor very small, limit it to 1/100
            print "Betas:", beta
            beta *= betaFactor
            #print beta, acceptanceRateArray,  np.power(acceptanceRateArray/idealAcceptanceRate,phi)
            print "Optimizing each Beta_mu: acceptance rates for each parameter:", acceptanceRateArray
            print "Optimize by multiplying current beta by:",betaFactor
            iterationCounter += 1
    return beta

