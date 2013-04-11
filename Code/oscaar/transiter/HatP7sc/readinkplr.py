import pyfits
import uncertainties

hdus=pyfits.open('kplr010666592-2009166044711_slc.fits')

timedays = hdus[1].data.TIME
timecorr = hdus[1].data.TIMECORR
sapflux = hdus[1].data.PDCSAP_FLUX
errsapflux = hdus[1].data.PDCSAP_FLUX_ERR

#MJD = hdus[1].data.MJD
b=51184.336
aa=sapflux/51150.0
#Rplan=1.363*Rj
#RK12=1.84*Rsun
#Rj/Rsun = 0.10051