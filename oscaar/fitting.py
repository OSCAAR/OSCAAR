import os
import numpy as np
from matplotlib import pyplot as plt
from scipy import optimize
import oscaar
import IO
import transitModel
from matplotlib.ticker import FormatStrFormatter
from time import sleep
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

def mcmc(t,flux,sigma,initParams,func,Nsteps,beta,saveInterval,verbose=False,loadingbar=True):
	"""
	Markov Chain Monte Carlo routine for fitting. Takes a set of fluxes `flux` 
	measured at times `t` with uncertainties `sigma`. Input fitting function `func` is fed
	initial parameters `initParams` and iterated through the chains
	a total of `Nsteps` times, randomly sampled from normal distributions
	with widths `beta`, and every `saveInterval`-th state in the chain 
	is saved for later analysis.
	
	Parameters
	---------- 
	t : list
		times
	flux : list
		fluxes
	sigma : list
		uncertainties in fluxes
	initParams : list
		initial parameter estimates, `x_0` in Ford 2005
	func : function
		fitting function
	Nsteps : int
		number of iterations
	beta : list
		widths of normal distribution to randomly sample for each parameter
	saveInterval : int
		number of steps between "saving" the accepted parameter in the chain.
		Must satisfy ``Nsteps % saveInterval ==0``.
	
	Returns
	-------
	bestp : list
		parameters at minimum chi^2
	x_0toN  : array
		trace of each parameter at each save step
	acceptanceRate: float
		the final acceptance rate of the chain
		
	Notes
	-----
	 * Developed by Brett Morris (NASA-GSFC/UMD)	
	 * Based on the theory codified by Ford 2005 in The Astronomical Journal, 129:1706-1717
	 * Code implementation partly influenced by Ian Crossfield's routines: http://www.mpia-hd.mpg.de/homes/ianc/python/transit.html
	
	"""
	
	Nsteps = int(Nsteps)			## Type cast where necessary
	saveInterval = int(saveInterval)
	assert Nsteps % saveInterval == 0, ("Must choose integer number of `saveInterval`s in `Nsteps`. "+\
				 "Currently: Nsteps %% saveInterval = %.2f (should be zero)" % (Nsteps % saveInterval))
	acceptedStates = 0
	nout = Nsteps/saveInterval

	## Prepare loading bar plot (if turned on)
	if loadingbar:
		plt.ion()
		statusBarFig = plt.figure(num=None, figsize=(5, 2), facecolor='w',edgecolor='k')
		statusBarFig.canvas.set_window_title('Running...')
		statusBarAx = statusBarFig.add_subplot(111,aspect=10)
		statusBarAx.set_title('Markov Chain Monte Carlo fitting...')
		statusBarAx.set_xlim([0,100])
		statusBarAx.set_xlabel('Percent Complete (%)')
		statusBarAx.get_yaxis().set_ticks([])
	
	## Metropolis-Hastings algorithm...
	x_n = initParams ## initial trial state, **Step 1 in Ford 2005**, n=0
	weights = 1./sigma**2
	x_0toN = np.zeros([len(x_n),nout],dtype=float)
	allchi = np.zeros(nout,dtype=float)
	bestp = None
	
	## Compute chi^2 using initial params
	trialModel = func(t,x_n)
	chisq_n = np.sum(((trialModel-flux)**2)*weights)
	chisq_min = 1e100	## Set very high initial chi-squared that will get immediately overwritten
	for n in range(Nsteps):
		## Update the loading bar every so often
		if loadingbar and n % 5000 == 0:
			plt.cla()
			statusBarAx.set_title('Markov Chain Monte Carlo fitting...')
			statusBarAx.set_xlim([0,100])
			statusBarAx.set_xlabel('Percent Complete (%)')
			statusBarAx.get_yaxis().set_ticks([])
			statusBarAx.barh([0],[100.0*n/Nsteps],[1],color='k')
			plt.draw()
		## Generate trial step in parameters, **Step 2 in Ford 2005**
		x_nplus1 = np.random.normal(x_n,beta)	 
			## ^^^ Sample gaussians with widths `beta` randomly centered 
			##		about each parameter in `params`
			
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
			
		if n % saveInterval == 0:		 ## Every `saveInterval`-th state, save it
			if verbose: print "Step",n,"of",Nsteps
			x_0toN[:,n/saveInterval] = np.copy(x_n)
			allchi[n/saveInterval] = chisq_n

	## Calculate acceptance rate, should ideally be ~0.44 (Ford 2005)
	acceptanceRate = float(acceptedStates)/Nsteps	
	plt.close()
	assert bestp is not None, "No best-fit found, chi^2 minimizing state not found"
	return bestp, x_0toN, acceptanceRate

