'''
Created on Feb 19, 2013

methods for calculating ephemerides

@author: bmmorris
'''

import numpy as np
from matplotlib import pyplot as plt
import matplotlib.cm as cm
import colorsys

class eph():
	
	def __init__(self,startSem,endSem):
		self.startSem = startSem
		self.endSem = endSem
		self.stars = {}
		self.allKeysT = []
		self.allKeysE = []
		self.allMidE = []
		self.allMidT = []
		self.bufferTime = 0.1  ## 0.1666 JD = 4 hours (four hours between sunset/sunrise and acceptable midtransit)
						  #0.08 ## JD = 2 hrs; only count complete transits with space bufferTime before and after transit
		self.UToffset = -0.43184 ## Hawaiian time zone conversion from UTC: -0.416666 = -10 hours (UTC), 
		## Convert 155.46 deg to hours: 10.36 hours, or 0.43184 days (JD)
		self.bars = 0.08
	def addStar(self,name,Tc,pmTc,P,pmP,V,K):
		self.stars[str(name)] = {}
		self.stars[str(name)]['Tc'] = Tc
		self.stars[str(name)]['pmTc'] = pmTc
		self.stars[str(name)]['P'] = P
		self.stars[str(name)]['pmP'] = pmP
		self.stars[str(name)]['V'] = V
		self.stars[str(name)]['K'] = K
		self.stars[str(name)]['MidT'] = self.midTransit(Tc,pmTc,P,pmP,name)
		self.stars[str(name)]['MidE'] = self.midEclipse(Tc,pmTc,P,pmP,name)

	def midTransit(self,Tc, pmTc, P, pmP,name):
		timeRange = np.arange(0,5000)
		transitTimes = Tc + P*timeRange
		pmTransitTimes = np.sqrt(pmTc**2 + (pmP*timeRange)**2)
		transitTimesInSem = transitTimes[(transitTimes < self.endSem)*(transitTimes > self.startSem)]#,pmTransitTimes[(pmTransitTimes < self.endSem)*(pmTransitTimes > self.startSem)][0][0]
		transitTimesInSemOffset = transitTimesInSem + self.UToffset	## offset for hawaiian time
		transitTimesAtNight = transitTimesInSem[(transitTimesInSemOffset - np.floor(transitTimesInSemOffset) > 0.25+self.bufferTime)*(transitTimesInSemOffset - np.floor(transitTimesInSemOffset) < 0.75-self.bufferTime)]
		for i in transitTimesAtNight: self.allKeysT.append(name)
		for time in transitTimesAtNight: self.allMidT.append(time)
		return transitTimesAtNight
	
	def midEclipse(self,Tc, pmTc, P, pmP,name):
		timeRange = np.arange(0,5000)
		eclipseTimes = Tc + P*(0.5 + timeRange)
		pmEclipseTimes = np.sqrt(pmTc**2 + (pmP*timeRange)**2)
		eclipseTimesInSem = eclipseTimes[(eclipseTimes < self.endSem)*(eclipseTimes > self.startSem)]#,pmEclipseTimes[(pmEclipseTimes < self.endSem)*(pmEclipseTimes > self.startSem)][0][0]
		eclipseTimesInSemOffset = eclipseTimesInSem + self.UToffset	## offset for hawaiian time
		eclipseTimesAtNight = eclipseTimesInSem[(eclipseTimesInSemOffset - np.floor(eclipseTimesInSemOffset) > 0.25+self.bufferTime)*(eclipseTimesInSemOffset - np.floor(eclipseTimesInSemOffset) < 0.75-self.bufferTime)]
		for i in eclipseTimesAtNight: self.allKeysE.append(name)
		for time in eclipseTimesAtNight: self.allMidE.append(time)
		return eclipseTimesAtNight
	
