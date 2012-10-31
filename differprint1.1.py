# Descendant of 'differ10.3.py'
import pylab as pyl
from matplotlib.widgets import Button, RadioButtons
import os
import math
import numpy as np
import matplotlib.pyplot as plt
import time
from time import strftime
import random

import diffmodule3 as dm ## Classes for "fluxArray" and "starObj"

def pstr(num,pad):
    strlen = len(str(num))
    lenpad = pad-strlen
    return str((lenpad*'0')+str(num))

def trunc(f, n):
    '''Truncates a float f to n decimal places without rounding'''
    slen = len('%.*f' % (n, f))
    return str(f)[:slen]


medianval = 10

os.system("ls diff_out/*.log > filelists/difffiles.txt")
difffiles = open('filelists/difffiles.txt','r').read().splitlines()

teststar = dm.starObj('001')

diffobjs = []
for j in range(0,len(difffiles)):
    diffs = open(difffiles[j],'r').read().splitlines()
    differr = np.zeros([len(diffs)])
    for i in range(0,len(diffs)):
        differr[i]=float(diffs[i].split()[1])
        diffs[i]=float(diffs[i].split()[0])
    diffobj = dm.diffArr(diffs,differr)
    diffobj.calcMedian(medianval,teststar.time())
    diffobjs.append(diffobj)

## From custbuttons.py \/ \/ \/
print diffobjs[0].err()
fig = pyl.figure()
fig.canvas.set_window_title('oscaar') 
ax = pyl.subplot(111)
figtext = 'Brett Morris (UMD)'
t = fig.text(0.7, 0.13, figtext, ha="left", va="center", rotation=0,size=12)
#ax.xaxis.major.formatter.set_scientific(False)
#pyl.subplots_adjust(left=0.1,right=0.78)
plottest = ax.errorbar(teststar.time(),diffobjs[0].arr(),yerr=diffobjs[0].err(),fmt='yo')
plotm, = ax.plot(diffobjs[0].medianx(),diffobjs[0].mediany(),'bo-')
pyl.legend((plottest,plotm),("Differential Magnitude",
                          str(medianval)+" pt Median"),numpoints=1)
pyl.xlabel('Time (JD)')
pyl.ylabel('Differential Magnitude')
pyl.title('Title')
dev = np.std(diffobjs[0].arr())*2
pyl.ylim(np.mean(diffobjs[0].arr())-2*dev,np.mean(diffobjs[0].arr())+2*dev)
ax.set_ylim(ax.get_ylim()[::-1])
pyl.xlim(min(teststar.time()),max(teststar.time()))
dind = range(0,len(diffobjs))
plt.savefig('diff_out/differprint.png')
plt.close()
