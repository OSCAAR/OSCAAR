import pylab as pyl
from matplotlib.widgets import Slider, Button, RadioButtons, CheckButtons
import os
import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import time
from time import strftime
import random

import diffmodule2 as dm ## Classes for "fluxArray" and "starObj"

def pstr(num,pad):
    strlen = len(str(num))
    lenpad = pad-strlen
    return str((lenpad*'0')+str(num))

def trunc(f, n):
    '''Truncates a float f to n decimal places without rounding'''
    slen = len('%.*f' % (n, f))
    return str(f)[:slen]

os.system("ls diff_out/*.log > filelists/difffiles.txt")
difffiles = open('filelists/difffiles.txt','r').read().splitlines()

teststar = dm.starObj('001')

diffobjs = []
for j in range(0,len(difffiles)):
    diffs = open(difffiles[j],'r').read().splitlines()
    for i in range(0,len(diffs)):
        diffs[i]=float(diffs[i])
    diffobj = dm.diffArr(diffs)
    diffobj.calcMedian(10)
    diffobjs.append(diffobj)

## From custbuttons.py \/ \/ \/

fig = pyl.figure(figsize=(10,8),dpi=80)
fig.canvas.set_window_title('oscaar') 

ax = pyl.subplot(111)
pyl.subplots_adjust(left=0.1,right=0.78)
plottest, = ax.plot(diffobjs[0].arr(),'yo')
plotm, = ax.plot(diffobjs[0].medianx(),diffobjs[0].mediany(),'bo-')
pyl.legend((plottest,plotm),("Differential Magnitude",
                          str(10)+" pt Median"),numpoints=1)
pyl.xlabel('Time (min)')
pyl.ylabel('Magnitude (apparent mag. + arbitrary constant)')
pyl.title('Differential Photometry, Star 0')
dev = np.std(diffobjs[0].arr())*2
pyl.ylim(np.mean(diffobjs[0].arr())-2*dev,np.mean(diffobjs[0].arr())+2*dev)
pyl.xlim(0,max(np.shape(diffobjs[0].arr())))
dind = range(0,len(diffobjs))

                ## bottom left corner x pos, y pos, width, height
rax2 = pyl.axes([0.80, 0.70, 0.16, 0.2], axisbg='lightgoldenrodyellow')
plotselect = RadioButtons(rax2, ('Test Star','Control Star','Residuals'))

rax3 = pyl.axes([0.88, 0.5, 0.08, 0.10], axisbg='lightgoldenrodyellow')
contnext = Button(rax3, 'Next\nControl')

rax4 = pyl.axes([0.80, 0.5, 0.08, 0.10], axisbg='lightgoldenrodyellow')
contprev = Button(rax4, 'Prev\nControl')

rax5 = pyl.axes([0.80, 0.45, 0.16, 0.05], axisbg='lightgoldenrodyellow')
resinext = Button(rax5, 'Random Residuals')

rax6 = pyl.axes([0.80, 0.25, 0.16, 0.05], axisbg='lightgoldenrodyellow')
medtog = Button(rax6, 'Toggle Median')

rax7 = pyl.axes([0.80, 0.3, 0.16, 0.05], axisbg='lightgoldenrodyellow')
gridtog = Button(rax7, 'Toggle Grid')

## Import logo graphic
emb1 = pyl.axes([0.80, 0.08, 0.16, 0.16], axisbg='w')
from pylab import imread
pyl.imshow(imread('logo2.png'))
emb1.set_xticks([])
emb1.set_yticks([])

