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


medianval = 22

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
fig = pyl.figure()
fig.canvas.set_window_title('oscaar') 
ax = pyl.subplot(111)
#figtext = 'Brett Morris (UMD)'
#t = fig.text(0.7, 0.13, figtext, ha="left", va="center", rotation=0,size=12)
#ax.xaxis.major.formatter.set_scientific(False)
#pyl.subplots_adjust(left=0.1,right=0.78)
t = fig.text(0.24, 0.14, "Ingress", ha="left", va="center",
             rotation=0,size=12,backgroundcolor='white')
t = fig.text(0.7, 0.14, "Egress", ha="left", va="center",
             rotation=0,size=12,backgroundcolor='white')
pyl.axvline(x=2455763.623611,ymin=0,ymax=1,color='k',
            linestyle=':',linewidth=1)
pyl.axvline(x=2455763.700000,ymin=0,ymax=1,color='k',
            linestyle=':',linewidth=1)

#print np.shape(diffobjs[0].arr())

yd = np.median(diffobjs[0].arr()[0:60])

displace = 4.5
#ctrl = np.array(diffobjs[10].arr())-displace-yd
test = np.array(diffobjs[0].arr())-yd

#t = fig.text(0.15, 0.85, "HD 189733", ha="left", va="center",
#             rotation=0,size=12,backgroundcolor='white')
#t = fig.text(0.15, 0.4, "Control Star", ha="left", va="center",
#             rotation=0,size=12,backgroundcolor='white')


plottest = ax.plot(teststar.time(),test,'o',color=(0.9,0.9,0.9),markersize=3)
#plotctr = ax.plot(teststar.time(),ctrl,'x',color=(0.1,0.1,0.1),markersize=3)
plotm, = ax.plot(diffobjs[0].medianx(),np.array(diffobjs[0].mediany())-yd,'s-',color=(0,0,0),markersize=6)
#plotm, = ax.plot(diffobjs[0].medianx(),np.array(diffobjs[0].mediany())-yd,'s-',color=(0,0,0),markersize=6)
#plotmctr, = ax.plot(diffobjs[10].medianx(),
#                    np.array(diffobjs[10].mediany())-displace-yd,'s-',color=(0,0,0),markersize=6)
##leg = ax.legend((plottest,plotm),("Differential Magnitude",
##                          str(medianval)+" pt Median"),numpoints=1,markerscale=1)
##for t in leg.get_texts():
##    t.set_fontsize('small')
pyl.xlabel('Time (JD)')
pyl.ylabel('Differential Magnitude')
pyl.title('Differential Photometry, 2011 Jul 20')
#pyl.grid('on')

dev = np.std(diffobjs[0].arr())*2
#pyl.ylim(np.mean(diffobjs[0].arr())-1.5*dev,np.mean(diffobjs[0].arr())+1.5*dev)
#ax.set_yticks(np.array(range(-35,140,20),dtype=float)/1000)
pyl.ylim(-0.015,0.045)
ax.set_ylim(ax.get_ylim()[::-1])
pyl.xlim(min(teststar.time()),max(teststar.time()))
dind = range(0,len(diffobjs))
#print max(diffobjs[0].arr()), min(diffobjs[0].arr())
plt.savefig('diff_out/differprint_edit2.png')
plt.show()
plt.close()
