import os
import math
import numpy as np
import pyfits
import time
from time import strftime
import glob

execfile('oscmds.py')                   ## Import custom functions:'mkdir','cd', 'cp'
mkdir('filelists')
#import wircMod as wm
def pstr(num,pad):
    strlen = len(str(num))
    lenpad = pad-strlen
    return str((lenpad*'0')+str(num))

global darkLoc, flatLoc, regsLoc, ingressUt, egressUt, imagLoc, track, aper, aprad, Kccd, aperplot, diffonoff, gui, trackplot, smoothConst, initGui


initGui = track = plot = aper = None


init = open('init.par', 'r').read().splitlines()
for i in range(0, len(init)):
    if len(init[i].split()) > 1 and init[i][0] != '#':
        inline = init[i].split(":")
        inline[0] = inline[0].strip()
        if inline[0] == 'Path to Dark Frames': darkLoc = str(inline[1].split('#')[0].strip()) ##Everything after # on a line in init.par is ignored
        if inline[0] == 'Path to Flat Frames': flatLoc = str(inline[1].split('#')[0].strip())
        if inline[0] == 'Path to data images':  imagLoc = str(inline[1].split('#')[0].strip())
        if inline[0] == 'Path to regions file': regsLoc = str(inline[1].split('#')[0].strip())
        if inline[0] == 'Star Tracking':    track = inline[1].split('#')[0].strip()
        if inline[0] == 'Aper':  aper = inline[1].split('#')[0].strip()
        if inline[0] == 'Radius':   aprad = float(inline[1].split('#')[0].strip())
        if inline[0] == 'CCD Saturation Limit':   satur = float(inline[1].split('#')[0].strip())
        if inline[0] == 'CCD Gain':    Kccd = float(inline[1].split('#')[0].strip())
        if inline[0] == 'Show Plots': aperplot = inline[1].split('#')[0].strip()
        if inline[0] == 'Perform Differential Photometry':    diffonoff = inline[1].split('#')[0].strip()
        if inline[0] == 'GUI': gui = inline[1].split('#')[0].strip()
        if inline[0] == 'Trackplot': trackplot = inline[1].split('#')[0].strip()
        if inline[0] == 'Smoothing Constant': smoothConst = float(inline[1].split('#')[0].strip())
        if inline[0] == 'Ingress': ingressUt = str(inline[1]) + ':' + str(inline[2]) + ':' + str(inline[3].split('#')[0].strip())
        if inline[0] == 'Egress': egressUt = str(inline[1]) + ':' + str(inline[2]) + ':' + str(inline[3].split('#')[0].strip()) ##inline is split at colon so these lines are a bit different
        if inline[0] == 'Init GUI': initGui = inline[1].split('#')[0].strip()

#darkLoc = '/home/dan/Downloads/20120616forSUMO/tres1-???d.fit' ## Path to dark frame(s)
#flatLoc = '/home/dan/Downloads/correctedFlat.fits'
#imagLoc = '/home/dan/Downloads/20120616forSUMO/tres1-???.fit'
#regsLoc = '/home/dan/Downloads/20120616forSUMO/rad4Stars2simplified/stars2.reg'
#track = 'on'
#aper = 'on'
#aprad = 4.0 ##!!! Constant aperture radius: enter in units of pixels
#satur = 60000
#Kccd = 1
#smoothConst = 3.0
#aperplot = 'off'
#diff = 'off'
#diffgui = 'off'
#diffonoff = 'off'
#gui = 'off'
#trackplot = 'off'

writeOutCorrected = 'off'

if aperplot == 'on' or trackplot == 'on':
    import matplotlib 
    import matplotlib.pyplot as plt
    matplotlib.interactive(True)
    plt.figure()
    #plt.show()

hdulist = pyfits.open(flatLoc)
flat_field = hdulist[0].data
flat_field = flat_field/np.median(flat_field)
#plt.imshow(flat_field);plt.show()
#############################################################


## If outputs from a previous exectution of photom__.py or any
## of its components are in the running directory, warn the user
## before overwriting them \/ \/ \/

##Create a list of image files and files to check against within Oscaar
##to overwrite check
checkfiles = glob.glob('*')
imgfiles = glob.glob(imagLoc)
imgfiles.sort()

overwcheck3 = None
overcheck('track_out', checkfiles, track) ##Checks if directories are already present
overcheck('aper_out', checkfiles, aper)   ##Prompts user for overwrite
overcheck('diff10', checkfiles, diffonoff)
overcheck('time_out', checkfiles, aper)
overcheck('diff_out', checkfiles, diffonoff)
for i in range(0,len(checkfiles)):
    if checkfiles[i]=='diff_out' and diffonoff == 'on':
        overwcheck3 = raw_input('WARNING: Overwrite /diff_out/ ? (Y/n): ')
        break
    if overwcheck3 == '' or overwcheck3 == 'Y' or overwcheck3 == 'y':
        os.system('rm -r corrected')
        mkdir('corrected')


mkdir('time_out')

if track=='on' or aper == 'on':
    execfile('darkframe5.py')               ## Open dark frames, average them = 'dark_avg'
    glob_dark_avg = dark_avg
    execfile('ds9parser4.py')               ## Open regions file, parse out coords -> init_x/y_list

    track_xmatrix = np.zeros([len(init_x_list),len(imgfiles)])  ## Generate matrices to hold the 
    track_ymatrix = np.zeros([len(init_y_list),len(imgfiles)])  ## (x,y) coords of stars