#	def midEclipseOld(self,Tc, pmTc, P, pmP,name):
#		timeRange = np.arange(0,5000)
#		eclipseTimes = Tc + P*(timeRange + 0.5)
#		pmEclipseTimes = np.sqrt(pmTc**2 + (pmP*timeRange)**2)
#		return eclipseTimes[(eclipseTimes < self.endSem)*(eclipseTimes > self.startSem)],pmEclipseTimes[(pmEclipseTimes < self.endSem)*(pmEclipseTimes > self.startSem)]

	def getMidT(self,star):
		return self.stars[str(star)]['MidT']

	def getMidE(self,star):
		return self.stars[str(star)]['MidE']

	def getVmag(self,star):
		return self.stars[str(star)]['V']

	def getAllVmags(self):
		Vmags = []
		for star in self.stars:
			Vmags.append(self.stars[star]['V'])
		return np.array(Vmags)


	def getKmag(self,star):
		return self.stars[str(star)]['K']

	def getAllKmags(self):
		Kmags = []
		for star in self.stars:
			Kmags.append(self.stars[star]['K'])
		return np.array(Kmags)

	def plotTransits(self,axis,format,alphaSetting,scaleSize=False,showLabels=False,showMags=False,yOffset=0.0):
		def get_color(color):
			for hue in range(color):
				hue = 1. * hue / color
				col = [int(x) for x in colorsys.hsv_to_rgb(hue, 1.0, 230)]
				yield "#{0:02x}{1:02x}{2:02x}".format(*col)
		color = get_color(len(self.stars))
		for star in self.stars:
			acolor = next(color)
			#plt.plot(self.getMidT(star),np.zeros_like(self.getMidT(star)),format,alpha=alphaSetting,label=star)
			if scaleSize:
				#mags = 15000./self.getAllVmags()**2#self.getVmag(star)
				mags = 500000./self.getAllKmags()**4#20000./self.getAllKmags()**2.5
				axis.scatter(self.getMidT(star),np.zeros_like(self.getMidT(star)),color=acolor,s=mags,label=star,alpha=alphaSetting)
			else:
				axis.errorbar(self.getMidT(star),np.zeros_like(self.getMidT(star)) + yOffset,xerr=self.bars,label=star,color=acolor,fmt=format,alpha=alphaSetting)


			if showMags:
				labels = [star+', $K_{mag} = '+str(self.getKmag(star))+'$' for i in range(len(self.getMidT(star)))]
			else:
				labels = [star for i in range(len(self.getMidT(star)))]
			if showLabels:
				for label, x, y in zip(labels, self.getMidT(star), np.zeros_like(self.getMidT(star)) + yOffset):
					axis.annotate(
				        label,xy = (x, y), xytext = (0,5), textcoords = 'offset points', ha = 'left', va = 'bottom', rotation=45)
						
		axis.legend(numpoints=1)

		def format_coord(x, y):
			return 'Cursor: '+jd2gd(x,returnString=True)+' UT'
		axis.format_coord = format_coord 

	def plotEclipses(self,axis,format,alphaSetting,showLabels=False,showMags=False,yOffset=0.0):
		def get_color(color):
			for hue in range(color):
				hue = 1. * hue / color
				col = [int(x) for x in colorsys.hsv_to_rgb(hue, 1.0, 230)]
				yield "#{0:02x}{1:02x}{2:02x}".format(*col)
		color = get_color(len(self.stars))
		for star in self.stars:
			acolor = next(color)
			#plt.plot(self.getMidT(star),np.zeros_like(self.getMidT(star)),format,alpha=alphaSetting,label=star)
			axis.errorbar(self.getMidE(star),np.zeros_like(self.getMidE(star)) + yOffset,xerr=self.bars,color=acolor,fmt=format,alpha=alphaSetting,label=star)

			if showMags:
				labels = [star+', $V_{mag} = '+str(self.getVmag(star))+'$' for i in range(len(self.getMidE(star)))]
			else:
				labels = [star for i in range(len(self.getMidE(star)))]
			if showLabels:
				for label, x, y in zip(labels, self.getMidE(star), np.zeros_like(self.getMidE(star)) + yOffset):
					axis.annotate(
				        label, xy = (x, y), xytext = (0,5),textcoords = 'offset points', ha = 'left', va = 'bottom', rotation=45)

		axis.legend(numpoints=1)
		
		def format_coord(x, y):
			return 'Cursor: '+jd2gd(x,returnString=True)+' UT'
		axis.format_coord = format_coord 
	
	def IDdoubleEclipses(self,axis,color='k',ls='-'):
		'''Identify nights with two well separated transits'''
		doubleNights = []
		goodNights = []
		
		for time in range(0,len(self.allMidE)):
			for otherTime in range(0,len(self.allMidE)):
				if time != otherTime and np.abs(self.allMidE[time]-self.allMidE[otherTime]) < 0.5:
					doubleNights.append(self.allMidE[time])
					if np.abs(self.allMidE[time]-self.allMidE[otherTime]) > 0.16:
						goodNights.append(self.allMidE[time])
		for time in goodNights:
			axis.axvline(ymin=0,ymax=1,x=time,color=color,ls=ls)
		return np.unique(goodNights)
	
	def IDdoubleTransits(self,axis,color='k',ls='-'):
		'''Identify nights with two well separated transits'''
		doubleNights = []
		goodNights = []
		
		for time in range(0,len(self.allMidT)):
			for otherTime in range(0,len(self.allMidT)):
				if time != otherTime and np.abs(self.allMidT[time]-self.allMidT[otherTime]) < 0.5:
					doubleNights.append(self.allMidT[time])
					if np.abs(self.allMidT[time]-self.allMidT[otherTime]) > 0.16:
						goodNights.append(self.allMidT[time])
		for time in goodNights:
			axis.axvline(ymin=0,ymax=1,x=time,color=color,ls=ls)
		return np.unique(goodNights)		
	
	def IDdoubles(self,axis,color='k',ls='-'):
		doubleNights = []
		goodNights = []
		
		for time in range(0,len(self.allMidT)):
			for otherTime in range(0,len(self.allMidE)):
				if time != otherTime and np.abs(self.allMidT[time]-self.allMidE[otherTime]) < 0.5:
					doubleNights.append(self.allMidT[time])
					if np.abs(self.allMidT[time]-self.allMidE[otherTime]) > 0.11:
						goodNights.append(self.allMidT[time])
		for time in goodNights:
			axis.axvline(ymin=0,ymax=1,x=time,color=color,ls=ls)		
		return np.unique(goodNights)
					
