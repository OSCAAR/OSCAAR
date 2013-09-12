"""
oscaar v2.0
Module for differential photometry

Developed by Brett Morris, 2011-2013
"""

import math

import numpy as np
from numpy import linalg as LA


def ut2jd(ut):
    """
    Convert times from Universal Time (UT) to Julian Date (JD)

    Parameters
    ----------
    ut : string
        Time in Universal Time (UT)

    Returns
    -------
    jd : float
        Julian Date (JD)
    """

    [date, Time] = ut.split(';')
    Time = Time.strip()
    [year, month, day] = date.split('-')
    [hour, minute, sec] = Time.split(':')
    year = int(year)
    month = int(month)
    day = int(day)
    hour = int(hour)
    minute = int(minute)
    sec = float(sec)
    
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
    fracOfDay = (hour/24.) + (minute/(24*60.)) + (sec/(24*60*60.))
    jd = years + fracOfDay
    return jd


def ut2jdSplitAtT(ut):
    """
    Convert times from Universal Time (UT) to Julian Date (JD), splitting
    the date and time at the "T"

    Parameters
    ----------
    ut : string
        Time in Universal Time (UT)

    Returns
    -------
    jd : float
        Julian Date (JD)
    """

    [date, Time] = ut.split('T')
    Time = Time.strip()
    [year, month, day] = date.split('-')
    [hour, minute, sec] = Time.split(':')
    year = int(year)
    month = int(month)
    day = int(day)
    hour = int(hour)
    minute = int(minute)
    sec = float(sec)
    
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
    fracOfDay = (hour/24.) + (minute/(24*60.)) + (sec/(24*60*60.))
    jd = years + fracOfDay
    return jd


def regressionScale(comparisonFlux, targetFlux, time, ingress, egress,
                    returncoeffs=False):
    """
    Use a least-squares regression to stretch and offset a comparison
    star fluxes to scale them to the relative intensity of the target
    star. Only do this regression considering the out-of-transit
    portions of the light curve.

    Parameters
    ----------
    comparisonFlux : numpy.ndarray
        Flux of a comparison star

    targetFlux : numpy.ndarray
        Flux of the target star

    time : numpy.ndarray
        List of times for each flux measurement in JD

    ingress : float
        Time of ingress (JD, assuming time list is in JD)

    egress : float
        Time of egress (JD, assuming time list is in JD)

    Returns
    -------
    scaledVector : numpy.ndarray
        Rescaled version of the comparisonFlux vector using the above
        described process
    """

    outOfTransit = (time < ingress) + (time > egress)
    regressMatrix = np.vstack([comparisonFlux[outOfTransit]]).T
    assert len(targetFlux[outOfTransit]) > 0, \
        'No fluxes marked as "out-of-transit" according to input ingress/egress'
    m = LA.lstsq(regressMatrix, targetFlux[outOfTransit])[0]
    scaledVector = m*comparisonFlux
    if returncoeffs:
        return scaledVector, m
    else:
        return scaledVector


def chiSquared(vector1, vector2):
    """Return :math:`$\chi^2$` (chi-squared) of two vectors"""

    return np.sum(np.power(vector1-vector2, 2))


def medianBin(time, flux, medianWidth):
    """
    Produce median binning of a flux vector

    Parameters
    ----------
    time : list or numpy.ndarray
        List of times in time series

    flux : list or numpy.ndarray
        List of fluxes, one for each time in `time` vector

    medianWidth : int
        Width of each bin in units of data points

    Returns
    -------
    [binnedTime, binnedFlux, binnedStd] : [list, list, list] \
            or [numpy.ndarray, numpy.ndarray, numpy.ndarray]
        The times, fluxes and uncertainties on each binned point,
        where `binnedTime` is the time for each bin, `binnedFlux`
        is the median flux in each bin, and `binnedStd` is the standard
        deviation of the points within each bin
    """

    numberBins = int(math.ceil(len(time)/float(medianWidth)))
    binnedTime = np.arange(numberBins, dtype=float)
    binnedFlux = np.arange(numberBins, dtype=float)
    binnedStd = np.arange(numberBins, dtype=float)
    for i in range(numberBins):
        fluxInBin = flux[i*medianWidth:(i+1)*medianWidth]
        binnedTime[i] = np.median(time[i*medianWidth:(i+1)*medianWidth])
        binnedFlux[i] = np.median(fluxInBin)
        binnedStd[i] = np.std(fluxInBin)
    return binnedTime, binnedFlux, binnedStd