if track == 'on':                       ## If stars must be tracked, import fitting package
    #import minuit                       ## and make a directory for the output star positions
    #execfile('trackDefocus6gauss.py')
    execfile('trackSmooth1.py')
    mkdir('track_out')

if track == None or track == 'off' and aper == 'on':
    track_smatrix = np.zeros([len(init_y_list),len(imgfiles)])
    os.system('ls track_out/*.log > filelists/trackfiles.txt')
    tracknames = open('filelists/trackfiles.txt','r').read().splitlines()
    for i in range(0,len(tracknames)):
        trackdata = open(tracknames[i],'r').read().splitlines()
        for j in range(0,len(trackdata)):
           # print tracknames[i],j
            track_xmatrix[i][j] = float(trackdata[j].split()[0])
            track_ymatrix[i][j] = float(trackdata[j].split()[1])
            track_smatrix[i][j] = float(trackdata[j].split()[2])
     
    hww_list = track_smatrix

if aper == 'on':                        ## If aperture photometry will be performed, make a
    execfile('aper12constantRadius.py')                ## directory for output, import function
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
    global scidata, row, col
    for i in range(0,len(imgfiles)):
        hdulist = pyfits.open(imgfiles[i])  ## Open FITS image
        headerInfo = hdulist[0].header
        scidata = hdulist[0].data
        JD = headerInfo['JD']
        timeout = open('time_out/time.log','a').write(str(JD)+'\n')

        scidata = (scidata - dark_avg)/flat_field       ## Subtract dark frame, normalize
                                                        ## to the flat field
        scidata = np.array(scidata)                                              
        if writeOutCorrected == 'on':
            hdu = pyfits.PrimaryHDU(scidata)
            pyfits.HDUList([hdu])
            pyfits.writeto('corrected/corrected'+str(i)+'.fits',scidata)
        for j in range(0,len(init_x_list)):
           # dark_avg = glob_dark_avg
            if i == 0:
                init_x = init_x_list[j]
                init_y = init_y_list[j]
            else:
                init_x = track_xmatrix[j][i-1]                     ## Use input values from ds9parser
                init_y = track_ymatrix[j][i-1]                     ## for star initial positions
            hww = hww_list[j]#[i]

            print ("IMAGE "+str(i+1)+"/"+str(len(imgfiles))+", STAR "+
                   str(j+1)+"/"+str(len(init_x_list))+"************************")

            if track == 'on':
                #try:                                    ## Try to find star positions
                outfile1 = open('track_out/star'+pstr(j+1,3)+'_coord.log','a')
                [xcenter_fit,ycenter_fit,sigma_fit] = trackSmooth(scidata,
                                        init_x, init_y, hww, smoothConst, aprad, plots=trackplot)

                row = xcenter_fit
                col = ycenter_fit
                track_xmatrix[j][i] = row
                track_ymatrix[j][i] = col

                outfile1.write(str(row)+' '+str(col)+' '+str(sigma_fit)+'\n')
                outfile1.close()

            if track == 'off':
                row = init_x_list[j]    #track_xmatrix[j][i]
                col = init_y_list[j]    #track_ymatrix[j][i]
                sigma_fit = hww     #track_smatrix[j][i]
                xcenter_fit = hww           ## This part was written to cancel out part of  
                ycenter_fit = hww           ## the 'aper' code that expects an input left over
                                            ## from 'trackstars'

            if aper == 'on':
                if aperplot == 'on':
                    if i%3 == 0:
                        aperplot = 'on'
                    else:
                        aperplot = 'on'
                outfile2 = open('aper_out/phot_out_'+pstr(j+1,3)+'.log','a')
                [flx, err, maxval] = aper12(imgfiles[i], row, col, hww, xcenter_fit,
                                   ycenter_fit, sigma_fit, aprad, satur, Kccd, plots=aperplot)
                if maxval > 0.90*satur:
                    outfile2.write(str(flx)+' '+str(err)+' *\n')
                    aperlog = open('aper_out/aper.par','a').write('SATURATION WARNING: Star '+str(j)+'\n')
                    print "WARNING: Saturation may have occurred here"
                elif err == 1.0 or flx == 1.0:
                    outfile2.write(str(flx)+' '+str(err)+' *\n')
                else:
                    outfile2.write(str(flx)+' '+str(err)+'\n')
                outfile2.close()

mkdir('plots')
mkdir('plots/histograms/')
global nStars
nStars = 18
starRange = range(1,nStars+1)

execfile('regressOutOfTransit3.py')
execfile('noiseToSignal3.py')

nA,StargetA,ScompA = noiseToSig('a',regressCoeffsA,regressConstA)
#nB,StargetB,ScompB = noiseToSig('b',regressCoeffsB,regressConstB)

initLines = open('init.par', 'r').read().splitlines()
init = open('init.par', 'w')
for i in range (0, len(initLines)):
    if initLines[i].split(':')[0] != 'Init GUI':
        init.write(initLines[i] + '\n')
init.close()

noisePlot = 'on'
if noisePlot == 'on':
    ax3 = fig.add_subplot(212)
    ax3.plot(combinedStackSorted[:,0],nA,'o')
    #ax3.plot(nB,'o')
    ax3.set_xlim([min(combinedStackSorted[:,0]),max(combinedStackSorted[:,0])])
    ax3.set_title('Noise to Signal Ratio')
    ax3.set_xlabel('Phase')
    ax3.set_ylabel('N/S')
    #plt.draw()
    if initGui == None:
        plt.show()
    else:
        plt.savefig('plots/lightCurve.png', fmt = '.png') 
time = combinedStackSorted[:,0]
lightCurve = combinedStackSorted[:,1]
execfile('LCscatter.py')