"""
Functions for handling dates.

Contains:
   gd2jd  -- converts gregorian date to julian date
   jd2gd  -- converts julian date to gregorian date

Wish list:
   Function to convert heliocentric julian date!



These functions were taken from Enno Middleberg's site of useful
astronomical python references:
http://www.astro.rub.de/middelberg/python/python.html

"Feel free to download, use, modify and pass on these scripts, but
please do not remove my name from it." --E. Middleberg
"""

# 2009-02-15 13:12 IJC: Converted to importable function


def gd2jd(*date):
	"""gd2jd.py converts a UT Gregorian date to Julian date.
	
	Usage: gd2jd.py (2009, 02, 25, 01, 59, 59)
	
	To get the current Julian date:
	import time
	gd2jd(time.gmtime())
	
	Hours, minutesutes and/or seconds can be omitted -- if so, they are
	assumed to be zero.
	
	Year and month are converted to type INT, but all others can be
	type FLOAT (standard practice would suggest only the final element
	of the date should be float)
		"""
	#print date
	#print date[0]
	date = date[0]
	
	date = list(date)
	
	if len(date)<3:
		print "You must enter a date of the form (2009, 02, 25)!"
		return -1
	elif len(date)==3:
		for ii in range(3): date.append(0)
	elif len(date)==4:
		for ii in range(2): date.append(0)
	elif len(date)==5:
		date.append(0)
	
	yyyy = int(date[0])
	mm = int(date[1])
	dd = float(date[2])
	hh = float(date[3])
	minutes = float(date[4])
	sec = float(date[5])
	#print yyyy,mm,dd,hh,minutes,sec
	
	UT=hh+minutes/60+sec/3600
	
	#print "UT="+`UT`
	
	total_seconds=hh*3600+minutes*60+sec
	fracday=total_seconds/86400
	
	#print "Fractional day: %f" % fracday
	# print dd,mm,yyyy, hh,minutes,sec, UT
	
	if (100*yyyy+mm-190002.5)>0:
		sig=1
	else:
		sig=-1
	
	JD = 367*yyyy - int(7*(yyyy+int((mm+9)/12))/4) + int(275*mm/9) + dd + 1721013.5 + UT/24 - 0.5*sig +0.5
	
	months=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
	
	#print "\n"+months[mm-1]+" %i, %i, %i:%i:%i UT = JD %f" % (dd, yyyy, hh, minutes, sec, JD),
	
	# Now calculate the fractional year. Do we have a leap year?
	daylist=[31,28,31,30,31,30,31,31,30,31,30,31]
	daylist2=[31,29,31,30,31,30,31,31,30,31,30,31]
	if (yyyy%4 != 0):
		days=daylist2
	elif (yyyy%400 == 0):
		days=daylist2
	elif (yyyy%100 == 0):
		days=daylist
	else:
		days=daylist2
	
	daysum=0
	for y in range(mm-1):
		daysum=daysum+days[y]
		daysum=daysum+dd-1+UT/24
	
	if days[1]==29:
		fracyear=yyyy+daysum/366
	else:
		fracyear=yyyy+daysum/365
	#print " = " + `fracyear`+"\n"
	return JD


