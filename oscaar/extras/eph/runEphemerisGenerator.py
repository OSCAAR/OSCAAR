'''
This tool generates custom transit and/or eclipse ephemerides
for your observatory and the dates you choose. You can also choose
a limiting target star magnitude (V) so that you don't get a list 
flooded by targets that are too dim to observe at your with your
equipment. Similarly, you can choose a lower limit on the transit
depths, so that you'll generate a calendar of events that you'll
be able to produce observe with decent signal/noise.

The exoplanet data are loaded from exoplanets.org, so please run 
this script while connected to the internet so that you can have
the most up-to-date exoplanet data.

Core developer: Brett Morris (NASA GSFC)
'''

from calculateEphemerides import *

parFile = 'maunaKea.par'   ## Path to observatory input parameter file

calculateEphemerides(parFile)
print 'runEpehemerisGenerator.py: Done.'