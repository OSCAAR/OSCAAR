'''
Created on Feb 25, 2013

Useful notes on PyEphem: http://zeus.asu.cas.cz/extra/pyephem-manual.html#ComputationsforParticularObservers
Note: be cautious of planets with alternate names: HAT-P-30 b = WASP-51 b

@author: bmmorris
'''
import ephem 	## PyEphem module
import numpy as np
import cPickle
from ephemeris import gd2jd, jd2gd
from matplotlib import pyplot as plt
from glob import glob
from os import getcwd, sep

pklDatabaseName = 'exoplanetDB2.pkl'     ## Name of exoplanet database C-pickle
pklDatabasePaths = glob(getcwd()+sep+pklDatabaseName)   ## list of files with the name pklDatabaseName in cwd
textDatabasePath = 'exoplanetData2.txt'  ## Path to the text file saved from exoplanets.org
calcEclipses = False                    ## Search for secondary eclipses? (type=bool)
textOut = True                          ## Print out .txt file report? (type=bool)
htmlOut = True                          ## Print out .html report? (type=bool)
''' Start and end dates of the observing semester'''
startSem = gd2jd((2013,4,16,22,0,0))	## Beginning date/time of observing period. Format: (YYYY,MM,DD,HH,MM,SS)
endSem = gd2jd((2013,5,1,22,0,0))       ## Ending date/time of observing period
observatory_elevation = 20.0            ## meters
observatory_temperature = 15.0          ## degrees C
observatory_minHorizon = '25:00:00'     ## deg:min:sec  (type=str)
observatory_latitude = '38:58:50.16'    ## deg:min:sec  (type=str). Positive = North
observatory_longitude = '-76:56:13.92'  ## deg:min:sec  (type=str). Positive = East
twilightType = '-6'                     ## Civil = -6 degrees; Nautical = -12 degrees; Astronomical = -18 degrees. (type=str)
observatory_name = 'University Of Maryland Observatory' ## Name of observatory for report header
v_limit = 12.0                          ## V-magnitude upper-limit (type = float)
depth_limit = 0.008                     ## Depth lower-limit in magnitudes (type = float)

'''If there's a previously archived database pickle in this current working 
   directory then use it, if not, parse "exoplanetData.txt" and make one.
   To download data from exoplanets.org, export (button in upper right) a table 
   with at least the following columns:
       RA_STRING: right ascension of the planet
       DEC_STRING: declination of the planet
       PER: orbital period of the planet
       TT: epoch of mid-transit
       T14: transit/eclipse duration
'''
if len(pklDatabasePaths) == 0:
	print 'Attempting to parse exoplanetData.txt data from exoplanetDB.org...'
	rawTable = open(textDatabasePath).read().splitlines()
	labels = rawTable[0].split(',')
	labelUnits = rawTable[1].split(',')
	rawTableArray = np.zeros([len(rawTable),len(rawTable[0].split(","))])
	exoplanetDB = {}						## Create dictionary for all planets
	for row in range(2,len(rawTable)): 
		splitRow = rawTable[row].split(',')
		exoplanetDB[splitRow[0]] = {}	## Create dictionary for this row's planet
		for col in range(1,len(splitRow)):
			exoplanetDB[splitRow[0]][labels[col]] = splitRow[col]
	exoplanetDB['units'] = {}		## Create entry for units of each subentry
	for col in range(0,len(labels)):
		exoplanetDB['units'][labels[col]] = labelUnits[col]
	
	output = open(pklDatabaseName,'wb')
	cPickle.dump(exoplanetDB,output)
	output.close()
else: 
	print 'Using previously parsed exoplanetData.txt data from exoplanets.org...'
	''' Import data from exoplanets.org, parsed by
	    exoplanetDataParser1.py'''
	inputFile = open(pklDatabaseName,'rb')
	exoplanetDB = cPickle.load(inputFile)
	inputFile.close()

