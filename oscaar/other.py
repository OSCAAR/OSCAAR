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

#######################################################################
#######################################################################       
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

    Note from Brett Morris: This conversion routine matches up to the "Numerical 
    Recipes" in C version from 2010-2100 CE, so I think we'll be ok for oscaar's
    purposes.
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
