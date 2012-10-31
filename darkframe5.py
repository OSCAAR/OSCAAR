## darkframe5.py for oscaar1.1.0

##  Opens dark frames, averages them,
##   sends average to global "dark_avg",
##   sums flat fields and normalizes them

print "Loading and averaging dark frames..."
os.system("ls "+darkLoc+" > filelists/darknames.txt")
files = open('filelists/darknames.txt','r').read().splitlines()

global dark_avg
for i in range(0,len(files)):
    hdulist = pyfits.open(files[i])
    scidata = hdulist[0].data
    if i==0:
        dark_avg = scidata
    dark_avg = (dark_avg + scidata)/2.

os.system("ls "+flatLoc+" > filelists/flatnames.txt")
files = open('filelists/flatnames.txt','r').read().splitlines()

global flat_field
flat_field=0
for i in range(0,len(files)):
    hdulist = pyfits.open(files[i])
    scidata = hdulist[0].data
    flat_field += (scidata-dark_avg)

flat_field = flat_field/np.mean(flat_field)
