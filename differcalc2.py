# Descendant of the original 'differ10.2.py'
import os
import math
import numpy as np
import matplotlib.pyplot as plt
import time
from time import strftime

import diffmodule3 as dm ## Classes for "fluxArray" and "starObj"

def pstr(num,pad):
    strlen = len(str(num))
    lenpad = pad-strlen
    return str((lenpad*'0')+str(num))

def trunc(f, n):
    '''Truncates a float f to n decimal places without rounding'''
    slen = len('%.*f' % (n, f))
    return str(f)[:slen]


print "Computing differential photometry..."
#os.system('mkdir diff10')
os.system('mkdir diff_out')

os.system("ls aper_out/*.log > filelists/aperfiles.txt")
flxfiles = open('filelists/aperfiles.txt','r').read().splitlines()
for j in range(1,len(flxfiles)+1):
    teststar = dm.starObj(pstr(j,3))        ## Initialize star object for test star
    testflux = dm.fluxArr(teststar)         ## Initialize flux object for test star
    testflux.avgFlux(teststar)              ## Add test star's flux to flux obj

    starobjs = []
    for i in range(2,len(flxfiles)+1):
        if i != j:                                    ## For stars other than test star,
            starobjs.append(dm.starObj(pstr(i,3)))    ## create star objs

    controlflux = dm.fluxArr(starobjs[0])   ## Initialize a flux object for the
                                            ## control stars
    for i in starobjs:
        if i.flags() == False and i.number() > 1:        ## Include control stars in the flux average
            controlflux.avgFlux(i)    ## that don't have flags

    diff = controlflux.magScale() - testflux.magScale()
    differr = (controlflux.err()**2 + testflux.err()**2)**0.5
                                            ## Take the difference of the log magnitudes
    diffobj = dm.diffArr(diff,differr)
    dlog = open('diff_out/diff_'+pstr(j,3)+'.log','w')
    for i in range(0,len(diff)):
        dlog.write(str(diff[i][0])+' '+str(differr[i][0])+'\n')
    dlog.close()