def jd2gd(jd,returnString=False):
	"""Task to convert a list of julian dates to gregorian dates
    description at http://mathforum.org/library/drmath/view/51907.html
    Original algorithm in Jean Meeus, "Astronomical Formulae for
    Calculators"

    2009-02-15 13:36 IJC: Converted to importable, callable function
    
    
    Note from author: This script is buggy and reports Julian dates which are 
    off by a day or two, depending on how far back you go. For example, 11 March 
    1609 converted to JD will be off by two days. 20th and 21st century seem to 
    be fine, though.
    """
	jd=jd+0.5
	Z=int(jd)
	F=jd-Z
	alpha=int((Z-1867216.25)/36524.25)
	A=Z + 1 + alpha - int(alpha/4)
	
	B = A + 1524
	C = int( (B-122.1)/365.25)
	D = int( 365.25*C )
	E = int( (B-D)/30.6001 )
	
	dd = B - D - int(30.6001*E) + F
	
	if E<13.5:
		mm=E-1
	
	if E>13.5:
		mm=E-13
	
	if mm>2.5:
		yyyy=C-4716
	
	if mm<2.5:
		yyyy=C-4715
	
	months=["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
	daylist=[31,28,31,30,31,30,31,31,30,31,30,31]
	daylist2=[31,29,31,30,31,30,31,31,30,31,30,31]
	
	h=int((dd-int(dd))*24)
	minutes=int((((dd-int(dd))*24)-h)*60)
	sec=86400*(dd-int(dd))-h*3600-minutes*60
	
	# Now calculate the fractional year. Do we have a leap year?
	if (yyyy%4 != 0):
		days=daylist2
	elif (yyyy%400 == 0):
		days=daylist2
	elif (yyyy%100 == 0):
		days=daylist
	else:
		days=daylist2
	
	hh = 24.0*(dd % 1.0)
	minutes = 60.0*(hh % 1.0)
	sec = 60.0*(minutes % 1.0)
	
	dd =  int(dd-(dd%1.0))
	hh =  int(hh-(hh%1.0))
	minutes =  int(minutes-(minutes%1.0))
	
	
	#print str(jd)+" = "+str(months[mm-1])+ ',' + str(dd) +',' +str(yyyy)
	#print str(h).zfill(2)+":"+str(minutes).zfill(2)+":"+str(sec).zfill(2)+" UTC"
	
	#print (yyyy, mm, dd, hh, minutes, sec)
	if returnString:
		return str(yyyy)+'-'+str(mm).zfill(2)+'-'+str(dd).zfill(2)+' '+str(hh).zfill(2)+':'+str(minutes).zfill(2)#+':'+str(sec)[0:2].zfill(2)
	else:
		return (yyyy, mm, dd, hh, minutes, sec)


