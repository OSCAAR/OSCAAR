'''
Ephemeris calculating tool that uses transit data from exoplanets.org
and astrometric calculations by PyEphem to tell you what transits you'll
be able to observe from your observatory in the near future.

Exoplanets.org citation: Wright et al. 2011
http://arxiv.org/pdf/1012.5676v3.pdf

Core developer: Brett Morris
'''
import ephem     ## PyEphem module
import numpy as np
import cPickle
from ephemeris import gd2jd, jd2gd
from matplotlib import pyplot as plt
from glob import glob
from os import getcwd, sep
from urllib import urlopen
import urllib2
from time import time
from os.path import getmtime
from copy import deepcopy
pklDatabaseName = 'exoplanetDB.pkl'     ## Name of exoplanet database C-pickle
pklDatabasePaths = glob(getcwd()+sep+pklDatabaseName)   ## list of files with the name pklDatabaseName in cwd
csvDatabasePath = 'exoplanets.csv'  ## Path to the text file saved from exoplanets.org
parFile = 'umo.par'

'''Parse the observatory .par file'''
parFileText = open('observatories/'+parFile,'r').read().splitlines()

def returnBool(value):
    '''Return booleans from strings'''
    if value == 'True': return True
    elif value == 'False': return False
    
for line in parFileText:
    parameter = line.split(':')[0]
    value = line.split(':')[1].strip()
    if parameter == 'name': observatory_name = value
    elif parameter == 'latitude': observatory_latitude = value
    elif parameter == 'longitude': observatory_longitude = value
    elif parameter == 'elevation': observatory_elevation = float(value)
    elif parameter == 'temperature': observatory_temperature = float(value)
    elif parameter == 'min_horizon': observatory_minHorizon = value
    elif parameter == 'start_date': startSem = gd2jd(eval(value))
    elif parameter == 'end_date': endSem = gd2jd(eval(value))
    elif parameter == 'v_limit': v_limit = float(value)
    elif parameter == 'depth_limit': depth_limit = float(value)
    elif parameter == 'calc_transits': calcTransits = returnBool(value)
    elif parameter == 'calc_eclipses': calcEclipses = returnBool(value)
    elif parameter == 'html_out': htmlOut = returnBool(value)
    elif parameter == 'text_out': textOut = returnBool(value)
    elif parameter == 'twilight': twilightType = value
    
'''First, check if there is an internet connection.'''
def internet_on():
    '''If internet connection is available, return True.'''
    try:
        response=urllib2.urlopen('http://www.google.com',timeout=10)
        return True
    except urllib2.URLError as err: pass
    return False
if internet_on():
    print "Internet connection detected."
else:
    print "WARNING: This script assumes that you're connected to the internet. This script may crash if you do not have an internet connection."

'''If there's a previously archived database pickle in this current working 
   directory then use it, if not, grab the data from exoplanets.org in one big CSV file and make one.
   If the old archive is >14 days old, grab a fresh version of the database from exoplanets.org.
'''
if glob(csvDatabasePath) == []:
    print 'No local copy of exoplanets.org database. Downloading one...'
    rawCSV = urlopen('http://www.exoplanets.org/csv-files/exoplanets.csv').read()
    saveCSV = open(csvDatabasePath,'w')
    saveCSV.write(rawCSV)
    saveCSV.close()
else: 
    '''If the local copy of the exoplanets.org database is >14 days old, download a new one'''
    secondsSinceLastModification = time() - getmtime(csvDatabasePath) ## in seconds
    daysSinceLastModification = secondsSinceLastModification/(60*60*24*30)
    if daysSinceLastModification > 14:
        print 'Your local copy of the exoplanets.org database is >14 days old. Downloading a fresh one...'
        rawCSV = urlopen('http://www.exoplanets.org/csv-files/exoplanets.csv').read()
        saveCSV = open(csvDatabasePath,'w')
        saveCSV.write(rawCSV)
        saveCSV.close()
    else: print "Your local copy of the exoplanets.org database is <14 days old. That'll do."

