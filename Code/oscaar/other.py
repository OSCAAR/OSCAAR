import shutil
from re import split
import cPickle
from shutil import copy
import os
def paddedStr(num,pad):
    '''Return the number num padded with zero-padding of length pad'''
    strlen = len(str(num))
    lenpad = pad-strlen
    return str((lenpad*'0')+str(num))

def homeDir():
    """Set the current directory to oscaar's home directory"""
    if 'OSCAAR' in os.getcwd().split('\\'):
        while os.getcwd().split('\\')[len(os.getcwd().split('\\'))-1] != 'OSCAAR':
            os.chdir(os.pardir)

def overWriteCheck(filename, checkfiles, varcheck):
    """Checks to see if a particular file should be overwritten based on whether varcheck is on or off"""
    overcheck = None
    for i in range(0, len(checkfiles)):
        if checkfiles[i]== filename and varcheck == 'on':
            overcheck = raw_input('WARNING: Overwrite /' + filename + '/ ? (Y/n): ')
            break
    if overcheck == '' or overcheck == 'Y' or overcheck == 'y':
        shutil.rmtree(filename)
        os.mkdir(filename)
        
