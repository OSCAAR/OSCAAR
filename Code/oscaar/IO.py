'''oscaar v2.0 
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
    """Change to directory a where a is a 
       string inside of single quotes. If a
       is empty, changes to parent directory"""
    if a is None:
        os.chdir(os.pardir)
    else:
        os.chdir(str(a))

def cp(a, b):
    """Copy file a to location b where a,b are
       strings inside of single quotes"""
    copy(str(a),str(b))

def parseRegionsFile(regsPath):
    '''Parse the DS9 regions file (written in .txt format) which contains
       the initial guesses for the stellar centroids, in the following format:
             "circle(<y-center>,<x-center>,<radius>)"
       The reversed x,y order comes from the different directions that FITS files
       are read-in with DS9 and PyFits.
       
       INPUTS: regsPath - Path to the DS9 regions file with stellar centroid coords
       
       RETURNS: init_x_list - Inital estimates of the x-centroids
       
                init_y_list - Inital estimates of the y-centroids
       
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
    
    INPUTS: data - oscaar.dataBank() object to save
    
            outputPath - Path for the saved numpy-pickle.
    '''
    if glob(outputPath) > 0 or glob(outputPath+'/oscaarDataBase.pkl') > 0 or glob(outputPath+'.pkl') > 0: ## Over-write check
        print 'WARNING: overwriting the most recent oscaarDataBase.pkl'
    
    if outputPath[len(outputPath)-4:len(outputPath)] == '.pkl':
        outputName = outputPath
    elif outputPath[-1] == '/': 
        outputName = outputPath+'oscaarDataBase.pkl'
    else: 
        outputName = outputPath+'.pkl'
    
    output = open(outputName,'wb')
    cPickle.dump(data,output)
    output.close()

def load(inputPath):
    '''
    Load everything from a oscaar.dataBank() object in a python pickle using cPickle.
    
    INPUTS: data - oscaar.dataBank() object to save
    
            outputPath - Path for the saved numpy-pickle.
    '''
    inputFile = open(inputPath,'rb')
    data = cPickle.load(inputFile)
    inputFile.close()
    return data

def plottingSettings(trackPlots,photPlots):
    '''
    Function for handling matplotlib figures across oscaar methods. 
    INPUTS: trackPlots - boolean for turning astrometry plots on and off
            photPlots - boolean for turning aperture photometry plots on and off
            
    RETURNS a list containing:
            fig - the figure object from matplotlib that will be displayed while oscaar is running
            subplotsDimensions - integer value that designates the x and y dimensions of the subplots
                                 within the figure plot
            photSubplotsOffset - if photPlots is True and trackPlots is True, then photSubplotsOffset
                                 will ensure that the aperture photometry plots are on the right-most
                                 subplot, otherwise it will assume that the aperture photometry plots
                                 are the only/first subplot.
            
            This list returned by plottingSettings() should be stored to a variable, and used as an
            argument in the phot() and trackSmooth() methods.
    '''
    if trackPlots or photPlots: plt.ion()   ## Turn on interactive plotting
    if trackPlots and photPlots:
        fig = plt.figure(num=None, figsize=(18, 3), facecolor='w',edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        subplotsDimensions = 140
        photSubplotsOffset = 3
        fig.canvas.set_window_title('oscaar2.0') 
    elif photPlots and not trackPlots:
        fig = plt.figure(num=None, figsize=(5, 5), facecolor='w',edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        subplotsDimensions = 110
        photSubplotsOffset = 0
        fig.canvas.set_window_title('oscaar2.0') 
    elif trackPlots and not photPlots:
        fig = plt.figure(num=None, figsize=(13.5, 4), facecolor='w',edgecolor='k')
        fig.subplots_adjust(wspace = 0.5)
        subplotsDimensions = 130
        photSubplotsOffset = 0
        fig.canvas.set_window_title('oscaar2.0') 
    else: 
        fig = plt.figure()
        subplotsDimensions = 110
        photSubplotsOffset = 0
    return [fig,subplotsDimensions,photSubplotsOffset]

