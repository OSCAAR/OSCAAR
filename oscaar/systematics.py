import numpy as np
import pyfits
from matplotlib import pyplot as plt
from glob import glob

def meanDarkFrame(darksPath):
    '''
    Returns the mean dark frame calculated from each dark frame in `darksPath`
    
    Parameters
    ----------
    darksPath : list of strings
        Paths to the dark frames
        
    Returns
    -------
        The mean of the dark frames in `darksPath`
    
    '''
    #darksPath = glob(darksPath)
    [dim1, dim2] = np.shape(pyfits.open(darksPath[0])[0].data)
    ## Create N-dimensional array for N dark frames, where the first 
    ##    two dimensions are the dimensions of the first image
    darks = np.zeros([len(darksPath),dim1,dim2])
    ## Return mean of all darks
    for i in range(0,len(darksPath)):
        darks[i,:,:] = pyfits.open(darksPath[i])[0].data
    return np.mean(darks,axis=0)

def standardFlatMaker(flatImagesPath,flatDarkImagesPath,masterFlatSavePath,plots=False):
    '''Make a master flat by taking a mean of a group of flat fields
    
    Parameters
    ----------
    flatImagesPath : string
        Path to the flat field exposures

    flatDarkImagesPath : string
        Path to the flat field darks
    
    masterFlatSavePath : string
        Where to save the master flat that is created
    
    plots : bool
        Plot the master flat on completion when plots=True
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

    masterFlat[masterFlat == 0] += np.finfo(np.float).eps 	## If pixel is 0, make it just above zero

    if plots:
        ## If plots == True, plot the resulting master flat
        fig = plt.figure()
        a = plt.imshow(masterFlat,interpolation='nearest')
        a.set_cmap('gray')
        plt.title('Normalized Master Flat Field')
        fig.colorbar(a)
        fig.canvas.set_window_title('oscaar2.0 - Master Flat') 
        plt.show()

    ## Write out a FITS file
    #np.save(masterFlatSavePath+'.npy',masterFlat)
    if masterFlatSavePath.endswith('.fits') or masterFlatSavePath.endswith('.fit'):
        pyfits.writeto(masterFlatSavePath,masterFlat)
    else: 
        pyfits.writeto(masterFlatSavePath+'.fits',masterFlat)
        
def twilightFlatMaker(flatImagesPath,flatDarkImagesPath,masterFlatSavePath,plots=False):
    '''
    Make a master flat using a series of images taken at twilight
    by fitting the individual pixel intensities over time using least-squares
    and use the intercept as the normalizing factor in the master flat.
    
    INPUTS: 
    flatImagesPath : string
        Path to the flat field exposures

    flatDarkImagesPath : string
        Path to the flat field darks
    
    masterFlatSavePath : string
        Where to save the master flat that is created
    
    plots : bool
        Plot the master flat on completion when plots=True
    '''
    ## Create zero array with the dimensions of the first image for the flat field
    [dim1, dim2] = np.shape(pyfits.getdata(flatImagesPath[0]))
    flatSum = np.zeros([dim1, dim2])

    ## Create N-dimensional array for N dark frames, where the first 
    ##    two dimensions are the dimensions of the first image
    darks = np.zeros([len(flatDarkImagesPath),dim1,dim2])

    ## Take mean of all darks
    for i in range(0,len(flatDarkImagesPath)):
        darks[i,:,:] = pyfits.getdata(flatDarkImagesPath[i])
    dark = np.mean(darks,axis=0)

    ## Create N-dimensional array for N flat frames, where the first 
    ##    two dimensions are the dimensions of the first image
    flats = np.zeros([len(flatImagesPath),dim1,dim2])

    ## Assemble data cube of flats
    for i in range(0,len(flatImagesPath)):
        flats[i,:,:] = pyfits.getdata(flatImagesPath[i]) - dark

    def linearFitIntercept(x,y):
        '''Use least-squares to find the best-fit y-intercept '''
        return np.linalg.lstsq(np.vstack([x,np.ones(len(x))]).T,y)[0][1] ## Returns intercept

    flat = np.zeros([dim1,dim2])
    for i in range(0,dim1):
        print 'Master flat computing step:',i+1,'of',dim1
        for j in range(0,dim2):
            flat[i,j] = linearFitIntercept(range(len(flats[:,i,j])),flats[:,i,j])

    masterFlat = flat/np.mean(flat)

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