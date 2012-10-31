## Main script to execute oscaar1.1.0

import os
import math
import numpy as np
import pyfits
import time
from time import strftime

execfile('oscmds.py')                   ## Import custom functions:'mkdir','cd', 'cp'
mkdir('filelists')

def pstr(num,pad):
    strlen = len(str(num))
    lenpad = pad-strlen
    return str((lenpad*'0')+str(num))

track = plot = aper = None
global darkLoc, flatLoc, regsLoc

init = open('init.par','r').read().splitlines()
for i in range(0,len(init)):
    if len(init[i].split()) > 1:
        inline = init[i].split()          ## Checks init.par for which parameters
        if inline[0] == 'darkLoc': darkLoc = str(inline[1]) ## to turn on and off
        if inline[0] == 'flatLoc': flatLoc = str(inline[1])
        if inline[0] == 'imagLoc': imagLoc = str(inline[1])
        if inline[0] == 'regsLoc': regsLoc = str(inline[1])
        if inline[0] == 'track':   track = inline[1]
        if inline[0] == 'estsig':  init_est_sig = float(inline[1])
        if inline[0] == 'trackplot': trackplot = inline[1]
        if inline[0] == 'aper':    aper = inline[1]
        if inline[0] == 'aprad':   aprad = float(inline[1])
        if inline[0] == 'satur':   satur = float(inline[1])
        if inline[0] == 'Kccd':    Kccd = float(inline[1])
        if inline[0] == 'aperplot': aperplot = inline[1]
        if inline[0] == 'diff':    diffonoff = inline[1]
        if inline[0] == 'diffgui':    gui = inline[1]        
        if inline[0] == 'diffallplots': diffallplots = str(inline[1])
        if inline[0] == 'difftoss': difftoss = float(inline[1])
        if inline[0] == 'diffplotsfilt': diffplotsfilt = str(inline[1])
        
os.system("ls "+imagLoc+" > filelists/filenames.txt")
imgfiles = open('filelists/filenames.txt','r').read().splitlines()

os.system("ls > filelists/filelist.txt")
checkfiles = open('filelists/filelist.txt','r').read().splitlines()

## If outputs from a previous exectution of photom__.py or any
## of its components are in the running directory, warn the user
## before overwriting them \/ \/ \/

overwcheck1 = overwcheck2 = overwcheck3 = overwcheck4 = overwcheck5 = None
for i in range(0,len(checkfiles)):
    if checkfiles[i]=='track_out' and track == 'on':
        overwcheck1 = raw_input('WARNING: Overwrite /track_out/ ? (Y/n): ')
        break
if overwcheck1 == '' or overwcheck1 == 'Y' or overwcheck1 == 'y':
    os.system('rm -r track_out')

for i in range(0,len(checkfiles)):
    if checkfiles[i]=='aper_out' and aper == 'on':
        overwcheck2 = raw_input('WARNING: Overwrite /aper_out/ ? (Y/n): ')
        break
if overwcheck2 == '' or overwcheck2 == 'Y' or overwcheck2 == 'y':
    os.system('rm -r aper_out')

for i in range(0,len(checkfiles)):
    if checkfiles[i]=='diff_out' and diffonoff == 'on':
        overwcheck3 = raw_input('WARNING: Overwrite /diff_out/ ? (Y/n): ')
        break
if overwcheck3 == '' or overwcheck3 == 'Y' or overwcheck3 == 'y':
    os.system('rm -r diff_out')
    mkdir('diff_out')
    
for i in range(0,len(checkfiles)):
    if checkfiles[i]=='diff10' and diffonoff == 'on':
        overwcheck4 = raw_input('WARNING: Overwrite /diff10/ ? (Y/n): ')
        break
if overwcheck4 == '' or overwcheck4 == 'Y' or overwcheck4 == 'y':
    os.system('rm -r diff10')
    mkdir('diff10')

mkdir('time_out')

if track=='on' or aper == 'on':
    execfile('darkframe5.py')               ## Open dark frames, average them = 'dark_avg'
    glob_dark_avg = dark_avg
    execfile('ds9parser4.py')               ## Open regions file, parse out coords -> init_x/y_list

    track_xmatrix = np.zeros([len(init_x_list),len(imgfiles)])  ## Generate matrices to hold the 
    track_ymatrix = np.zeros([len(init_y_list),len(imgfiles)])  ## (x,y) coords of stars

if track == 'on':                       ## If stars must be tracked, import fitting package
    import minuit                       ## and make a directory for the output star positions
    execfile('trackstar2.py')
    mkdir('track_out')