def mcmc_iterate(t,flux,sigma,initParams,func,Nsteps,beta,saveInterval,verbose=False):
 	"""
	   MCMC routine specifically for optimizing the beta parameters with the 
	   optimizeBeta() function. 
 
 	   Parameters
	   ---------- 
		t : list
			time
		flux : list
			fluxes
		sigma : list
			uncertainties in fluxes
		initParams : list 
			initial parameter estimates, `x_0` in Ford 2005
		func : function 
			fitting function
		Nsteps : int
			number of steps to try in the chains
		beta : list
			widths of normal distribution to randomly sample for each parameter
	
		Returns
		-------
		acceptanceRateArray : list 
			Acceptance rates for each beta_mu   
		
		Notes
		-----
		 * Developed by Brett Morris (NASA-GSFC/UMD)	
		 * Based on the theory codified by Ford 2005 in The Astronomical Journal, 129:1706-1717
		 * Code implementation partly influenced by Ian Crossfield's routines: http://www.mpia-hd.mpg.de/homes/ianc/python/transit.html 
	"""   
	
	bestp = None
	timeout_counter = 0
	while bestp == None:
		timeout_counter += 1
		assert timeout_counter < 1e3, "mcmc_iterate time out: Your initial parameters are likely very poor,"+\
					"and the MCMC script can't find a best-fit solution starting from them. Try better initial parameters."
		Niterations = 5*len(initParams)#20 ##40000	## Hard coded in Evan's code as 4e4

		
		## Change one of the initial parameters at random per each iteration
		randomInitParamIndex = np.floor(np.random.uniform(0,len(initParams),Niterations))	## array of random indices of initParams
		NacceptancesPerParameter = np.zeros(len(initParams))	## initialize arrays
		NstepsPerParameter = np.zeros(len(initParams))
		originalInitParams = np.copy(initParams)
		for i in range(Niterations):
			initParams = originalInitParams
			#print "Iteration",i,"of",Niterations
			testParamIndex = int(randomInitParamIndex[i])	## This initParam index will be tested
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
			chisq_min = 1e100	## Set very high initial chi-squared that will get immediately overwritten
			for n in range(Nsteps):
				## Generate trial step in parameters, **Step 2 in Ford 2005**
				x_nplus1 = np.random.normal(x_n,beta)	 
					## ^^^ Sample gaussians with widths `beta` randomly centered 
					##		about each parameter in `params`
					
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
					
				if n % saveInterval == 0:		 ## Every `saveInterval`-th state, save it
					if verbose: print "Step",n,"of",Nsteps
					x_0toN[:,n/saveInterval] = np.copy(x_n)
					allchi[n/saveInterval] = chisq_n
		
			## Calculate acceptance rate, should ideally be ~0.44 (Ford 2005)
			acceptanceRate = float(acceptedStates)/Nsteps	
		
			#assert bestp is not None, "No best-fit found, chi^2 minimizing state not found"
			#return bestp, x_0toN, acceptanceRate
		acceptanceRateArray = NacceptancesPerParameter/NstepsPerParameter 
	
	return acceptanceRateArray


