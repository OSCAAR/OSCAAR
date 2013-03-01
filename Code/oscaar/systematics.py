import numpy as np
import pyfits
from matplotlib import pyplot as plt
from glob import glob

def meanDarkFrame(darksPath):
    '''Return the mean dark frame calculated from each dark frame in darksPath'''
    darkFiles = glob(darksPath)
    [dim1, dim2] = np.shape(pyfits.open(darkFiles[0])[0].data)
    ## Create N-dimensional array for N dark frames, where the first 
    ##    two dimensions are the dimensions of the first image
    darks = np.zeros([len(darkFiles),dim1,dim2])
    ## Return mean of all darks
    for i in range(0,len(darkFiles)):
        darks[i,:,:] = pyfits.open(darkFiles[i])[0].data
    return np.mean(darks,axis=0)

def masterFlatMaker(flatImagesPath,flatDarkImagesPath,masterFlatSavePath,plots=False):
    '''Make a master flat by taking a mean of a group of flat fields
    
    INPUTS: flatImagesPath - Path to the flat field exposures
    
            flatDarkImagesPath - Path to the flat field darks
            
            masterFlatSavePath - Where to save the master flat that is created
            
            plots - Plot the master flat on completion when plots=True
    '''
    ## Create zero array with the dimensions of the first image for the flat field
    [dim1, dim2] = np.shape(pyfits.open(flatImagesPath[0])[0].data)
    flatSum = np.zeros([dim1, dim2])

    ## Create N-dimensional array for N dark frames, where the first 
    ##    two dimensions are the dimensions of the first image
    darks = np.zeros([len(flatDarkImagesPath),dim1,dim2])

    ## Take mean of all darks
    for i in range(0,len(flatDarkImagesPath)):
        darks[i,:,:] = pyfits.open(flatDarkImagesPath[i])[0].data
    dark = np.mean(darks,axis=0)

    ## Sum up all flat fields, subtract mean dark frame from each flat
    for flatImage in flatImagesPath:
        flatSum += pyfits.open(flatImage)[0].data - dark
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
    pyfits.writeto(masterFlatSavePath+'.fits',masterFlat)

