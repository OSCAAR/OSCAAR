'''Simple flat fielding routine for oscaar2.0. Creates a mean dark frame,
   then sums each dark corrected flat field, and normalizes the sum.'''

import numpy as np
from pyfits import open as pyfitsOpen, writeto
from glob import glob
from matplotlib import pyplot as plt

## Inputs for GUI: Paths to the flat fields, the flat-darks, and output path for the master flat
flatImagesPath = glob('/Users/bmorris/Desktop/Exoplanets/20120616/flats/flatSky-???.fit')
flatDarkImagesPath = glob('/Users/bmorris/Desktop/Exoplanets/20120616/flats/flatSky-???d.fit')
masterFlatSavePath = '/Users/bmorris/Desktop/Exoplanets/20120616/flats/tmpMasterFlat'
plots = True

## Create zero array with the dimensions of the first image for the flat field
[dim1, dim2] = np.shape(pyfitsOpen(flatImagesPath[0])[0].data)
flatSum = np.zeros([dim1, dim2])

## Create N-dimensional array for N dark frames, where the first 
##    two dimensions are the dimensions of the first image
darks = np.zeros([len(flatDarkImagesPath),dim1,dim2])

## Take mean of all darks
for i in range(0,len(flatDarkImagesPath)):
    darks[i,:,:] = pyfitsOpen(flatDarkImagesPath[i])[0].data
dark = np.mean(darks,axis=0)

## Sum up all flat fields, subtract mean dark frame from each flat
for flatImage in flatImagesPath:
    flatSum += pyfitsOpen(flatImage)[0].data - dark
## Divide the summed flat fields by their mean to obtain a flat frame
masterFlat = flatSum/np.mean(flatSum)

if plots:
    ## If plots == True, plot the resulting master flat
    fig = plt.figure()
    a = plt.imshow(masterFlat,interpolation='nearest')
    a.set_cmap('gray')
    plt.title('Normalized Master Flat Field')
    fig.colorbar(a)
    fig.canvas.set_window_title('oscaar2.0 - Master Flat') 
    plt.show()


## Write out both a Numpy pickle (.NPY) and a FITS file
np.save(masterFlatSavePath+'.npy',masterFlat)
writeto(masterFlatSavePath+'.fits',masterFlat)