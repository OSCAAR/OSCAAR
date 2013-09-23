import os
import re
import sys
import wx
import IO
import shutil
import oscaar
import urllib2
import zipfile
import datetime
import subprocess
import webbrowser
import numpy as np
import systematics
import timeConversions

from glob import glob
from matplotlib import pyplot
from mathMethods import medianBin
from oscaar.extras.knownSystemParameters import returnSystemParams
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigCanvas

APP_EXIT = 1


class OscaarFrame(wx.Frame):

    '''
    This class is the main frame of the OSCAAR GUI.
    '''

    def __init__(self, parent, objectID):

        '''
        This method defines the initialization of this class.
        '''

        self.aboutOpen = False
        self.loadOldPklOpen = False
        self.loadFittingOpen = False
        self.etdOpen = False
        self.loadMasterFlat = False
        self.overWrite = False
        self.ds9Open = False
        self.messageFrame = False
        self.IP = wx.Frame
        self.loadFitError = False
        self.loadEphFrame = False
        self.singularOccurance = 0
        self.extraRegionsOpen = False
        self.programmersEdit = False
        self.loadObservatoryFrame = False
        self.ccdGain = "1.0"
        self.exposureTime = "JD"
        self.switchTimes = 0

        self.title = "OSCAAR"
        wx.Frame.__init__(self, None, -1, self.title)
        self.panel = wx.Panel(self)

        if sys.platform == "win32":
            self.fontType = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        else:
            self.fontType = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)

        self.static_bitmap = wx.StaticBitmap(self.panel)
        self.logo = wx.Image(os.path.join(os.path.dirname(__file__), 'images',
                                          'logo4.png'), wx.BITMAP_TYPE_ANY)
        self.bitmap = wx.BitmapFromImage(self.logo)
        self.static_bitmap.SetBitmap(self.bitmap)

        self.paths = AddLCB(self.panel, -1, name="mainGUI", rowNum=5, vNum=15,
                            hNum=5, font=self.fontType)
        self.topBox = wx.BoxSizer(wx.HORIZONTAL)
        self.topBox.Add(self.paths, border=5, flag=wx.ALL)

        tupleList = [('zoom', "Track Zoom: ",
                      'Enter a number for the zoom here.', '15'),
                     ('radius', "Aperture Radius: ",
                      'Enter a decimal for the radius here.', '4.5'),
                     ('smoothing', "Smoothing Constant: ",
                      'Enter an integer for smoothing here.', '3')]

        self.leftBox = ParameterBox(self.panel, -1, tupleList, rows=5, cols=2,
                                    vNum=10, hNum=10, font=self.fontType)

        tupleList = [('ingress', "Ingress, UT (YYYY/MM/DD)",
                      "Enter a date in the correct format here.",
                      "YYYY/MM/DD"),
                     ('egress', "Egress, UT (YYYY/MM/DD)",
                      "Enter a date in the correct format here.",
                      "YYYY/MM/DD"),
                     ('rbTrackPlot', "Tracking Plots: ", "On", "Off"),
                     ('rbPhotPlot', "Photometry Plots: ", "On", "Off"),
                     ('rbFitAfterPhot', "Fit After Photometry ", "On", "Off")]

        self.radioBox = ParameterBox(self.panel, -1, tupleList, rows=5, cols=3,
                                     vNum=10, hNum=10, font=self.fontType)

        self.sizer0 = wx.FlexGridSizer(rows=1, cols=4)
        self.buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        self.buttonBox.Add(self.sizer0, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.ephButton = wx.Button(self.panel, label="Ephemeris")
        self.masterFlatButton = wx.Button(self.panel,
                                          label="Master Flat Maker")
        self.ds9Button = wx.Button(self.panel, label="Open DS9")
        self.runButton = wx.Button(self.panel, label="Run")
        self.observatoryButton = wx.Button(self.panel, label="Extra " + \
                                           "Observatory Parameters")
        self.Bind(wx.EVT_BUTTON,
                  lambda evt: self.singularExistance(evt,
                                                     self.loadObservatoryFrame,
                                                     "observatory"),
                  self.observatoryButton)
        self.Bind(wx.EVT_BUTTON,
                  lambda evt: self.singularExistance(evt, self.loadEphFrame,
                                                     "ephemeris"),
                  self.ephButton)
        self.Bind(wx.EVT_BUTTON,
                  lambda evt: self.singularExistance(evt, self.loadMasterFlat,
                                                     "masterFlat"),
                  self.masterFlatButton)
        self.Bind(wx.EVT_BUTTON,
                  lambda evt: self.singularExistance(evt, self.ds9Open,
                                                     "ds9"),
                  self.ds9Button)
        self.Bind(wx.EVT_BUTTON, self.runOscaar, self.runButton)
        self.sizer0.Add(self.ephButton, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.sizer0.Add(self.masterFlatButton, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.sizer0.Add(self.ds9Button, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        self.sizer0.Add(self.runButton, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        self.rightBox = wx.BoxSizer(wx.VERTICAL)
        self.rightBox.Add(self.radioBox, 0, flag=wx.ALIGN_CENTER | wx.ALL,
                          border=5)
        self.rightBox.Add(self.buttonBox, 0, flag=wx.ALIGN_CENTER | wx.ALL,
                          border=5)
        self.leftBox2 = wx.BoxSizer(wx.VERTICAL)
        self.leftBox2.Add(self.leftBox, 0, flag=wx.ALIGN_CENTER | wx.ALL,
                          border=5)
        self.leftBox2.Add(self.observatoryButton, 0, flag=wx.ALIGN_CENTER |
                          wx.ALL, border=5)

        self.bottomBox = wx.BoxSizer(wx.HORIZONTAL)
        self.bottomBox.Add(self.leftBox2, 0, flag=wx.ALIGN_CENTER)
        self.bottomBox.Add(self.rightBox, 0, flag=wx.ALIGN_CENTER | wx.ALL,
                           border=5)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.static_bitmap, 0, flag=wx.ALIGN_LEFT)
        self.vbox.Add(self.topBox, 0, flag=wx.ALIGN_CENTER)
        self.vbox.Add(self.bottomBox, 0, flag=wx.CENTER | wx.ALL, border=5)
        self.create_menu()
        self.CreateStatusBar()
        self.vbox.AddSpacer(10)
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)

        self.setDefaults()

        iconloc = os.path.join(os.path.dirname(__file__), 'images',
                               'logo4noText.ico')
        icon1 = wx.Icon(iconloc, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon1)

        self.Center()
        self.Show()

    def create_menu(self):

        '''
        This method creates the menu bars that are at the top of the main GUI.

        Notes
        -----
        This method has no input or return parameters. It will simply be used
         as self.create_menu() when in the initialization method for an
         OscaarFrame instance.
        '''

        menubar = wx.MenuBar()

        menu_file = wx.Menu()
        m_quit = menu_file.Append(wx.ID_EXIT, "Quit\tCtrl+Q",
                                  "Quit this application.")
        self.Bind(wx.EVT_MENU, self.on_exit, m_quit)

        menu_help = wx.Menu()
        m_help = menu_help.Append(wx.ID_HELP, "Help\tCtrl+H",
                                  "More Information about how to use this" + \
                                  " application.")
        self.Bind(wx.EVT_MENU,
                  lambda evt: self.openLink(evt,
                                            "https://github.com/OSCAAR/" + \
                                            "OSCAAR/tree/master/docs/" + \
                                            "documentationInProgress"),
                  m_help)

        menu_oscaar = wx.Menu()
        m_loadOld = menu_oscaar.Append(-1, "Load old output\tCtrl+L",
                                       "Load an old output file for " + \
                                       "further analysis.")
        m_loadFitting = menu_oscaar.Append(-1, "Fitting Routines\tCtrl-F",
                                           "Different fitting methods for " + \
                                           "analysis of an old .pkl file.")
        m_extraRegions = menu_oscaar.Append(-1, "Extra Regions File Sets",
                                            "Add extra regions files to " + \
                                            "specific referenced images.")
        self.Bind(wx.EVT_MENU,
                  lambda evt: self.singularExistance(evt, self.loadOldPklOpen,
                                                     "loadOld"),
                  m_loadOld)
        self.Bind(wx.EVT_MENU,
                  lambda evt: self.singularExistance(evt, self.loadFittingOpen,
                                                     "loadFitting"),
                  m_loadFitting)
        self.Bind(wx.EVT_MENU,
                  lambda evt: self.singularExistance(evt,
                                                     self.extraRegionsOpen,
                                                     "extra"),
                  m_extraRegions)
        
        menu_czech = wx.Menu()
        m_etd = menu_czech.Append(-1, "Czech ETD Format", "Take a .pkl file " \
                                   "and convert the data to a format that is " \
                                   "accepted by the Czech Astronomical " \
                                   "Society's exoplanet transit database.")
        m_ttp = menu_czech.Append(-1, "Transit Time Predictions",
                                   "Transit time predictions from the " + \
                                   "Czech Astronomical Society.")
        self.Bind(wx.EVT_MENU,
                  lambda evt: self.openLink(evt,
                                            "http://var2.astro.cz/ETD/" + \
                                            "predictions.php"),
                  m_ttp)
        self.Bind(wx.EVT_MENU,
                  lambda evt: self.singularExistance(evt, self.etdOpen, "etd"),
                  m_etd)
                
        menu_update = wx.Menu()
        m_update = menu_update.Append(-1, "Check For Updates", "Check to see" \
                                      "if you have the latest commit for " \
                                      "this version of oscaar.")
        self.Bind(wx.EVT_MENU, self.checkSHA, m_update)
        
        menu_about = wx.Menu()
        m_about = menu_about.Append(-1, "About", "Contributors of OSCAAR.")
        self.Bind(wx.EVT_MENU,
                  lambda evt: self.singularExistance(evt, self.aboutOpen,
                                                     "about"),
                  m_about)
        
        menubar.Append(menu_file, "File")
        menubar.Append(menu_oscaar, "Oscaar")
        menubar.Append(menu_czech, "Czech ETD")
        menubar.Append(menu_update, "Update")
        menubar.Append(menu_help, "Help")
        menubar.Append(menu_about, "About")
        self.SetMenuBar(menubar)

    def runOscaar(self, event):

        '''
        This method will activate when the run button on the main GUI is
         pressed. It executes the differentialPhotometry.py script.

        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The *
             represents a wild card value.

        Notes
        -----
        There is nothing to return for this method. Upon completion a window
         will open with the light curve that was produced from the data and
         input parameters.
        '''

        self.values = {}
        invalidDarkFrames = self.checkFileInputs(self.paths.boxList[1].
                                                 GetValue(), saveNum=1)
        masterFlat = self.paths.boxList[2].GetValue().strip()
        invalidDataImages = self.checkFileInputs(self.paths.boxList[3].
                                                 GetValue(), saveNum=3)
        regionsFile = self.paths.boxList[4].GetValue().strip()
        self.outputFile = self.paths.boxList[5].GetValue().strip()
        self.values["radius"] = self.leftBox.userParams["radius"].GetValue()
        self.radiusError = "radius"

        if invalidDarkFrames != "":
            self.IP = InvalidParameter(invalidDarkFrames, self, -1,
                                       stringVal="fits",
                                       secondValue="the path to Dark Frames")
        elif os.path.isfile(masterFlat) != True or \
        (masterFlat.lower().endswith(".fit") != True and \
         masterFlat.lower().endswith(".fits") != True):
            tempString = masterFlat
            if len(masterFlat.split(",")) > 1:
                tempString = ""
                for string in masterFlat.split(","):
                    if string == "" and len(masterFlat.split(",")) == 2:
                        tempString += ","
                    else:
                        tempString += "\n" + string.strip()
            self.IP = InvalidParameter(tempString, self, -1,
                                       stringVal="master",
                                       secondValue="path to the Master Flat")
        elif invalidDataImages != "":
            self.IP = InvalidParameter(invalidDataImages, self, -1,
                                       stringVal="fits",
                                       secondValue="the path to Data Images")
        elif self.checkRegionsBox(regionsFile) == False:
            pass
        elif not os.path.isdir(self.outputFile.rpartition(str(os.sep))[0]) or \
             not len(self.outputFile) > \
             (len(self.outputFile[:self.outputFile.rfind(os.sep)]) + 1):
            self.IP = InvalidParameter(self.outputFile, self, -1,
                                       stringVal="output",
                                       secondValue="output file")
        elif self.checkAperture(self.values["radius"]) != True:
            self.IP = InvalidParameter(self.leftBox.userParams["radius"].
                                       GetValue(), self, -1,
                                       stringVal=self.radiusError)
        elif self.timeAndDateCheck(self.radioBox.userParams['ingress1'].
                                   GetValue(),
                                   self.radioBox.userParams['egress1'].
                                   GetValue(),
                                   self.radioBox.userParams['ingress'].
                                   GetValue(),
                                   self.radioBox.userParams['egress'].
                                   GetValue()) == True:
            try:
                tempList = ["smoothing", "zoom"]
                for string in tempList:
                    self.values[string] = int(self.leftBox.userParams[string].GetValue())
                    self.leftBox.userParams[string].SetValue(str(self.values[string]))

                self.paths.boxList[2].SetValue(masterFlat)
                self.paths.boxList[5].SetValue(self.outputFile)
                
                # This code here writes all the parameters to the init.par file.
                
                init = open(os.path.join(os.path.dirname(__file__),'init.par'), 'w')
                init.write("Path to Dark Frames: " + self.paths.boxList[1].GetValue() + "\n")
                init.write("Path to Data Images: " + self.paths.boxList[3].GetValue() + "\n")
                init.write("Path to Master-Flat Frame: " + self.paths.boxList[2].GetValue() + "\n")
                init.write("Path to Regions File: " + self.paths.boxList[4].GetValue() + "\n")
                if not self.paths.boxList[5].GetValue().lower().endswith(".pkl"):
                    init.write("Output Path: " + self.paths.boxList[5].GetValue() + ".pkl\n")
                else:
                    init.write("Output Path: " + self.paths.boxList[5].GetValue() + "\n")
        
                self.parseTime(self.radioBox.userParams["ingress"].GetValue(),
                               self.radioBox.userParams["ingress1"].GetValue(), 'Ingress: ',  init, name="ingress")
                self.parseTime(self.radioBox.userParams["egress"].GetValue(),
                               self.radioBox.userParams["egress1"].GetValue(), 'Egress: ',  init, name="egress")
                if self.radioBox.userParams['rbTrackPlot'].GetValue():
                    init.write("Plot Tracking: " + "on"+ "\n")
                else:
                    init.write("Plot Tracking: " + "off"+ "\n")
                if self.radioBox.userParams['rbPhotPlot'].GetValue():
                    init.write("Plot Photometry: " + "on"+ "\n")
                else:
                    init.write("Plot Photometry: " + "off"+ "\n")
                
                init.write("Smoothing Constant: " + str(self.values["smoothing"]) + '\n')
                init.write("Radius: " + str(self.values["radius"]) + '\n')
                init.write("Tracking Zoom: " + str(self.values["zoom"]) + '\n')
                init.write("CCD Gain: " + self.ccdGain + "\n")
                init.write("Exposure Time Keyword: " + self.exposureTime + "\n")
                init.close()
                if self.loadFittingOpen == False:
                    if os.path.isfile(self.outputFile) or os.path.isfile(self.outputFile + '.pkl'):
                        if self.overWrite == False:
                            OverWrite(self, -1, "Overwrite Output File", self.outputFile, "Output File")
                            self.overWrite = True
                    else:
                        diffPhotCall = "from oscaar import differentialPhotometry"
                        subprocess.check_call(['python','-c',diffPhotCall])
                        if self.radioBox.userParams["rbFitAfterPhot"].GetValue() == True:
                            wx.CallAfter(self.createFrame)

                else:
                    if self.loadFitError == False:
                        self.IP = InvalidParameter("", self, -1, stringVal="fitOpen")
                        self.loadFitError = True
            except ValueError:
                string2 = string
                if string2 == "smoothing":
                    string2 = "smoothing constant"
                self.IP = InvalidParameter(self.leftBox.userParams[string].GetValue(),self,-1, stringVal="leftbox", secondValue=string2)
    
    def timeAndDateCheck(self, time1, time2, date1, date2):
        
        '''
        This method checks that the times and dates entered in the main GUI are in the correct format.
        
        Parameters
        ----------
        time1 : string
            The ingress time of the transit that was observed.
        
        time2 : string
            The egress time of the transit that was observed.
            
        date1 : string
            The date for the ingress of the transit.
        
        date2 : string
            The date for the egress of the transit.
        
        Returns
        -------
        literal : bool
            Returns true if the parameters are all in the correct format, otherwise it returns false.
        
        Notes
        -----
        The correct format for the times is HH:MM:SS, while for the dates it is YYYY/MM/DD. This method
        will also check that real dates have been entered, as well as that the ingress time always
        is before the egress time.
        '''
        
        years = []
        months = []
        days = []
        hours = []
        minutes = []
        seconds = []
        
        for timeArray, value in [(time1.split(":"), time1),
                                 (time2.split(":"), time2)]:
            if len(timeArray) != 3:
                self.IP = InvalidParameter(value, self, -1, stringVal="dateTime", secondValue="time")
                return False
            else:
                try:
                    hour = int(timeArray[0].strip())
                    hours.append(hour)
                    minute = int(timeArray[1].strip())
                    minutes.append(minute)
                    second = int(timeArray[2].strip())
                    seconds.append(second)
    
                    if len(timeArray[0].strip()) > 2 or len(timeArray[1].strip()) > 2 or len(timeArray[2].strip()) > 2:
                        self.IP = InvalidParameter(value, self, -1, stringVal="dateTime", secondValue="time")
                        return False
                    
                    if hour > 23 or hour < 0 or minute > 59 or minute < 0 or second > 59 or second < 0:
                        self.IP = InvalidParameter(value, self, -1, stringVal="dateTime", secondValue="time")
                        return False
                    
                except ValueError:
                    self.IP = InvalidParameter(value, self, -1, stringVal="dateTime", secondValue="time")
                    return False
                
        for dateArray,value in [(date1.split("/"),date1),
                                (date2.split("/"),date2)]:
            if len(dateArray) != 3:
                self.IP = InvalidParameter(value, self, -1, stringVal="dateTime", secondValue="date")
                return False
            else:
                try:
                    year = int(dateArray[0].strip())
                    years.append(year)
                    month = int(dateArray[1].strip())
                    months.append(month)
                    day = int(dateArray[2].strip())
                    days.append(day)
                    
                    if len(dateArray[0].strip()) != 4 or len(dateArray[1].strip()) > 2 or len(dateArray[2].strip()) > 2:
                        self.IP = InvalidParameter(value, self, -1, stringVal="dateTime", secondValue="date")
                        return False
                    minYear = datetime.date.today().year - 100
                    maxYear = datetime.date.today().year + 100
                    if year < minYear or year > maxYear or month > 12 or month < 0 or day > 31 or day < 0 or \
                       month == 0 or year == 0 or day == 0:
                        self.IP = InvalidParameter(value, self, -1, stringVal="dateTime", secondValue="date")
                        return False
                except ValueError:
                    self.IP = InvalidParameter(value, self, -1, stringVal="dateTime", secondValue="date")
                    return False

        if years[0] > years[1]:
            self.IP = InvalidParameter(date1, self, -1, stringVal="logicalDate")
            return False
        elif years[0] == years[1]:
            if months[0] > months[1]:
                self.IP = InvalidParameter(date1, self, -1, stringVal="logicalDate")
                return False
            elif months[0] == months[1]:
                if days[0] > days[1]:
                    self.IP = InvalidParameter(date1, self, -1, stringVal="logicalDate")
                    return False
                elif days[0] == days[1]:
                    if hours[0] > hours[1]:
                        self.IP = InvalidParameter(time1, self, -1, stringVal="logicalTime")
                        return False
                    elif hours[0] == hours[1]:
                        if minutes[0] > minutes[1]:
                            self.IP = InvalidParameter(time1, self, -1, stringVal="logicalTime")
                            return False
                        elif minutes[0] == minutes[1]:
                            if seconds[0] >= seconds [1]:
                                self.IP = InvalidParameter(time1, self, -1, stringVal="logicalTime")
                                return False
        return True
    
    def checkAperture(self, stringVal):
        
        '''
        This method parses the string from the aperture radius text box to make sure that the values
        are in the correct format and valid.
        
        Parameters
        ----------
        stringVal : string
            The input of the aperture radius text box in the main GUI.
        
        Returns
        -------
        literal : bool
            True if the values are valid and false otherwise.
        
        Notes
        -----
        This method will check the radius step interval is not larger than the max and min radii, as well
        as that the max radius is always larger than the min radius. Only when using 3 values in this text control
        box, the GUI will interpret it as (min radius, max radius, step interval), otherwise it only computes
        the specific values entered. 
        '''
        
        splitString = stringVal.split(",")
        if len(splitString) == 1:
            try:
                float(splitString[0])
                self.leftBox.userParams["radius"].SetValue(str(float(splitString[0])))
                return True
            except ValueError:
                self.radiusError = "radiusNum"
                return False

        elif len( splitString) == 3:
            minRadius = splitString[0].strip()
            maxRadius = splitString[1].strip()
            stepSize = splitString[2].strip()
            try:
                minRadius = float(minRadius)
                maxRadius = float(maxRadius)
                stepSize = float(stepSize)
                if minRadius == maxRadius:
                    self.radiusError = "radiusEqual"
                    return False
                elif minRadius > maxRadius:
                    self.radiusError = "radiusLogic"
                    return False
                elif (maxRadius-minRadius) < stepSize:
                    self.radiusError = "radiusStep"
                    return False
                
                if stepSize == 0:
                    self.radiusError = "radiusLogic"
                    return False
                elif minRadius == 0 or maxRadius == 0:
                    self.radiusError = "radiusLogic"
                    return False
                self.values["radius"] = str(minRadius) + "," + str(maxRadius) + "," + str(stepSize)
                self.leftBox.userParams["radius"].SetValue(str(minRadius) + "," + str(maxRadius) + "," + str(stepSize))
                return True

            except ValueError:
                self.radiusError = "radiusNum"
                return False
        else:
            stringTemp = ""
            for num in splitString:
                numStrip = num.strip()
                try:
                    float(numStrip)
                    if numStrip == 0:
                        self.radiusError = "radiusLogic2"
                        return False
                except ValueError:
                    self.radiusError = "radiusNum"
                    return False
                stringTemp += str(float(numStrip)) + ","
            
            self.values["radius"] = stringTemp.rpartition(",")[0]
            self.leftBox.userParams["radius"].SetValue(stringTemp.rpartition(",")[0])
            return True
    
    def setDefaults(self):
        
        '''
        This method will set the default values for the text boxes in the main GUI with those
        listed in the init.par file.
        
        Notes
        -----
        This is a recursive string parser that searches for the provided keywords.
        '''
        
        if self.programmersEdit == True:
            init = open("init.par","r").read().splitlines()
        else:
            oscaarpath = os.path.dirname(os.path.abspath(oscaar.__file__))
            init = open(os.path.join(oscaarpath,'init.par'), 'r').read().splitlines()
        for line in init:
            if len(line.split()) > 1:
                inline = line.split(':', 1)
                name = inline[0].strip()
                value = str(inline[1].strip())
                tempList = [("Path to Master-Flat Frame", 2),
                            ("Path to Regions File", 4),
                            ("Ingress", "ingress"),("Egress", "egress"),
                            ("Radius", "radius"),("Tracking Zoom", "zoom"),
                            ("Plot Tracking", "rbTrackPlot"),
                            ("Plot Photometry", "rbPhotPlot"),("Smoothing Constant", "smoothing"),
                            ("Output Path",5),("Path to Dark Frames", 1),("Path to Data Images", 3),
                            ("CCD Gain",""),("Exposure Time Keyword","")]
                
                for string,save in tempList:
                    if string == name:
                        if name == "Smoothing Constant" or name == "Tracking Zoom":
                            self.leftBox.userParams[save].SetValue(value)
                        elif name == "Radius":
                            stripTemp = [x.strip() for x in value.split(",")]
                            stringTemp = ""
                            for eachTemp in stripTemp:
                                stringTemp += eachTemp + ","
                            self.leftBox.userParams[save].SetValue(stringTemp.rpartition(",")[0])
                        elif name == "Plot Photometry" or name == "Plot Tracking":
                            if value == "off":
                                save += "1"
                            self.radioBox.userParams[save].SetValue(True)
                        elif name == "Path to Dark Frames" or name == "Path to Data Images":
                            tempArray = value.split(",")
                            tempArray[:] = [x.strip() for x in tempArray]
                            finalString = ""
                            for eachString in tempArray:
                                finalString += eachString + ","
                            self.paths.boxList[save].SetValue(finalString.rpartition(",")[0])
                        elif name == "Path to Master-Flat Frame" or name == "Path to Regions File" or\
                             name == "Output Path":
                            self.paths.boxList[save].SetValue(value)
                        elif name == "CCD Gain":
                            self.ccdGain = value
                        elif name == "Exposure Time Keyword":
                            self.exposureTime = value
                        else:
                            date = value.split(";")[0].strip().replace("-","/")
                            time = value.split(";")[1].strip()
                            for eachOne, other in [(date,""),(time,"1")]:
                                if other == "1":
                                    separator = ":"
                                else:
                                    separator = "/"
                                stripTemp = [x.strip() for x in eachOne.split(separator)]
                                stringTemp = ""
                                for eachTemp in stripTemp:
                                    stringTemp += eachTemp + separator
                                if other == "1":
                                    self.radioBox.userParams[save+"1"].SetValue(stringTemp.rpartition(separator)[0])
                                else:
                                    self.radioBox.userParams[save].SetValue(stringTemp.rpartition(separator)[0])

    def checkFileInputs(self,array,saveNum):
        
        '''
        This checks that the files from a text control box are valid .fit/.fits files. Then it refreshes
        the text control box with a string of the valid files.
        
        Parameters
        ----------
        array : string
            The list of files from a text control box in the main GUI.
        
        saveNum : int
            When it refreshes the text control box, the method needs to know which box to do it for. The box numbers from
            the main GUI are in order 1-5 (this is only for the input file text boxes).
        
        Returns
        -------
        errorString : string
            A string of all of the invalid files that were entered in the input file text box.
            
        Notes
        -----
        If errorString returns '' (empty), this means that all of the entered files were valid.
        '''
        
        errorString = ""
        setValueString = ""
        array2 = []
        smallArray = ""
        for element in array.split(","):
            element = element.strip()
            if element.lower().endswith(os.sep):
                tempElement = element + "*.fit"
                element += "*.fits"
                smallArray = "-1"
            if smallArray == "":
                if len(glob(element)) < 1:
                    errorString += element
                elif len(glob(element)) > 1:
                    for element2 in glob(element):
                        if element2.lower().endswith(".fit") or element2.lower().endswith(".fits"):
                            array2.append(element2)
                        else:
                            errorString += "\n" + element2
                elif not element.lower().endswith(".fit") and not element.lower().endswith(".fits"):
                    errorString += "\n" + element
                else:
                    array2.append(glob(element)[0])
            else:
                if len(glob(tempElement)) < 1 and len(glob(element)) < 1:
                    errorString += "\n" + tempElement + ",\n" + element
                else:
                    if len(glob(tempElement)) >= 1:
                        for element2 in glob(tempElement):
                            array2.append(element2)
                    if len(glob(element)) >= 1:
                        for element2 in glob(element):
                            array2.append(element2)
        if not array:
            return "No Values Entered"
        else:
            if errorString == "":
                setValueString = ""
                uniqueArray = np.unique(array2).tolist()
                for eachString in uniqueArray:
                    setValueString += eachString + ","
                if saveNum == 3 and (len(uniqueArray) < 2):
                    errorString = self.paths.boxList[3].GetValue()
                    return errorString
                self.paths.boxList[saveNum].SetValue(setValueString.rpartition(",")[0])
            return errorString
        
    def checkRegionsBox(self, boxValue):
        
        '''
        This method specifically checks that the regions file input box in the main GUI has files that are in 
        the correct format.
        
        Parameters
        ----------
        boxValue : string
            The value of the regions file box.
            
        Returns
        -------
        literal : bool
            True if all of the files are valid, false otherwise.
        
        Notes
        -----
        The correct format for files in the regions file box is (somefile.reg,referencefile.fits;). The semicolon will
        separate different sets of regions and reference files. Only if there is one regions file is it acceptable to
        not include a reference file, otherwise you must.
        '''
        
        setValueString = ""
        tempString = ""
        if boxValue == "":
            self.IP = InvalidParameter(boxValue, self, -1, stringVal="emptyReg")
            return False
        splitSets = boxValue.split(";")
        checkSet = self.paths.boxList[3].GetValue().strip().split(",")
        try:
            if len(splitSets[0].split(",")) == 1 and len(splitSets[1]) == 0 and len(splitSets) == 2 and \
               splitSets[0].split(",")[0].strip().lower().endswith(".reg"):
                setValueString = splitSets[0].strip() + "," + self.paths.boxList[3].GetValue().split(",")[0].strip() + ";"
            elif splitSets[0].split(",")[1].strip() == "" and len(splitSets[1]) == 0 and len(splitSets) == 2:
                if splitSets[0].split(",")[0].strip().lower().endswith(".reg") != True or \
                   len(glob(splitSets[0].split(",")[0])) != 1:
                    self.IP = InvalidParameter("\nRegions: "+ splitSets[0].split(",")[0]
                                     + "\nReference: " + splitSets[0].split(",")[1], self, -1, stringVal="invalidReg")
                    return False
                setValueString = splitSets[0].split(",")[0].strip() + "," + \
                                 self.paths.boxList[3].GetValue().split(",")[0].strip() + ";"
            else:
                try:
                    for eachSet in splitSets:
                        if eachSet != "":
                            tempString = "tempReg"
                            tempReg = eachSet.split(",")[0].strip()
                            tempString = "tempRef"
                            tempRef = eachSet.split(",")[1].strip()
                            if len(glob(tempReg)) != 1 or tempReg.lower().endswith(".reg") == False:
                                self.IP = InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, stringVal="invalidReg")
                                return False
                            elif len(glob(tempRef)) != 1 or (tempRef.lower().endswith(".fits") == False and 
                                                             tempRef.lower().endswith(".fit") == False):
                                self.IP = InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, stringVal="invalidRef")
                                return False
                            elif all(tempRef != temp for temp in checkSet):
                                self.IP = InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, stringVal="invalidRefExist")
                                return False
                            setValueString += tempReg + "," + tempRef + ";"
                except IndexError:
                    if tempString == "tempReg":
                        tempReg = ""
                    elif tempString == "tempRef":
                        tempRef = ""
                    if len(eachSet.split(",")) == 1:
                        self.IP = InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, stringVal="outofbounds")
                        return False
        except IndexError:
            if splitSets[0].split(",")[0].strip().lower().endswith(".reg") != True or \
                   len(glob(splitSets[0].split(",")[0])) != 1:
                if len(splitSets[0].split(",")) == 1:
                    temp = ""
                else:
                    temp = splitSets[0].split(",")[1]
                self.IP = InvalidParameter("\nRegions: "+ splitSets[0].split(",")[0] 
                                 + "\nReference: " + temp, self, -1, stringVal="invalidReg")
                return False
            setValueString = splitSets[0].split(",")[0].strip() + "," + \
                             self.paths.boxList[3].GetValue().split(",")[0].strip()
            splitSets[0] = setValueString
            setValueString = ""
            try:
                for eachSet in splitSets:
                    if eachSet != "":
                        tempString = "tempReg"
                        tempReg = eachSet.split(",")[0].strip()
                        tempString = "tempRef"
                        tempRef = eachSet.split(",")[1].strip()
                        if len(glob(tempReg)) != 1 or tempReg.lower().endswith(".reg") == False:
                            self.IP = InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, stringVal="invalidReg")
                            return False
                        elif len(glob(tempRef)) != 1 or (tempRef.lower().endswith(".fits") == False and 
                                                         tempRef.lower().endswith(".fit") == False):
                            self.IP = InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, stringVal="invalidRef")
                            return False
                        elif all(tempRef != temp for temp in checkSet):
                            self.IP = InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, stringVal="invalidRefExist")
                            return False
                        setValueString += tempReg + "," + tempRef + ";"
            except IndexError:
                if tempString == "tempReg":
                    tempReg = ""
                elif tempString == "tempRef":
                    tempRef = ""
                if len(eachSet.split(",")) == 1:
                    self.IP = InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, stringVal="outofbounds")
                    return False
        refArray = []
        regArray = []
        tempDict = {}
        for eachSet in setValueString.split(";"):
            if len(eachSet.split(",")) != 1:
                reg = eachSet.split(",")[0]
                ref = eachSet.split(",")[1]
                regTemp = reg in regArray
                refTemp = ref in refArray
                if regTemp == False and refTemp == False:
                    regArray.append(reg)
                    refArray.append(ref)
                    tempDict[reg] = ref
                elif regTemp == False and refTemp == True:
                    for key, val in tempDict.items():
                        if val == ref:
                            tempReg = key
                    tempString = "\nRegions: " + reg + "\nReference: " + ref + "\nBecause ---" + "\nRegions: " + \
                    tempReg + "\nIs already associated with the reference file."
                    self.IP = InvalidParameter(tempString, self, -1, stringVal="referenceImageDup")
                    return False
                elif regTemp == True and refTemp == False:
                    tempRef = tempDict.get(reg)
                    tempString = "\nRegions: " + reg + "\nReference: " + ref + "\nBecause ---" + "\nRegions: " + \
                    reg + "\nIs already associated with:\nReference: " + tempRef
                    self.IP = InvalidParameter(tempString, self, -1, stringVal="regionsDup")
                    return False
        
        setValueString = ""
        for key, val in tempDict.items():
            setValueString += key + "," + val + ";"
        self.paths.boxList[4].SetValue(setValueString)
        return True
    
    def singularExistance(self, event, value, name):
        
        '''
        This method checks to make sure that there is only one frame of each class open at once, as to not
        have two fitting frames open and such.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        
        value : bool
            Indicates whether or not there is already an instance of the class open.
        
        name : string
            The keyword defining the name of the class for which a frame is about to be opened.
        
        Notes
        -----
        There is nothing returned for this method. On a successful completion, a new frame will appear. If
        `value` is True however, then the method does nothing because there is already an instance of the frame
        open, so it will not duplicate it.       
        '''

        if value == False:
            if name == "about":
                AboutFrame(self,-1)
                self.aboutOpen = True
            elif name == "loadOld":
                LoadOldPklFrame(self, -1)
                self.loadOldPklOpen = True
            elif name == "loadFitting":
                FittingFrame(self, -1)
                self.loadFittingOpen = True
            elif name == "masterFlat":
                MasterFlatFrame(self, -1)
                self.loadMasterFlat = True
            elif name == "ephemeris":
                EphemerisFrame(self, -1)
                self.loadEphFrame = True
            elif name == "ds9":
                if sys.platform == "win32":
                    errorType = WindowsError
                else:
                    errorType = OSError
                try:
                    subprocess.Popen([os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),
                                                   'extras','ds9',sys.platform,'ds9')])
                except errorType:
                    self.IP = InvalidParameter("", self, -1, stringVal="ds9")
            elif name == "extra":
                invalidDataImages = self.checkFileInputs(self.paths.boxList[3].GetValue(), saveNum=3)
                if invalidDataImages != "":
                    self.IP = InvalidParameter(invalidDataImages, self, -1, stringVal="fits", secondValue="the path to Data Images")
                elif self.checkRegionsBox(self.paths.boxList[4].GetValue()) == True:
                    ExtraRegions(self,-1)
                    self.extraRegionsOpen = True
            elif name == "observatory":
                invalidDataImages = self.checkFileInputs(self.paths.boxList[3].GetValue(), saveNum=3)
                if invalidDataImages != "":
                    self.IP = InvalidParameter(invalidDataImages, self, -1, stringVal="fits", secondValue="the path to Data Images")
                else:
                    ObservatoryFrame(self, -1)
                    self.loadObservatoryFrame = True
            elif name == "etd":
                ETDFrame(self, -1)
                self.etdOpen = True
                    
    def parseTime(self, date, time, text, filename, name=""):
        
        '''
        This method prints the dates and times of the transit into the init.par file in the correct format.
        
        Parameters
        ----------
        date : string
            A string of the date in the format YYYY/MM/DD.
        
        time : string
            A string of the time in the format HH:MM:SS.
        
        text : string
            The name of what should be entered in the init.par file before the actual values (ingress or egress).
        
        filename : file
            The open file that the value will be appended to.
        
        name : string, optional
            The name of the text box that will be refreshed.
        
        Notes
        -----
        When it is done printing into init.par, the method refreshes the values of the text control boxes for ingress
        and egress so there are no spaces and such in between.
        '''
        
        dateArr = str(date).split('/')
        result = dateArr[0].strip() + '-' + dateArr[1].strip() + '-' + dateArr[2].strip() + ' ; '
        timeArr = str(time).split(":")
        result += timeArr[0].strip() + ":" + timeArr[1].strip() + ':' + timeArr[2].strip()
        filename.write(text + result + '\n')
        
        self.radioBox.userParams[name].SetValue(dateArr[0].strip() + '/' + dateArr[1].strip() + '/' + dateArr[2].strip())
        self.radioBox.userParams[name+"1"].SetValue(timeArr[0].strip() + ":" + timeArr[1].strip() + ':' +
                                                    timeArr[2].strip())

    def createFrame(self):
        
        '''
        This method allows the fitting frame to be opened after the completion of the differentialPhotometry.py script
        so that users may work on their light curves.
        '''
        
        if self.loadFittingOpen == False:
            if not self.outputFile.lower().endswith(".pkl"):
                FittingFrame(self, -1, self.outputFile + ".pkl")
                self.loadFittingOpen = True
            else:
                FittingFrame(self, -1, self.outputFile)
                self.loadFittingOpen = True
    
    def checkSHA(self, event):
        
        '''
        This method checks the secure hash algorithm that is saved when 
        oscaar is installed in __init__.py against the one online for the 
        latest commit.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * 
            represents a wild card value.
        
        Notes
        -----
        There is no return. If both the sha's are equal, then the latest 
        version of oscaar is installed, and a pop up message explains so. If 
        they are not equal, a message pops up to tell the user to download 
        the latest commit.
        '''
        
        url = urllib2.urlopen("https://github.com/OSCAAR/OSCAAR/commits/" \
                              "master").read()
        mostRecentCommit = re.search('href="/OSCAAR/OSCAAR/commit/[a-z0-9]*', 
                                  str(url)).group(0).rpartition("/")[2]
        try:
            currentCommit = oscaar.__sha__
            if mostRecentCommit == currentCommit:
                self.IP = InvalidParameter("", self, -1, stringVal="upToDate")
            else:
                self.IP = InvalidParameter("", self, -1, stringVal="newCommit")
        except AttributeError:
            self.IP = InvalidParameter("", self, -1, stringVal="installAgain")
        except urllib2.URLError:
            self.IP = InvalidParameter("", self, -1, stringVal="installAgain")

    def openLink(self, event, string):
        
        '''
        This opens a new tab in the default web browser with the specified link.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        
        string : string
            The web url that will be opened.
        '''
        
        webbrowser.open_new_tab(string)
    
    def on_exit(self, event):
        
        '''
        This method defines the action quit from the menu. It closes the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()

class ObservatoryFrame(wx.Frame):
    
    '''
    This is a frame for updating extra parameters that would define an observatory's configuration.
    '''

    def __init__(self, parent, objectID):
        
        '''
        This method defines the initialization of this class.
        '''

        if sys.platform == "win32":
            self.fontType = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        else: 
            self.fontType = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)

        wx.Frame.__init__(self, parent, objectID, "Change Observatory Parameters")
        self.panel = wx.Panel(self)
        self.parent = parent
        self.messageFrame = False
        self.IP = wx.Frame
        self.titlebox = wx.StaticText(self.panel, -1, "Observatory Parameters")
        self.titleFont = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.titlebox.SetFont(self.titleFont)
        
        paramsList = [('ccd',"CCD Gain: ",
                 'Enter a decimal for the gain here.', self.parent.ccdGain)]
        
        # Quick check to see the available keywords from the header for a fits file. 
        #    header = pyfits.getheader(self.parent.paths.boxList[3].GetValue().split(",")[0]).keys()
        #    print header
        
        bestKeyword, self.allKeys, acceptedKeys, conversion = \
            timeConversions.findKeyword(self.parent.paths.boxList[3].GetValue().split(",")[0])
        
        if conversion: pass
        self.unionKeys = []
        for eachKey in self.allKeys:
            if eachKey in acceptedKeys:
                self.unionKeys.append(eachKey)
        
        self.timeLabel = wx.StaticText(self.panel, -1, 'Select Exposure Time Keyword: ')
        self.timeLabel.SetFont(self.fontType)
        if self.parent.switchTimes == 0:
            self.timeList = wx.ComboBox(self.panel, value = bestKeyword, choices = sorted(self.unionKeys),
                                        size=(75,wx.DefaultSize.GetHeight()))
            self.parent.switchTimes = 1
        else:
            self.timeList = wx.ComboBox(self.panel, value = self.parent.exposureTime, choices = sorted(self.unionKeys),
                                        size=(75,wx.DefaultSize.GetHeight()))
        self.timeList.Bind(wx.EVT_COMBOBOX, self.updateTime)

        self.dropBox = wx.BoxSizer(wx.HORIZONTAL)
        self.dropBox.Add(self.timeLabel, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 10)
        self.dropBox.Add(self.timeList, 0, flag = wx.ALIGN_CENTER)
        
        self.params = ParameterBox(self.panel, -1, paramsList, rows=5, cols=2, vNum=10, hNum=10, font=self.fontType)
       
        self.updateButton = wx.Button(self.panel, label = "Update")
        self.Bind(wx.EVT_BUTTON, self.update, self.updateButton)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.titlebox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.vbox.Add(self.params, 0, flag = wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, border = 5)
        self.vbox.Add(self.dropBox, 0, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        self.vbox.Add(self.updateButton, 0, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.create_menu()
        self.CreateStatusBar()
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.Center()
        self.Show()      
    
    def updateTime(self,event):
        
        '''
        This updates the exposure time keyword variable for parsing the .fit(s) files in the parent OscaarFrame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.exposureTime = self.timeList.GetValue()
    
    def update(self, event):
        
        '''
        This updates the exposure time keyword for parsing .fit(s) files as well as the ccd gain in the init.par file.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        if self.checkParams() == True:
            self.parent.ccdGain = self.params.userParams["ccd"].GetValue()
            self.parent.exposureTime = self.timeList.GetValue()         
            string = open(os.path.join(os.path.dirname(__file__),'init.par'), 'r').read().splitlines()
            stringCopy = np.copy(string)
            for line in stringCopy:
                if ("CCD Gain:" in line) or ("Exposure Time Keyword:" in line):
                    string.remove(line)
            observ = open(os.path.join(os.path.dirname(__file__),'init.par'), 'w')
            observ.write('\n'.join(string))
            observ.write("\nCCD Gain: " + self.params.userParams["ccd"].GetValue() + "\n")
            observ.write("Exposure Time Keyword: " + self.timeList.GetValue() + "\n")

    def checkParams(self):
        
        '''
        This is check to make sure that the ccd gain and exposure time keyword are valid, 
        before updating the init.par file.
        
        Returns
        -------
        literal : bool
            True if both ccd gain and exposure time keyword are valid, false otherwise.
        '''
        
        try:
            tempCCD = float(self.params.userParams["ccd"].GetValue())
            self.params.userParams["ccd"].SetValue(str(tempCCD))
            timeKey = self.timeList.GetValue().strip()
            if timeKey == "":
                self.IP = InvalidParameter(timeKey, self, -1, stringVal="emptyKeyword")
                return False
            elif not timeKey in self.allKeys:
                self.IP = InvalidParameter(timeKey, self, -1, stringVal="invalidKeyword")
                return False
            elif (not timeKey in self.unionKeys) and (timeKey in self.allKeys):
                self.IP = InvalidParameter(timeKey, self, -1, stringVal="emailKeyword")
                return False
            self.timeList.SetValue(timeKey)
        except ValueError:
            self.IP = InvalidParameter(self.params.userParams["ccd"].GetValue(),self,-1, stringVal="leftbox", secondValue="ccd")
            return False
        return True

    def create_menu(self):
        
        '''
        This method creates the menu bars that are at the top of the observatory frame.
        
        Notes
        -----
        This method has no input or return parameters. It will simply be used as self.create_menu()
        when in the initialization method for an instance of this frame.
        '''
        
        menubar = wx.MenuBar()
        menu_file = wx.Menu()
        m_quit = menu_file.Append(wx.ID_EXIT, "Quit\tCtrl+Q", "Quit this application.")
        self.Bind(wx.EVT_MENU, self.on_exit, m_quit)
    
        menubar.Append(menu_file, "File")
        self.SetMenuBar(menubar)
    
    def on_exit(self,event):
        
        '''
        This method defines the action quit from the menu. It closes the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()

    def onDestroy(self,event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.loadObservatoryFrame = False

class ExtraRegions(wx.Frame):
    
    '''
    This frame allows a user to append multiple regions files and their respective reference files as sets to the 
    regions file text box in the parent OscaarFrame.
    '''

    def __init__(self, parent, objectID):
        
        '''
        This method defines the initialization of this class.
        '''

        if sys.platform == "win32":
            self.fontType = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        else: 
            self.fontType = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)

        wx.Frame.__init__(self, parent, objectID, "Extra Regions Files")
        self.panel = wx.Panel(self)
        self.parent = parent
        self.messageFrame = False
        self.IP = wx.Frame
        self.titlebox = wx.StaticText(self.panel, -1, "Extra Regions Files")
        self.titleFont = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.titlebox.SetFont(self.titleFont)
        self.set1 = AddLCB(self.panel, -1, name="Path to Regions File: ,Path to Reference Image: ", rowNum=2, vNum=5,
                            hNum=5, boxName ="Set 1", font=self.fontType)
        self.set2 = AddLCB(self.panel, -1, name="Path to Regions File: ,Path to Reference Image: ", rowNum=2, vNum=5,
                             hNum=5, boxName="Set 2", font=self.fontType)
        self.set3 = AddLCB(self.panel, -1, name="Path to Regions File: ,Path to Reference Image: ", rowNum=2, vNum=5,
                             hNum=5, boxName="Set 3", font=self.fontType)
        self.set4 = AddLCB(self.panel, -1, name="Path to Regions File: ,Path to Reference Image: ", rowNum=2, vNum=5,
                            hNum=5, boxName="Set 4", font=self.fontType)
        self.set5 = AddLCB(self.panel, -1, name="Path to Regions File: ,Path to Reference Image: ", rowNum=2, vNum=5,
                            hNum=5, boxName="Set 5", font=self.fontType)
        self.addSet1= wx.Button(self.panel, -1, label = "Add Set 1")
        self.Bind(wx.EVT_BUTTON, lambda evt, lambdaStr=self.addSet1.Label: self.addSet(evt,lambdaStr), self.addSet1)
        self.addSet2= wx.Button(self.panel, -1, label = "Add Set 2")
        self.Bind(wx.EVT_BUTTON, lambda evt, lambdaStr=self.addSet2.Label: self.addSet(evt,lambdaStr), self.addSet2)
        self.addSet3= wx.Button(self.panel, -1, label = "Add Set 3")
        self.Bind(wx.EVT_BUTTON, lambda evt, lambdaStr=self.addSet3.Label: self.addSet(evt,lambdaStr), self.addSet3)
        self.addSet4= wx.Button(self.panel, -1, label = "Add Set 4")
        self.Bind(wx.EVT_BUTTON, lambda evt, lambdaStr=self.addSet4.Label: self.addSet(evt,lambdaStr), self.addSet4)
        self.addSet5= wx.Button(self.panel, -1, label = "Add Set 5")
        self.Bind(wx.EVT_BUTTON, lambda evt, lambdaStr=self.addSet5.Label: self.addSet(evt,lambdaStr), self.addSet5)
        
        self.vbox2 = wx.BoxSizer(wx.VERTICAL)
        self.vbox2.Add(self.addSet1, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 35)
        self.vbox2.Add(self.addSet2, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 35)
        self.vbox2.Add(self.addSet3, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 35)
        self.vbox2.Add(self.addSet4, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 35)
        self.vbox2.Add(self.addSet5, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 35)
        
        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.set1, 0, flag=wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.hbox1.Add(self.addSet1, 0, flag=wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.set2, 0, flag=wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.hbox2.Add(self.addSet2, 0, flag=wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3.Add(self.set3, 0, flag=wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.hbox3.Add(self.addSet3, 0, flag=wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox4.Add(self.set4, 0, flag=wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.hbox4.Add(self.addSet4, 0, flag=wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox5.Add(self.set5, 0, flag=wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.hbox5.Add(self.addSet5, 0, flag=wx.ALIGN_CENTER | wx.ALL, border = 5)
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.titlebox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.vbox.Add(self.hbox1, 0, flag = wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, border = 10)
        self.vbox.Add(self.hbox2, 0, flag = wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, border = 10)
        self.vbox.Add(self.hbox3, 0, flag = wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, border = 10)
        self.vbox.Add(self.hbox4, 0, flag = wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, border = 10)       
        self.vbox.Add(self.hbox5, 0, flag = wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, border = 10)
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.create_menu()
        self.CreateStatusBar()
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.Center()
        self.Show()
    
    def addSet(self, event, stringName):
        
        '''
        This is the method that adds a regions files and reference file set to the regions file
        box in the parent frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        
        stringName : string
            A string to differentiate the different sets which a user could be trying to add.
        
        Notes
        -----
        There is no return, but upon successful completion a set in the form (somefile.reg,referencefile.fits;)
        will be added to the regions file box in the parent frame.
        '''
        
        if stringName == "Add Set 1":
            useSet = self.set1
        elif stringName == "Add Set 2":
            useSet = self.set2
        elif stringName == "Add Set 3":
            useSet = self.set3
        elif stringName == "Add Set 4":
            useSet = self.set4
        elif stringName == "Add Set 5":
            useSet = self.set5
        regions = useSet.boxList[1].GetValue().strip()
        reference = useSet.boxList[2].GetValue().strip()
        if self.SetCheck(regions, reference) == True:
            
            useSet.boxList[1].SetValue(regions)
            useSet.boxList[2].SetValue(reference)
            setString = regions + "," + reference
            dataImages = self.parent.paths.boxList[3].GetValue().strip().split(",")
            regionsBox = self.parent.paths.boxList[4].GetValue()
            uniqueSet = True
            uniqueReg = True
            uniqueRef = True
    
            for eachSet in regionsBox.split(";"):
                if len(eachSet.split(",")) == 2:
                    tempReg = eachSet.split(",")[0].strip()
                    tempRef = eachSet.split(",")[1].strip()
                    if tempReg == regions and tempRef == reference:
                        uniqueSet = False
                        break
                    elif tempReg == regions:
                        uniqueReg = False
                        break
                    elif tempRef == reference:
                        uniqueRef = False
                        break

            if uniqueSet == False:
                self.IP = InvalidParameter("", self, -1, stringVal="setExists")
            elif uniqueReg == False:
                tempString = "\nRegions: " + regions + "\nReference: " + reference + "\nBecause ---" + "\nRegions: " + \
                             tempReg + "\nIs already associated with:\nReference: " + tempRef
                self.IP = InvalidParameter(tempString, self, -1, stringVal="regionsDup")
            elif uniqueRef == False:
                tempString = "\nRegions: " + regions + "\nReference: " + reference + "\nBecause ---" + "\nRegions: " + \
                             tempReg + "\nIs already associated with this reference file."
                self.IP = InvalidParameter(tempString, self, -1, stringVal="referenceImageDup")
            elif all(reference != temp for temp in dataImages):
                self.IP = InvalidParameter("\nRegions: "+ regions + "\nReference: " + reference, self, -1, stringVal="invalidRefExist")
            else:
                regionsBox += setString + ";"
                self.parent.paths.boxList[4].SetValue(regionsBox)
                self.IP = InvalidParameter("", self, -1, stringVal="regionsUpdate")
    
    def SetCheck(self, reg, ref):
        
        '''
        This method checks whether or not the regions file and reference file given are valid files
        for their respective roles.
        
        Parameters
        ----------
        reg : string
            A value from a regions file text box that needs to be checked.
        
        ref : string
            A value from a reference file text box that needs to be checked.
        
        Returns
        -------
        literal : bool
            True if both files are valid, false otherwise.
        '''
        
        if reg == "":
            self.IP = InvalidParameter(reg, self, -1, stringVal="regionsError1")
            return False
        elif ref == "":
            self.IP = InvalidParameter(ref, self, -1, stringVal="regionsError1")
            return False

        if len(glob(reg)) != 1:
            tempString = reg
            if len(reg.split(",")) > 1:
                tempString = ""
                for string in reg.split(","):
                    if string == "":
                        tempString += ","
                    else:
                        tempString += "\n" + string.strip()
            self.IP = InvalidParameter(tempString, self, -1, stringVal="regionsError2")
            return False
        elif len(glob(ref)) != 1:
            tempString = ref
            if len(ref.split(",")) > 1:
                tempString = ""
                for string in ref.split(","):
                    if string == "":
                        tempString += ","
                    else:
                        tempString += "\n" + string.strip()
            self.IP = InvalidParameter(tempString, self, -1, stringVal="regionsError2")
            return False
        elif reg.lower().endswith(".reg") == False:
            self.IP = InvalidParameter(reg, self, -1, stringVal="regionsError3")
            return False
        elif ref.lower().endswith(".fits") == False and ref.lower().endswith(".fit") == False:
            self.IP = InvalidParameter(ref, self, -1, stringVal="regionsError4")
            return False
        return True        

    def create_menu(self):
        
        '''
        This method creates the menu bars that are at the top of the extra regions frame.
        
        Notes
        -----
        This method has no input or return parameters. It will simply be used as self.create_menu()
        when in the initialization method for an instance of this frame.
        '''
        
        menubar = wx.MenuBar()
        menu_file = wx.Menu()
        m_quit = menu_file.Append(wx.ID_EXIT, "Quit\tCtrl+Q", "Quit this application.")
        self.Bind(wx.EVT_MENU, self.on_exit, m_quit)
    
        menubar.Append(menu_file, "File")
        self.SetMenuBar(menubar)
    
    def on_exit(self,event):
        
        '''
        This method defines the action quit from the menu. It closes the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()

    def onDestroy(self,event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.extraRegionsOpen = False

class MasterFlatFrame(wx.Frame):
    
    '''
    This frame allows the user to create a master flat using their own images.
    '''
    
    def __init__(self, parent, objectID):
        
        '''
        This method defines the initialization of this class.
        '''
        
        wx.Frame.__init__(self, parent, objectID, "Master Flat Maker")
        self.panel = wx.Panel(self)
        self.parent = parent
        self.overWrite = False
        self.messageFrame = False
        self.IP = wx.Frame
        
        self.titlebox = wx.StaticText(self.panel, -1, 'OSCAAR: Master Flat Maker')
        self.titleFont = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.titlebox.SetFont(self.titleFont)
        
        self.path1 = AddLCB(self.panel, -1, name="Path to Flat Images: ", multFiles=True, saveType=None)
        self.path2 = AddLCB(self.panel, -1, name="Path to Dark Flat Images: ", multFiles=True, saveType=None)
        self.path3 = AddLCB(self.panel, -1, name="Path to Save Master Flat: ", saveType=wx.FD_SAVE)
        
        tupleList = [('rbTrackPlot',"","On","Off")]
        self.plotBox = ParameterBox(self.panel,-1,tupleList, name = "Plots")
        tupleList = [('rbFlatType',"","Standard","Twilight")]
        self.flatBox = ParameterBox(self.panel,-1,tupleList, name = "Flat Type")
        self.runButton = wx.Button(self.panel, -1, label = "Run")
        self.Bind(wx.EVT_BUTTON, self.run, self.runButton)
        
        
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.plotBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        self.hbox.Add(self.flatBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        self.hbox.Add(self.runButton, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.titlebox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        self.vbox.Add(self.path1, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        self.vbox.Add(self.path2, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        self.vbox.Add(self.path3, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        self.vbox.Add(self.hbox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.create_menu()
        self.CreateStatusBar()
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.Center()
        self.Show()

    def run(self,event):
        
        '''
        This runs either the standardFlatMaker or twilightFLatMaker method from the systematics.py to create a master flat.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
            
        Notes
        -----
        There is no return, on successful completion a window will open up with what the master flat looks like.
        '''
        
        path = self.path3.boxList[1].GetValue().strip()
        self.flatImages = self.checkFileInputs(self.path1.boxList[1].GetValue(), self.path1.boxList[1])
        self.darkFlatImages = self.checkFileInputs(self.path2.boxList[1].GetValue(), self.path2.boxList[1])
        if self.flatImages != "":
            self.IP = InvalidParameter(self.flatImages, self, -1, stringVal="flat1")
        elif self.darkFlatImages != "":
            self.IP = InvalidParameter(self.darkFlatImages, self, -1, stringVal="flat2")
        elif not path:
            self.IP = InvalidParameter(str(path), self, -1, stringVal="flat3")
        elif not os.path.isdir(path[path.rfind(os.sep)]) or \
             not len(path) > (len(path[:path.rfind(os.sep)]) + 1):
            self.IP = InvalidParameter(path, self, -1, stringVal="flat3")
        else:
            self.flatImages = []
            self.darkFlatImages = []
            for pathname in self.path1.boxList[1].GetValue().split(','):
                self.flatImages += glob(pathname)
            for pathname in self.path2.boxList[1].GetValue().split(','):
                self.darkFlatImages += glob(pathname)
            if not path.lower().endswith('.fits') and not path.lower().endswith('.fit'):
                path += '.fits'
            pathCorrected = path.replace('/', os.sep)
            outfolder = pathCorrected[:pathCorrected.rfind(os.sep)] + os.sep + '*'
            self.plotCheck = self.plotBox.userParams['rbTrackPlot'].GetValue()
            if pathCorrected in glob(outfolder):
                if self.overWrite == False:
                    OverWrite(self, -1, "Overwrite Master Flat", pathCorrected, "MasterFlat")
                    self.overWrite = True
            else:
                if self.flatBox.userParams['rbFlatType'].GetValue() == True:
                    systematics.standardFlatMaker(self.flatImages, self.darkFlatImages, self.path3.boxList[1].GetValue(),
                                              self.plotCheck)
                else:
                    systematics.twilightFlatMaker(self.flatImages, self.darkFlatImages, self.path3.boxList[1].GetValue(),
                                              self.plotCheck)

    def checkFileInputs(self,array,box):
        
        '''
        This method checks to make sure that the files entered in a text box in the master flat frame are valid.
        
        Parameters
        ----------
        array : string
            A list of all of the files that need to be checked.
        
        box : wx.TextCtrl
            The box that gets refreshed with a string of the valid files.
            
        Returns
        -------
        errorString : string
            A list of all the files that were invalid.
            
        Notes
        -----
        If `errorString` returns '' (empty), that means that all the files were valid.
        '''
        
        errorString = ""
        setValueString = ""
        array2 = []
        smallArray = ""
        for element in array.split(","):
            element = element.strip()
            if element.lower().endswith(os.sep):
                tempElement = element + "*.fit"
                element += "*.fits"
                smallArray = "-1"
            if smallArray == "":
                if len(glob(element)) < 1:
                    errorString += element
                elif len(glob(element)) > 1:
                    for element2 in glob(element):
                        if element2.lower().endswith(".fit") or element2.lower().endswith(".fits"):
                            array2.append(element2)
                        else:
                            errorString += "\n" + element2
                elif not element.lower().endswith(".fit") and not element.lower().endswith(".fits"):
                    errorString += "\n" + element
                else:
                    array2.append(glob(element)[0])
            else:
                if len(glob(tempElement)) < 1 and len(glob(element)) < 1:
                    errorString += "\n" + tempElement + ",\n" + element
                else:
                    if len(glob(tempElement)) >= 1:
                        for element2 in glob(tempElement):
                            array2.append(element2)
                    if len(glob(element)) >= 1:
                        for element2 in glob(element):
                            array2.append(element2)
        if not array:
            return "No Values Entered"
        else:
            if errorString == "":
                setValueString = ""
                uniqueArray = np.unique(array2).tolist()
                for eachString in uniqueArray:
                    setValueString += eachString + ","
                box.SetValue(setValueString.rpartition(",")[0])
            return errorString

    def create_menu(self):
        
        '''
        This method creates the menu bars that are at the top of the master flat frame.
        
        Notes
        -----
        This method has no input or return parameters. It will simply be used as self.create_menu()
        when in the initialization method for an instance of this frame.
        '''
        
        menubar = wx.MenuBar()
        menu_file = wx.Menu()
        m_quit = menu_file.Append(wx.ID_EXIT, "Quit\tCtrl+Q", "Quit this application.")
        self.Bind(wx.EVT_MENU, self.on_exit, m_quit)
    
        menubar.Append(menu_file, "File")
        self.SetMenuBar(menubar)
    
    def on_exit(self,event):
        
        '''
        This method defines the action quit from the menu. It closes the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''

        self.Destroy()

    def onDestroy(self,event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.loadMasterFlat = False

class AboutFrame(wx.Frame):
    
    '''
    This is a frame about OSCAAR and its contributors.
    '''

    def __init__(self, parent, objectID):
        
        '''
        This method defines the initialization of this class.
        '''
        
        wx.Frame.__init__(self, parent, objectID, "About OSCAAR")
        self.panel = wx.Panel(self)
        self.parent = parent
        
        self.static_bitmap = wx.StaticBitmap(self.panel, style=wx.ALIGN_CENTER)
        self.logo = wx.Image(os.path.join(os.path.dirname(os.path.abspath(__file__)),'images/logo4noText.png'),
                             wx.BITMAP_TYPE_ANY)
        self.bitmap = wx.BitmapFromImage(self.logo)
        self.static_bitmap.SetBitmap(self.bitmap)
        
        titleText = '\n'.join(['OSCAAR 2.0 beta',\
                     'Open Source differential photometry Code for Amateur Astronomical Research',\
                     'Created by Brett M. Morris (NASA GSFC/UMD)\n'])

        contribText = '\n'.join(['Other Contributors:',\
                     'Daniel Galdi (UMD)',\
                     'Luuk Visser (LU/TUD)',\
                     'Nolan Matthews (UMD)',\
                     'Dharmatej Mikkilineni (UMD)',\
                     'Harley Katz (UMD)',\
                     'Sam Gross (UMD)',\
                     'Naveed Chowdhury (UMD)',\
                     'Jared King (UMD)',\
                     'Steven Knoll (UMD)'])
        
        self.titleText = wx.StaticText(self.panel, -1, label = titleText, style = wx.ALIGN_CENTER)
        self.contribText = wx.StaticText(self.panel, -1, label = contribText, style = wx.ALIGN_CENTER)
        
        self.viewRepoButton = wx.Button(self.panel, -1, label = "Open Code Repository (GitHub)")
        self.exitButton = wx.Button(self.panel, -1, label = "Close")
        self.Bind(wx.EVT_BUTTON, lambda evt: self.parent.openLink(evt, "https://github.com/OSCAAR/OSCAAR"),
                  self.viewRepoButton)
        self.exitButton.Bind(wx.EVT_BUTTON, self.exit)
        
        self.buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        self.buttonBox.Add(self.viewRepoButton, 0, flag = wx.ALIGN_CENTER | wx.RIGHT, border = 20)
        self.buttonBox.Add(self.exitButton, 0, flag = wx.ALIGN_CENTER)
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.static_bitmap, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        self.vbox.Add(self.titleText, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        self.vbox.Add(self.contribText, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        self.vbox.Add(self.buttonBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.vbox.AddSpacer(10)
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.Center()
        self.Show()

    def exit(self, event):
        
        '''
        This method defines the action quit for the button `close`. It closes the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()

    def onDestroy(self, event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.aboutOpen = False


class OverWrite(wx.Frame): 
    
    '''
    This class creates a frame that prompts a user action for whether or not a file can be overwritten. Based
    on the user's response, different methods are activated.
    '''
     
    def __init__(self, parent, objectID, title, path, check):

        '''
        This method defines the initialization of this class.
        '''
        
        wx.Frame.__init__(self, parent, objectID, title)
        self.panel = wx.Panel(self)
        self.parent = parent     
        self.path = path
        self.text = wx.StaticText(self.panel, -1, "Are you sure you want to overwrite\n" + self.path + "?")
        self.yesButton = wx.Button(self.panel, label = "Yes")
        self.noButton = wx.Button(self.panel,label = "No")
        self.SetFocus()
        if check == "MasterFlat":
            self.Bind(wx.EVT_BUTTON, self.onMasterFlat, self.yesButton)
        elif check == "Output File":
            self.Bind(wx.EVT_BUTTON, self.onOutputFile, self.yesButton)
        self.Bind(wx.EVT_BUTTON, self.onNO, self.noButton)
        
        self.sizer0 = wx.FlexGridSizer(rows=2, cols=1) 
        self.buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        self.buttonBox.Add(self.yesButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.buttonBox.Add(self.noButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.text,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.buttonBox, 0,wx.ALIGN_CENTER|wx.ALL,5)
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.doNothing)
        self.panel.SetSizer(self.hbox)
        self.hbox.Fit(self)
        self.Center()
        self.Show()
        
    def onMasterFlat(self,event):
        
        '''
        When the user selects `yes` in this frame with the parent frame being the master flat frame, then
        a new master flat will be created, overwriting the currently selected one.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()
        self.parent.overWrite = False  
        os.remove(self.path)
        if self.parent.flatBox.userParams['rbFlatType'].GetValue() == True:
            systematics.standardFlatMaker(self.parent.flatImages, self.parent.darkFlatImages, 
                                     self.parent.path3.boxList[1].GetValue(), self.parent.plotCheck)
        else:
            systematics.twilightFlatMaker(self.parent.flatImages, self.parent.darkFlatImages, 
                                     self.parent.path3.boxList[1].GetValue(), self.parent.plotCheck)

    def onOutputFile(self,event):
        
        '''
        This method is for whether or not to override the existing .pkl file that was specified in the output path
        text box in the parent OSCAAR frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()
        self.parent.overWrite = False
        diffPhotCall = "from oscaar import differentialPhotometry"
        subprocess.check_call(['python','-c',diffPhotCall])
        if self.parent.radioBox.userParams["rbFitAfterPhot"].GetValue() == True:
            wx.CallAfter(self.parent.createFrame)

    def onNO(self, event):
        
        '''
        When a user presses the `no` button, this method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame. It then
        will close the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.overWrite = False    
        self.Destroy()
        
    def doNothing(self,event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.overWrite = False
        pass


class EphemerisFrame(wx.Frame):
    
    '''
    This frame will allow users to calculate the positions of different planets in the sky
    for a given time frame at a specified observatory.
    '''

    def __init__(self, parent, objectID):

        '''
        This method defines the initialization of this class.
        '''
        
        wx.Frame.__init__(self, parent, objectID, "Ephemerides")
        
        self.panel = wx.Panel(self)
        self.parent = parent
        self.messageFrame = False
        self.IP = wx.Frame
        
        self.titlebox = wx.StaticText(self.panel, -1, 'Ephemeris Calculator')
        self.titleFont = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.titlebox.SetFont(self.titleFont)
        
        self.titlebox2 = wx.StaticText(self.panel, -1, 'Advanced Options')
        self.titlebox2.SetFont(self.titleFont)
        
        if sys.platform == "win32":
            self.fontType = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        else: 
            self.fontType = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
            
        self.calculateButton = wx.Button(self.panel, -1, label = "Calculate")
        self.Bind(wx.EVT_BUTTON, self.calculate, self.calculateButton)
        
        obsList = glob(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'extras','eph','observatories','*.par'))
        self.nameList = {}
        for currentFile in obsList:
            for line in open(currentFile,'r').read().splitlines():
                if line.split(":")[0] == "name":
                    self.nameList[line.split(":")[1].strip()] = currentFile
        
        self.obsLabel = wx.StaticText(self.panel, -1, 'Select Observatory: ')
        self.obsLabel.SetFont(self.fontType)
        self.obsList = wx.ComboBox(self.panel, value = 'Observatories',
                                   choices = sorted(self.nameList.keys()) + ["Enter New Observatory"])
        self.obsList.Bind(wx.EVT_COMBOBOX, self.update)

        self.dropBox = wx.BoxSizer(wx.HORIZONTAL)
        self.dropBox.Add(self.obsLabel, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 10)
        self.dropBox.Add(self.obsList, 0, flag = wx.ALIGN_CENTER)
        
        tupleList = [('observatoryName',"Name of Observatory: ","",""),
                     ('fileName',"Enter File Name: ","",""),
                     ('obsStart',"Start of Observation, UT (YYYY/MM/DD): ",
                      "Enter a date in the correct format here.",datetime.date.today().strftime("%Y/%m/%d")),
                     ('obsEnd',"End of Observation, UT (YYYY/MM/DD): ",
                      "Enter a date in the correct format here.",(datetime.datetime.now()+datetime.timedelta(days=7)
                                                                  ).strftime("%Y/%m/%d")),
                     ('upperLimit',"Apparent Mag. Upper Limit: ","","0.0"),
                     ('lowerLimit',"Depth Lower Limit: ","","0.0")]
        self.leftBox = ParameterBox(self.panel,-1,tupleList, rows=6, cols=2, vNum = 5, hNum = 15, font = self.fontType)
        
        tupleList = [("latitude","Latitude (deg:min:sec): ","","00:00:00"),
                     ("longitude","Longitude (deg:min:sec): ","","00:00:00"),
                     ("elevation","Observatory Elevation (m): ","","0.0"),
                     ("temperature","Temperature (degrees C): ","","0.0"),
                     ("lowerElevation","Lower Elevation Limit (deg:min:sec): ","","00:00:00")]
        self.leftBox2 = ParameterBox(self.panel, -1, tupleList, rows=5, cols=2, vNum = 5, hNum = 15, font =self.fontType)
        
        self.twilightChoices = {}
        self.twilightChoices["Civil Twilight (-6 degrees)"] = "-6"
        self.twilightChoices["Nautical Twilight (-12 degrees)"] = "-12"
        self.twilightChoices["Astronomical Twilight (-18 degrees)"] = "-18"
        
        self.twilightLabel = wx.StaticText(self.panel, -1, "Select Twilight Type: ")
        self.twilightLabel.SetFont(self.fontType)
        self.twilightList = wx.ComboBox(self.panel, value = "Civil Twilight (-6 degrees)", 
                                        choices = sorted(self.twilightChoices.keys()))
        
        self.dropBox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.dropBox2.Add(self.twilightLabel, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 10)
        self.dropBox2.Add(self.twilightList, 0, flag = wx.ALIGN_CENTER)       
        
        tupleList = [('rbBand',"","V","K")]
        self.band = ParameterBox(self.panel,-1,tupleList, name = "Band Type")
        tupleList = [('rbShowLT',"","On","Off")]
        self.showLT = ParameterBox(self.panel,-1,tupleList, name = "Show Local Times", secondButton = True)
        
        self.botRadioBox = wx.BoxSizer(wx.HORIZONTAL)
        self.botRadioBox.Add(self.showLT, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 10)
        self.botRadioBox.Add(self.band, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 15)
       
        tupleList = [('rbCalcEclipse',"","True","False")]
        self.calcEclipseBox = ParameterBox(self.panel,-1,tupleList, name = "Calculate Eclipses", secondButton = True)
        tupleList = [('rbHtmlOut',"","True", "False")]
        self.htmlBox = ParameterBox(self.panel,-1,tupleList, name = "HTML Out")
        tupleList = [('rbTextOut',"","True","False")]
        self.textBox = ParameterBox(self.panel,-1,tupleList, name = "Text Out")
        tupleList = [('rbCalcTransits',"","True","False")]
        self.calcTransitsBox = ParameterBox(self.panel,-1,tupleList, name = "Calculate Transits")
        

        self.radioBox = wx.BoxSizer(wx.VERTICAL)
        self.radioBox.Add(self.calcTransitsBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.radioBox.Add(self.calcEclipseBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.radioBox.Add(self.htmlBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.radioBox.Add(self.textBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        
        self.topBox = wx.BoxSizer(wx.HORIZONTAL)
        self.topBox.Add(self.leftBox, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 5)
        self.topBox.Add(self.calculateButton, 0, flag = wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT, border = 5)
        
        self.leftVertBox = wx.BoxSizer(wx.VERTICAL)
        self.leftVertBox.Add(self.leftBox2, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.leftVertBox.Add(self.dropBox2, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.leftVertBox.Add(self.botRadioBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
         
        self.botBox = wx.BoxSizer(wx.HORIZONTAL)
        self.botBox.Add(self.leftVertBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.botBox.Add(self.radioBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.titlebox, 0, flag = wx.ALIGN_CENTER | wx.TOP, border = 5)
        self.vbox.Add(self.dropBox, 0, flag = wx.ALIGN_LEFT | wx.TOP, border = 10)
        self.vbox.Add(self.topBox, 0, flag = wx.ALIGN_CENTER)
        self.vbox.Add(self.titlebox2, 0, flag = wx.ALIGN_CENTER)
        self.vbox.Add(self.botBox, 0, flag = wx.ALIGN_CENTER)
        
        self.create_menu()
        self.CreateStatusBar()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.Center()
        self.Show()
    
    def calculate(self, event):
        
        '''
        After checking to see if all of the parameters entered are valid, this method actually runs
        the calculateEphemerides method from the eph.py file to get the transit times and such for
        different planets.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        
        Notes
        -----
        On successful completion a new window will open in the default browser for your machine with the
        ephemeris chart open.
        '''
        
        try:
            import oscaar.extras.eph.calculateEphemerides as eph
            import ephem
            ephem.sun_radius
            if self.parameterCheck() == True:
                
                if self.parent.singularOccurance == 0 and self.showLT.userParams["rbShowLT"].GetValue():
                    self.parent.singularOccurance = 1
                    self.IP = InvalidParameter("", self, -1, stringVal="warnError")
                else:
                    outputPath = str(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),
                                                  'extras','eph','ephOutputs','eventReport.html'))
                    path = os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),
                                        'extras','eph','observatories', self.leftBox.userParams["fileName"].GetValue() + '.par')
                    
                    if not self.nameList.has_key(self.name):
                        self.nameList[self.name] = path
                        self.obsList.Append(self.name)
                    
                    self.saveFile(path)
                    eph.calculateEphemerides(path)
            
                    if self.htmlBox.userParams["rbHtmlOut"].GetValue() == True:
                        webbrowser.open_new_tab("file:"+2*os.sep+outputPath)
        except ImportError:
            self.IP = InvalidParameter("", self, -1, stringVal="importError")

    def parameterCheck(self):
        
        '''
        This is a local method for this class that checks to make sure all of the 
        parameters that can be manipulated by the user are valid.
        
        Returns
        -------
        literal : bool
            False if any of the parameters are invalid, true otherwise.
        '''

        self.name = self.leftBox.userParams["observatoryName"].GetValue().strip()
        self.fileName = self.leftBox.userParams["fileName"].GetValue().strip()
        self.latitude = self.leftBox2.userParams["latitude"].GetValue().strip()
        self.longitude = self.leftBox2.userParams["longitude"].GetValue().strip()
        self.elevation = self.leftBox2.userParams["elevation"].GetValue().strip()
        self.temperature = self.leftBox2.userParams["temperature"].GetValue().strip()
        self.lowerElevation = self.leftBox2.userParams["lowerElevation"].GetValue().strip()
        self.startingDate = self.leftBox.userParams["obsStart"].GetValue().strip()
        self.endingDate = self.leftBox.userParams["obsEnd"].GetValue().strip()
        self.upperLimit = self.leftBox.userParams["upperLimit"].GetValue().strip()
        self.lowerLimit = self.leftBox.userParams["lowerLimit"].GetValue().strip()
        self.twilight = self.twilightList.GetValue().strip()

        if self.name == "" or self.name == "Enter the name of the Observatory":
            self.IP = InvalidParameter(self.name, self, -1, stringVal="obsName")
            return False
        elif self.fileName == "" or self.fileName == "Enter the name of the file":
            self.IP = InvalidParameter(self.fileName, self, -1, stringVal="obsFile")
            return False
        years = []
        months = []
        days = []
        for dateArray,value in [(self.startingDate.split("/"),self.startingDate),
                                (self.endingDate.split("/"),self.endingDate)]:
            if len(dateArray) != 3:
                self.IP = InvalidParameter(value, self, -1, stringVal="obsDate")
                return False
            else:
                try:
                    year = int(dateArray[0].strip())
                    years.append(year)
                    month = int(dateArray[1].strip())
                    months.append(month)
                    day = int(dateArray[2].strip())
                    days.append(day)
                    
                    if len(dateArray[0].strip()) != 4 or len(dateArray[1].strip()) > 2 or len(dateArray[2].strip()) > 2:
                        self.IP = InvalidParameter(value, self, -1, stringVal="obsDate")
                        return False
                    minYear = datetime.date.today().year - 100
                    maxYear = datetime.date.today().year + 100
                    if year < minYear or year > maxYear or month > 12 or month < 0 or day > 31 or day < 0 or \
                       month == 0 or year == 0 or day == 0:
                        self.IP = InvalidParameter(value, self, -1, stringVal="dateRange")
                        return False
                except ValueError:
                    self.IP = InvalidParameter(value, self, -1, stringVal="obsDate")
                    return False

        if years[0] > years[1]:
            self.IP = InvalidParameter(self.startingDate, self, -1, stringVal="logicalDate")
            return False
        elif years[0] == years[1]:
            if months[0] > months[1]:
                self.IP = InvalidParameter(self.startingDate, self, -1, stringVal="logicalDate")
                return False
            elif months[0] == months[1]:
                if days[0] >= days[1]:
                    self.IP = InvalidParameter(self.startingDate, self, -1, stringVal="logicalDate")
                    return False
        
        for coordArray, value, coordType in [(self.latitude.split(":"),self.latitude, "lat"), 
                                  (self.longitude.split(":"),self.longitude, "long")]:
            if(len(coordArray) != 3):
                self.IP = InvalidParameter(value, self, -1, stringVal="coordTime")
                return False
            else:
                try:
                    deg = float(coordArray[0].strip())
                    minutes = float(coordArray[1].strip())
                    sec = float(coordArray[2].strip())
                    if coordType == "lat":
                        self.latitude = str(deg) + ":" + str(minutes) + ":" + str(sec)
                        if abs(deg) > 90.0 or minutes >= 60 or minutes < 0.0 or sec >= 60 or sec < 0.0:
                            self.IP = InvalidParameter(value, self, -1, stringVal="coordRange")
                            return False
                    elif coordType == "long":
                        self.longitude = str(deg) + ":" + str(minutes) + ":" + str(sec)
                        if abs(deg) > 180.0 or minutes >= 60 or minutes < 0.0 or sec >= 60 or sec < 0.0:
                            self.IP = InvalidParameter(value, self, -1, stringVal="coordRange")
                            return False
                    if abs(deg) == 90 and coordType == "lat":
                        if minutes != 0 or sec != 0:
                            self.IP = InvalidParameter(value, self, -1, stringVal="coordRange")
                            return False
                    elif abs(deg) == 180 and coordType == "long":
                        if minutes != 0 or sec != 0:
                            self.IP = InvalidParameter(value, self, -1, stringVal="coordRange")
                            return False
                except ValueError:
                    self.IP = InvalidParameter(value, self, -1, stringVal="coordTime")
                    return False
        try:
            tempString = "elevation"
            temp1 = float(self.elevation)
            tempString = "temperature"
            temp2 = float(self.temperature)
            tempString = "apparent magnitude upper limit"
            temp3 = float(self.upperLimit)
            tempString = "depth lower limit"
            temp4 = float(self.lowerLimit)
            tempString = "lower elevation limit"
            
            if temp3: pass
            
            stripElevation = self.lowerElevation.split(":")

            if len(stripElevation) != 3:
                self.IP = InvalidParameter(self.lowerElevation, self, -1, stringVal="lowerElevation")
                return False

            temp6 = int(stripElevation[0])
            temp7 = int(stripElevation[1])
            temp8 = int(stripElevation[2])
            
            if temp6 < 0.0 or temp6 > 90 or temp7 >= 60 or temp7 < 0.0 or temp8 >= 60 or temp8 < 0.0:
                self.IP = InvalidParameter(self.lowerElevation, self, -1, stringVal="lowerElevation")
                return False
            elif temp6 == 90:
                if temp7 != 0 or temp8 != 0:
                    self.IP = InvalidParameter(self.lowerElevation, self, -1, stringVal="lowerElevation")
                    return False
              
            self.lowerElevation = stripElevation[0].strip() + ":" + stripElevation[1].strip() + ":" +\
                                  stripElevation[2].strip()
            
            if temp1 < 0:
                self.IP = InvalidParameter(self.elevation, self, -1, stringVal="tempElevNum", secondValue="elevation")
                return False
            
            elif temp2 < 0:
                self.IP = InvalidParameter(self.temperature, self, -1, stringVal="tempElevNum", secondValue="temperature")
                return False
            
            elif temp4 < 0:
                self.IP = InvalidParameter(self.lowerLimit, self, -1, stringVal="tempElevNum", secondValue="depth lower limit")
                return False

        except ValueError:
            if tempString == "temperature":
                self.IP = InvalidParameter(self.temperature, self, -1, stringVal="tempElevNum", secondValue=tempString)
            elif tempString == "apparent magnitude upper limit":
                self.IP = InvalidParameter(self.upperLimit, self, -1, stringVal="tempElevNum", secondValue=tempString)
            elif tempString == "depth lower limit":
                self.IP = InvalidParameter(self.lowerLimit, self, -1, stringVal="tempElevNum", secondValue=tempString)
            elif tempString == "lower elevation limit":
                self.IP = InvalidParameter(self.lowerElevation, self, -1, stringVal="lowerElevation")
            else:
                self.IP = InvalidParameter(self.elevation, self, -1, stringVal="tempElevNum", secondValue=tempString)
            return False
        
        if all(self.twilight != temp for temp in ["Civil Twilight (-6 degrees)",
                                         "Nautical Twilight (-12 degrees)",
                                         "Astronomical Twilight (-18 degrees)"]):
            self.IP = InvalidParameter(self.twilight, self, -1, stringVal="twilight")
            return False
                
        return True
    
    def update(self, event):

        '''
        This method is bound to the drop down list of observatories that can be selected in the 
        frame. Once an observatory is chosen, this method updates all relevant text fields with the
        appropriate parameters.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        if self.obsList.GetValue() == "Enter New Observatory":
            self.leftBox.userParams["observatoryName"].SetValue("Enter the name of the Observatory")
            self.leftBox.userParams["fileName"].SetValue("Enter the name of the file")
        else:
            radioBoxes = self.radioBox.GetChildren()
            radioList = []
            for eachBox in radioBoxes:
                window = eachBox.GetWindow()
                children = window.GetChildren()
                for child in children:
                    if isinstance(child, wx.RadioButton):
                        radioList.append(child)
                        
            lines = open(self.nameList[self.obsList.GetValue()],"r").read().splitlines()
            self.leftBox.userParams["fileName"].SetValue(os.path.split(self.nameList[self.obsList.GetValue()
                                                                                     ])[1].split(".")[0])
            for eachLine in lines:
                if len(eachLine.split()) > 1:
                    inline = eachLine.split(':', 1)
                    name = inline[0].strip()
                    value = str(inline[1].strip())
                    tempList = [("name","observatoryName"),("min_horizon","lowerElevation"),("mag_limit","upperLimit"),
                                ("depth_limit","lowerLimit"),("latitude",""),("longitude",""),("elevation",""),
                                ("temperature",""),("twilight",""),("calc_transits",0),("calc_eclipses",2),
                                ("html_out",4),("text_out",6), ("show_lt","rbShowLT"), ("band","rbBand")]
                
                    for string,saveName in tempList:
                        if string == name:
                            if any(temp == name for temp in ["name","mag_limit","depth_limit"]):
                                self.leftBox.userParams[saveName].SetValue(str(value))
                            elif any(temp == name for temp in ["latitude","longitude","elevation","temperature",
                                                               "twilight","min_horizon","time_zone", "band"]):
                                if saveName == "":
                                    saveName = name
                                if name == "twilight":
                                    tempStr = [temp for temp in self.twilightChoices.keys() \
                                               if self.twilightChoices[temp] == value]
                                    if len(tempStr) != 0:
                                        self.twilightList.SetValue(tempStr[0])
                                elif name == "show_lt":
                                    if value == "0":
                                        saveName = saveName + "1"
                                    self.showLT.userParams[saveName].SetValue(True)
                                elif name == "band":
                                    if value == "K":
                                        saveName = saveName + "1"
                                    self.band.userParams[saveName].SetValue(True)
                                else:
                                    self.leftBox2.userParams[saveName].SetValue(str(value))
                            elif any(temp == name for temp in ["calc_transits","calc_eclipses","html_out","text_out"]):
                                if(value == "False"):
                                    saveName = saveName + 1
                                radioList[saveName].SetValue(True)

    def saveFile(self, fileName):
        
        '''
        This method saves all the current parameters in the window for a selected
        observatory to a text file. This allows the user to quickly select the observatory
        with pre-loaded parameters after an initial setup.
        
        Parameters
        ----------
        fileName : string
            The name of the file that will be saved with all of the user inputs.
        '''
        
        startDate = [x.strip() for x in self.leftBox.userParams["obsStart"].GetValue().split("/")]
        endDate = [x.strip() for x in self.leftBox.userParams["obsEnd"].GetValue().split("/")]
        dates = {}
        for date, stringDate in [(startDate,"date1"), (endDate,"date2")]:
            for stringNum in date:
                if stringNum == "08":
                    date[date.index(stringNum)] = "8"
                elif stringNum == "09":
                    date[date.index(stringNum)] = "9"

            date += ["0","0","0"]
            tempString = "("
            for num in range(0,len(date)):
                if num != len(date)-1:
                    tempString += date[num] + ","
                else:
                    tempString += date[num]
            tempString += ")"
            dates[stringDate] = tempString
        
        newObs = open(fileName, "w")
        newObs.write("name: " + self.name + "\n")
        newObs.write("latitude: " + self.latitude + "\n")
        newObs.write("longitude: " + self.longitude + "\n")
        newObs.write("elevation: " + self.elevation + "\n")
        newObs.write("temperature: " + self.temperature + "\n")
        newObs.write("min_horizon: " + self.lowerElevation + "\n")
        newObs.write("start_date: " + dates["date1"] + "\n")
        newObs.write("end_date: " + dates["date2"] + "\n")
        newObs.write("mag_limit: " + self.upperLimit + "\n")
        newObs.write("depth_limit: " + self.lowerLimit + "\n")
        newObs.write("calc_transits: " + str(self.calcTransitsBox.userParams["rbCalcTransits"].GetValue()) + "\n")
        newObs.write("calc_eclipses: " + str(self.calcEclipseBox.userParams["rbCalcEclipse"].GetValue()) + "\n")
        newObs.write("html_out: " + str(self.htmlBox.userParams["rbHtmlOut"].GetValue()) + "\n")
        newObs.write("text_out: " + str(self.textBox.userParams["rbTextOut"].GetValue()) + "\n")
        newObs.write("twilight: " + self.twilightChoices[self.twilight] + "\n")
        tempLT = str(self.showLT.userParams["rbShowLT"].GetValue())
        if tempLT == "True":
            tempLT = "1"
        else:
            tempLT = "0"
        newObs.write("show_lt: " + tempLT + "\n")
        tempString = str(self.band.userParams["rbBand"].GetValue())
        if tempString == "True":
            bandString = "V"
        else:
            bandString = "K"
        newObs.write("band: "+ bandString)
        newObs.close()

    def create_menu(self):
        
        '''
        This method creates the menu bars that are at the top of the ephemeris frame.
        
        Notes
        -----
        This method has no input or return parameters. It will simply be used as self.create_menu()
        when in the initialization method for an instance of this frame.
        '''
        
        menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_save = menu_file.Append(wx.ID_SAVE, "Save\tCtrl+S", "Save data to a zip folder.")
        m_quit = menu_file.Append(wx.ID_EXIT, "Quit\tCtrl+Q", "Quit this application.")
        self.Bind(wx.EVT_MENU, self.on_exit, m_quit)
        self.Bind(wx.EVT_MENU, self.saveOutput, m_save)
        
        menubar.Append(menu_file, "File")
        self.SetMenuBar(menubar)

    def saveOutput(self, event):
        
        '''
        This method will save the output of the ephemeris calculations as a zip file.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        dlg = wx.FileDialog(self, message = "Save your output...", style = wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            outputPath = dlg.GetPath()
            if self.parameterCheck():
                self.calculate(None)
                shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'extras','eph','ephOutputs'),
                                outputPath)
                outputArchive = zipfile.ZipFile(outputPath+'.zip', 'w')
                for name in glob(outputPath+os.sep+'*'):
                    outputArchive.write(name, os.path.basename(name), zipfile.ZIP_DEFLATED)
                shutil.rmtree(outputPath)
                outputArchive.close()
        dlg.Destroy()
    
    def on_exit(self,event):
        
        '''
        This method defines the action quit from the menu. It closes the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()
        
    def onDestroy(self, event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.loadEphFrame = False

class FittingFrame(wx.Frame):
    
    '''
    After you have created your own light curve, there are different fitting methods that 
    you can do. Currently the only fitting method in place is MCMC.
    '''

    def __init__(self, parent, objectID, path = ''):
        
        '''
        This method defines the initialization of this class.
        '''
        
        self.path = path
        self.title = "Fitting Methods"
        self.loadMCMC = False
        wx.Frame.__init__(self, parent, objectID, self.title)
        
        self.panel = wx.Panel(self)
        self.parent = parent
        self.messageFrame = False
        self.IP = wx.Frame
        
        self.box = AddLCB(self.panel,-1,name="Path to Output File: ")
        self.box2 = AddLCB(self.panel, -1, name="Results Output Path (.txt): ", saveType=wx.FD_SAVE)
        self.vbox2= wx.BoxSizer(wx.VERTICAL)
        self.vbox2.Add(self.box, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox2.Add(self.box2, border=5, flag=wx.ALL)
        self.box.boxList[1].SetValue(self.path)
        
        self.plotMCMCButton = wx.Button(self.panel,label="MCMC Fit", size = (130,25))
        self.Bind(wx.EVT_BUTTON, self.plotMCMC, self.plotMCMCButton)
        self.sizer0 = wx.FlexGridSizer(rows=2, cols=4)
        self.sizer0.Add(self.plotMCMCButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        
        self.pklPathTxt = self.box.boxList[1]
        self.saveLocation = self.box2.boxList[1]
        self.create_menu()

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.vbox2, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.sizer0, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.vbox.AddSpacer(10)
        self.panel.SetSizer(self.vbox)
        self.CreateStatusBar()
        self.vbox.Fit(self)
        self.Center()
        self.Show()

    def create_menu(self):
        
        '''
        This method creates the menu bars that are at the top of the ephemeris frame.
        
        Notes
        -----
        This method has no input or return parameters. It will simply be used as self.create_menu()
        when in the initialization method for an instance of this frame.
        '''
        
        self.menubar = wx.MenuBar()
    
        menu_file = wx.Menu()
        m_browse = menu_file.Append(-1,"Browse","Browse for a .pkl file to use.")
        self.Bind(wx.EVT_MENU, lambda event: self.browseButtonEvent(event,'Choose Path to Output File',self.pklPathTxt,
                                                                   False,wx.FD_OPEN),m_browse)
        m_browse2 = menu_file.Append(-1, "Browse2", "Browse a save location for the results.")
        self.Bind(wx.EVT_MENU, lambda event: self.browseButtonEvent(event,'Choose Path to Output File',self.saveLocation,
                                                                   False,wx.FD_SAVE),m_browse2)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "Exit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
    
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def browseButtonEvent(self, event, message, textControl, fileDialog, saveDialog):
        
        '''
        This method defines the `browse` function for selecting a file on any OS.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        
        message : string
            The message that tells the user what to choose.
            
        textControl : wx.TextCtrl
            The box in the frame that will be refreshed with the files that are chosen by the user.
            
        fileDialog : bool
            If true, the style is wx.FD_MULTIPLE, otherwise it is the same as the `saveDialog`.
            
        saveDialog : wx.FD_*
            The style of the box that will appear. The * represents a wild card value for different types.
        '''
                           
        if not fileDialog:
            dlg = wx.FileDialog(self, message = message, style = saveDialog)
        else: 
            dlg = wx.FileDialog(self, message = message,  style = wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            if saveDialog == wx.SAVE:
                filenames = [dlg.GetPath()]
            else:
                filenames = dlg.GetPaths()
            textControl.Clear()
            for i in range(0,len(filenames)):
                if i != len(filenames)-1:
                    textControl.WriteText(filenames[i] + ',')
                else:
                    textControl.WriteText(filenames[i])
        dlg.Destroy()

    def plotLSFit(self,event):
        
        '''
        This method is for a least squares fitting method that is not in use right now.
        '''
        
        if self.validityCheck():
            global pathText
            global loadLSFit
            pathText = self.pklPathTxt.GetValue()
            if loadLSFit == False:
                LeastSquaresFitFrame()
                loadLSFit = True
    
    def plotMCMC(self,event):
        
        '''
        This method checks that the file chosen to be loaded is valid, and that there is a valid save
        file selected for the output of the MCMC calculations.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        if self.validityCheck():
            tempSaveLoc = self.saveLocation.GetValue()
            if not os.path.isdir(tempSaveLoc.rpartition(str(os.sep))[0]) or \
            not len(tempSaveLoc) > (len(tempSaveLoc[:tempSaveLoc.rfind(os.sep)]) + 1):
                self.IP = InvalidParameter(tempSaveLoc, self, -1, stringVal="output", secondValue="results output file")
            else:
                try:
                    self.pathText = self.pklPathTxt.GetValue()
                    self.data = IO.load(self.pathText)
                    if self.loadMCMC == False:
                        MCMCFrame(self, -1)
                        self.loadMCMC = True
                except AttributeError:
                    self.IP = InvalidParameter("", self, -1, stringVal="oldPKL") 

    def validityCheck(self):
        
        '''
        This is a fitting frame specific method that checks whether or not the given .pkl file
        is valid.
        '''
        
        pathName = self.pklPathTxt.GetValue()
        if pathName != "":
            if pathName.lower().endswith(".pkl"):
                if os.path.isfile(pathName) == False:
                    self.IP = InvalidParameter(pathName, self, -1, stringVal="path")
                    return False
            else:
                self.IP = InvalidParameter(pathName, self, -1, stringVal="path")
                return False 
        else:
            self.IP = InvalidParameter(pathName, self, -1, stringVal="path")
            return False
        return True
    
    def on_exit(self, event):
        
        '''
        This method defines the action quit from the menu. It closes the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()
    
    def onDestroy(self, event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.loadFittingOpen = False

class ETDFrame(wx.Frame):
    
    '''
    This frame converts the data from a .pkl into the correct format in a text
    file that can be accepted by the Czech exoplanet transit database.
    '''
    
    def __init__(self, parent, objectID):
        
        '''
        This method defines the initialization of this class.
        '''
        
        self.title = "ETD Conversion"
        wx.Frame.__init__(self, parent, objectID, self.title)
        
        self.panel = wx.Panel(self)
        self.parent = parent
        self.messageFrame = False
        self.data = ""
        
        self.box = AddLCB(self.panel,-1, parent2 = self, name="Path to Output File: ", updateRadii = True)    
        self.box2 = AddLCB(self.panel, -1, name="Results Output Path (.txt): ", saveType=wx.FD_SAVE)
        
        self.apertureRadii = []
        self.apertureRadiusIndex = 0
        self.radiusLabel = wx.StaticText(self.panel, -1, 'Select Aperture Radius: ')
        self.radiusList = wx.ComboBox(self.panel, value = "", choices = "", size = (100, wx.DefaultSize.GetHeight()))
        self.radiusList.Bind(wx.EVT_COMBOBOX, self.radiusIndexUpdate)    
         
        self.updateRadiiButton = wx.Button(self.panel, label = "Update Radii List")
        self.Bind(wx.EVT_BUTTON, self.updateRadiiList, self.updateRadiiButton)
        
        self.dropBox = wx.BoxSizer(wx.HORIZONTAL)
        self.dropBox.Add(self.radiusLabel, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 10)
        self.dropBox.Add(self.radiusList, 0, flag = wx.ALIGN_CENTER)
        
        self.convertToETDButton = wx.Button(self.panel,label = 'Convert to ETD Format') 

        self.Bind(wx.EVT_BUTTON, self.convertToETD, self.convertToETDButton)
        
        self.sizer0 = wx.FlexGridSizer(rows=2, cols=3)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.sizer0, 0, wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.hbox.Add(self.updateRadiiButton, 0, wx.ALIGN_CENTER |wx. ALL, border = 5)
        self.hbox.Add(self.dropBox, 0, flag=wx.ALIGN_CENTER | wx.ALL, border=10)

        self.sizer0.Add(self.convertToETDButton,0,wx.ALIGN_CENTER|wx.ALL,5)
         
        self.pklPathTxt = self.box.boxList[1]
        self.saveLocation = self.box2.boxList[1]
        self.create_menu()

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.box, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.box2, 0, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        self.vbox.Add(self.hbox, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.vbox.AddSpacer(10)
        self.panel.SetSizer(self.vbox)
        self.CreateStatusBar()
        self.vbox.Fit(self)
        self.Center()
        self.Show()

    def create_menu(self):
        
        '''
        This method creates the menu bars that are at the top of the ETDFrame.
        
        Notes
        -----
        This method has no input or return parameters. It will simply be used as self.create_menu()
        when in the initialization method for an instance of this frame.
        '''
    
        self.menubar = wx.MenuBar()
    
        menu_file = wx.Menu()
        m_browse = menu_file.Append(-1,"Browse","Browse for a .pkl file to use.")
        self.Bind(wx.EVT_MENU, lambda event: self.browseButtonEvent(event,'Choose Path to Output File',self.pklPathTxt,False,
                                                                   wx.FD_OPEN),m_browse)
        m_browse2 = menu_file.Append(-1, "Browse2", "Browse a save location for the results.")
        self.Bind(wx.EVT_MENU, lambda event: self.browseButtonEvent(event,'Choose Path to Output File',self.saveLocation,
                                                                   False,wx.FD_SAVE),m_browse2)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "Exit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
    
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def browseButtonEvent(self, event, message, textControl, fileDialog, saveDialog):
        
        '''
        This method defines the `browse` function for selecting a file on any OS.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        
        message : string
            The message that tells the user what to choose.
            
        textControl : wx.TextCtrl
            The box in the frame that will be refreshed with the files that are chosen by the user.
            
        fileDialog : bool
            If true, the style is wx.FD_MULTIPLE, otherwise it is the same as the `saveDialog`.
            
        saveDialog : wx.FD_*
            The style of the box that will appear. The * represents a wild card value for different types.
        '''
        
        if not fileDialog:
            dlg = wx.FileDialog(self, message = message, style = saveDialog)
        else: 
            dlg = wx.FileDialog(self, message = message,  style = wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            if saveDialog == wx.SAVE:
                filenames = [dlg.GetPath()]
            else:
                filenames = dlg.GetPaths()
            textControl.Clear()
            for i in range(0,len(filenames)):
                if i != len(filenames)-1:
                    textControl.WriteText(filenames[i] + ',')
                else:
                    textControl.WriteText(filenames[i])

        if self.validityCheck(throwException = False): 
            try:    
                self.radiusList.Clear()
                self.data = IO.load(self.box.boxList[1].GetValue())
                self.apertureRadii = np.empty_like(self.data.apertureRadii)
                self.apertureRadii[:] = self.data.apertureRadii
                radiiString = [str(x) for x in self.data.apertureRadii]
                for string in radiiString:
                    self.radiusList.Append(string)
                self.radiusList.SetValue(radiiString[0])
            except AttributeError:
                self.IP = InvalidParameter("", self, -1, stringVal="oldPKL") 
        
        dlg.Destroy()
    
    def convertToETD(self, event):

        '''
        This method uses the czechETDstring method from the databank.py class
        to convert the data into the appropriate format.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''

        if self.validityCheck() and self.radiusCheck():
            tempSaveLoc = self.saveLocation.GetValue()
            if not os.path.isdir(tempSaveLoc.rpartition(str(os.sep))[0]) or \
            not len(tempSaveLoc) > (len(tempSaveLoc[:tempSaveLoc.rfind(os.sep)]) + 1):
                self.IP = InvalidParameter(tempSaveLoc, self, -1, stringVal="output", secondValue="results output file")
            else:
                if not tempSaveLoc.lower().endswith(".txt"):
                    tempSaveLoc += ".txt"
                openFile = open(tempSaveLoc, 'w')
                openFile.write(self.data.czechETDstring(self.apertureRadiusIndex))
                openFile.close()
                self.IP = InvalidParameter("", self, -1, stringVal="successfulConversion")

    def validityCheck(self, throwException=True):

        '''
        This method checks to make sure that the entered .pkl file is valid and can
        be used.
        
        Parameters
        ----------
        throwException : bool, optional
            If true there will be a pop up frame that will explain the reason for why
            the selected file cannot be used if it is invalid. If false, no error message
            will pop up when an invalid file is selected.
        
        Returns
        -------
        literal : bool
            False if the selected file is invalid, true otherwise.
        '''
        
        pathName = self.pklPathTxt.GetValue()
        if pathName != "":
            if pathName.lower().endswith(".pkl"):
                if os.path.isfile(pathName) == False:
                    if throwException:
                        self.IP = InvalidParameter(pathName, self, -1, stringVal="path")
                    return False
            else:
                if throwException:
                    self.IP = InvalidParameter(pathName, self, -1, stringVal="path")
                return False 
        else:
            if throwException:
                self.IP = InvalidParameter(pathName, self, -1, stringVal="path")
            return False
        return True

    def radiusCheck(self):
        
        '''
        This method checks to make sure that if the user enters an aperture radius that they
        would like to plot, that it is a valid number in the list of saved aperture radii for
        the selected file.
        
        Returns
        -------
        literal : bool
            False if the aperture radius selected is not a number or not in the approved list,
            true otherwise.
        '''
        
        if len(self.apertureRadii) == 0:
            self.IP = InvalidParameter(str(self.apertureRadii), self, -1, stringVal="radiusListError", secondValue="etdError")
            return False
        elif self.radiusList.GetValue() == "":
            self.IP = InvalidParameter(self.radiusList.GetValue(), self, -1, stringVal="radiusError")
            return False
        try:
            self.tempNum = np.where(self.epsilonCheck(self.apertureRadii,float(self.radiusList.GetValue())))
            if len(self.tempNum[0]) == 0:
                tempString = self.radiusList.GetValue() + " was not found in " + str(self.apertureRadii)
                self.IP = InvalidParameter(tempString, self, -1, stringVal="radiusListError2")
                return False
        except ValueError:
            self.IP = InvalidParameter(self.radiusList.GetValue(), self, -1, stringVal="radiusError")
            return False
        return True
    
    def updateRadiiList(self, event):
        
        '''
        This method will manually update the drop down menu for the available aperture radii that can
        be chosen from the .pkl file.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
             
        Notes
        -----
        On successful completion, a list of available radii should be shown in the drop down menu of the frame.
        '''
        
        if self.validityCheck():
            try:
                self.radiusList.Clear()
                self.data = IO.load(self.box.boxList[1].GetValue())
                self.apertureRadii = np.empty_like(self.data.apertureRadii)
                self.apertureRadii[:] = self.data.apertureRadii
                radiiString = [str(x) for x in self.data.apertureRadii]
                for string in radiiString:
                    self.radiusList.Append(string)
                self.radiusList.SetValue(radiiString[0])
            except AttributeError:
                self.IP = InvalidParameter("", self, -1, stringVal="oldPKL") 

    def epsilonCheck(self,a,b):
        
        ''' 
        This method checks that two numbers are within machine precision of each other
        because otherwise we get machine precision difference errors when mixing
        single and double precision NumPy floats and pure Python built-in float types.
        
        Parameters
        ----------
        a : array
            An array of float type numbers to check through.
        
        b : float
            The number that is being checked for in the array.
        
        Returns
        -------
        literal : array
            This is an array of booleans.
            
        Notes
        -----
        There a boolean literals of true in the return array if any number in `a` is within machine precision
        of `b`.
        
        Examples
        --------
        Inputs: `a` = [0, 1.0, 2.0, 3.0, 4.0], `b` = 3.0
        Return: [False, False, False, True, False]
        '''
        
        return np.abs(a-b) < np.finfo(np.float32).eps

    def radiusIndexUpdate(self, event):
        
        '''
        This method updates the current index in the list of available radii that this frame will use to plot different
        things. It does this by calling self.epsiloCheck to get an array of booleans. Afterwards, it selects the location
        of the boolean 'True' and marks that as the new index.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.        
        '''
        
        self.apertureRadiusIndex = np.where(self.epsilonCheck(self.apertureRadii, float(self.radiusList.GetValue())))[0][0]
        
    def on_exit(self, event):
        
        '''
        This method defines the action quit from the menu. It closes the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()
    
    def onDestroy(self, event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.etdOpen = False        
        
class LoadOldPklFrame(wx.Frame):
    
    '''
    This frame loads an old .pkl file so that you can make different plots with the
    saved data.
    '''

    def __init__(self, parent, objectID):
        
        '''
        This method defines the initialization of this class.
        '''
        
        self.title = "Load An Old .pkl File"
        wx.Frame.__init__(self, parent, objectID, self.title)
        
        self.panel = wx.Panel(self)
        self.parent = parent
        self.loadGraphFrame = False
        self.messageFrame = False
        self.IP = wx.Frame
        self.data = ""
        
        self.box = AddLCB(self.panel,-1, parent2 = self, buttonLabel="Browse\t (Ctrl-O)",
                          name="Path to Output File: ", updateRadii = True)    
        
        self.apertureRadii = []
        self.apertureRadiusIndex = 0
        self.radiusLabel = wx.StaticText(self.panel, -1, 'Select Aperture Radius: ')
        self.radiusList = wx.ComboBox(self.panel, value = "", choices = "", size = (100, wx.DefaultSize.GetHeight()))
        self.radiusList.Bind(wx.EVT_COMBOBOX, self.radiusIndexUpdate)    
         
        self.updateRadiiButton = wx.Button(self.panel, label = "Update Radii List")
        self.Bind(wx.EVT_BUTTON, self.updateRadiiList, self.updateRadiiButton)
        
        self.dropBox = wx.BoxSizer(wx.HORIZONTAL)
        self.dropBox.Add(self.radiusLabel, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 10)
        self.dropBox.Add(self.radiusList, 0, flag = wx.ALIGN_CENTER)
        
        self.rightBox = wx.BoxSizer(wx.VERTICAL)
        self.rightBox.Add(self.updateRadiiButton, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        self.rightBox.Add(self.dropBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.box, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 10)
        
        if sys.platform == 'win32':
            self.plotLightCurveButton = wx.Button(self.panel,label = 'Plot Light Curve', size = (130,25)) 
            self.plotRawFluxButton = wx.Button(self.panel,label = 'Plot Raw Fluxes', size = (130,25))
            self.plotScaledFluxesButton = wx.Button(self.panel,label = 'Plot Scaled Fluxes', size = (130,25))  
            self.plotCentroidPositionsButton = wx.Button(self.panel, label = 'Trace Stellar Centroid Positions', size = (170,25))
            self.plotComparisonStarWeightingsButton = wx.Button(self.panel,label = 'Plot Comparison\nStar Weightings', size = (110,37))   
            self.plotInteractiveLightCurveButton = wx.Button(self.panel,label = 'Plot Interactive Light Curve', size = (170,25))        
        elif sys.platform == 'darwin':
            self.plotLightCurveButton = wx.Button(self.panel,label = 'Plot Light Curve', size = (130,25)) 
            self.plotRawFluxButton = wx.Button(self.panel,label = 'Plot Raw Fluxes', size = (130,25))
            self.plotScaledFluxesButton = wx.Button(self.panel,label = 'Plot Scaled Fluxes', size = (130,25))
            self.plotCentroidPositionsButton = wx.Button(self.panel,-1,label = 'Trace Stellar\nCentroid Positions', size = (150,40))
            self.plotComparisonStarWeightingsButton = wx.Button(self.panel,-1,label = 'Plot Comparison\nStar Weightings', size = (150,40))
            self.plotInteractiveLightCurveButton = wx.Button(self.panel,-1,label = 'Plot Interactive Light Curve', size = (190,25))
        else:
            self.plotLightCurveButton = wx.Button(self.panel,label = 'Plot Light Curve', size = (130,30)) 
            self.plotRawFluxButton = wx.Button(self.panel,label = 'Plot Raw Fluxes', size = (130,30))
            self.plotScaledFluxesButton = wx.Button(self.panel,label = 'Plot Scaled Fluxes', size = (135,30))
            self.plotCentroidPositionsButton = wx.Button(self.panel,-1,label = 'Trace Stellar\nCentroid Positions', size = (150,45))
            self.plotComparisonStarWeightingsButton = wx.Button(self.panel,-1,label = 'Plot Comparison\nStar Weightings', size = (150,45))
            self.plotInteractiveLightCurveButton = wx.Button(self.panel,-1,label = 'Plot Interactive Light Curve', size = (195,30))

        self.Bind(wx.EVT_BUTTON, self.plotLightCurve, self.plotLightCurveButton)
        self.Bind(wx.EVT_BUTTON, self.plotRawFlux, self.plotRawFluxButton)
        self.Bind(wx.EVT_BUTTON, self.plotScaledFluxes,self.plotScaledFluxesButton)
        self.Bind(wx.EVT_BUTTON, self.plotCentroidPosition, self.plotCentroidPositionsButton)
        self.Bind(wx.EVT_BUTTON, self.plotComparisonStarWeightings, self.plotComparisonStarWeightingsButton)
        self.Bind(wx.EVT_BUTTON, self.plotInteractiveLightCurve, self.plotInteractiveLightCurveButton)
        
        self.sizer0 = wx.FlexGridSizer(rows=2, cols=3)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.sizer0, 0, wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.hbox2.Add(self.rightBox, 0, wx.ALIGN_CENTER |wx. ALL, border = 5)

        self.sizer0.Add(self.plotLightCurveButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotRawFluxButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotScaledFluxesButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotCentroidPositionsButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotComparisonStarWeightingsButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotInteractiveLightCurveButton,0,wx.ALIGN_CENTER|wx.ALL,5)
         
        self.pklPathTxt = self.box.boxList[1]
        self.create_menu()

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.hbox, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.vbox.AddSpacer(10)
        self.panel.SetSizer(self.vbox)
        self.CreateStatusBar()
        self.vbox.Fit(self)
        self.Center()
        self.Show()

    def create_menu(self):
         
        '''
        This method creates the menu bars that are at the top of the load old pkl frame.
        
        Notes
        -----
        This method has no input or return parameters. It will simply be used as self.create_menu()
        when in the initialization method for an instance of this frame.
        '''
    
        self.menubar = wx.MenuBar()
    
        menu_file = wx.Menu()
        m_browse = menu_file.Append(-1,"Browse\tCtrl-O","Browse")
        self.Bind(wx.EVT_MENU,lambda event: self.browseButtonEvent(event,'Choose Path to Output File',self.pklPathTxt,False,
                                                                   wx.FD_OPEN),m_browse)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "Exit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
    
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def browseButtonEvent(self, event, message, textControl, fileDialog, saveDialog):
        
        '''
        This method defines the `browse` function for selecting a file on any OS.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        
        message : string
            The message that tells the user what to choose.
            
        textControl : wx.TextCtrl
            The box in the frame that will be refreshed with the files that are chosen by the user.
            
        fileDialog : bool
            If true, the style is wx.FD_MULTIPLE, otherwise it is the same as the `saveDialog`.
            
        saveDialog : wx.FD_*
            The style of the box that will appear. The * represents a wild card value for different types.
        '''
        
        if not fileDialog:
            dlg = wx.FileDialog(self, message = message, style = saveDialog)
        else: 
            dlg = wx.FileDialog(self, message = message,  style = wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            if saveDialog == wx.SAVE:
                filenames = [dlg.GetPath()]
            else:
                filenames = dlg.GetPaths()
            textControl.Clear()
            for i in range(0,len(filenames)):
                if i != len(filenames)-1:
                    textControl.WriteText(filenames[i] + ',')
                else:
                    textControl.WriteText(filenames[i])

        if self.validityCheck(throwException = False): 
            try:    
                self.radiusList.Clear()
                self.data = IO.load(self.box.boxList[1].GetValue())
                self.apertureRadii = np.empty_like(self.data.apertureRadii)
                self.apertureRadii[:] = self.data.apertureRadii
                radiiString = [str(x) for x in self.data.apertureRadii]
                for string in radiiString:
                    self.radiusList.Append(string)
                self.radiusList.SetValue(radiiString[0])
            except AttributeError:
                self.IP = InvalidParameter("", self, -1, stringVal="oldPKL") 
        
        dlg.Destroy()

    def plotLightCurve(self, event):
        
        '''
        This method will plot the light curve of the data that has been saved in an
        old .pkl file for the specific aperture radius that is selected.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        
        Notes
        -----
        On successful completion a plot will open up in a new window.
        '''
        
        if self.validityCheck() and self.radiusCheck():
            if self.tempNum[0][0] != self.apertureRadiusIndex:
                self.apertureRadiusIndex = self.tempNum[0][0]
            print 'Loading file: '+self.pklPathTxt.GetValue()
            
            commandstring = "import oscaar.IO; data=oscaar.IO.load('%s'); data.plotLightCurve(apertureRadiusIndex=%s)" \
                                % (self.pklPathTxt.GetValue(),self.apertureRadiusIndex)

            subprocess.Popen(['python','-c',commandstring])


    def plotRawFlux(self, event):
        
        '''
        This method will plot the raw fluxes of the data that has been saved in an
        old .pkl file for the specific aperture radius that is selected.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
             
        Notes
        -----
        On successful completion a plot will open up in a new window.
        '''
        
        if self.validityCheck() and self.radiusCheck():
            if self.tempNum[0][0] != self.apertureRadiusIndex:
                self.apertureRadiusIndex = self.tempNum[0][0]
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar.IO; data=oscaar.IO.load('%s'); data.plotRawFluxes(apertureRadiusIndex=%s)" \
                                % (self.pklPathTxt.GetValue(),self.apertureRadiusIndex)
                                
            subprocess.Popen(['python','-c',commandstring])

    def plotScaledFluxes(self, event):
        
        '''
        This method will plot the scaled fluxes of the data that has been saved in an
        old .pkl file for the specific aperture radius that is selected.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
             
        Notes
        -----
        On successful completion a plot will open up in a new window.
        '''

        if self.validityCheck() and self.radiusCheck():
            if self.tempNum[0][0] != self.apertureRadiusIndex:
                self.apertureRadiusIndex = self.tempNum[0][0]
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar.IO; data=oscaar.IO.load('%s'); data.plotScaledFluxes(apertureRadiusIndex=%s)" \
                              % (self.pklPathTxt.GetValue(),self.apertureRadiusIndex)

            subprocess.Popen(['python','-c',commandstring])
    
    def plotCentroidPosition(self, event):
        
        '''
        This method will plot the centroid positions of the data that has been saved in an
        old .pkl file.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
             
        Notes
        -----
        On successful completion a plot will open up in a new window.
        '''
        
        if self.validityCheck():
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar.IO; data=oscaar.IO.load('%s'); data.plotCentroidsTrace()" \
                                % (self.pklPathTxt.GetValue())

            subprocess.Popen(['python','-c',commandstring])

    def plotComparisonStarWeightings(self, event):
        
        '''
        This method will plot the comparison star weightings of the data that has been saved in an
        old .pkl file for the specific aperture radius that is selected.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
             
        Notes
        -----
        On successful completion a plot will open up in a new window.
        '''
        
        if self.validityCheck() and self.radiusCheck():
            if self.tempNum[0][0] != self.apertureRadiusIndex:
                self.apertureRadiusIndex = self.tempNum[0][0]
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar.IO; data=oscaar.IO.load('%s');" \
                            "data.plotComparisonWeightings(apertureRadiusIndex=%s)" \
                            % (self.pklPathTxt.GetValue(),self.apertureRadiusIndex)

            subprocess.Popen(['python','-c',commandstring])
    
    def plotInteractiveLightCurve(self, event):
        
        '''
        This method will plot the interactive light curve of the data that has been saved in an
        old .pkl file for the specific aperture radius that is selected.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
             
        Notes
        -----
        On successful completion a plot will open up in a new window.
        '''
        
        if self.validityCheck() and self.radiusCheck():
            if self.tempNum[0][0] != self.apertureRadiusIndex:
                self.apertureRadiusIndex = self.tempNum[0][0]
            if self.loadGraphFrame == False:   
                GraphFrame(self, -1)
                self.loadGraphFrame = True
            
    def validityCheck(self, throwException=True):

        '''
        This method checks to make sure that the entered .pkl file is valid and can
        be used.
        
        Parameters
        ----------
        throwException : bool, optional
            If true there will be a pop up frame that will explain the reason for why
            the selected file cannot be used if it is invalid. If false, no error message
            will pop up when an invalid file is selected.
        
        Returns
        -------
        literal : bool
            False if the selected file is invalid, true otherwise.
        '''

        pathName = self.pklPathTxt.GetValue()
        if pathName != "":
            if pathName.lower().endswith(".pkl"):
                if os.path.isfile(pathName) == False:
                    if throwException:
                        self.IP = InvalidParameter(pathName, self, -1, stringVal="path")
                    return False
            else:
                if throwException:
                    self.IP = InvalidParameter(pathName, self, -1, stringVal="path")
                return False 
        else:
            if throwException:
                self.IP = InvalidParameter(pathName, self, -1, stringVal="path")
            return False
        return True

    def radiusCheck(self):
        
        '''
        This method checks to make sure that if the user enters an aperture radius that they
        would like to plot, that it is a valid number in the list of saved aperture radii for
        the selected file.
        
        Returns
        -------
        literal : bool
            False if the aperture radius selected is not a number or not in the approved list,
            true otherwise.
        '''
        
        if len(self.apertureRadii) == 0:
            self.IP = InvalidParameter(str(self.apertureRadii), self, -1, stringVal="radiusListError")
            return False
        elif self.radiusList.GetValue() == "":
            self.IP = InvalidParameter(self.radiusList.GetValue(), self, -1, stringVal="radiusError")
            return False
        try:
            self.tempNum = np.where(self.epsilonCheck(self.apertureRadii,float(self.radiusList.GetValue())))
            if len(self.tempNum[0]) == 0:
                tempString = self.radiusList.GetValue() + " was not found in " + str(self.apertureRadii)
                self.IP = InvalidParameter(tempString, self, -1, stringVal="radiusListError2")
                return False
        except ValueError:
            self.IP = InvalidParameter(self.radiusList.GetValue(), self, -1, stringVal="radiusError")
            return False
        return True
    
    def updateRadiiList(self, event):
        
        '''
        This method will manually update the drop down menu for the available aperture radii that can
        be chosen from the .pkl file.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
             
        Notes
        -----
        On successful completion, a list of available radii should be shown in the drop down menu of the frame.
        '''
                
        if self.validityCheck():
            try:
                self.radiusList.Clear()
                self.data = IO.load(self.box.boxList[1].GetValue())
                self.apertureRadii = np.empty_like(self.data.apertureRadii)
                self.apertureRadii[:] = self.data.apertureRadii
                radiiString = [str(x) for x in self.data.apertureRadii]
                for string in radiiString:
                    self.radiusList.Append(string)
                self.radiusList.SetValue(radiiString[0])
            except AttributeError:
                self.IP = InvalidParameter("", self, -1, stringVal="oldPKL") 

    def epsilonCheck(self,a,b):
        
        ''' 
        This method checks that two numbers are within machine precision of each other
        because otherwise we get machine precision difference errors when mixing
        single and double precision NumPy floats and pure Python built-in float types.
        
        Parameters
        ----------
        a : array
            An array of float type numbers to check through.
        
        b : float
            The number that is being checked for in the array.
        
        Returns
        -------
        literal : array
            This is an array of booleans.
            
        Notes
        -----
        There a boolean literals of true in the return array if any number in `a` is within machine precision
        of `b`.
        
        Examples
        --------
        Inputs: `a` = [0, 1.0, 2.0, 3.0, 4.0], `b` = 3.0
        Return: [False, False, False, True, False]
        '''
        
        return np.abs(a-b) < np.finfo(np.float32).eps

    def radiusIndexUpdate(self, event):
        
        '''
        This method updates the current index in the list of available radii that this frame will use to plot different
        things. It does this by calling self.epsiloCheck to get an array of booleans. Afterwords, it selects the location
        of the boolean 'True' and marks that as the new index.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.        
        '''
        
        self.apertureRadiusIndex = np.where(self.epsilonCheck(self.apertureRadii, float(self.radiusList.GetValue())))[0][0]
        
    def on_exit(self, event):
        
        '''
        This method defines the action quit from the menu. It closes the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()
    
    def onDestroy(self, event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.loadOldPklOpen = False
    

class GraphFrame(wx.Frame):
    
    '''
    This is the class for the interactive light curve plot frame. It allows a user to continuously
    plot a light curve with a new bin size as well as change the names of the axes and title.
    '''
    
    title = 'Interactive Light Curve Plot'

    def __init__(self, parent, objectID):
        
        '''
        This method defines the initialization of this class.
        '''
        
        wx.Frame.__init__(self, parent, objectID, self.title, style = wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | 
                                                                                            wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        self.pT = parent.pklPathTxt.GetValue()
        self.parent = parent
        self.apertureRadiusIndex = self.parent.apertureRadiusIndex
        self.create_menu()
        self.statusbar = self.CreateStatusBar()
        self.create_main_panel()
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.Centre()
        self.Show()

    def create_menu(self):
        
        '''
        This method creates the menu bars that are at the top of the graph frame.
        
        Notes
        -----
        This method has no input or return parameters. It will simply be used as self.create_menu()
        when in the initialization method for an instance of this frame.
        '''
        
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_expt = menu_file.Append(-1, "&Save plot\tCtrl-S", "Save plot to file")
        self.Bind(wx.EVT_MENU, self.on_save_plot, m_expt)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
        
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def create_main_panel(self):
        
        '''
        This method creates a wxPython panel that will update everytime a new instance of the 
        light curve plot is generated.
        '''

        self.panel = wx.Panel(self)
        self.init_plot()
        self.canvas = FigCanvas(self.panel, -1, self.fig)
        self.box = ScanParamsBox(self.panel,-1)

        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.box, border=5, flag=wx.ALL)
        self.plotButton = wx.Button(self.panel,label = 'Plot')
        self.Bind(wx.EVT_BUTTON,self.draw_plot, self.plotButton)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)  
        self.vbox.Add(self.hbox, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.plotButton,0,flag=wx.ALIGN_CENTER|wx.TOP)
        self.vbox.AddSpacer(10)
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)

    def init_plot(self):
        
        '''
        This is the initial plot that is displayed. It uses a bin size of 10 for the light curve.
        '''
        
        self.data = IO.load(self.pT)
        self.pointsPerBin = 10

        binnedTime, binnedFlux, binnedStd = medianBin(self.data.times,self.data.lightCurves[self.apertureRadiusIndex],
                                                      self.pointsPerBin)
        self.fig = pyplot.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
        self.dpi = 100
        self.axes = self.fig.add_subplot(111)
        self.axes.set_axis_bgcolor('white')
        self.axes.set_title('Light Curve', size=12)
        
        def format_coord(x, y):
            
            '''
            Function to give data value on mouse over plot.
            '''
            
            return 'JD=%1.5f, Flux=%1.4f' % (x, y)
        
        self.axes.format_coord = format_coord 
        self.axes.errorbar(self.data.times,self.data.lightCurves[self.apertureRadiusIndex],
                           yerr=self.data.lightCurveErrors[self.apertureRadiusIndex],fmt='k.',ecolor='gray')
        self.axes.errorbar(binnedTime, binnedFlux, yerr=binnedStd, fmt='rs-', linewidth=2)
        self.axes.axvline(ymin=0,ymax=1,x=self.data.ingress,color='k',ls=':')
        self.axes.axvline(ymin=0,ymax=1,x=self.data.egress,color='k',ls=':')
        self.axes.set_title(('Light curve for aperture radius %s' % self.data.apertureRadii[self.apertureRadiusIndex]))
        self.axes.set_xlabel('Time (JD)')
        self.axes.set_ylabel('Relative Flux')

    def draw_plot(self,event):
        
        '''
        This method will redraw the plot every time the user presses the plot button in the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
             
        Notes
        -----
        On successful completion with at least one parameter changed, the new plot will show up in the panel of
        the frame.
        '''
        
        self.box.update()
        self.box.setMax(len(self.data.times))
        
        if self.box.boxCorrect() == True and self.box.boxDiff() == True:
            
            print "Re-drawing Plot"
            
            self.xlabel = self.box.userinfo['xlabel'].GetValue()
            self.ylabel = self.box.userinfo['ylabel'].GetValue()
            self.plotTitle = self.box.userinfo['title'].GetValue()
            self.pointsPerBin = int(self.box.userinfo['bin'].GetValue())
            
            binnedTime, binnedFlux, binnedStd = medianBin(self.data.times,self.data.lightCurves[self.apertureRadiusIndex],
                                                          self.pointsPerBin)
           
            if sys.platform == 'win32': 
                self.fig = pyplot.figure(num=None, figsize=(10, 6.75), facecolor='w',edgecolor='k')
            else: 
                self.fig = pyplot.figure(num=None, figsize=(10, 8.0), facecolor='w',edgecolor='k')
            
            self.dpi = 100
            self.axes = self.fig.add_subplot(111)
            self.axes.set_axis_bgcolor('white')
            self.axes.set_title('Light Curve', size=12)
            
            def format_coord(x, y):
                
                '''
                Function to give data value on mouse over plot.
                '''
                
                return 'JD=%1.5f, Flux=%1.4f' % (x, y)

            self.axes.format_coord = format_coord 
            self.axes.errorbar(self.data.times,self.data.lightCurves[self.apertureRadiusIndex],
                               yerr=self.data.lightCurveErrors[self.apertureRadiusIndex],fmt='k.',ecolor='gray')
            self.axes.errorbar(binnedTime, binnedFlux, yerr=binnedStd, fmt='rs-', linewidth=2)
            self.axes.axvline(ymin=0,ymax=1,x=self.data.ingress,color='k',ls=':')
            self.axes.axvline(ymin=0,ymax=1,x=self.data.egress,color='k',ls=':')
            self.axes.set_title(self.plotTitle)
            self.axes.set_xlabel(self.xlabel)
            self.axes.set_ylabel(self.ylabel)

            self.canvas = FigCanvas(self.panel, -1, self.fig)

    def on_save_plot(self, event):
        
        '''
        This method will save the plot you create as a .png file.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''

        file_choices = "PNG (*.png)|*.png"
        
        dlg = wx.FileDialog(
            self, 
            message="Save plot as...",
            defaultDir=os.getcwd(),
            defaultFile="plot.png",
            wildcard=file_choices,
            style=wx.SAVE)
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.canvas.print_figure(path, dpi=self.dpi)
            self.flash_status_message("Saved to %s" % path)
    
    def flash_status_message(self, msg, flash_len_ms=1500):
        
        '''
        This method will show a message for a brief moment on the status bar at the bottom of the frame.
        
        Parameters
        ----------
        msg : string
            The message that will appear.
            
        flash_len_ms : int, optional
            The amount of time the message should appear for in milliseconds.
        '''
        
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(
            wx.EVT_TIMER, 
            self.on_flash_status_off, 
            self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)
    
    def on_flash_status_off(self, event):
        
        '''
        This clears the status bar of the frame after a message has been displayed.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.statusbar.SetStatusText('')
    
    def on_exit(self, event):
        
        '''
        This method defines the action quit from the menu. It closes the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()
    
    def onDestroy(self, event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''

        self.parent.loadGraphFrame = False



class LeastSquaresFitFrame(wx.Frame):
    
    '''
    This class is not in use right now.
    '''
    
    """
    title = "Least Squares Fit"
    
    def __init__(self):
        
        wx.Frame.__init__(self, None,-1, self.title)
        
        self.panel = wx.Panel(self)
        
        self.pT = pathText
        self.data = IO.load(self.pT)
         
        self.box1 = AddLCB(self.panel,-1,name="planet")
        self.Bind(wx.EVT_BUTTON,self.update,self.box1.updateButton)
        self.topBox = wx.BoxSizer(wx.HORIZONTAL)
        self.topBox.Add(self.box1, border=5, flag=wx.ALL)
        
        self.list =  [
                    ('Rp/Rs',"Ratio of Radii (Rp/Rs):",
                     'Enter a ratio of the radii here.',''),
                    ('a/Rs',"a/Rs:",
                     'Enter a value for a/Rs here.',''),
                    ('per',"Period:",
                     'Enter a value for the period here.',''),
                    ('inc',"Inclination:",
                     'Enter a value for the inclination here.',''),
                    ('ecc',"Eccentricity: ", 
                     'Enter a value for the eccentricity here.',''),
                    ('t0',"t0:",
                     'Enter a value for t0 here.',
                     str(transiterFit.calcMidTranTime(self.data.times,self.data.lightCurves[radiusNum]))),
                    ('gamma1',"Gamma 1:",
                     'Enter a value for gamma 1 here.','0.0'),
                    ('gamma2'," Gamma 2:",
                     'Enter a value for gamma 2 here.','0.0'),
                    ('pericenter',"Pericenter:",
                     'Enter an arguement for the pericenter here.','0.0'),
                    ('limbdark',"Limb-Darkening Parameter:",
                     'Enter an arguement for limb-darkening here.','False')
                    ]

        self.box = ParameterBox(self.panel,-1,self.list,name="Input Parameters")
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.box, border=5, flag=wx.ALL)
        
        self.plotButton = wx.Button(self.panel,label = 'Plot')
        self.Bind(wx.EVT_BUTTON,self.plot, self.plotButton)

        self.sizer0 = wx.FlexGridSizer(rows=1, cols=10)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotButton,0,wx.ALIGN_CENTER|wx.ALL,5)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.topBox, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.hbox, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_CENTER | wx.TOP)
#         
#         self.box.userParams['t0'].SetValue(str(oscaar.transiterFit.calcMidTranTime(self.data.times,self.data.lightCurve)))
#         
        self.vbox.AddSpacer(10)
        self.vbox.AddSpacer(10)
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.create_menu()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.Center()
        self.Show()

    def plot(self,event):
        
        self.tempLimbDark = self.box.userParams['limbdark'].GetValue()

        list = [(self.box.userParams['Rp/Rs'].GetValue(),"Rp/Rs"),(self.box.userParams['a/Rs'].GetValue(),"a/Rs"),
                (self.box.userParams['per'].GetValue(),"per"), (self.box.userParams['inc'].GetValue(),"inc"),
                (self.box.userParams['ecc'].GetValue(),"ecc"), (self.box.userParams['t0'].GetValue(),"t0"),
                (self.box.userParams['gamma1'].GetValue(),"gamma1"),(self.box.userParams['gamma2'].GetValue(),"gamma2"),
                (self.box.userParams['pericenter'].GetValue(),"pericenter"), 
                (self.tempLimbDark,"limbdark")]

        if checkParams(self,list) == True:
            
            if self.box.userParams['limbdark'].GetValue() == 'False':
                self.tempLimbDark = False
            
            fit, success = transiterFit.run_LMfit(self.data.getTimes(), self.data.lightCurves[radiusNum],
                                                  self.data.lightCurveErrors[radiusNum],
                                                  float(self.box.userParams['Rp/Rs'].GetValue()),
                                                  float(self.box.userParams['a/Rs'].GetValue()),
                                                  float(self.box.userParams['inc'].GetValue()),
                                                  float(self.box.userParams['t0'].GetValue()),
                                                  float(self.box.userParams['gamma1'].GetValue()),
                                                  float(self.box.userParams['gamma2'].GetValue()),
                                                  float(self.box.userParams['per'].GetValue()),
                                                  float(self.box.userParams['ecc'].GetValue()),
                                                  float(self.box.userParams['pericenter'].GetValue()),
                                                  fitLimbDark=self.tempLimbDark, plotting=True)
            n_iter = 300
#             Rp,aRs,inc,t0,gam1,gam2=oscaar.transiterFit.run_MCfit(n_iter,self.data.getTimes(),
#                 self.data.lightCurve, self.data.lightCurveError,fit,success,
#                 float(self.box.GetPeriod()),float(self.box.GetEcc()),
#                 float(self.box.GetPericenter()),float(self.box.GetGamma1()),float(self.box.GetGamma2()), plotting=False)

    def update(self,event):
        if self.box1.boxList[1].GetValue() == '':
            self.IP = InvalidParameter(self.box1.boxList[1].GetValue(), None,-1, stringVal="planet")
        else:
            self.planet = self.box1.boxList[1].GetValue()
            [RpOverRs,AOverRs,per,inc,ecc] = returnSystemParams.transiterParams(self.planet)
            
            if RpOverRs == -1 or AOverRs == -1 or per == -1 or inc == -1 or ecc == -1:
                self.IP = InvalidParameter(self.box1.boxList[1].GetValue(), None,-1, stringVal="planet")
            else:
                self.box.userParams['Rp/Rs'].SetValue(str(RpOverRs))
                self.box.userParams['a/Rs'].SetValue(str(AOverRs))
                self.box.userParams['per'].SetValue(str(per))
                self.box.userParams['inc'].SetValue(str(inc))
                self.box.userParams['ecc'].SetValue(str(ecc))
                self.IP = InvalidParameter("",None,-1, stringVal="params")

    def create_menu(self):
    
        # These commands create a drop down menu with the exit command.
    
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
        
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)
        
    def on_exit(self, event):
        self.Destroy()
    
    def onDestroy(self, event):
        global loadLSFit
        loadLSFit = False
    """

class MCMCFrame(wx.Frame):
    
    '''
    This frame allows the user to edit a number of different parameters to run the
    Markov Chain Monte Carlo routine for fitting.
    '''
    
    title = "MCMC Fit"
    
    def __init__(self, parent, objectID):

        '''
        This method defines the initialization of this class.
        '''
        
        wx.Frame.__init__(self, parent, objectID, self.title)
        
        self.panel = wx.Panel(self)
        self.parent = parent
        self.messageFrame = False
        self.IP = wx.Frame
        self.pT = self.parent.pathText
        self.saveLoc = self.parent.saveLocation.GetValue()
        self.data = self.parent.data
        
        self.LCB = AddLCB(self.panel,-1,name="planet")
        self.Bind(wx.EVT_BUTTON,self.update,self.LCB.updateButton)

        radiiString = [str(x) for x in self.data.apertureRadii]
        self.apertureRadiusIndex = 0
        self.radiusLabel = wx.StaticText(self.panel, -1, 'Select Aperture Radius: ')
        self.radiusList = wx.ComboBox(self.panel, value = str(self.data.apertureRadii[0]), choices = radiiString)
        self.radiusList.Bind(wx.EVT_COMBOBOX, self.radiusUpdate)    
        
        self.dropBox = wx.BoxSizer(wx.HORIZONTAL)
        self.dropBox.Add(self.radiusLabel, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 10)
        self.dropBox.Add(self.radiusList, 0, flag = wx.ALIGN_CENTER)
        
        self.topBox = wx.BoxSizer(wx.HORIZONTAL)
        self.topBox.Add(self.LCB, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.topBox.Add(self.dropBox, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        
        tupleList = [('Rp/Rs',"Ratio of Radii (Rp/Rs):", 'Enter a ratio of the radii here.','0.11'),
                     ('a/Rs',"a/Rs:", 'Enter a value for a/Rs here.','14.1'),
                     ('inc',"Inclination:", 'Enter a value for the inclination here.','90.0'),
                     ('t0',"t0:", 'Enter a value for the mid transit time here.','2456427.9425593214')]
        
        self.box = ParameterBox(self.panel,-1,tupleList,"Free Parameters",rows=4,cols=2)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.box, border=5, flag=wx.ALL)
        
        tupleList = [('b-Rp/Rs',"Beta Rp/Rs:", 'Enter a beta for Rp/Rs here.','0.005'),
                     ('b-a/Rs',"Beta a/Rs:", 'Enter a beta for a/Rs here.','0.005'),
                     ('b-inc',"Beta Inclination:", 'Enter a beta for inclination here.','0.005'),   
                     ('b-t0',"Beta t0:", 'Enter a beta for the mid transit time here.','0.005')]
        
        self.box2 = ParameterBox(self.panel,-1,tupleList,"Beta's",rows=4,cols=2)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.box2, border=5, flag=wx.ALL)

        tupleList = [('per',"Period:", 'Enter a value for the period here.','1.580400'),
                     ('gamma1',"gamma1:", 'Enter a value for gamma1 here.','0.23'),
                     ('gamma2',"gamma2:", 'Enter a value for gamma2 here.','0.3'),
                     ('ecc',"Eccentricity:", 'Enter a value for the eccentricity here.','0.0'),
                     ('pericenter',"Pericenter:", 'Enter a value for the pericenter here.','0.0')]
        
        self.box3 = ParameterBox(self.panel,-1,tupleList,"Fixed Parameters")
        self.hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3.Add(self.box3, border=5, flag=wx.ALL)        
        
        tupleList = [('saveiteration',"Iteration to save:", 'Enter a number for the nth iteration to be saved.','10'),
                     ('burnfrac',"Burn Fraction:", 'Enter a decimal for the burn fraction here.','0.20'),
                     ('acceptance',"Acceptance:", 'Enter a value for the acceptance rate here.','0.30'),
                     ('number', "Number of Steps:", 'Enter a value for the total steps here.','10000')]
        
        self.box4 = ParameterBox(self.panel,-1,tupleList,"Fit Parameters")
        self.hbox4 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox4.Add(self.box4, border=5, flag=wx.ALL)
                
        self.plotButton = wx.Button(self.panel,label = 'Run and Plot')
        self.Bind(wx.EVT_BUTTON,self.plot, self.plotButton)

        self.sizer0 = wx.FlexGridSizer(rows=1, cols=10)
        self.hbox5 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox5.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotButton,0,wx.ALIGN_CENTER|wx.ALL,5)


        self.vbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.vbox2.Add(self.hbox, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox2.Add(self.hbox2, 0, flag=wx.ALIGN_CENTER | wx.TOP)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.topBox, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.vbox2, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.hbox3, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.hbox4, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.hbox5, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        
        self.vbox.AddSpacer(10)
        self.vbox.AddSpacer(10)
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.create_menu()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.Center()
        self.Show()
    
    def create_menu(self):
        
        '''
        This method creates the menu bars that are at the top of the MCMC frame.
        
        Notes
        -----
        This method has no input or return parameters. It will simply be used as self.create_menu()
        when in the initialization method for an instance of this frame.
        '''
        
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
        
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def plot(self,event):
        
        '''
        After checking that all of the user editable parameters in the frame are valid and loaded
        as a list of variables, this method actually exexcutes the MCMC fitting routine by calling it from
        the fitting.py file.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.     
        '''
        
        tupleList = [(self.box.userParams['Rp/Rs'].GetValue(),"Rp/Rs"),
                     (self.box.userParams['a/Rs'].GetValue(),"a/Rs"),
                     (self.box3.userParams['per'].GetValue(),"per"), 
                     (self.box.userParams['inc'].GetValue(),"inc"),
                     (self.box3.userParams['ecc'].GetValue(),"ecc"), 
                     (self.box.userParams['t0'].GetValue(),"t0"),
                     (self.box3.userParams['gamma1'].GetValue(),"gamma1"),
                     (self.box3.userParams['gamma2'].GetValue(),"gamma2"),
                     (self.box3.userParams['pericenter'].GetValue(),"pericenter"),
                     (self.box4.userParams['saveiteration'].GetValue(),"saveiteration"), 
                     (self.box4.userParams['acceptance'].GetValue(),"acceptance"),
                     (self.box4.userParams['burnfrac'].GetValue(),"burnfrac"), 
                     (self.box4.userParams['number'].GetValue(),"number")]
        
        if checkParams(self,tupleList) == True and self.radiusCheck() == True:
            
            initParams = [float(self.box.userParams['Rp/Rs'].GetValue()),float(self.box.userParams['a/Rs'].GetValue()),
                          float(self.box3.userParams['per'].GetValue()), float(self.box.userParams['inc'].GetValue()),
                          float(self.box3.userParams['gamma1'].GetValue()),float(self.box3.userParams['gamma2'].GetValue()),
                          float(self.box3.userParams['ecc'].GetValue()),float(self.box3.userParams['pericenter'].GetValue()),
                          float(self.box.userParams['t0'].GetValue())]
            
            nSteps = float(self.box4.userParams['number'].GetValue())
            initBeta = (np.zeros([4]) + 0.012).tolist()        
            idealAcceptanceRate = float(self.box4.userParams['acceptance'].GetValue())
            interval = float(self.box4.userParams['saveiteration'].GetValue())
            burnFraction = float(self.box4.userParams['burnfrac'].GetValue())
            
            # Spawn a new process to execute the MCMC run separately.
            mcmcCall = 'import oscaar.fitting; mcmcinstance = oscaar.fitting.mcmcfit("%s",%s,%s,%s,%s,%s,%s); mcmcinstance.run(updatepkl=True, apertureRadiusIndex=%s); mcmcinstance.plot(num=%s)' % \
                         (self.pT,initParams,initBeta,nSteps,interval,idealAcceptanceRate,burnFraction,
                          self.apertureRadiusIndex,self.apertureRadiusIndex)
            subprocess.check_call(['python','-c',mcmcCall])
            
            # Load the data again and save it in a text file.
            self.data = IO.load(self.pT)
            if not self.saveLoc.lower().endswith(".txt"):
                self.saveLoc += ".txt"
            outfile = open(self.saveLoc,'w')
            outfile.write(self.data.uncertaintyString())
            outfile.close()

    def radiusCheck(self):
        
        '''
        This method checks to make sure that the aperture radius entered is valid and in the list
        available for the selected .pkl file.
        
        Returns
        -------
        literal : bool
            True if the radius is valid, false otherwise.
        '''
        
        if self.radiusList.GetValue() == "":
            self.IP = InvalidParameter(self.radiusList.GetValue(), self, -1, stringVal="radiusError")
            return False
        try:
            condition = self.epsilonCheck(self.data.apertureRadii,float(self.radiusList.GetValue()))
            self.tempNum = np.array(self.data.apertureRadii)[condition]
            if len(self.tempNum) == 0:
                tempString = self.radiusList.GetValue() + " was not found in " + str(self.data.apertureRadii)
                self.IP = InvalidParameter(tempString, self, -1, stringVal="radiusListError2")
                return False
        except ValueError:
            self.IP = InvalidParameter(self.radiusList.GetValue(), self, -1, stringVal="radiusError")
            return False
        return True

    def update(self,event):
        
        '''
        This method will update the appropriate parameters for the frame, if a user selects
        an appropriate planet name from the exoplanet.org database.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.     
        '''
                
        if self.LCB.boxList[1].GetValue() == '':
            self.IP = InvalidParameter(self.LCB.boxList[1].GetValue(), self,-1, stringVal="planet")
        else:
            self.planet = self.LCB.boxList[1].GetValue()
            [RpOverRs,AOverRs,per,inc,ecc] = returnSystemParams.transiterParams(self.planet)
            
            if RpOverRs == -1 or AOverRs == -1 or per == -1 or inc == -1 or ecc == -1:
                self.IP = InvalidParameter(self.LCB.boxList[1].GetValue(), self,-1, stringVal="planet")
            else:
                self.box.userParams['Rp/Rs'].SetValue(str(RpOverRs))
                self.box.userParams['a/Rs'].SetValue(str(AOverRs))
                self.box3.userParams['per'].SetValue(str(per))
                self.box.userParams['inc'].SetValue(str(inc))
                self.box3.userParams['ecc'].SetValue(str(ecc))
                self.IP = InvalidParameter("",self,-1, stringVal="params")

    def epsilonCheck(self,a,b):
        
        ''' 
        This method checks that two numbers are within machine precision of each other
        because otherwise we get machine precision difference errors when mixing
        single and double precision NumPy floats and pure Python built-in float types.
        
        Parameters
        ----------
        a : array
            An array of float type numbers to check through.
        
        b : float
            The number that is being checked for in the array.
        
        Returns
        -------
        literal : array
            This is an array of booleans.
            
        Notes
        -----
        There a boolean literals of true in the return array if any number in `a` is within machine precision
        of `b`.
        
        Examples
        --------
        Inputs: `a` = [0, 1.0, 2.0, 3.0, 4.0], `b` = 3.0
        Return: [False, False, False, True, False]
        '''
        
        a = np.array(a)
        return np.abs(a-b) < np.finfo(np.float32).eps

    def radiusUpdate(self, event):
        
        '''
        This method updates the current index in the list of available radii that this frame will use to plot MCMC.
        It does this by calling self.epsiloCheck to get an array of booleans. Afterwords, it selects the location
        of the boolean 'True' and marks that as the new index.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.        
        '''
        
        self.apertureRadiusIndex = np.where(self.epsilonCheck(self.data.apertureRadii, 
                                                              float(self.radiusList.GetValue())))[0][0]
                
    def on_exit(self, event):
         
        '''
        This method defines the action quit from the menu. It closes the frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()
    
    def onDestroy(self, event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.loadMCMC = False

class ParameterBox(wx.Panel):
    
    '''
    This is a general method that is used throughout the GUI to create an interactive box
    with multiple text controls for user input.
    
    Parameters
    ----------
    parent : window
        The parent window that this box will be associated with.
    
    objectID : int
        The identity number of the object.
    
    tupleList : array
        An array of tuples for the different text controls desired. The tuple must be four strings.
    
    name : string, optional
        The name of the box for the current set of parameters. It is displayed in the upper left hand corner.
    
    rows : int, optional
        The number of rows for the box.
        
    cols : int, optional
        The number of columns for the box.
    
    vNum : int, optional
        The vertical displacement between each text control.
    
    hNum : int, optional
        The horizontal displacement between each text control.
    
    font : wx.font(), optional
        The type of style you would like the text to be displayed as.
    
    secondButton : bool, optional
        If a radio button is created by this class, the first value of the radio button will be selected
        since the default value is false. IF this variable is true however, the second value of the radio
        button is selected.

    Notes
    -----
    The list that is given as a parameter must be an array of tuples. The format for these tuples is 
    (string, string, string, string). The first string will be the keyword (widget) to select that specific 
    text box to work with in the code. The second string is the name of the parameter that will appear in the GUI.  
    The third string will be the tooltip that is seen if the user hovers over the box. The fourth string is 
    the default value for that parameter.
    
    If however, the widget name begins with 'rb', a radio button will be created. In this scenario, the second
    string will be the name of the parameter, with the 3rd and 4th strings being the values of the two radio
    buttons that will be created.
    '''
    
    def __init__(self, parent, objectID, tupleList, name="", rows=1, cols=10, vNum=0, hNum=0, font=wx.NORMAL_FONT, 
                 secondButton=False):
                   
        wx.Panel.__init__(self,parent,objectID)
        box1 = wx.StaticBox(self, -1, name)
        sizer = wx.StaticBoxSizer(box1, wx.VERTICAL)
        self.userParams = {}
        sizer0 = wx.FlexGridSizer(rows=rows, cols=cols, vgap=vNum, hgap=hNum)
        sizer.Add(sizer0, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        
        for (widget, labeltxt, ToolTip, value) in tupleList:
            label = wx.StaticText(self, -1, labeltxt, style=wx.ALIGN_CENTER)
            sizer0.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
            label.SetFont(font)
            
            if widget == "observatoryName" or widget == "fileName":
                self.userParams[widget] = wx.TextCtrl(self, -1, value = value, size = (220,wx.DefaultSize.GetHeight()))
            elif not widget.find('rb') == 0:
                self.userParams[widget] = wx.TextCtrl(self, -1, value = value)

            if widget.find('rb') == 0:
                label1 = ToolTip
                label2 = value
                self.userParams[widget] = wx.RadioButton(self, label = label1, style = wx.RB_GROUP)
                sizer0.Add(self.userParams[widget], 0, wx.ALIGN_CENTRE|wx.ALL, 0)
                if secondButton == True:
                    self.userParams[widget+"1"] = wx.RadioButton(self, label = label2)
                    self.userParams[widget+"1"].SetValue(True)
                else:
                    self.userParams[widget+"1"] = wx.RadioButton(self, label = label2)
                    self.userParams[widget].SetValue(True)
                    
                sizer0.Add(self.userParams[widget+"1"], 0, wx.ALIGN_CENTRE|wx.ALL, 0)
            else:
                self.userParams[widget].SetToolTipString(ToolTip)
                sizer0.Add(self.userParams[widget], 0, wx.ALIGN_CENTRE|wx.ALL, 0)
             
            if widget == "ingress" or widget == "egress":
                value = "00:00:00"
                self.userParams[widget+"1"] = wx.TextCtrl(self, -1, value = value)
                self.userParams[widget+"1"].SetToolTipString(ToolTip)
                sizer0.Add(self.userParams[widget+"1"], 0, wx.ALIGN_CENTRE|wx.ALL, 0)
             
        self.SetSizer(sizer)
        sizer.Fit(self)

class AddLCB(wx.Panel):

    '''
    This creates the set of a label, control box, and button. Usually used to let a user
    browse and select a file.
    
    Parameters
    ----------
    parent : window
        The parent panel that this box will be associated with.
    
    objectID : int
        The identity number of the object.
        
    parent2 : window, optional
        Usually the parent is the panel that the LCB gets created in. If however, there is a need
        to use the actual parent frame, a second window is allowed to be linked.
    
    name : string, optional
        The name of the label for the static box. If the name is 'mainGUI' or 'planet' a different set gets
        created.
    
    buttonLabel : string, optional
        The name of the button that is created.
    
    multFiles : bool, optional
        If true, when browsing for files the user can select multiple ones. If false, only one file is
        allowed to be selected.
    
    rowNum : int, optional
        The number of rows for the box.
        
    colNum : int, optional
        The number of columns for the box.
    
    vNum : int, optional
        The vertical displacement between each text control.
    
    hNum : int, optional
        The horizontal displacement between each text control.
    
    font : wx.font(), optional
        The type of style you would like the text to be displayed as.
        
    updateRadii : bool, optional
        If true, this method will update the available aperture radii list for the drop down menu in the 
        parent frame.
    
    boxName : string, optional
        The name of the box for the current LCB set. It is displayed in the upper left hand corner. 
    
    height : int, optional
        The height of the control box.
    
    saveType : wx.FD_*, optional
        The style of the box that will appear. The * represents a wild card value for different types.
    '''
    
    def __init__(self, parent, objectID, parent2=None, name='', buttonLabel="Browse", multFiles=False, rowNum=1, colNum=3,
                 vNum=0, hNum=0, font=wx.NORMAL_FONT, updateRadii=False, boxName="", height=20, saveType=wx.FD_OPEN):
        
        wx.Panel.__init__(self,parent,objectID)
        box1 = wx.StaticBox(self, -1, boxName)
        box1.SetFont(font)
        sizer = wx.StaticBoxSizer(box1, wx.VERTICAL)
        self.parent = parent2
        self.messageFrame = False
        self.IP = wx.Frame
        self.boxList = {}
        self.buttonList = {}
        sizer0 = wx.FlexGridSizer(rows=rowNum, cols=colNum, vgap=vNum, hgap=hNum)
        sizer.Add(sizer0, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        iterationNumber = 0
        extraName = ""
        if name == "mainGUI":
            extraName = "mainGUI"
            name = "Path to Dark Frames: ,Path to Master Flat: ,Path to Data Images: ,Path to Regions File: ," + \
                    "Output Path: "
        for eachName in name.split(","):
            if sys.platform != "win32":
                if eachName == "Path to Dark Frames: " or eachName == "Path to Data Images: ":
                    height = 35
                else:
                    height = 25
            if eachName == "Path to Dark Frames: " or eachName == "Path to Data Images: " or eachName == "Path to "+\
                           "Regions File: ":
                if extraName == "mainGUI":
                    multFiles = True
                    saveType = None
            elif eachName == "Path to Master Flat: ":
                multFiles = False
                saveType = wx.FD_OPEN
            elif eachName == "Output Path: ":
                multFiles = False
                saveType = wx.FD_SAVE
            iterationNumber += 1
            if eachName == 'planet':
                self.label = wx.StaticText(self, -1, "Planet Name", style=wx.ALIGN_CENTER)
                self.label.SetFont(font)
                self.boxList[iterationNumber] = wx.TextCtrl(self, -1, value='GJ 1214 b', style=wx.TE_RICH)
                self.boxList[iterationNumber].SetToolTipString("Enter the name of a planet from the" +\
                                                          "exoplanet.org database here.")
            else:
                self.label = wx.StaticText(self, -1, eachName, style=wx.ALIGN_CENTER)
                self.label.SetFont(font)
                self.boxList[iterationNumber] = wx.TextCtrl(self, -1, size=(500,height), style=wx.TE_RICH)

            sizer0.Add(self.label, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
            sizer0.Add(self.boxList[iterationNumber], 0, wx.ALIGN_CENTRE|wx.ALL, 0)
            
            if eachName == 'planet':
                self.updateButton = wx.Button(self, -1, "Update Parameters")
                sizer0.Add(self.updateButton,0,wx.ALIGN_CENTER|wx.ALL,0)
            else:
                if sys.platform != 'win32':
                    if buttonLabel == "Browse\t (Cntrl-O)":
                        buttonLabel = "Browse\t("+u'\u2318'"-O)"
                    self.buttonList[iterationNumber] = wx.Button(self, -1, buttonLabel)
                else:
                    self.buttonList[iterationNumber] = wx.Button(self, -1, buttonLabel)
                self.buttonList[iterationNumber].Bind(wx.EVT_BUTTON, lambda event, lambdaIter = iterationNumber,
                                                      lambdaMult = multFiles, lambdaSave = saveType:
                self.browseButtonEvent(event, "Choose Path(s) to File(s)",self.boxList[lambdaIter], lambdaMult,
                                       lambdaSave, update=updateRadii))
                sizer0.Add(self.buttonList[iterationNumber],0,wx.ALIGN_CENTRE|wx.ALL,0)         
        self.SetSizer(sizer)
        sizer.Fit(self)

    def browseButtonEvent(self, event, message, textControl, fileDialog, saveDialog, update=False):
        
        '''
        This method defines the `browse` function for selecting a file on any OS.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        
        message : string
            The message that tells the user what to choose.
            
        textControl : wx.TextCtrl
            The box in the frame that will be refreshed with the files that are chosen by the user.
            
        fileDialog : bool
            If true, the style is wx.FD_MULTIPLE, otherwise it is the same as the `saveDialog`.
            
        saveDialog : wx.FD_*
            The style of the box that will appear. The * represents a wild card value for different types.
        
        update : bool, optional
            This will update the aperture radii list for a selected file in the parent frame if true.
        '''
        
        if not fileDialog:
            dlg = wx.FileDialog(self, message = message, style = saveDialog)
        else: 
            dlg = wx.FileDialog(self, message = message,  style = wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            if saveDialog == wx.SAVE:
                filenames = [dlg.GetPath()]
            else:
                filenames = dlg.GetPaths()
            textControl.Clear()
            for i in range(0,len(filenames)):
                if i != len(filenames)-1:
                    textControl.WriteText(filenames[i] + ',')
                else:
                    textControl.WriteText(filenames[i])
        
        if update == True:
            try:
                if self.parent.validityCheck(throwException = False):
                    self.parent.radiusList.Clear()
                    self.parent.data = IO.load(self.parent.box.boxList[1].GetValue())
                    self.parent.apertureRadii = np.empty_like(self.parent.data.apertureRadii)
                    self.parent.apertureRadii[:] = self.parent.data.apertureRadii
                    radiiString = [str(x) for x in self.parent.data.apertureRadii]
                    for string in radiiString:
                        self.parent.radiusList.Append(string)
                    self.parent.radiusList.SetValue(radiiString[0])
            except AttributeError:
                self.IP = InvalidParameter("", self, -1, stringVal="oldPKL") 
            
        dlg.Destroy()

class ScanParamsBox(wx.Panel):
    
    '''
    This is the box that is used in the GraphFrame class for an interactive light curve plot.
    '''
    
    def __init__(self,parent,objectID):
        
        '''
        This is the initialization of the box. It has four controls: bin size, title, x-axis label,
        and y-axis label.
        '''
        
        wx.Panel.__init__(self,parent,objectID)
        self.messageFrame = False
        self.IP = wx.Frame
        box1 = wx.StaticBox(self, -1, "Descriptive information")
        sizer = wx.StaticBoxSizer(box1, wx.VERTICAL)
        self.userinfo = {}
        sizer0 = wx.FlexGridSizer(rows=2, cols=4)
        sizer.Add(sizer0, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        for (widget,label,ToolTip) in [
            ('bin',"Bin Size:",
             'Enter a bin number here.'),
            ('title',"Title:",
             'Enter a name for the title here.'),
            ('xlabel',"X-Axis Name:",
             'Enter a name for the X-Axis here.'),
            ('ylabel',"Y-Axis Name:",
             'Enter a name for the Y-Axis here.')
            ]:
            label = wx.StaticText(self, -1, label, style=wx.ALIGN_CENTER)
            sizer0.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
            if widget == 'bin':
                self.userinfo[widget] = wx.TextCtrl(self, -1,value='10')
            elif widget == 'xlabel':
                self.userinfo[widget] = wx.TextCtrl(self, -1,value='Time (JD)')
            elif widget == 'ylabel':
                self.userinfo[widget] = wx.TextCtrl(self, -1,value='Relative Flux')
            elif widget == 'title':
                self.userinfo[widget] = wx.TextCtrl(self, -1,value='Light Curve')
            self.userinfo[widget].SetToolTipString(ToolTip)
            sizer0.Add(self.userinfo[widget], 0, wx.ALIGN_CENTRE|wx.ALL, 0)
        
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.oldNum = self.userinfo['bin'].GetValue()
        self.newNum = self.userinfo['bin'].GetValue()
        self.oldX = str(self.userinfo['xlabel'].GetValue())
        self.newX = str(self.userinfo['xlabel'].GetValue())
        self.oldY = str(self.userinfo['ylabel'].GetValue())
        self.newY = str(self.userinfo['ylabel'].GetValue())
        self.oldtitle = str(self.userinfo['title'].GetValue())
        self.newtitle = str(self.userinfo['title'].GetValue())
        self.max = 100
    
    def boxCorrect(self):
        
        '''
        This method checks to make sure that the user input for bin size is a number
        as well as greater than the miniumum bin size of 5. The maximum bin size depends
        on the light curve that was loaded. 
        '''
        
        if self.userinfo['bin'].GetValue() == '':
            self.IP = InvalidParameter(self.userinfo['bin'].GetValue(), self, -1, secondValue=str(self.max))
            return False
        else:
            try:
                self.var = int(self.userinfo['bin'].GetValue())
            except ValueError:
                self.IP = InvalidParameter(self.userinfo['bin'].GetValue(), self, -1, secondValue=str(self.max))
                return False
             
            if int(self.userinfo['bin'].GetValue()) <= 4 or int(self.userinfo['bin'].GetValue()) > self.max:
                self.IP = InvalidParameter(self.userinfo['bin'].GetValue(), self,-1, secondValue=str(self.max))
                return False
            else:
                return True

    def boxDiff(self):
        
        '''
        This method will determine if a new plot needs to be made or not.
        
        Returns
        -------
        literal : bool
            If true, one of the four parameters for this box was changed, and a new plot needs to be made. If
            no change has been made then it returns false.
        '''
        
        if not self.oldNum == self.newNum:
            self.oldNum = self.newNum
            return True
        elif not self.oldX == self.newX:
            self.oldX = self.newX
            return True
        elif not self.oldY == self.newY:
            self.oldY = self.newY
            return True
        elif not self.oldtitle == self.newtitle:
            self.oldtitle = self.newtitle
            return True
        else:
            return False
        
    def update(self):
        
        '''
        Before checking if a parameter has been changed using the above boxDiff() method, this method
        updates the current values of each control to be checked against the old values.
        '''
        
        self.newNum = self.userinfo['bin'].GetValue()
        self.newX = self.userinfo['xlabel'].GetValue()
        self.newY = self.userinfo['ylabel'].GetValue()
        self.newtitle = self.userinfo['title'].GetValue()
    
    def setMax(self, length):
        
        '''
        Sets the maximum bin size for the plot.
        
        Parameters
        ----------
        length : int
            Number for the max bin size.
        '''
        
        self.max = length

class InvalidParameter(wx.Frame):
    
    '''
    This class is universally used throughout the code to relay any pop-up messages
    to the user.
    '''

    def __init__(self, message, parent, objectID, stringVal='', secondValue='0', columns=2):
        
        '''
        This is the initialization of the popup message. It varies greatly depending on what
        the user needs to see.
        
        Parameters
        ----------
        message : string
            Usually the invalid value that was entered by the user somewhere. Left blank if
            instead of an error, a message just needs to be seen by the user.
        
        parent : window
            The parent class that this frame will open up from and is associated with.
        
        objectID : int
            The identity number of the object.
        
        stringVal : string, optional
            This is the string that is used to determine what type of message will appear in the frame
            that pops up.
        
        secondValue : string, optional
            If a second value needs to be displayed besides `message`, this is where it is entered.
            
        columns : int, optional
            The number of columns that this frame will have.
            
        Notes
        -----
        There is no return, but on successful completion of initialization a window will pop up
        with a message for the user.
        '''

        if sys.platform == "win32":
            wx.Frame.__init__(self, parent, objectID, 'Invalid Parameter', size = (500,110))
        else:
            wx.Frame.__init__(self, parent, objectID, 'Invalid Parameter', size = (500,100))
            self.create_menu()
            self.Bind(wx.EVT_CHAR_HOOK, self.onCharOkay)   
        
        self.parent = parent
        if self.parent.messageFrame == True:
            pass
        else:
            self.parent.messageFrame = True
            if stringVal == "params":
                self.SetTitle("Updated Parameters")
                self.Bind(wx.EVT_CHAR_HOOK, self.onOkay)
            elif stringVal == "ds9":
                self.SetTitle("DS9 Error")
            elif stringVal == "fitOpen":
                self.SetTitle("Fitting Frame Open Error")
            elif stringVal == "warnError":
                self.SetTitle("Warning about local times!")
            elif stringVal == "regionsUpdate":
                self.SetTitle("Regions File Set Added!")
            elif stringVal == "setExists":
                self.SetTitle("Set Exists!")
    
            self.panel = wx.Panel(self)
            self.string = "invalid"
            
            if secondValue != '0':
                self.string = "The bin size must be between 5 and "+ secondValue +"."
            if stringVal == "Rp/Rs":
                self.string = "The value for Rp over Rs must be between 0 and 1."
            elif stringVal == "a/Rs":
                self.string = "The value for A over Rs must be greater than 1."
            elif stringVal == "inc":
                self.string = "The value for the inclincation must be between 0 and 90."
            elif stringVal == "t0":
                self.string = "The value for the mid-transit time, t0, must be greater than 0."
            elif stringVal == "gamma1":
                self.string = "The value entered for gamma1 must be a number."
            elif stringVal == "gamma2":
                self.string = "The value entered for gamma2 must be a number."
            elif stringVal == "gamma":
                self.string = "The value for Gamma1 + Gamma2 must be less than or equal to 1."
            elif stringVal == "per":
                self.string = "The value for the period must be greater than 0."
            elif stringVal == "ecc":
                self.string = "The value for the eccentricity must be between 0 and 1."
            elif stringVal == "pericenter":
                self.string = "The value for the pericenter must be greater than or equal to 0."
            elif stringVal == "planet":
                self.string = "The name of the planet does not exist in the database."
            elif stringVal == "limbdark":
                self.string = "The parameter for Limb-Darkening must be either 'False', 'linear', or 'quadratic'."
            elif stringVal == "saveiteration":
                self.string = "The iterative step to be saved must be greater than or equal to 5."
            elif stringVal == "acceptance":
                self.string = "The acceptance rate must be greater than 0."
            elif stringVal == "burnfrac":
                self.string = "The burn number must be greater than 0 and less than or equal to 1."
            elif stringVal == "number":
                self.string = "The number of total steps must be greater than or equal to 10."
            elif stringVal == "mod":
                self.string = "The iterative step to be saved cannot be greater than the total number of steps."
            elif stringVal == "flat1":
                self.string = "The path(s) to flat images must be fixed."
            elif stringVal == "flat2":
                self.string = "The path(s) to dark flat images must be fixed."
            elif stringVal == "flat3":
                self.string = "The path to save the master flat must be fixed."
            elif stringVal == "fits":
                self.string = "One or more of the files in " + secondValue + " need to be fixed."
            elif stringVal == "master":
                self.string = "Either more than one file has been entered, or the file entered needs to be fixed in the " + \
                              secondValue + "."
            elif stringVal == "output":
                self.string = "Either you entered a directory, or the specified path cannot be made for the " + secondValue + \
                              "."
            elif stringVal == "leftbox":
                self.string = "Please enter a number for the " + secondValue + "."
            elif stringVal == "dateTime":
                self.string = "Please check the format and values entered for the ingress or egress " + secondValue + ".\n"
                if secondValue == "date":
                    self.string += "The year must be within 100 years of today, the month must be between 1 and 12\nand" +\
                                   " the day must be between 1 and 31."
                elif secondValue == "time":
                    self.string += "The hour must be between 0 and 23, while both the minutes and seconds must be between"+\
                                  " 0 and 59.\nThe format is hh:mm:ss."
            elif stringVal == "obsName" or stringVal == "obsFile":
                self.string = "The observatory name or file name must be fixed."
            elif stringVal == "logicalDate":
                self.string = "The starting date must come before the ending date."
            elif stringVal == "logicalTime":
                self.string = "The starting time must come before the ending time when the dates are equal."
            elif stringVal == "obsDate":
                self.string = "The starting date and ending date both need to be in the format YYYY/MM/DD with integers."
            elif stringVal == "dateRange":
                self.string = "The year must be within 100 years of today, the month must be between 1 and 12,\nand the"+\
                              " day must be between 1 and 31."
            elif stringVal == "coordRange":
                self.string = "The latitude must be between 90 and -90 degrees, while the longitude must be \nbetween "+\
                              "0 and 180 degrees. Both must have min and sec in between 0 and 59."
            elif stringVal == "coordTime":
                self.string = "The longitude and latitude must be in the format Deg:Min:Sec with numbers."
            elif stringVal == "tempElevNum":
                if secondValue == "apparent magnitude upper limit":
                    self.string = "The " + secondValue + " must be a number."
                else:
                    self.string = "The " + secondValue + " must be a number greater than or equal to 0."
            elif stringVal == "twilight":
                self.string = "The twilight must be -6, -12, or -18. Please select one from the drop down menu."
            elif stringVal == "lowerElevation":
                self.string = "The lower elevation limist needs to be in the format Deg:Min:Sec, "+\
                              "with min and sec\nbetween 0 and 59. The degrees must be between 0 and 90."
            elif stringVal == "radiusNum":
                self.string = "The aperture radii values must be numbers."
            elif stringVal == "radiusEqual":
                self.string = "The min and max aperture radii cannot be equal."
            elif stringVal == "radiusStep":
                self.string = "The aperture radii step size cannot be smaller than the difference between the maximum\n" + \
                              "radius and the minimum radius. The format for this is \"min, max, stepsize\"."
            elif stringVal == "radiusLogic":
                self.string = "The minimum aperture radius must be smaller than the maximum. None of the 3 parameters\n" + \
                              "can be equal to 0."
            elif stringVal == "radiusLogic2":
                self.string = "None of the aperture radii can be equal to 0."
            elif stringVal == "radiusError":
                self.string = "The radius you entered was empty or not a number. Please enter a valid number."
            elif stringVal == "radiusListError":
                if secondValue == "etdError":
                    self.string = "The conversion method here depends on the aperture radii list from the .pkl file. You\n" + \
                                  "must update the radii list to continue."
                else:
                    self.string = "The plotting methods rely on the aperture radii list from the .pkl file. You\n" + \
                                  "must update the radii list to continue."
            elif stringVal == "radiusListError2":
                self.string = "The radius you entered was not in the aperture radii list for this .pkl file.\n" + \
                              "Please pick a radius from the approved radii in the drop down menu."
            elif stringVal == "utZone":
                self.string = "The time zone must be between -12 and 12. Please choose one from the drop down menu."
            elif stringVal == "regionsError1":
                self.string = "Either the regions file or reference file for this set is empty. You cannot add an " + \
                              "extra\nregions file without a referenced data image."
            elif stringVal == "regionsError2":
                self.string = "You have entered a filename that does not exist or more than one file. There can " + \
                              "only be one regions file\nand one reference file entered at a time for a set."
            elif stringVal == "regionsError3":
                self.string = "The regions file must be a valid .reg file."
            elif stringVal == "regionsError4":
                self.string = "The reference file must be a valid .fits or .fit file."
            elif stringVal == "emptyReg":
                self.string = "You must enter a regions file. If you wish you can enter additional sets of regions " + \
                              "files\nafter at least one has been entered."
            elif stringVal == "invalidReg":
                self.string = "This regions file was not found, or is not a vaild .reg file."
            elif stringVal == "invalidRef":
                self.string = "This reference file was not found, or is not a valid .fits or .fit file."
            elif stringVal == "invalidRefExist":
                self.string = "This reference file was not found in the list of data images. Please add it to the list of" + \
                              "data images and try again."
            elif stringVal == "outofbounds":
                self.string = "You must enter extra regions files as sets with a reference file. The format is " + \
                              "\"regionsFiles,referenceFile;\"."
            elif stringVal == "referenceImageDup":
                self.string = "The reference image you have listed in this set is already assigned to another regions file."
            elif stringVal == "emptyKeyword":
                self.string = "The exposure time keyword cannot be empty. Please use a valid phrase, or choose from " + \
                              "the drop down menu."
            elif stringVal == "invalidKeyword":
                self.string = "The keyword you entered was not found in the header of the first data image."
            elif stringVal == "emailKeyword":
                self.string = "This keyword is in the header file of the first data image, but is not something we " + \
                              "have a conversion method for.\nPlease email us the keyword you are trying to use and we " + \
                              "will include it into our list of possible keywords."
            elif stringVal == "saveLocation":
                self.string = "Either you entered a directory, or the specified path cannot be made to save the results " + \
                              "of MCMC in a text file."
            elif stringVal == "regionsDup":
                self.string = "The regions file that you have entered is already assigned to another reference image."
            
            self.okButton = wx.Button(self.panel,label = "Okay", pos = (125,30))
            self.Bind(wx.EVT_BUTTON, self.onOkay, self.okButton)
            
            if stringVal == "path":
                self.text = wx.StaticText(self.panel, -1, "The following is an invalid output path: " + message)
            elif stringVal == "params":
                self.text = wx.StaticText(self.panel, -1, "The appropriate parameters have been updated.")
            elif stringVal == "ds9":
                self.Bind(wx.EVT_WINDOW_DESTROY, self.ds9Error)
                self.text = wx.StaticText(self.panel, -1, 
                                           "It seems that ds9 may not have installed correctly, please try again.")
            elif stringVal == "importError":
                self.text = wx.StaticText(self.panel, -1, "Failed to import ephem, please try again.")
            elif stringVal == "fitOpen":
                self.Bind(wx.EVT_WINDOW_DESTROY, self.fitError)
                self.text = wx.StaticText(self.panel, -1, "Please close the fitting frame window and try again.")
            elif stringVal == "warnError":
                self.Bind(wx.EVT_WINDOW_DESTROY, self.parent.calculate)
                self.text = wx.StaticText(self.panel, -1, "Please be careful. The local times are calculated using " + \
                                          "PyEphem's ephem.localtime(\"input\") method. Make sure\nthat this method " + \
                                          "produces the correct local time for yourself. If you don't know how to check " + \
                                          "this, please refer\nto the documentation from the help menu in the main frame. " + \
                                          "This message is shown once per GUI session,\nand will run the calculations " + \
                                          "for the current parameters as soon as you close this window.")
            elif stringVal == "oldPKL":
                self.text = wx.StaticText(self.panel, -1, "This seems to be an outdated .pkl file, sorry. Try creating" + \
                                          " a new .pkl file from the main frame and try again.\nIf this .pkl file is" + \
                                          " important and cannot be recreated, talk to our developers for information on" + \
                                          " how to extract \nthe data from the file.")
            elif stringVal == "regionsUpdate":
                self.text = wx.StaticText(self.panel, -1, "This set has been added to the list of regions sets "+ \
                                          "in the main GUI.")
            elif stringVal == "setExists":
                self.text = wx.StaticText(self.panel, -1, "The set you are trying to add is already there! " + \
                                          "Please add a different set.")
            elif stringVal == "upToDate":
                self.Title = "Up To Date"
                self.text = wx.StaticText(self.panel, -1, "The version of " \
                                          "OSCAAR that you have is currently " \
                                          "up to date!\n\nYour version is from "\
                                          "commit: \n" + oscaar.__sha__ )
            elif stringVal == "newCommit":
                self.Title = "New Commit Available!"
                self.text = wx.StaticText(self.panel, -1, "The current vers" \
                                          "ion that you have is out of date. " \
                                          "Please visit our GitHub page at "\
                                          "\n http://www.github.com/OSCAAR/"\
                                          "OSCAAR\nand retrieve the latest "\
                                          "commit.\n\nYour version is from "\
                                          "commit: \n" + oscaar.__sha__)
            elif stringVal == "installAgain":
                self.Title = "Error"
                self.text = wx.StaticText(self.panel, -1, "There seems to be an outdated __init__ file. Please"\

                                          " reinstall OSCAAR to use this update function.")

            elif stringVal == "noInternetConnection":
                self.Title = "Error"
                self.text = wx.StaticText(self.panel, -1, "An internet"\
                            " connection is needed to access this function, "\
                            "no connection is detected. Please check your "\
                            "connection and try again.")
            
            elif stringVal == "successfulConversion":
                self.Title = "Conversion Completed"
                self.text = wx.StaticText(self.panel, -1, "A file that the Czech ETD will accept has been created!")
            else:
                self.text = wx.StaticText(self.panel, -1, self.string +"\nThe following is invalid: " + message)
            
            self.sizer0 = wx.FlexGridSizer(rows=2, cols=columns) 
            self.hbox = wx.BoxSizer(wx.HORIZONTAL)
            self.hbox.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)
            self.sizer0.Add(self.text,0,wx.ALIGN_CENTER|wx.ALL,5)
            self.sizer0.Add(self.okButton,0,wx.ALIGN_CENTER|wx.ALL,5)
            
            self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
            self.panel.SetSizer(self.hbox)
            self.hbox.Fit(self)
            self.Center()
            self.Show()

    def ds9Error(self, event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.ds9Open = False

    def fitError(self, event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.loadFitError = False

    def create_menu(self):
        
        '''
        This method creates the menu bars that are at the top of the InvalidParameter frame.
        
        Notes
        -----
        This method has no input or return parameters. It will simply be used as self.create_menu()
        when in the initialization method for an instance of this frame.
        '''
        
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_exit = menu_file.Append(-1, "Exit", "Exit")
        self.Bind(wx.EVT_MENU, self.onOkay, m_exit)
        
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)
    
    def onCharOkay(self,event):
        
        '''
        This method allows for users on a Mac to close the InvalidParameter frame by just pressing the
        enter key when it pops up.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.keycode = event.GetKeyCode()
        if self.keycode == wx.WXK_RETURN:
            self.Destroy()
    
    def onOkay(self, event):
        
        '''
        This method defines the action quit from the menu. It closes the frame. In this class it also
        defines what happens when the user clicks the ok button.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.Destroy()
    
    def onDestroy(self, event):
        
        '''
        Whenever this frame is closed, this secondary method updates a variable in the parent
        class to make sure that it knows there is no active instance of this frame.
        
        Parameters
        ----------
        event : wx.EVT_*
            A wxPython event that allows the activation of this method. The * represents a wild card value.
        '''
        
        self.parent.messageFrame = False


def checkParams(self, tupleList):
    
    '''
    This method checks to make sure that all of the parameters and values that are in
    `tupleList` are valid for the MCMC and LeastSquaresFit classes.
    
    Parameters
    ----------
    tupleList : array
        The input is an array of tuples in the form: (int,string).
    
    Returns
    -------
    literal : bool
        True if all of the parameters required to run MCMC or LeastSquaresFit are valid,
        false otherwise.
    '''
    
    self.tempGamma1 = -1
    self.tempGamma2 = -1
    self.tempSaveIteration = -1
    self.tempNumber = -1
    
    for (number,string) in tupleList:
        if number == '':
            self.IP = InvalidParameter(number, self,-1, stringVal=string)
            return False
        else:
            try:
                if string !="limbdark":
                    self.tmp = float(number)
            except ValueError:
                self.IP = InvalidParameter(number, self,-1, stringVal=string)
                return False
            if string == "Rp/Rs":
                if float(number)>1 or float(number)<0:
                    self.IP = InvalidParameter(number, self,-1, stringVal=string)
                    return False
            if string == "a/Rs":
                if float(number) <= 1:
                    self.IP = InvalidParameter(number, self,-1, stringVal=string)
                    return False
            if string == "per":
                if float(number) < 0:
                    self.IP = InvalidParameter(number, self,-1, stringVal=string)
                    return False
            if string == "inc":
                if float(number) < 0 or float(number) > 90:
                    self.IP = InvalidParameter(number, self,-1, stringVal=string)
                    return False
            if string == "t0":
                if float(number) < 0:
                    self.IP = InvalidParameter(number, self,-1, stringVal=string)
                    return False
            if string == "ecc":
                if float(number) < 0 or float(number) > 1:
                    self.IP = InvalidParameter(number, self,-1, stringVal=string)
                    return False
            if string == "pericenter":
                if float(number) < 0:
                    self.IP = InvalidParameter(number, self,-1, stringVal=string)
                    return False
            if string == "limbdark":
                if (number != "False"):
                    if (number != "linear"):
                        if(number != "quadratic"):
                            self.IP = InvalidParameter(number,self,-1,stringVal=string)
                            return False
            if string == 'gamma1':
                self.tempGamma1 = number
            if string == 'gamma2':
                self.tempGamma2 = number
            if string == "saveiteration":
                self.tempSaveIteration = float(number)
                if float(number) < 5:
                    self.IP = InvalidParameter(number,self,-1,stringVal=string)
                    return False
            if string == "number":
                self.tempNumber = float(number)
                if float(number) < 10:
                    self.IP = InvalidParameter(number,self,-1,stringVal=string)
                    return False
            if string == "acceptance":
                if float(number) <= 0:
                    self.IP = InvalidParameter(number,self,-1,stringVal=string)
                    return False
            if string == "burnfrac":
                if float(number) > 1 or float(number) <= 0:
                    self.IP = InvalidParameter(number,self,-1,stringVal=string)
                    return False
    
    if(self.tempNumber != -1) and (self.tempSaveIteration != -1):
        if (self.tempNumber % self.tempSaveIteration) != 0:
            tempString = str(self.tempSaveIteration)+" < "+str(self.tempNumber)
            self.IP = InvalidParameter(tempString,self,-1,stringVal="mod")
            return False
    
    self.totalGamma = float(self.tempGamma1) + float(self.tempGamma2)
    self.totalString = str(self.totalGamma)
    if self.totalGamma > 1:
        self.IP = InvalidParameter(self.totalString, self,-1, stringVal="gamma")
        return False

    return True

###################
#This Runs The GUI#
###################


def main():

    '''
    This allows oscaarGUI to be imported without
    automatically opening the frame every time.
    '''

    pass

if __name__ == "oscaar.oscaarGUI" or __name__ == "__main__":

    '''
    If oscaarGUI is imported through oscaar, or if it is run
    as a standalone program, the frame will open.
    '''

    app = wx.App(False)
    OscaarFrame(parent=None, objectID=-1)
    app.MainLoop()
    main()
