##import math
##import numpy as np
import matplotlib.pyplot as plt
##import matplotlib.image as mpimg
##import pyfits
##from mpl_toolkits.mplot3d import axes3d

def aper12(infile, est_x, est_y, hww, xcenter_fit, ycenter_fit, sigma_fit, aprad, sat, Kccd, plots=None):
    """Perform Gaussian fitting to find the center of a star near pixel (est_x, est_y)
       with estimated radial width est_sigma in a cropped portion of the image of radius
       hww, and do aperture photometry on it to find the flux, parameterizing the size
       of the aperture by the constant aprad. If plots = 'on',
       plots will be shown."""

    ## *******<from gauss4.py>**********

    rad = aprad                           ## Factor of sigma out radially
                                                    ## considered for the source radius
    irad = aprad                         ## (same as above) ...inner radius
    orad = 5+aprad                      ##                 ...outer radius

#    Kccd = 0.77999997                                ## CCD specific inputs
#    saturation = 60000

    ## *******<From aper1.py>**********

    scidatacrop = scidata[row-orad:row+orad+2,col-orad:col+orad+2]
    [dimx,dimy] = scidatacrop.shape

    rowcrop = colcrop = orad+0.5                    ## Expected center of the star
                                                    ## in the cropped coordinates
    [dimx,dimy] = scidatacrop.shape 

    ixsrc = np.zeros([dimx,dimy])                   ## Pull out array of pixels
    ixsrc_vals = []                                 ## in the 'source' region
    for a in range(0,dimy):                         ## (where the star is)
        for b in range(0,dimx):
            if ((a-colcrop)**2 + (b-rowcrop)**2) <= rad**2:
                ixsrc[b,a] = 1
                ixsrc_vals.append(scidatacrop[b,a])

    ixsky = np.zeros([dimx,dimy])                   ## Pull out array of pixels
    ixsky_vals = []                                 ## in the 'sky' region
    for a in range(0,dimy):                         ## (background sky, no stars)
        for b in range(0,dimx):
            if ((a-colcrop)**2 + (b-rowcrop)**2) <= orad**2 and (
                (a-colcrop)**2 + (b-rowcrop)**2) >= irad**2:
                ixsky[b,a] = 1
                ixsky_vals.append(scidatacrop[b,a])
    #print ixsrc_vals
    maxval = max(ixsrc_vals)
    sky = np.median(ixsky_vals)                     ## Take the source-background 
    pix = np.array(ixsrc_vals) - sky                ## sum and divide by CCD gain
    sig = np.sqrt(np.abs(np.array(ixsrc_vals))/Kccd)**2        ## to get ADU counts
    sig = math.sqrt(np.sum(sig))
    ssig = np.std(np.array(ixsky_vals)/Kccd)*math.sqrt(len(ixsky_vals))
    flx = np.sum(pix)/Kccd
    err = math.sqrt(sig**2 + ssig**2)
    if math.isnan(flx) == True:
        flx = 1.0
    if math.isnan(err) == True:
        err = 1.0
    if plots == 'on':
        
#        plt.clf()
        #fig = plt.figure()
        plt.subplot(211)
        img=plt.imshow(scidata)                         ## Plot image centered on star,
        plt.xlim(col-1*orad,col+1*orad)                 ## set colorbar accordingly
        plt.ylim(row+1*orad,row-1*orad)
        #img.set_clim([float(sky),float(max(ixsrc_vals))])
        img.set_clim([5000,10000])
        #img.set_clim([100,10000])  ## standard scale
        #img.set_clim([-10000,10000])
        img.set_interpolation('nearest')
#        plt.colorbar()
        #plt.draw()

        
        p = np.arange(0,360)*(math.pi/180)
        def rcos1(a): return col+irad*math.cos(a)       ## Plot inner radius circle
        def rsin1(a): return row+irad*math.sin(a)
        xc1 = map(rcos1,p)
        yc1 = map(rsin1,p)
        def rcos2(a): return col+orad*math.cos(a)       ## Plot outer radius circle
        def rsin2(a): return row+orad*math.sin(a)
        xc2 = map(rcos2,p)
        yc2 = map(rsin2,p)
        plt.plot(xc1,yc1,'r',linewidth=4)
        plt.plot(xc2,yc2,'r',linewidth=4)
        plt.draw()
        time.sleep(1)

    ## *******</from aper1.py>**********

    return [flx, err, maxval]
