##darkfram3.py
##  Called by photom6.py
##  Opens dark frames, averages them,
##   sends average to global "dark_avg",
##   repeats similar procedure for flat fields

import glob

print "Loading and averaging dark frames..."
files = glob.glob(darkLoc)

global dark_avg
for i in range(0,len(files)):
    hdulist = pyfits.open(files[i])
    scidata = hdulist[0].data
    if i==0:
        dark_avg = scidata
    dark_avg = (dark_avg + scidata)
dark_avg = dark_avg/len(files)

os.system("ls "+flatLoc+" > filelists/flatnames.txt")
files = open('filelists/flatnames.txt','r').read().splitlines()

global flat_field
flat_field=0
for i in range(0,len(files)):
    hdulist = pyfits.open(files[i])
    scidata = hdulist[0].data
    flat_field += (scidata-dark_avg)

flat_field = flat_field/np.mean(flat_field)