class features:
    testtog = 'on'
    conttog = 'off'
    resitog = 'off'
    ax = ax
    ind = 1
    def mediantog(self,event):
        if self.testtog == 'on':
            plotm.set_visible(not plotm.get_visible())
        if self.conttog == 'on':
            plotmcont.set_visible(not plotmcont.get_visible())
        if self.resitog == 'on':
            print "Oops! You must be viewing Test or Control Stars to toggle the median line."
        pyl.draw()
        
    def gridtog(self,event):
        ax.grid()
        pyl.draw()
        
    def func2(self,label):
        if label == 'Test Star' and self.testtog == 'off':
            self.ax.clear()
            ax = self.ax
            ax = pyl.subplot(111)
            plottest, = ax.plot(diffobjs[0].arr(),'yo')
            global plotm
            plotm, = ax.plot(diffobjs[0].medianx(),diffobjs[0].mediany(),'bo-')
            ax.legend((plottest,plotm),("Differential Magnitude",
                                      str(10)+" pt Median"),numpoints=1)
            pyl.xlabel('Time')
            pyl.ylabel('Magnitude (apparent mag. + arbitrary constant)')
            pyl.title('Differential Photometry, TEST STAR (Star 0)')
            dev = np.std(diffobjs[0].arr())*2
            pyl.ylim(np.mean(diffobjs[0].arr())-2*dev,np.mean(diffobjs[0].arr())+2*dev)
            pyl.xlim(0,max(np.shape(diffobjs[0].arr())))
            self.testtog = 'on'
            
        if label != 'Test Star' and self.testtog == 'on':
            self.testtog = 'off'
            
        if label == 'Control Star' and self.conttog == 'off':
            self.ax.clear()
            ax = self.ax
            ax = pyl.subplot(111)
            plotcont, = ax.plot(diffobjs[self.ind].arr(),'yo')
            global plotmcont
            plotmcont, = ax.plot(diffobjs[self.ind].medianx(),diffobjs[self.ind].mediany(),'bo-')
            ax.legend((plotcont,plotmcont),("Differential Magnitude",
                                      str(10)+" pt Median"),numpoints=1)
            pyl.xlabel('Time')
            pyl.ylabel('Magnitude (apparent mag. + arbitrary constant)')
            pyl.title('Control Star, Star '+str(self.ind))
            dev = np.std(diffobjs[self.ind].arr())*2
            pyl.ylim(np.mean(diffobjs[self.ind].arr())-2*dev,
                     np.mean(diffobjs[self.ind].arr())+2*dev)
            pyl.xlim(0,max(np.shape(diffobjs[self.ind].arr())))
            self.conttog = 'on'
            
        if label != 'Control Star' and self.conttog == 'on':
            self.conttog = 'off'    

        if label == 'Residuals' or label == 'Random Residuals' and self.resitog == 'off':
            self.ax.clear()
            ax = self.ax
            ax = pyl.subplot(111)
            choose = range(2,len(diffobjs))
            self.r1 = random.choice(choose)
            self.r2 = random.choice(choose)
            if self.r1 == self.r2:
                self.r2 +=1 
            ax.plot(dm.starObj(pstr(self.r1,3)).flux()/np.mean(dm.starObj(pstr(self.r1,3)).flux())-
                    dm.starObj(pstr(self.r2,3)).flux()/np.mean(dm.starObj(pstr(self.r2,3)).flux()),'bo')
            pyl.xlabel('Time')
            pyl.ylabel('Deviation From Mean Normalized Intensity')
            pyl.title('Difference in Normalized Intensity: Stars '+str(self.r1)+' and '+str(self.r2))
            grid = ax.grid()
            self.resitog = 'on'
        if label != 'Residuals' and self.resitog == 'on':
            self.resitog = 'off'

        pyl.draw()

    def nextcont(self,event):
        if self.conttog == 'off':
            print "Oops! You aren't currently viewing Control Stars."
        else:
            if self.ind == len(diffobjs)-1:
                self.ind = 0
            self.ind +=1
            self.conttog = 'off'
            self.func2('Control Star')
            
    def prevcont(self,event):
        if self.conttog == 'off':
            print "Oops! You aren't currently viewing Control Stars."
        else:
            if self.ind == 1:
                self.ind = len(diffobjs)
            self.ind -=1
            self.conttog = 'off'
            self.func2('Control Star')

    def nextresi(self,event):
        if self.resitog == 'off':
            print "Oops! You aren't currently viewing Residuals."
        else:
            self.resitog == 'off'
            self.func2('Residuals')

plotstuff = features()
plotselect.on_clicked(plotstuff.func2)
contnext.on_clicked(plotstuff.nextcont)
contprev.on_clicked(plotstuff.prevcont)
resinext.on_clicked(plotstuff.nextresi)
gridtog.on_clicked(plotstuff.gridtog)
medtog.on_clicked(plotstuff.mediantog)

pyl.show()




