import numpy as np

class starObj:
    def __init__(self, num):
        '''Extract the fluxes and errors from aper_out and the (x,y)
           position from track_out for a star with padded number "num".'''
        self.num = str(num)
        aperout = open('aper_out/phot_out_'+str(self.num)+'.log').read().splitlines()
        aperflx = np.zeros([len(aperout),1])
        apererr = np.zeros([len(aperout),1])
        flags = False
        for i in range(0,len(aperout)):
            aperflx[i] = float(aperout[i].split()[0])
            apererr[i] = float(aperout[i].split()[1])
            if len(aperout[i].split())==3:
                flags = True
        self.aperflx = aperflx
        self.apererr = apererr
        self.flag = flags
        
        trackout = open('track_out/star'+str(self.num)+'_coord.log').read().splitlines()
        trackx = np.zeros([len(trackout),1])
        tracky = np.zeros([len(trackout),1])
        for i in range(0,len(trackout)):
            trackx[i] = float(trackout[i].split()[0])
            tracky[i] = float(trackout[i].split()[1])
        self.x = trackx
        self.y = tracky

        timeout = open('time_out/time.log').read().splitlines()
        times = []
        for i in range(0,len(trackout)):
            times.append(float(timeout[i]))
        self.times = times

    def time(self):
        '''Returns JD of each observation from FITS header'''
        return self.times

        
    def flux(self):
        '''Returns this star object's instrumental flux measurements'''
        return self.aperflx

    def err(self):
        '''Returns this star object's instrumental flux measurement
           error'''
        return self.apererr

    def trackx(self):
        '''Returns this star object's x pixel position '''
        return self.x
    
    def tracky(self):
        '''Returns this star object's y pixel position '''
        return self.y
    
    def flags(self):
        '''Returns True if the star has an asterisk (*)
           in the aperture photometry output, otherwise
           returns False'''
        return self.flag
    def number(self):
        '''Returns the star number entered at initialization'''
        return int(self.num)

    
class fluxArr:
    def __init__(self, starobj):
        '''Create an array for star fluxes of the same length
           as the length of the flux array stored in the object
           "starobj"'''
        self.fluxarr = np.zeros([len(starobj.aperflx),1],dtype=float)
        self.fluxerr = np.zeros([len(starobj.apererr),1],dtype=float)
        self.starcount = 0.0

    def arr(self):
        '''Return the array of fluxes stored in this object'''
        return self.fluxarr

    def avgFlux(self,starobj):
        '''Take the average of the fluxes of starobj and
           the stored fluxArr object, store that as the new
           flux array'''
        self.starcount += 1.0
        self.fluxarr = (self.arr()*(self.starcount-1) + starobj.flux()) / float(self.starcount)
        fluxerr = abs((2.5*starobj.err())/(starobj.flux()*np.log(10)))
        if self.starcount == 1:
            self.fluxerr = fluxerr
        else:
            self.fluxerr = (self.err()**2 + (fluxerr)**2)**0.5
        
    def starCount(self):
        '''Returns the number of stars that have been averaged
           into this flux array object'''
        return self.starcount

    def magScale(self):
        '''Returns flux array in a magnitude scale,
           ie:   -2.5*log10(flux)'''
        return 2.5*np.log10(self.arr())

    def err(self):
        return self.fluxerr

class diffArr:
    def __init__(self,inarray,Err):
        self.inarray = inarray
        self.Err = Err
    def arr(self):
        return self.inarray
    def err(self):
        return self.Err
    
    def calcMedian(self,mwidth,timearr):
        arrlen = max(np.shape(self.arr()))
        scaler = max(timearr)-min(timearr)
        self.median_y = []
        self.median_x = []
        for i in range(0,arrlen/mwidth):
            self.median_y.append(np.median(self.arr()[(i*mwidth):((1+i)*mwidth)]))
            self.median_x.append( min(timearr)+(0.5*(float(i*mwidth)+float((1+i)*mwidth)))*(scaler/arrlen) )

    def medianx(self):
        return self.median_x
    def mediany(self):
        return self.median_y







