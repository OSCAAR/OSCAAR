import pyfits

###########################################################################
###########################################################################

def jd2jd(jd):
    return jd

def dateobs2jd(ut):
    '''
    Convert times from Universal Time (UT) to Julian Date (JD), splitting the date and time at the "T"
    
    INPUTS: ut - Time in Universial Time (UT)
    
    RETURNS: jd - Julian Date (JD)
    '''
    [date, Time] = ut.split('T')
    Time = Time.strip()
    [year, month, day] = date.split('-')
    [hour, min, sec] = Time.split(':')
    year = int(year); month = int(month); day = int(day)
    hour = int(hour); min = int(min); sec = float(sec)
    #years = (int(year) + 4716)*365.25
    if month == 1 or month == 2: 
        month += 12
        year -= 1
    a = year/100
    b = a/4
    c = 2-a+b
    d = day
    e = np.floor(365.25*(year+4716))
    f = np.floor(30.6001*(month+1))
    years = c+d+e+f-1524.5
    fracOfDay = (hour/24.) + (min/(24*60.)) + (sec/(24*60*60.))
    jd = years + fracOfDay
    return jd


def mjd2jd(mjd):
    '''
    Definition of Modified Julian Date (MJD): MJD = JD - 2400000.5
    JD = MJD + 2400000.5
    '''
    return mjd + float(2400000.5)

###########################################################################
###########################################################################

    
def findKeyword(fitsFile): 
    '''
    Enter the path to a fits file, and findKeyword will return the tuple: 
    (useKeyword, allKeys, conversionFunction)
    
    where 
      - `useKeyword` is the FITS header keyword that should be used to find
        the time of the exposure, 
      - `allKeys` is the list of all header keywords in the first exposure
      - `conversionFunction` is a function that will convert the time value stored in 
        the keyword denoted by `useKeyword` to Julian Date
    '''
    
    
    ## All keys in FITS header for the file
    allKeys = pyfits.getheader(fitsFile).keys()
    
    ## List of potential keywords to search for
    knownkeys = ["JD","MJD-OBS","DATE-OBS","UTC-OBS"]
    conversions = [jd2jd, mjd2jd, dateobs2jd, dateobs2jd]
    conversionFunction = None
    useKeyword = None
    
    ## Search for keywords for which we've predefined conversion functions 
    j = -1
    while useKeyword == None and j < len(knownkeys)-1:
        j += 1
        if knownkeys[j] in allKeys:
            conversionFunction = conversions[j]
            useKeyword = knownkeys[j]
 
    if useKeyword == None: print "No known keywords found"
    return useKeyword, allKeys, knownkeys, conversionFunction

#for file in fitsfiles: 
#    #print findKeyword(file)
#    bestKeyword, allKeys, convert2jd = findKeyword(file)
#    assert bestKeyword != None, 'None of FITS header keywords in your first exposure are known keywords.'+\
#                            'Contact the OSCAAR team if you think it should be!'
#    fileheader = pyfits.getheader(file)
#    rawTimeOfExposure = fileheader[bestKeyword]
#    jd = convert2jd(rawTimeOfExposure)
#    print 'All keys:',allKeys,'\nBest keyword:',bestKeyword,'->',jd,'\n'
#    