''' Set up observatory parameters '''
observatory = ephem.Observer()
observatory.lat =  observatory_latitude#'38:58:50.16'	## Input format-  deg:min:sec  (type=str)
observatory.long = observatory_longitude#'-76:56:13.92' ## Input format-  deg:min:sec  (type=str)
observatory.elevation = observatory_elevation   # m
observatory.temp = observatory_temperature ## Celsius 
observatory.horizon = observatory_minHorizon	## Input format-  deg:min:sec  (type=str)
#observatory.date = '2013/1/18 00:48:47'#10:04:14'	
def trunc(f, n):
    '''Truncates a float f to n decimal places without rounding'''
    slen = len('%.*f' % (n, f))
    return str(f)[:slen]
    
def RA(planet):
	'''Type: str, Units:  hours:min:sec'''
	return exoplanetDB[planet]['RA_STRING']
def dec(planet):
	'''Type: str, Units:  deg:min:sec'''
	return exoplanetDB[planet]['DEC_STRING']
def period(planet):
	'''Units:  days'''
	return float(exoplanetDB[planet]['PER'])
def epoch(planet):
	'''Tc at mid-transit. Units:  days'''
	if exoplanetDB[planet]['TT'] == '': return 0.0
	else: return float(exoplanetDB[planet]['TT'])
def duration(planet):
	'''Transit/eclipse duration. Units:  days'''
	if exoplanetDB[planet]['T14'] == '': return 0.0
	else: return float(exoplanetDB[planet]['T14'])
def V(planet):
	'''V mag'''
	if exoplanetDB[planet]['V'] == '': return 0.0
	else: return float(exoplanetDB[planet]['V'])
def KS(planet):
	'''KS mag'''
	if exoplanetDB[planet]['KS'] == '': return 0.0
	else: return float(exoplanetDB[planet]['KS'])

def depth(planet):
	'''Transit depth'''
	if exoplanetDB[planet]['DEPTH'] == '': return 0.0
	else: return float(exoplanetDB[planet]['DEPTH'])

########################################################################################
########################################################################################

def datestr2list(datestr):
	''' Take strings of the form: "2013/1/18 20:08:18" and return them as a
		tuple of the same parameters'''
	year,month,others = datestr.split('/')
	day, time = others.split(' ')
	hour,minute,sec = time.split(':')
	return (int(year),int(month),int(day),int(hour),int(minute),int(sec))

def list2datestr(inList):
	'''Converse function to datestr2list'''
	inList = map(str,inList)
	return inList[0]+'/'+inList[1]+'/'+inList[2]+' '+inList[3].zfill(2)+':'+inList[4].zfill(2)+':'+inList[5].zfill(2)

def list2datestrHTML(inList):
	'''Converse function to datestr2list'''
	inList = map(str,inList)
	return inList[1].zfill(2)+'/'+inList[2].zfill(2)+'<br />'+inList[3].zfill(2)+':'+inList[4].zfill(2)

def simbadURL(planet):
	if exoplanetDB[planet]['SIMBADURL'] == '': return 'http://simbad.harvard.edu/simbad/'
	else: return exoplanetDB[planet]['SIMBADURL']

def RADecHTML(planet):
    return '<a href="'+simbadURL(planet)+'">'+RA(planet).split('.')[0]+'<br />'+dec(planet).split('.')[0]+'</a>'

def midTransit(Tc, P, start, end):
	'''Calculate mid-transits between Julian Dates start and end, using a 2500 
	   orbital phase kernel since T_c (for 2 day period, 2500 phases is 14 years)
	   '''
	Nepochs = np.arange(0,2500)
	transitTimes = Tc + P*Nepochs
	transitTimesInSem = transitTimes[(transitTimes < end)*(transitTimes > start)]
	return transitTimesInSem

def midEclipse(Tc, P, start, end):
	'''Calculate mid-eclipses between Julian Dates start and end, using a 2500 
	   orbital phase kernel since T_c (for 2 day period, 2500 phases is 14 years)
	   '''
	Nepochs = np.arange(0,2500)
	transitTimes = Tc + P*(0.5 + Nepochs)
	transitTimesInSem = transitTimes[(transitTimes < end)*(transitTimes > start)]
	return transitTimesInSem