if track == None or track == 'off' and aper == 'on':
    track_smatrix = np.zeros([len(init_y_list),len(imgfiles)])
    os.system('ls track_out/*.log > filelists/trackfiles.txt')
    tracknames = open('filelists/trackfiles.txt','r').read().splitlines()
    for i in range(0,len(tracknames)):
        trackdata = open(tracknames[i],'r').read().splitlines()
        for j in range(0,len(trackdata)):
            track_xmatrix[i][j] = float(trackdata[j].split()[0])
            track_ymatrix[i][j] = float(trackdata[j].split()[1])
            track_smatrix[i][j] = float(trackdata[j].split()[2])
            
if aper == 'on':                        ## If aperture photometry will be performed, make a
    execfile('aper11.py')                ## directory for output, import function
    mkdir('aper_out')
    aperlog = open('aper_out/aper.par','w').write(
                                          'start time: '+strftime("%d %b %Y %H:%M", time.localtime())+'\n'
                                          'nStars: '+str(len(init_x_list))+'\n'
                                          'nImages: '+str(len(imgfiles))+'\n'
                                          'aprad = '+str(aprad)+'\n'
                                          'track = '+str(track)+'\n')
if plot == 'on':
    from mpl_toolkits.mplot3d import axes3d
    import matplotlib.pyplot as plt
    import matplotlib.image as mpimg    ## If plots will be made, import plotting packages

if track == 'on':
    track_xmatrix[:,0] = init_x_list
    track_ymatrix[:,0] = init_y_list

if aper == 'on' or track == 'on':
    for i in range(0,len(imgfiles)):
        hdulist = pyfits.open(imgfiles[i])  ## Open FITS image
        scidata = hdulist[0].data
        scidata = (scidata - dark_avg)/flat_field       ## Subtract dark frame, normalize
                                                        ## to the flat field
        header = hdulist[0].header
        JD = header['JD']
        timeout = open('time_out/time.log','a').write(str(JD)+'\n')
        for j in range(0,len(init_x_list)):
            dark_avg = glob_dark_avg
            if i == 0:
                init_x = init_x_list[j]
                init_y = init_y_list[j]
            else:
                init_x = track_xmatrix[j][i-1]                     ## Use input values from ds9parser
                init_y = track_ymatrix[j][i-1]                     ## for star initial positions

            hww = hww_list[j]
            
            print ("IMAGE "+str(i+1)+"/"+str(len(imgfiles))+", STAR "+
                   str(j+1)+"/"+str(len(init_x_list))+"************************")

            if track == 'on':
                try:                                    ## Try to find star positions
                    outfile1 = open('track_out/star'+pstr(j+1,3)+'_coord.log','a')
                    #if i == j == 0:
                    est_sigma = init_est_sig
                    [xcenter_fit, ycenter_fit, sigma_fit] = trackstar2(scidata,
                                            init_x, init_y, hww, est_sigma, plots=trackplot)

                    row = (init_x - hww) + xcenter_fit
                    col = (init_y - hww) + ycenter_fit
                    track_xmatrix[j][i] = row
                    track_ymatrix[j][i] = col
#                    est_sigma=sigma_fit
                    if sigma_fit <= 0:
                        print "WARNING: Tracking fit produced sigma=<0"
                        sigma_fit = 1.5
                    
                    outfile1.write(str(row)+' '+str(col)+' '+str(sigma_fit)+'\n')
                    outfile1.close()
                except minuit.MinuitError:
                    ## If fitting fails, the input guess for the fit (the last successful
                    ## fit position) will be used as the fit result. The error will be
                    ## noted with a "*" in the tracking output.'''
                    print "ERROR: Fit not found for this frame."
                    outfile1 = open('track_out/star'+pstr(j+1,3)+'_coord.log','a')
                    outfile1.write(str(row)+' '+str(col)+' '+str(sigma_fit)+' *\n')
                    outfile1.close()
            if track == 'off':
                row = track_xmatrix[j][i]
                col = track_ymatrix[j][i]
                sigma_fit = track_smatrix[j][i]
                xcenter_fit = hww           ## This part was written to cancel out part of  
                ycenter_fit = hww           ## the 'aper' code that expects an input left over
                                            ## from 'trackstars'

            if aper == 'on':
                outfile2 = open('aper_out/phot_out_'+pstr(j+1,3)+'.log','a')
                [flx, err, maxval] = aper11(imgfiles[i], row, col, hww, xcenter_fit,
                                   ycenter_fit, sigma_fit, aprad, satur, Kccd, plots=aperplot)
                if maxval > 0.90*satur:
                    outfile2.write(str(flx)+' '+str(err)+' *\n')
                    aperlog = open('aper_out/aper.par','a').write('SATURATION WARNING: Star '+str(j)+'\n')
                    print "WARNING: Saturation may have occurred here"
                else:
                    outfile2.write(str(flx)+' '+str(err)+'\n')
                outfile2.close()

if diffonoff == 'on':
    execfile('differcalc2.py')

if gui == 'on':
    execfile('differgui2.py')
print "photom15.py: Done."