def optimizeBeta(t,flux,sigma,initParams,func,beta,idealAcceptanceRate,plot=True):
	'''
		The `beta` input parameters for the MCMC function determine the 
		acceptance rate of the Metropolis-Hastings algorithm. According
		to Ford 2005, the ideal acceptance rate is ~0.25 - ~0.44. This routine
		is designed to take an initial guess for each of the beta parameters
		and tweak them until they produce good acceptance rates for each parameter.
		This is achieved by randomly perturbing each initial parameter with the small
		perturbation by randomly sampling a normal distribution with a width given by
		the initial beta vector `beta`. optimizeBeta() then tries running an MCMC chain
		briefly to find the acceptance rate for that beta parameter. If the acceptance
		rates are two high, for example, then the beta is too low, and optimizeBeta() 
		will increase beta. This process continues until the beta vector produces
		acceptance rates within 10% of the `idealAcceptanceRate`, which according to
		Ford (2005) should be between 0.25-0.44.
	
	   Parameters
	   ---------- 
		t : list
			time
		flux : list
			fluxes
		sigma : list
			uncertainties in fluxes
		initParams : list 
			initial parameter estimates, `x_0` in Ford 2005
		func : function 
			fitting function
		beta : list
			widths of normal distribution to randomly sample for each parameter
		idealAcceptanceRate : float
			desired acceptance rate to be produced by the optimized `beta`
		
		Returns
		-------
		beta : list
			the beta vector optimized so that running a MCMC chain should produce
			acceptance rates near `idealAcceptanceRate` (vector)

		Notes
		-----
		 * Developed by Brett Morris (NASA-GSFC/UMD)	
		 * Based on the theory codified by Ford 2005 in The Astronomical Journal, 129:1706-1717
		 * Code implementation partly influenced by Evan Sinukoff's MCMC_Evan_Master_v3_new22.pro
	'''
	
	Nsteps = len(initParams)*100.0	  ## do N iterations per parameter
	saveInterval = 10.0					## Save every Nth step
	acceptanceRateArray = mcmc_iterate(t,flux,sigma,initParams,func,Nsteps,beta,saveInterval,verbose=False)

	if plot:
		plt.ion()
		fig = plt.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
		fig.canvas.set_window_title('Beta optimization...')
		axis = fig.add_subplot(111)
		axis.set_title("Optimizing the set of $\\beta_\mu$...")
		axis.set_xlabel("Optimization iteration")
		axis.set_ylabel("Acceptance Rate")
		axis.axhline(xmin=0,xmax=1,y=1.1*idealAcceptanceRate,linestyle="--",linewidth=2,color='r')
		axis.axhline(xmin=0,xmax=1,y=0.9*idealAcceptanceRate,linestyle="--",linewidth=2,color='r')		

	for paramIndex in range(0,len(initParams)):	## For each random parameter to be changed,
		iterationCounter = 0		## Count how many times the while loop has been run
		while any(acceptanceRateArray > 1.1*idealAcceptanceRate) or any(acceptanceRateArray < 0.9*idealAcceptanceRate):	## While the acceptance rate is unacceptable (Ford 2005), 
			assert iterationCounter<1e2,"After 100 trials, the input beta parameters were not successfully optimized. Try new initial beta values."

			## Calculate the acceptance rates for each individual beta parameter
			acceptanceRateArray = mcmc_iterate(t,flux,sigma,initParams,func,Nsteps,beta,saveInterval,verbose=False)

			## If the acceptance rate is too high, the normal distributions sampled about each input parameter
			## are not wide enough, so try increasing the beta_mu term by raising (acceptanceRate/idealAcceptanceRate)
			## to a positive power `phi`, so that betaFactor = (acceptanceRate/idealAcceptanceRate)^phi > 1 and therefore
			## beta_mu * betaFactor > beta_mu, i.e., the next beta_mu will be larger.
			## If the acceptance rate is too low, take betaFactor < 1, and if the acceptance rate is good, take
			## phi to be zero, i.e., betaFactor = 1.0, or "make no change in beta_mu on this step"
			phi = np.zeros(len(acceptanceRateArray)) ## Initialize `phi` array
			
			phi[acceptanceRateArray > 1.1*idealAcceptanceRate] = 1	
			phi[acceptanceRateArray < 0.9*idealAcceptanceRate] = 1
			#phi[acceptanceRateArray > 1.4*idealAcceptanceRate] = 3			## If very far from within the limits, use higher power
			#phi[acceptanceRateArray < 0.6*idealAcceptanceRate] = 3			
			phi[(acceptanceRateArray <= 1.1*idealAcceptanceRate)*(acceptanceRateArray >= 0.9*idealAcceptanceRate)] = 0
			betaFactor = np.power(acceptanceRateArray/idealAcceptanceRate,phi) ## Change beta by a factor of `betaFactor
			betaFactor[betaFactor < 0.01] = 0.01		## If betaFactor very small, limit it to 1/100
			print "Betas:", beta
			beta *= betaFactor
			print "Optimizing each Beta_mu: acceptance rates for each parameter:", acceptanceRateArray
			print "Optimize by multiplying current beta by:",betaFactor
			iterationCounter += 1

			if plot: 
				for acceptanceRate in acceptanceRateArray:
					axis.plot(iterationCounter,acceptanceRate,marker='o',markersize=10,alpha=0.6,markeredgecolor='none')
					plt.xlim([0,iterationCounter+1])
					plt.draw()
				plt.pause(1)
	if plot:
		sleep(1)	## Pause for a second so the user can see that the solution has been reached
		plt.ioff()
		plt.close()
	return beta