'''Choose which planets from the database to include in the search, 
   assemble a list of them.'''
planets = []
for planet in exoplanetDB:
    #if V(planet) != '---' and depth(planet) != '---' and float(V(planet)) <= v_limit and float(depth(planet)) >= depth_limit:
    if V(planet) != 0.0 and depth(planet) != 0.0 and float(V(planet)) <= v_limit and float(depth(planet)) >= depth_limit:
        planets.append(planet)

transits = {}
if calcEclipses: eclipses = {}
for day in np.arange(startSem,endSem+1):
	transits[str(day)] = []
	if calcEclipses: eclipses[str(day)] = []
planetsNeverUp = []
for planet in planets:		
    for day in np.arange(startSem,endSem+1,1.0):
        ''' Calculate sunset/rise times'''
        observatory.horizon = twilightType	## Astronomical twilight, Input format-  deg:min:sec  (type=str), http://rhodesmill.org/pyephem/rise-set.html#computing-twilight
        observatory.date = list2datestr(jd2gd(day))
        sun = ephem.Sun()
        try:
            sunrise = gd2jd(datestr2list(str(observatory.next_rising(sun, use_center=True))))
            sunset = gd2jd(datestr2list(str(observatory.next_setting(sun, use_center=True))))
            sunriseStr = str(observatory.next_rising(sun, use_center=True))
            sunsetStr = str(observatory.next_setting(sun, use_center=True))
            '''Calculate mid-transits that occur on this night'''	
            transitEpochs = midTransit(epoch(planet),period(planet),sunset,sunrise)
            eclipseEpochs = midEclipse(epoch(planet),period(planet),sunset,sunrise)
            if len(transitEpochs) != 0:
                transitEpoch = transitEpochs[0]
                ingress = transitEpoch-duration(planet)/2
                egress = transitEpoch+duration(planet)/2
                
                ''' Calculate positions of host stars'''
                observatory.horizon = observatory_minHorizon	## Input format-  deg:min:sec  (type=str)
                star = ephem.FixedBody()
                star._ra = ephem.hours(RA(planet))
                star._dec = ephem.degrees(dec(planet))
                star.compute(observatory)
                bypassTag = False
                try: 
                    starrise = gd2jd(datestr2list(str(observatory.next_rising(star))))
                    starset = gd2jd(datestr2list(str(observatory.next_setting(star))))
                except ephem.AlwaysUpError:
                    '''If the star is always up, you don't need starrise and starset to 
                       know that the event should be included further calculations'''
                    print 'Woo! '+str(planet)+' is always above the horizon.'
                    bypassTag = True
                
                '''If star is above horizon and sun is below horizon:'''		
                if ((ingress > sunset and egress < sunrise) and (ingress > starrise and egress < starset)) or bypassTag:
    #				print '\nComplete transit'
    #				print 'Date:',observatory.date
    #				print 'Sunset/rise:',sunsetStr,sunriseStr
    ##				print 'Transit epoch:',list2datestr(jd2gd(transitEpoch))
    #				print 'Starrise/set:',observatory.next_rising(star), observatory.next_setting(star)
    #				print 'Ing/egr:',list2datestr(jd2gd(ingress)),list2datestr(jd2gd(egress))
    #				print 'Hrs dark:',24.*(ephem.Date(sunriseStr)-ephem.Date(sunsetStr))
                    transitInfo = [planet,transitEpoch,duration(planet)/2,'transit']
                    transits[str(day)].append(transitInfo)
                    
                #else: print 'Partial transit'
            if calcEclipses and len(eclipseEpochs) != 0:
                eclipseEpoch = eclipseEpochs[0]
                ingress = eclipseEpoch-duration(planet)/2
                egress = eclipseEpoch+duration(planet)/2
                
                ''' Calculate positions of host stars'''
                observatory.horizon = observatory_minHorizon	## Input format-  deg:min:sec  (type=str)
                star = ephem.FixedBody()
                star._ra = ephem.hours(RA(planet))
                star._dec = ephem.degrees(dec(planet))
                star.compute(observatory)
                
                starrise = gd2jd(datestr2list(str(observatory.next_rising(star))))
                starset = gd2jd(datestr2list(str(observatory.next_setting(star))))
                
                '''If star is above horizon and sun is below horizon:'''
                if (ingress > sunset and egress < sunrise) and (ingress > starrise and egress < starset):
                    eclipseInfo = [planet,eclipseEpoch,duration(planet)/2,'eclipse']
                    eclipses[str(day)].append(eclipseInfo)
                #else: print 'Partial eclipse'
        except ephem.NeverUpError:
            if str(planet) not in planetsNeverUp:
                print 'WARNING: '+str(planet)+' is never above the horizon. Ignoring it.'
                planetsNeverUp.append(str(planet))
