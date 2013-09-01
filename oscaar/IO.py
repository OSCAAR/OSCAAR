'''OSCAAR v2.0 
   Module for differential photometry
   Developed by Brett Morris, 2011-2013'''
import numpy as np
from numpy import linalg as LA
import pyfits
from matplotlib import pyplot as plt
import matplotlib.cm as cm
from scipy import ndimage, optimize
from time import sleep
import shutil
from glob import glob
from re import split
import cPickle
from shutil import copy
import os

def cd(a=None):

    '''
    Change to a different directory than the current one.
    
    Parameters
    ----------
    a : string
        Location of the directory to change to.
    
    Notes
    -----
    If `a` is empty, this function will change to the parent directory.
    '''

    if a is None:
        os.chdir(os.pardir)
    else:
        os.chdir(str(a))

def cp(a, b):

    '''
    Copy a file to another location.
    
    Parameters
    ----------
    a : string
        Path of the file to be copied.
    b : string
        Location where the file will be copied to. 
    '''

    copy(str(a),str(b))

def parseRegionsFile(regsPath):

    '''
    Parse a regions file for a set of data.

    Parameters
    ----------
    regsPath : string
        Location of the regions file to be parsed.
    
    Returns
    -------
    init_x_list : array
        An array containing the x-values of the parsed file.
    init_y_list : array
        An array containing the y-values of the parsed file.
    '''

    regionsData = open(regsPath,'r').read().splitlines()
    init_x_list = []
    init_y_list = []
    for i in range(0,len(regionsData)):
        if regionsData[i][0:6] == 'circle':
            y,x = split("\,",split("\(",regionsData[i])[1])[0:2]
            init_y_list.append(float(y))
            init_x_list.append(float(x))
    return init_x_list,init_y_list
    
def save(data,outputPath):

    '''
    Save everything in oscaar.dataBank object <data> to a python pickle using cPickle.

    Parameters
    ----------
    data : string
        File location of an oscaar.dataBank() object to save.
    outputPath : string
        Path to which the numpy-pickle will be saved.   
    '''

    if glob(outputPath) > 0 or glob(outputPath+os.sep+'oscaarDataBase.pkl') > 0 or glob(outputPath+'.pkl') > 0: ## Over-write check
        print 'WARNING: could potentially overwrite the most recent oscaarDataBase.pkl'
    
    if outputPath.endswith('.pkl') or outputPath.endswith('.PKL'):
        outputName = outputPath
    elif outputPath[-1] == os.sep: 
        outputName = outputPath+'oscaarDataBase.pkl'
    else: 
        outputName = outputPath+'.pkl'

    try: del data.convertToJD   ## cPickle can not save functions, so delete the function data.convertToJD before saving the object data
    except: pass
    
    output = open(outputName,'wb')
    cPickle.dump(data,output)
    output.close()

def load(inputPath):

    '''
    Load everything from a oscaar.dataBank() object in a python pickle using cPickle.
     
    Parameters
    ----------
    inputPath : string
        File location of an oscaar.dataBank() object to save into a pickle.
     
    Returns
    -------
    data : string
        Path for the saved numpy-pickle.
    '''

    inputFile = open(inputPath,'rb')
    data = cPickle.load(inputFile)
    inputFile.close()
    return data

def plottingSettings(trackPlots,photPlots,statusBar=True):

    '''
    **Description :** Function for handling matplotlib figures across OSCAAR methods.
    
    Parameters
    ----------
    trackPlots : bool
        Used to turn the astrometry plots on and off.
        
    photPlots : bool
        Used to turn the aperture photometry plots on and off.
        
    statusBar : bool, optional
        Used to turn the status bar on and off.
       
    Returns
    -------
    [fig,subplotsDimensions,photSubplotsOffset] : [figure, int, int]
        An array with 3 things. The first is the figure object from matplotlib that will be displayed while 
        OSCAAR is running. The second is the integer value that designates the x and y dimensions of the 
        subplots within the figure plot. The third is the the number correlating to the location of the 
        aperture photometry plots, which depends on the values of trackPlots and photPlots.
    statusBarFig : figure
        A figure object from matplotlib showing the status bar for completion.
    statusBarAx : figure.subplot
        A subplot from a matplotlib figure object that represents what is drawn.
    
    Notes
    -----
    This list returned by plottingSettings() should be stored to a variable, and used as an
    argument in the phot() and trackSmooth() methods.
    '''

    if trackPlots or photPlots: 
        plt.ion()
        statusBarFig = 0 
        statusBarAx = 0
    if trackPlots and photPlots:
        fig = plt.figure(num=None, figsize=(18, 3), facecolor='w',edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        subplotsDimensions = 140
        photSubplotsOffset = 3
        statusSubplotOffset = 6
        statusBarAx = None
        fig.canvas.set_window_title('oscaar2.0') 
    elif photPlots and not trackPlots:
        fig = plt.figure(num=None, figsize=(5, 5), facecolor='w',edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        subplotsDimensions = 110
        photSubplotsOffset = 0
        statusSubplotOffset = 2
        statusBarAx = None
        fig.canvas.set_window_title('oscaar2.0') 
    elif trackPlots and not photPlots:
        fig = plt.figure(num=None, figsize=(13.5, 4), facecolor='w',edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        subplotsDimensions = 130
        photSubplotsOffset = 0
        statusSubplotOffset = 5
        statusBarAx = None
        fig.canvas.set_window_title('oscaar2.0') 
    elif not trackPlots and not photPlots:
        statusBarFig = plt.figure(num=None, figsize=(5, 2), facecolor='w',edgecolor='k')
        statusBarFig.canvas.set_window_title('oscaar2.0') 
        statusBarAx = statusBarFig.add_subplot(111,aspect=10)
        statusBarAx.set_title('oscaar2.0 is running...')
        statusBarAx.set_xlim([0,100])
        statusBarAx.set_xlabel('Percent Complete (%)')
        statusBarAx.get_yaxis().set_ticks([])
        subplotsDimensions = 111
        photSubplotsOffset = 0
        fig = 0
        subplotsDimensions=0
        photSubplotsOffset = 0
    return [fig,subplotsDimensions,photSubplotsOffset],statusBarFig,statusBarAx
    