def get_uncertainties(param,bestFitParameter):
	"""
	Find the uncertainties from a MCMC parameter chain. 
	
	Parameters
	----------
	param : list
		parameter chain from the completed MCMC algorithm
	
	bestFitParam : float
		the best-fit (chi-squared) minimizing value for the
		parameter chain
	
	Returns
	-------
	[plus,minus] : list of floats
		the upper and lower 1-sigma uncertainties on the best fit
		parameter `bestFitParameter`
	
	"""
	lowerHalf = param[param < bestFitParameter]
	upperHalf = param[param > bestFitParameter]
	
	plus = np.sqrt(np.sum((upperHalf - bestFitParameter)**2)/(len(upperHalf)-1))
	minus = np.sqrt(np.sum((lowerHalf - bestFitParameter)**2)/(len(lowerHalf)-1))
	return [plus,minus]

def histplot(parameter,axis,title,bestFitParameter):
	"""
	Plot a histogram with 50 bins displaying the parameter chain
	frequencies for the chain `parameter` with best fit value
	`bestFitParameter`. Name the figure after the parameter `title`
	and plot it to the axis `axis`. 
	
	"""
	postburn = parameter[burnFraction*len(parameter):len(parameter)]	## Burn beginning of chain
	Nbins = 50			  ## Plot histograms with 15 bins
	n, bins, patches = axis.hist(postburn, Nbins, normed=0, facecolor='white',histtype='stepfilled')  ## Generate histogram
	plus,minus = get_uncertainties(postburn,bestFitParameter)   ## Calculate uncertainties on best fit parameter
	axis.axvline(ymin=0,ymax=1,x=bestFitParameter+plus,ls=':',color='r')	## Plot vertical lines representing uncertainties
	axis.axvline(ymin=0,ymax=1,x=bestFitParameter-minus,ls=':',color='r')
	axis.set_ylim([0,np.max(n)])		
	axis.set_title(title)

def updatePKL(bestp,allparams,acceptanceRate,pklPath,uncertainties):
	"""
	Load an OSCAAR pkl, add the MCMC parameters to the file, save it again. 
	
	Parameters
	----------
	bestp : list
		best-fit values for each parameter
		
	allparams : array
		2D array where each saved state of the chains is stored along one dimension,
		for each fitting parameter (along the other)
		
	acceptanceRate : float
		the final acceptance rate acheived in the chain
		
	pklPath : str
		path to the pkl to overwrite.
	
	"""
	data = IO.load(pklPath)
	data.updateMCMC(bestp,allparams,acceptanceRate,pklPath,uncertainties)
	IO.save(data,pklPath)
	