def removeEmptySets(dictionary):
	'''Remove days where there were no transits/eclipses from the transit/eclipse list dictionary. 
	   Can't iterate through the transits dictionary with a for loop because it would change length 
	   as keys get deleted, so loop through with while loop until all entries are not empty sets'''
	dayCounter = startSem
	while any(dictionary[day] == [] for day in dictionary):	
		if dictionary[str(dayCounter)] == []:
			del dictionary[str(dayCounter)]
		dayCounter += 1

removeEmptySets(transits)
if calcEclipses: removeEmptySets(eclipses)

events = {}
def mergeDictionaries(dict):
	for key in dict:
		if any(key == eventKey for eventKey in events) == False:	## If key does not exist in events,
			if np.shape(dict[key])[0] == 1:	## If new event is the only one on that night, add only it
				events[key] = [dict[key][0]]
			else:			## If there were multiple events that night, add them each
				events[key] = []
				for event in dict[key]:
					events[key].append(event)
		else:
			if np.shape(dict[key])[0] > 1: ## If there are multiple entries to append,
				for event in dict[key]:
					events[key].append(event)
			else:							## If there is only one to add,
				events[key].append(dict[key][0])
mergeDictionaries(transits)
if calcEclipses: mergeDictionaries(eclipses)

if textOut: 
    '''Write out a text report with the transits/eclipses. Write out the time of 
       ingress, egress, whether event is transit/eclipse, elapsed in time between
       ingress/egress of the temporally isolated events'''
    report = open('eventReport.txt','w')
    allKeys = []
    for key in events:
        allKeys.append(key)

    allKeys = np.array(allKeys)[np.argsort(allKeys)]
    for key in allKeys:
        if np.shape(events[key])[0] > 1:
            elapsedTime = []
            
            for i in range(1,len(events[key])):
                nextPlanet = events[key][1]
                planet = events[key][0]
                double = False
                '''If the other planet's ingress is before this one's egress, then'''
                if ephem.Date(list2datestr(jd2gd(float(nextPlanet[1]-nextPlanet[2])))) -\
                         ephem.Date(list2datestr(jd2gd(float(planet[1]+planet[2])))) > 0.0:
                    double = True
                    elapsedTime.append(ephem.Date(list2datestr(jd2gd(float(nextPlanet[1]-nextPlanet[2])))) - \
                         ephem.Date(list2datestr(jd2gd(float(planet[1]+planet[2])))))
                    
                if ephem.Date(list2datestr(jd2gd(float(planet[1]-planet[2])))) - \
                         ephem.Date(list2datestr(jd2gd(float(nextPlanet[1]+nextPlanet[2])))) > 0.0:
                    '''If the other planet's egress is before this one's ingress, then'''
                    double = True
                    elapsedTime.append(ephem.Date(list2datestr(jd2gd(float(planet[1]-planet[2])))) - \
                         ephem.Date(list2datestr(jd2gd(float(nextPlanet[1]+nextPlanet[2])))))
            
            if double:
                report.write(list2datestr(jd2gd(float(key)+1)).split(' ')[0]+'\t'+'>1 event'+'\t'+str(np.max(elapsedTime)*24.0)+'\t'+'\n')
            else:
                report.write(list2datestr(jd2gd(float(key)+1)).split(' ')[0]+'\n')
            for planet in events[key]:
                if planet[3] == 'transit':
                    report.write('\t'+str(planet[0])+'\t'+str(planet[3])+'\t'+list2datestr(jd2gd(float(planet[1]-planet[2]))).split('.')[0]+'\t'+list2datestr(jd2gd(float(planet[1]+planet[2]))).split('.')[0]+'\n')
                elif calcEclipses and planet[3] == 'eclipse':
                    report.write('\t'+str(planet[0])+'\t'+str(planet[3])+'\t'+list2datestr(jd2gd(float(planet[1]-planet[2]))).split('.')[0]+'\t'+list2datestr(jd2gd(float(planet[1]+planet[2]))).split('.')[0]+'\n')

            report.write('\n')
        elif np.shape(events[key])[0] == 1:
            planet = events[key][0]
            report.write(list2datestr(jd2gd(float(key)+1)).split(' ')[0]+'\n')
            if planet[3] == 'transit':
                    report.write('\t'+str(planet[0])+'\t'+str(planet[3])+'\t'+list2datestr(jd2gd(float(planet[1]-planet[2]))).split('.')[0]+'\t'+list2datestr(jd2gd(float(planet[1]+planet[2]))).split('.')[0]+'\n')
            elif calcEclipses and planet[3] == 'eclipse':
                    report.write('\t'+str(planet[0])+'\t'+str(planet[3])+'\t'+list2datestr(jd2gd(float(planet[1]-planet[2]))).split('.')[0]+'\t'+list2datestr(jd2gd(float(planet[1]+planet[2]))).split('.')[0]+'\n')
            report.write('\n')
    report.close()


