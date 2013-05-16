
import numpy as np
import ctypes

'''
	generateModelLC.py defines the function simulateLC(), which 
    loads the C library containing occultquad() so that analytical
    transit light curves can be produced in python by passing 
    pythonic arguments to the C code. 
'''

## Resources on using ctypes:
# http://docs.python.org/2/library/ctypes.html#ctypes.c_float
# http://www.scipy.org/Cookbook/Ctypes#head-0c422ad0dcf3a37f8c16d4cfd85e37e1f7290214
# http://docs.scipy.org/doc/numpy/reference/routines.ctypeslib.html

def simulateLC(t,modelParams):
    [p,ap,P,i,gamma1,gamma2,e,longPericenter,t0] = modelParams

    ###################################################################################################
    ## Ctypes definitions from C-libraries
    lib = np.ctypeslib.load_library('c/transit1forLMLS','.') 	## Loads transit1torturetest.so as a library
    occultquad = lib.occultquad
    occultquad.argtypes = [np.ctypeslib.ndpointer(np.float64,flags='aligned,C_CONTIGUOUS'),	#t
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
                               np.ctypeslib.ndpointer(np.float64,flags='aligned,C_CONTIGUOUS')]	# F
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
    #NpointsInT = (P*percentOfOrbit/100.0 - -1.0*P*percentOfOrbit/100.0)/Npoints	
    #t = np.arange(-1.0*P*percentOfOrbit/100.0,P*percentOfOrbit/100.0,NpointsInT,dtype=np.float32)

    ## np.require() will force the ndarrays to the right dtype as assigned in the `argtypes` list.
    n = len(t)
    t = np.require(t,np.float64)
    F = np.empty_like(t,dtype=np.float64)
    occultquad(t, p,  ap,  P,  i,  gamma1,  gamma2, e,longPericenter, t0,  n,  F)	## Simulate fake data
    return F
