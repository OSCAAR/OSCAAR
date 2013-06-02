import numpy as np
import cPickle
import os
from glob import glob
from urllib import urlopen
import urllib2
import oscaar
from time import time
from os.path import getmtime


def internet_connected():
    '''If internet connection is available, return True.'''
    try:
        response=urllib2.urlopen('http://www.google.com',timeout=10)
        return True
    except urllib2.URLError as err: pass
    return False

def downloadAndPickle():
    pklDatabaseName = os.path.join(os.path.dirname(oscaar.__file__),'extras','knownSystemParameters','exoplanetDB.pkl')	 ## Name of exoplanet database C-pickle
    pklDatabasePaths = glob(pklDatabaseName)   ## list of files with the name pklDatabaseName in cwd
    csvDatabaseName = os.path.join(os.path.dirname(oscaar.__file__),'extras','knownSystemParameters','exoplanets.csv')  ## Path to the text file saved from exoplanets.org
    csvDatabasePaths = glob(csvDatabaseName)

    '''First, check if there is an internet connection.'''

    if internet_connected():
        print "Internet connection detected."
    else:
        print "WARNING: This script assumes that you're connected to the internet. This script may crash if you do not have an internet connection."

    '''If there's a previously archived database pickle in this current working 
        directory then use it, if not, grab the data from exoplanets.org in one big CSV file and make one.
        If the old archive is >14 days old, grab a fresh version of the database from exoplanets.org.
        '''
    if csvDatabasePaths == []:
        print 'No local copy of exoplanets.org database. Downloading one...'
        rawCSV = urlopen('http://www.exoplanets.org/csv-files/exoplanets.csv').read()
        saveCSV = open(csvDatabaseName,'w')
        saveCSV.write(rawCSV)
        saveCSV.close()
    else: 
        '''If the local copy of the exoplanets.org database is >14 days old, download a new one'''
        secondsSinceLastModification = time() - getmtime(csvDatabaseName) ## in seconds
        daysSinceLastModification = secondsSinceLastModification/(60*60*24*30)
        if daysSinceLastModification > 14:
            print 'Your local copy of the exoplanets.org database is >14 days old. Downloading a fresh one...'
            rawCSV = urlopen('http://www.exoplanets.org/csv-files/exoplanets.csv').read()
            saveCSV = open(csvDatabaseName,'w')
            saveCSV.write(rawCSV)
            saveCSV.close()
        else: print "Your local copy of the exoplanets.org database is <14 days old. That'll do."

    if len(pklDatabasePaths) == 0:
        print 'Parsing '+os.path.split(csvDatabaseName)[1]+', the CSV database from exoplanets.org...'
        rawTable = open(csvDatabaseName).read().splitlines()
        labels = rawTable[0].split(',')
        labelUnits = rawTable[1].split(',')
        rawTableArray = np.zeros([len(rawTable),len(labels)])
        exoplanetDB = {}
        planetNameColumn = np.arange(len(labels))[np.array(labels,dtype=str)=='NAME'][0]
        for row in range(1,len(rawTable)): 
            splitRow = rawTable[row].split(',')
            exoplanetDB[splitRow[planetNameColumn]] = {}	## Create dictionary for this row's planet
            for col in range(0,len(splitRow)):
                exoplanetDB[splitRow[planetNameColumn]][labels[col]] = splitRow[col]
        
        output = open(pklDatabaseName,'wb')
        cPickle.dump(exoplanetDB,output)
        output.close()
    else: 
        print 'Using previously parsed database from exoplanets.org...'
        ''' Import data from exoplanets.org, parsed by
            exoplanetDataParser1.py'''
        inputFile = open(pklDatabaseName,'rb')
        exoplanetDB = cPickle.load(inputFile)
        inputFile.close()
    
    return exoplanetDB