if htmlOut: 
    '''Write out a text report with the transits/eclipses. Write out the time of 
       ingress, egress, whether event is transit/eclipse, elapsed in time between
       ingress/egress of the temporally isolated events'''
    report = open('eventReport.html','w')
    allKeys = []
    for key in events:
        allKeys.append(key)
    ## http://www.kryogenix.org/code/browser/sorttable/
    htmlheader = '\n'.join([
        '<!doctype html>',\
        '<html>',\
        '	<head>',\
        '		<meta http-equiv="content-type" content="text/html; charset=UTF-8" />',\
        '		<title>Ephemeris</title>',\
        '		<link rel="stylesheet" href="stylesheetEphem.css" type="text/css" />',\
        '		<base target="_blank">',\
        '       <script src="sorttable.js"></script>',\
        '	</head>',\
        '	<body>',\
        '		<div id="textDiv">',\
        '		<h1>Ephemerides for: '+observatory_name+'</h1>',\
        '		<h2>Observing dates (UT): '+list2datestr(jd2gd(startSem)).split(' ')[0]+' - '+list2datestr(jd2gd(endSem)).split(' ')[0]+'</h2>'
        '       Click the column headers to sort. '])

    tableheader = '\n'.join([
        '\n		<table class="sortable" id="eph" align=center>',\
        '		<tr> <th>Planet</th>  	<th>Event</th>	<th>Ingress <br />(MM/DD<br />HH:MM, UT)</th> <th>Egress <br />(MM/DD<br />HH:MM, UT)</th> <th>V mag</th> <th>Depth (mag)</th> <th>Duration (hrs)</th> <th>RA/Dec</th></tr>'])
    tablefooter = '\n'.join([
        '\n		</table>',\
        '		<br /><br />',])
    htmlfooter = '\n'.join([
        '\n		<p class="headinfo">',\
        '		Developed by: Brett Morris<br>',\
        '		</p>',\
        '		</div>',\
        '	</body>',\
        '</html>'])
    report.write(htmlheader)
    report.write(tableheader)

    allKeys = np.array(allKeys)[np.argsort(allKeys)]
    for key in allKeys:
        def writeHTMLOut():
            indentation = '		'
            middle = '</td><td>'.join([str(planet[0]),str(planet[3]),list2datestrHTML(jd2gd(float(planet[1]-planet[2]))).split('.')[0],\
                                       list2datestrHTML(jd2gd(float(planet[1]+planet[2]))).split('.')[0],trunc(V(str(planet[0])),2),\
                                       trunc(depth(planet[0]),4),trunc(24.0*duration(planet[0]),2),RADecHTML(planet[0])])
            line = indentation+'<tr><td>'+middle+'</td></tr>\n'
            report.write(line)
    
        if np.shape(events[key])[0] > 1:
            elapsedTime = []
            
            for i in range(1,len(events[key])):
                nextPlanet = events[key][1]
                planet = events[key][0]
                double = False
                '''If the other planet's ingress is before this one's egress, then'''
                if ephem.Date(list2datestr(jd2gd(float(nextPlanet[1]-nextPlanet[2])))) -\
                         ephem.Date(list2datestr(jd2gd(float(planet[1]+planet[2])))) > 0.0:
                    double = True
                    elapsedTime.append(ephem.Date(list2datestr(jd2gd(float(nextPlanet[1]-nextPlanet[2])))) - \
                         ephem.Date(list2datestr(jd2gd(float(planet[1]+planet[2])))))
                    
                if ephem.Date(list2datestr(jd2gd(float(planet[1]-planet[2])))) - \
                         ephem.Date(list2datestr(jd2gd(float(nextPlanet[1]+nextPlanet[2])))) > 0.0:
                    '''If the other planet's egress is before this one's ingress, then'''
                    double = True
                    elapsedTime.append(ephem.Date(list2datestr(jd2gd(float(planet[1]-planet[2])))) - \
                         ephem.Date(list2datestr(jd2gd(float(nextPlanet[1]+nextPlanet[2])))))
            
            #if double:
            #    report.write(list2datestr(jd2gd(float(key)+1)).split(' ')[0]+'\t'+'>1 event'+'\t'+str(np.max(elapsedTime)*24.0)+'\t'+'\n')
            #else:
            #    report.write(list2datestr(jd2gd(float(key)+1)).split(' ')[0]+'\n')
            for planet in events[key]:
                if planet[3] == 'transit':
                    writeHTMLOut()
                elif calcEclipses and planet[3] == 'eclipse':
                    writeHTMLOut()          
            #report.write('\n')
        elif np.shape(events[key])[0] == 1:
            planet = events[key][0]
            #report.write(list2datestr(jd2gd(float(key)+1)).split(' ')[0]+'\n')
            if planet[3] == 'transit':
                    writeHTMLOut()
            elif calcEclipses and planet[3] == 'eclipse':
                    writeHTMLOut()
           # report.write('\n')
    report.write(tablefooter)
    report.write(htmlfooter)
    report.close()