if len(pklDatabasePaths) == 0:
    print 'Parsing '+csvDatabasePath+', the CSV database from exoplanets.org...'
    rawTable = open(csvDatabasePath).read().splitlines()
    labels = rawTable[0].split(',')
    labelUnits = rawTable[1].split(',')
    rawTableArray = np.zeros([len(rawTable),len(rawTable[0].split(","))])
    exoplanetDB = {}
    planetNameColumn = np.arange(len(rawTable[0].split(',')))[np.array(rawTable[0].split(','),dtype=str)=='NAME'][0]
    for row in range(2,len(rawTable)): 
        splitRow = rawTable[row].split(',')
        #exoplanetDB[splitRow[0]] = {}    ## Create dictionary for this row's planet
        exoplanetDB[splitRow[planetNameColumn]] = {}    ## Create dictionary for this row's planet
        for col in range(0,len(splitRow)):
            #exoplanetDB[splitRow[0]][labels[col]] = splitRow[col]
            exoplanetDB[splitRow[planetNameColumn]][labels[col]] = splitRow[col]
    #exoplanetDB['units'] = {}        ## Create entry for units of each subentry
    #for col in range(0,len(labels)):
    #    exoplanetDB['units'][labels[col]] = labelUnits[col]
    
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

''' Set up observatory parameters '''
observatory = ephem.Observer()
observatory.lat =  observatory_latitude#'38:58:50.16'    ## Input format-  deg:min:sec  (type=str)
observatory.long = observatory_longitude#'-76:56:13.92' ## Input format-  deg:min:sec  (type=str)
observatory.elevation = observatory_elevation   # m
observatory.temp = observatory_temperature      ## Celsius 
observatory.horizon = observatory_minHorizon    ## Input format-  deg:min:sec  (type=str)

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
    
def transitBool(planet):
    '''True if exoplanet is transiting, False if detected by other means'''
    if exoplanetDB[planet]['TRANSIT'] == '0': return 0
    elif exoplanetDB[planet]['TRANSIT'] == '1': return 1
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

def list2datestrHTML(inList,alt):
    '''Converse function to datestr2list'''
    inList = map(str,inList)
    #return inList[1].zfill(2)+'/'+inList[2].zfill(2)+'<br />'+inList[3].zfill(2)+':'+inList[4].zfill(2)
    return inList[1].zfill(2)+'/<strong>'+inList[2].zfill(2)+'</strong><br />'+inList[3].zfill(2)+':'+inList[4].split('.')[0].zfill(2)+'; '+alt+'&deg;'

def simbadURL(planet):
    if exoplanetDB[planet]['SIMBADURL'] == '': return 'http://simbad.harvard.edu/simbad/'
    else: return exoplanetDB[planet]['SIMBADURL']

def RADecHTML(planet):
    return '<a href="'+simbadURL(planet)+'">'+RA(planet).split('.')[0]+'<br />'+dec(planet).split('.')[0]+'</a>'

def constellation(planet):
    return exoplanetDB[planet]['Constellation']

def orbitReference(planet):
    return exoplanetDB[planet]['TRANSITURL']

def nameWithLink(planet):
    return '<a href="'+orbitReference(planet)+'">'+planet+'</a>'

def mass(planet):
    if exoplanetDB[planet]['MASS'] == '': return '---'
    else: return trunc(float(exoplanetDB[planet]['MASS']),2)

def semimajorAxis(planet):
    #return trunc(0.004649*float(exoplanetDB[planet]['AR'])*float(exoplanetDB[planet]['RSTAR']),3)   ## Convert from solar radii to AU
    return trunc(float(exoplanetDB[planet]['SEP']),3)

def radius(planet):
    return trunc(float(exoplanetDB[planet]['R']),2) ## Convert from solar radii to Jupiter radii

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
    if V(planet) != 0.0 and depth(planet) != 0.0 and float(V(planet)) <= v_limit and float(depth(planet)) >= depth_limit and transitBool(planet):
        planets.append(planet)

if calcTransits: transits = {}
if calcEclipses: eclipses = {}
for day in np.arange(startSem,endSem+1):
    if calcTransits: transits[str(day)] = []
    if calcEclipses: eclipses[str(day)] = []
planetsNeverUp = []

def ingressEgressAlt(planet,observatory,ingress,egress):
    altitudes = []
    for time in [ingress,egress]:
        observatory.date = list2datestr(jd2gd(time))
        star = ephem.FixedBody()
        star._ra = ephem.hours(RA(planet))
        star._dec = ephem.degrees(dec(planet))
        star.compute(observatory)
        altitudes.append(str(ephem.degrees(star.alt)).split(":")[0])
    return altitudes