class mcmcfit:
	def __init__(self,dataBankPath,initParams,initBeta,Nsteps,saveInterval,idealAcceptanceRate,burnFraction):
		'''
		Initialize the `mcmc` object with the initial parameters and data needed
		to prepare the MCMC run. 
		
		Parameters
		----------
		dataBankPath : string
			Path to a saved instance of the dataBank object from 
			`oscaar.save` which we'll use to extract the times, 
			fluxes and uncertainties in the light curve (string).
								
		initParams : list
			Initial parameter estimates, `x_0` in Ford 2005. Should be in 
			the following order: RpOverRs,aOverRs,per,inc,gamma1,gamma2,ecc,longPericenter,t0
									
		Nsteps : int
			number of steps/links in the MCMC chain
		
		initBeta : list
			widths of normal distribution to randomly sample for each parameter
								
		saveInterval : int
			number of steps between "saves", ie, storing
			the current step for later analysis
								
		idealAcceptanceRate : float
			ideal acceptance rate that you would like the chain to 
			have, definied by Ford 2005. Ideally ~0.25-0.44.
								
		burnFraction : float 
			fraction of saved steps at the beginning of the chains 
			to discard when computing uncertainties. Typically ~0.20
		'''
		## Load parameters
		self.data = IO.load(dataBankPath)
		self.dataBankPath = dataBankPath
		self.initParams = np.require(initParams,dtype=np.float64)
		self.Nsteps = Nsteps
		self.initBeta = initBeta
		self.idealAcceptanceRate = idealAcceptanceRate
		self.saveInterval = saveInterval
		self.burnFraction = burnFraction
		## Choose the implementation of transit light curve function to use:
		self.func = transitModel.occultquad  
	
	def run(self,updatepkl=False, apertureRadiusIndex=0):
		'''
		Run the MCMC algorithms: 
		
		Parameters
		----------
		updatepkl : boolean, optional
			update the OSCAAR save pkl file from which the data had
			been loaded with the MCMC best fit parameters, parameter
			chains, and acceptance rate. 
		
		apertureRadiusIndex : integer, optional
			Integer index of the aperture radius for which you'd like
			to compute the MCMC fit, from the aperture 
			radius range list
		'''

		def occult4params(t,freeparams,allparams=self.initParams):
			'''Allow 4 parameters to vary freely, keep the others fixed at the values assigned below'''
			RpOverRs_free,aOverRs_free,inc_free,t0_free = freeparams
			RpOverRs,aOverRs,per,inc,gamma1,gamma2,ecc,longPericenter,t0 = allparams
			return transitModel.occultquad(t,[RpOverRs_free,aOverRs_free,per,inc_free,gamma1,gamma2,ecc,longPericenter,t0_free])

		RpOverRs,aOverRs,per,inc,gamma1,gamma2,ecc,longPericenter,t0 = self.initParams
		initParams = [RpOverRs,aOverRs,inc,t0]
		beta = optimizeBeta(self.data.times,self.data.lightCurves[apertureRadiusIndex],self.data.lightCurveErrors[apertureRadiusIndex],\
											initParams,occult4params,self.initBeta,idealAcceptanceRate=self.idealAcceptanceRate)


		self.bestp, self.allparams, self.acceptanceRate = mcmc(self.data.times,self.data.lightCurves[apertureRadiusIndex],\
									self.data.lightCurveErrors[apertureRadiusIndex],initParams,occult4params,self.Nsteps,beta,\
									self.saveInterval,verbose=False,loadingbar=True)
		self.MCMCuncertainties = []
		for i in range(len(self.allparams)):
			self.MCMCuncertainties.append(get_uncertainties(self.allparams[i],self.bestp[i]))
		
		print self.bestp,self.allparams,self.acceptanceRate
		print self.MCMCuncertainties
		if updatepkl: updatePKL(self.bestp,self.allparams,self.acceptanceRate,self.dataBankPath,self.MCMCuncertainties)

	def plot(self, num=0):
		def occult4params(t,freeparams,allparams=self.initParams):
			'''Allow 4 parameters to vary freely, keep the others fixed at the values assigned below'''
			RpOverRs_free,aOverRs_free,inc_free,t0_free = freeparams
			RpOverRs,aOverRs,per,inc,gamma1,gamma2,ecc,longPericenter,t0 = allparams
			return transitModel.occultquad(t,[RpOverRs_free,aOverRs_free,per,inc_free,gamma1,gamma2,ecc,longPericenter,t0_free])

		bestp = self.bestp
		allparams = self.allparams
		acceptanceRate = self.acceptanceRate
		data = IO.load(self.dataBankPath)
		burnFraction = self.burnFraction
		x = data.times
		y = data.lightCurves[num]
		sigma_y = data.lightCurveErrors[num]
	
		##############################
		# Prepare figures
		plt.ioff()
		fig = plt.figure(num=0, figsize=(10, 10), facecolor='w',edgecolor='k')		
		fig.canvas.set_window_title('MCMC Results: Chains') 

		figLC = plt.figure(num=1, figsize=(10, 8), facecolor='w',edgecolor='k')
		figLC.canvas.set_window_title('MCMC Results: Light Curve') 

		LCax1 = figLC.add_subplot(211)
		LCax2 = figLC.add_subplot(212,sharex=LCax1)
		ax1 = fig.add_subplot(421)
		ax2 = fig.add_subplot(422)
		ax3 = fig.add_subplot(423)
		ax4 = fig.add_subplot(424)
		ax5 = fig.add_subplot(425)
		ax6 = fig.add_subplot(426)
		ax7 = fig.add_subplot(427)
		ax8 = fig.add_subplot(428)

		yfit = occult4params(x,bestp)
		LCax1.errorbar(x,y,yerr=sigma_y,fmt='o',color='k')
		LCax1.plot(x,yfit,'r',linewidth=3,alpha=0.75)
		LCax1.set_title("Fit with MCMC")
		LCax1.set_xlabel("Time (JD)")
		LCax1.set_ylabel("Relative Flux")
		def format_coord(x, y):
			# '''Function to give data value on mouse over plot.'''
			return "Time (JD): %.6f, Flux: %f" % (x,y)
		LCax1.format_coord = format_coord
		
		LCax2.errorbar(x,y-yfit,yerr=sigma_y,fmt='o',color='k')
		LCax2.axhline(xmin=0,xmax=1,y=0,ls=':',color='gray')
		LCax2.set_title("Fit Residuals")
		LCax2.set_xlabel("Time (JD)")
		LCax2.set_ylabel("Relative Flux")
		def format_coord(x, y):
			# '''Function to give data value on mouse over plot.'''
			return "Time (JD): %.6f, Flux: %f" % (x,y)
		LCax2.format_coord = format_coord
		##############################
		# Plot traces and histograms of mcmc params
		p = allparams[0,:]
		ap = allparams[1,:]
		i = allparams[2,:]
		t0 = allparams[3,:]
		abscissa = np.arange(len(allparams[0,:]))   ## Make x-axis for trace plots

		def chainplot(parameter,axis,title,format,burnFraction=burnFraction):
			#yfmt.set_powerlimits((-30,30))
			#fmt2 = FormatStrFormatter('%.15f')
			#axis.yaxis.set_major_formatter(fmt2)
			axis.plot(abscissa,parameter,'k.')
			axis.axvline(ymin=0,ymax=1,x=burnFraction*len(abscissa),linestyle=':',color='gray',linewidth=1.5)
			axis.set_title(title+" Chain")
			axis.set_xlabel('Saved Step Index')
			axis.set_ylabel(title)
			axis.get_yaxis().get_major_formatter().set_useOffset(False)
			def format_coord(x, y):
				# '''Function to give data value on mouse over plot.'''
				return format % (x,y)
			axis.format_coord = format_coord 
			
			#yfmt = axis.yaxis.get_major_formatter()
			#yfmt.set_powerlimits((-50,50))

		chainplot(p,ax1,'$R_p / R_s$','Step: %i,  Rp/Rs: %f')
		chainplot(ap,ax3,'$a / R_s$','Step: %i,  a/Rs: %f')
		chainplot(i,ax5,'Inclination','Step: %i,  Inclination: %f')
		chainplot(t0,ax7,'Mid-Transit Time','Step: %i, Mid-Trans Time: %.6f')


		def histplot(parameter,axis,title,bestFitParameter,format):
			postburn = parameter[burnFraction*len(parameter):len(parameter)]	## Burn beginning of chain
			Nbins = 50			  ## Plot histograms with 15 bins
			n, bins, patches = axis.hist(postburn, Nbins, normed=0, facecolor='white',histtype='stepfilled',linewidth=1.5)  ## Generate histogram
			plus,minus = get_uncertainties(postburn,bestFitParameter)   ## Calculate uncertainties on best fit parameter
			axis.axvline(ymin=0,ymax=1,x=bestFitParameter+plus,ls='--',color='r',linewidth=1.5)	## Plot vertical lines representing uncertainties
			axis.axvline(ymin=0,ymax=1,x=bestFitParameter-minus,ls='--',color='r',linewidth=1.5)	   
			axis.axvline(ymin=0,ymax=1,x=bestFitParameter,color='r',linewidth=2)	   
			axis.set_ylabel('Frequency')
			axis.set_xlabel(title) 
			axis.set_title(title)
			axis.set_ylim([0,np.max(n)])		
			def format_coord(x, y):
				# '''Function to give data value on mouse over plot.'''
				return format % (x,y)
			axis.format_coord = format_coord 
		## Plot the histograms
		histplot(p,ax2,'$R_p / R_s$',bestp[0],"Rp/Rs: %f,  Freq: %i")
		histplot(ap,ax4,'$a / R_s$',bestp[1],"a/Rs: %f,  Freq: %i")
		histplot(i,ax6,'Inclination',bestp[2],"Inclination: %f,  Freq: %i")
		histplot(t0,ax8,'Mid-Transit Time',bestp[3],"Mid-Trans Time: %.6f, Freq: %i")
		#fig.subplots_adjust(wspace=0.4,hspace=0.3,bottom=0.1, right=0.95, left=0.05, top=0.95)
		figLC.subplots_adjust(wspace=0.4,hspace=0.2,bottom=0.1, right=0.9, left=0.1, top=0.95)
		fig.tight_layout()
		#plt.savefig("mcmc_results.png",bbox_inches='tight')	 ## Save plot
		plt.show()