plots = False
if plots:
	import matplotlib.cm as cm
	import colorsys
	
	times = []
	names = []
	durations = []
	eventType = []
	for key in events:
		for event in events[key]:
			names.append(event[0])
			times.append(event[1])
			durations.append(event[2])
			eventType.append(event[3])
	
	def eventTyper(eventType):
		if eventType == 'transit': return 0
		if eventType == 'eclipse': return 1
	
	eventType = map(eventTyper,eventType)

	showMags = False
	scaleSize = False
	showLabels = True
	bars = 0.083	## 2 hours
	alphaSetting = 0.7
	format = 'o'
	
	fig = plt.figure(figsize=(24,8))
	axis = fig.add_subplot(111)
	
	def get_color(color):
		for hue in range(color):
			hue = 1. * hue / color
			col = [int(x) for x in colorsys.hsv_to_rgb(hue, 1.0, 230)]
			yield "#{0:02x}{1:02x}{2:02x}".format(*col)
	axis.errorbar(times,eventType,xerr=durations,fmt=format,alpha=alphaSetting)
	
	if showLabels:
		for label, x, y in zip(names, times, eventType):
			axis.annotate(
		        label,xy = (x, y), xytext = (0,5), textcoords = 'offset points', ha = 'left', va = 'bottom', rotation=45)
				
	#axis.legend(numpoints=1)
	
	def format_coord(x, y):
		return 'Cursor: '+jd2gd(x,returnString=True)+' UT'
	axis.format_coord = format_coord 
	
	plt.show()