for planet in planets:        
    for day in np.arange(startSem,endSem+1,1.0):
        ''' Calculate sunset/rise times'''
        observatory.horizon = twilightType    ## Astronomical twilight, Input format-  deg:min:sec  (type=str), http://rhodesmill.org/pyephem/rise-set.html#computing-twilight
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
            if calcTransits and len(transitEpochs) != 0:
                transitEpoch = transitEpochs[0]
                ingress = transitEpoch-duration(planet)/2
                egress = transitEpoch+duration(planet)/2
                
                ''' Calculate positions of host stars'''
                observatory.horizon = observatory_minHorizon    ## Input format-  deg:min:sec  (type=str)
                star = ephem.FixedBody()
                star._ra = ephem.hours(RA(planet))
                star._dec = ephem.degrees(dec(planet))
                star.compute(observatory)
                exoplanetDB[planet]['Constellation'] = ephem.constellation(star)[0]
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
                if (ingress > sunset and egress < sunrise) and (ingress > starrise and egress < starset) or bypassTag:
                    ingressAlt,egressAlt = ingressEgressAlt(planet,observatory,ingress,egress)
                    transitInfo = [planet,transitEpoch,duration(planet)/2,'transit',ingressAlt,egressAlt]
                    transits[str(day)].append(transitInfo)
                    
                #else: print 'Partial transit'
            if calcEclipses and len(eclipseEpochs) != 0:
                eclipseEpoch = eclipseEpochs[0]
                ingress = eclipseEpoch-duration(planet)/2
                egress = eclipseEpoch+duration(planet)/2
                
                ''' Calculate positions of host stars'''
                observatory.horizon = observatory_minHorizon    ## Input format-  deg:min:sec  (type=str)
                star = ephem.FixedBody()
                star._ra = ephem.hours(RA(planet))
                star._dec = ephem.degrees(dec(planet))
                star.compute(observatory)
                exoplanetDB[planet]['Constellation'] = ephem.constellation(star)[0]
                                
                starrise = gd2jd(datestr2list(str(observatory.next_rising(star))))
                starset = gd2jd(datestr2list(str(observatory.next_setting(star))))
                
                '''If star is above horizon and sun is below horizon:'''
                if (ingress > sunset and egress < sunrise) and (ingress > starrise and egress < starset):
                    ingressAlt,egressAlt = ingressEgressAlt(planet,observatory,ingress,egress)
                    eclipseInfo = [planet,eclipseEpoch,duration(planet)/2,'eclipse',ingressAlt,egressAlt]
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

if calcTransits: removeEmptySets(transits)
if calcEclipses: removeEmptySets(eclipses)

events = {}
def mergeDictionaries(dict):
    for key in dict:
        if any(key == eventKey for eventKey in events) == False:    ## If key does not exist in events,
            if np.shape(dict[key])[0] == 1:    ## If new event is the only one on that night, add only it
                events[key] = [dict[key][0]]
            else:            ## If there were multiple events that night, add them each
                events[key] = []
                for event in dict[key]:
                    events[key].append(event)
        else:
            if np.shape(dict[key])[0] > 1: ## If there are multiple entries to append,
                for event in dict[key]:
                    events[key].append(event)
            else:                            ## If there is only one to add,
                events[key].append(dict[key][0])
if calcTransits: mergeDictionaries(transits)
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
                if calcTransits and planet[3] == 'transit':
                    report.write('\t'+str(planet[0])+'\t'+str(planet[3])+'\t'+list2datestr(jd2gd(float(planet[1]-planet[2]))).split('.')[0]+'\t'+list2datestr(jd2gd(float(planet[1]+planet[2]))).split('.')[0]+'\n')
                if calcEclipses and planet[3] == 'eclipse':
                    report.write('\t'+str(planet[0])+'\t'+str(planet[3])+'\t'+list2datestr(jd2gd(float(planet[1]-planet[2]))).split('.')[0]+'\t'+list2datestr(jd2gd(float(planet[1]+planet[2]))).split('.')[0]+'\n')

            report.write('\n')
        elif np.shape(events[key])[0] == 1:
            planet = events[key][0]
            report.write(list2datestr(jd2gd(float(key)+1)).split(' ')[0]+'\n')
            if calcTransits and planet[3] == 'transit':
                    report.write('\t'+str(planet[0])+'\t'+str(planet[3])+'\t'+list2datestr(jd2gd(float(planet[1]-planet[2]))).split('.')[0]+'\t'+list2datestr(jd2gd(float(planet[1]+planet[2]))).split('.')[0]+'\n')
            if calcEclipses and planet[3] == 'eclipse':
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
        '    <head>',\
        '        <meta http-equiv="content-type" content="text/html; charset=UTF-8" />',\
        '        <title>Ephemeris</title>',\
        '        <link rel="stylesheet" href="stylesheetEphem.css" type="text/css" />',\
        '        <base target="_blank">',\
        '       <script src="sorttable.js"></script>',\
        '    </head>',\
        '    <body>',\
        '        <div id="textDiv">',\
        '        <h1>Ephemerides for: '+observatory_name+'</h1>',\
        '        <h2>Observing dates (UT): '+list2datestr(jd2gd(startSem)).split(' ')[0]+' - '+list2datestr(jd2gd(endSem)).split(' ')[0]+'</h2>'
        '       Click the column headers to sort. '])

    tableheader = '\n'.join([
        '\n        <table class="sortable" id="eph">',\
        '        <tr> <th>Planet<br /><span class="small">[Link: Orbit ref.]</span></th>      <th>Event</th>    <th>Ingress <br /><span class="small">(MM/DD<br />HH:MM, UT)</span></th> <th>Egress <br /><span class="small">(MM/DD<br />HH:MM, UT)</span></th>'+\
            '<th>V mag</th> <th>Depth<br />(mag)</th> <th>Duration<br />(hrs)</th> <th>RA/Dec<br /><span class="small">[Link: Simbad ref.]</span></th> <th>Const.</th> <th>Mass<br />(M<sub>J</sub>)</th>'+\
            '<th>Semimajor <br />Axis (AU)</th> <th>Radius<br />(R<sub>J</sub>)</th></tr>'])
    tablefooter = '\n'.join([
        '\n        </table>',\
        '        <br /><br />',])
    htmlfooter = '\n'.join([
        '\n        <p class="headinfo">',\
        '        Developed by Brett Morris with great gratitude for the help of <a href="http://rhodesmill.org/pyephem/">PyEphem</a>,<br/>',\
        '        and for up-to-date exoplanet parameters from <a href="http://www.exoplanets.org/">exoplanets.org</a> (<a href="http://adsabs.harvard.edu/abs/2011PASP..123..412W">Wright et al. 2011</a>).<br />',\
        '        </p>',\
        '        </div>',\
        '    </body>',\
        '</html>'])
    report.write(htmlheader)
    report.write(tableheader)

    allKeys = np.array(allKeys)[np.argsort(allKeys)]
    for key in allKeys:
        def writeHTMLtransit():
            indentation = '        '
            middle = '</td><td>'.join([nameWithLink(planet[0]),str(planet[3]),list2datestrHTML(jd2gd(float(planet[1]-planet[2])),planet[4]),\
                                       list2datestrHTML(jd2gd(float(planet[1]+planet[2])),planet[5]),trunc(V(str(planet[0])),2),\
                                       trunc(depth(planet[0]),4),trunc(24.0*duration(planet[0]),2),RADecHTML(planet[0]),constellation(planet[0]),\
                                       mass(planet[0]),semimajorAxis(planet[0]),radius(planet[0])])
            line = indentation+'<tr><td>'+middle+'</td></tr>\n'
            report.write(line)
        
        def writeHTMLeclipse():
            indentation = '        '
            middle = '</td><td>'.join([nameWithLink(planet[0]),str(planet[3]),list2datestrHTML(jd2gd(float(planet[1]-planet[2])),planet[4]),\
                                       list2datestrHTML(jd2gd(float(planet[1]+planet[2])),planet[5]),trunc(V(str(planet[0])),2),\
                                       '---',trunc(24.0*duration(planet[0]),2),RADecHTML(planet[0]),constellation(planet[0]),\
                                       mass(planet[0]),semimajorAxis(planet[0]),radius(planet[0])])
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
                if calcTransits and planet[3] == 'transit':
                    writeHTMLtransit()
                if calcEclipses and planet[3] == 'eclipse':
                    writeHTMLeclipse()          
            #report.write('\n')
        elif np.shape(events[key])[0] == 1:
            planet = events[key][0]
            #report.write(list2datestr(jd2gd(float(key)+1)).split(' ')[0]+'\n')
            if calcTransits and planet[3] == 'transit':
                    writeHTMLtransit()
            if calcEclipses and planet[3] == 'eclipse':
                    writeHTMLeclipse()
           # report.write('\n')
    report.write(tablefooter)
    report.write(htmlfooter)
    report.close()
#print exoplanetDB['HD 209458 b']