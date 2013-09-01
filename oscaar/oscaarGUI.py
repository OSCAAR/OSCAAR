import threading
import sys
if not hasattr(sys, 'real_prefix'):
    import wx
import os
from glob import glob
from time import strftime
import datetime
import webbrowser
import subprocess
import shutil
import zipfile

from mathMethods import medianBin
import random
import oscaar
#import transiterFit
import systematics
import IO
from matplotlib import pyplot
import matplotlib
from oscaar.extras.knownSystemParameters import returnSystemParams
from matplotlib.figure import Figure
if not hasattr(sys, 'real_prefix'):
    from matplotlib.backends.backend_wxagg import \
        FigureCanvasWxAgg as FigCanvas, \
        NavigationToolbar2WxAgg as NavigationToolbar
import numpy as np
import pylab
import pyfits
import timeConversions

APP_EXIT = 1

class OscaarFrame(wx.Frame): ##Defined a class extending wx.Frame for the GUI
    
    def __init__(self):
        
        self.aboutOpen = False
        self.loadOldPklOpen = False
        self.loadFittingOpen = False
        self.loadMasterFlat = False
        self.overWrite = False
        self.ds9Open = False
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
        wx.Frame.__init__(self,None,-1, self.title)
        self.panel = wx.Panel(self)
                
        if sys.platform == "win32":
            self.fontType = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        else: 
            self.fontType = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        
        self.static_bitmap = wx.StaticBitmap(self.panel)
        self.logo = wx.Image(os.path.join(os.path.dirname(__file__),'images','logo4.png'), wx.BITMAP_TYPE_ANY)
        self.bitmap = wx.BitmapFromImage(self.logo)
        self.static_bitmap.SetBitmap(self.bitmap)
        
        self.paths = AddLCB(self.panel, -1, name="mainGUI", str="Browse", rowNum=5, vNum=15, hNum=5, font=self.fontType)
        self.topBox = wx.BoxSizer(wx.HORIZONTAL)
        self.topBox.Add(self.paths, border = 5, flag = wx.ALL)

        list = [('zoom',"Track Zoom: ",
                 'Enter a number for the zoom here.','15'),
                ('radius',"Aperture Radius: ",
                 'Enter a decimal for the radius here.','4.5'),
                ('smoothing',"Smoothing Constant: ", 
                 'Enter an integer for smoothing here.','3')]
        
        self.leftBox = ParameterBox(self.panel, -1, list, rows=5, cols=2, vNum=10, hNum=10, font=self.fontType)    
        
        list = [('ingress',"Ingress, UT (YYYY/MM/DD)",
                 "Enter a date in the correct format here.","YYYY/MM/DD"),
                ('egress',"Egress, UT (YYYY/MM/DD)",
                 "Enter a date in the correct format here.","YYYY/MM/DD"),
                ('trackPlot',"Tracking Plots: ","none",''),
                ('photPlot',"Photometry Plots: ","none",''),
                ('flatType',"Fit After Photometry ","On","Off")]

        self.radioBox = ParameterBox(self.panel, -1, list, rows=5, cols=3, vNum=10, hNum=10, font=self.fontType)
        
        self.sizer0 = wx.FlexGridSizer(rows=1, cols=4)
        self.buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        self.buttonBox.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)
        self.ephButton = wx.Button(self.panel, label="Ephemeris")
        self.masterFlatButton = wx.Button(self.panel, label = "Master Flat Maker")
        self.ds9Button = wx.Button(self.panel, label = "Open DS9")
        self.runButton = wx.Button(self.panel, label = "Run")
        self.observatoryButton = wx.Button(self.panel, label = "Extra Observatory Parameters")
        
        self.Bind(wx.EVT_BUTTON, lambda evt: self.singularExistance(evt, self.loadEphFrame, "ephemeris"), self.ephButton)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.singularExistance(evt, self.loadMasterFlat, "masterFlat"),
                  self.masterFlatButton)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.singularExistance(evt, self.ds9Open, "ds9"), self.ds9Button)
        self.Bind(wx.EVT_BUTTON, self.runOscaar, self.runButton)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.singularExistance(evt, self.loadObservatoryFrame, "observatory"),
                  self.observatoryButton)
        self.sizer0.Add(self.ephButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.masterFlatButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.ds9Button,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.runButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        
        self.rightBox = wx.BoxSizer(wx.VERTICAL)
        self.rightBox.Add(self.radioBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.rightBox.Add(self.buttonBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.leftBox2 = wx.BoxSizer(wx.VERTICAL)
        self.leftBox2.Add(self.leftBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.leftBox2.Add(self.observatoryButton, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)

        self.bottomBox = wx.BoxSizer(wx.HORIZONTAL)
        self.bottomBox.Add(self.leftBox2, 0, flag = wx.ALIGN_CENTER)
        self.bottomBox.Add(self.rightBox, 0, flag = wx.ALIGN_CENTER|wx.ALL, border =5)
        
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.static_bitmap,0,flag = wx.ALIGN_LEFT)
        self.vbox.Add(self.topBox, 0, flag = wx.ALIGN_CENTER)
        self.vbox.Add(self.bottomBox, 0, flag = wx.CENTER | wx.ALL, border = 5)
        self.create_menu()
        self.CreateStatusBar()
        self.vbox.AddSpacer(10)
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        
        self.setDefaults()
        
        iconloc = os.path.join(os.path.dirname(__file__),'images','logo4noText.ico')
        icon1 = wx.Icon(iconloc, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon1)       
        
        self.Center()
        self.Show()
        
    def create_menu(self):
    
        # These commands create the menu bars that are at the top of the GUI.
    
        menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_quit = menu_file.Append(wx.ID_EXIT, "Quit\tCtrl+Q", "Quit this application.")
        self.Bind(wx.EVT_MENU, self.on_exit, m_quit)
        
        menu_help = wx.Menu()
        m_help = menu_help.Append(wx.ID_HELP, "Help\tCtrl+H", "More Information about how to use this application.")
        self.Bind(wx.EVT_MENU, lambda evt: self.openLink(evt, 
                  "https://github.com/OSCAAR/OSCAAR/tree/master/docs/documentationInProgress"),
                  m_help)
        
        menu_oscaar = wx.Menu()
        m_ttp = menu_oscaar.Append(-1, "Transit Time Predictions", 
                                      "Transit time predictions from the Czech Astronomical Society.")
        m_about = menu_oscaar.Append(-1, "About", "Contributors of OSCAAR.")
        m_loadOld = menu_oscaar.Append(-1, "Load old output\tCtrl+L", "Load an old output file for further analysis.")
        m_loadFitting = menu_oscaar.Append(-1, "Fitting Routines\tCtrl-F", 
                                              "Different fitting methods for analysis of an old .pkl file.")
        m_extraRegions = menu_oscaar.Append(-1, "Extra Regions File Sets", 
                                            "Add extra regions files to specific referenced images.")
        
        self.Bind(wx.EVT_MENU, lambda evt: self.openLink(evt, "http://var2.astro.cz/ETD/predictions.php"), m_ttp)
        self.Bind(wx.EVT_MENU, lambda evt: self.singularExistance(evt, self.aboutOpen, "about"), m_about)
        self.Bind(wx.EVT_MENU, lambda evt: self.singularExistance(evt, self.loadOldPklOpen, "loadOld"), m_loadOld)
        self.Bind(wx.EVT_MENU, lambda evt: self.singularExistance(evt, self.loadFittingOpen, "loadFitting"), m_loadFitting)
        self.Bind(wx.EVT_MENU, lambda evt: self.singularExistance(evt, self.extraRegionsOpen, "extra"), m_extraRegions)
        menubar.Append(menu_file, "File")
        menubar.Append(menu_help, "Help")
        menubar.Append(menu_oscaar, "Oscaar")
        self.SetMenuBar(menubar)       

    def runOscaar(self, event):
        self.values = {}
#         notes = open(os.path.join(os.path.dirname(__file__),'outputs','notes.txt'), 'w')
#         notes.write('\n\n\n------------------------------------------'+\
#                     '\nRun initiated (LT): '+strftime("%a, %d %b %Y %H:%M:%S"))
#         if self.leftBox.userParams['notes'].GetValue() == 'Enter notes to be saved here.':
#             notes.write('\nNo notes entered.')
#         else:
#             notes.write('\nNotes: '+ self.leftBox.userParams['notes'].GetValue())
#         notes.close()
        
        invalidDarkFrames = self.checkFileInputs(self.paths.boxList[1].GetValue(), saveNum=1)
        masterFlat = self.paths.boxList[2].GetValue().strip()
        invalidDataImages = self.checkFileInputs(self.paths.boxList[3].GetValue(), saveNum=3)
        regionsFile = self.paths.boxList[4].GetValue().strip()
        self.outputFile = self.paths.boxList[5].GetValue().strip()
        self.values["radius"] = self.leftBox.userParams["radius"].GetValue()
        self.radiusError = "radius"
        
        if invalidDarkFrames != "": 
            InvalidParameter(invalidDarkFrames, None, -1, str="fits", max="the path to Dark Frames")
        elif os.path.isfile(masterFlat) != True or (masterFlat.lower().endswith(".fit") != True and \
             masterFlat.lower().endswith(".fits") != True) :
            tempString = masterFlat
            if len(masterFlat.split(",")) > 1:
                tempString = ""
                for string in masterFlat.split(","):
                    if string == "" and len(masterFlat.split(",")) == 2:
                        tempString += ","
                    else:
                        tempString += "\n" + string.strip()
            InvalidParameter(tempString, None, -1, str="master", max="path to the Master Flat")
        elif invalidDataImages != "":
            InvalidParameter(invalidDataImages, None, -1, str="fits", max="the path to Data Images")
#         elif os.path.isfile(regionsFile) != True or regionsFile.endswith(".reg") != True:
#             tempString = regionsFile
#             if len(regionsFile.split(",")) > 1:
#                 tempString = ""
#                 for string in regionsFile.split(","):
#                     if string == "" and len(regionsFile.split(",")) == 2:
#                         tempString += ","
#                     else:
#                         tempString += "\n" + string.strip()
        elif self.checkRegionsBox(regionsFile) == False:  
            pass
#             InvalidParameter(regionsFile, None, -1, str="master", max="path to Regions File")
        elif not os.path.isdir(self.outputFile.rpartition(str(os.sep))[0]) or \
             not len(self.outputFile) > (len(self.outputFile[:self.outputFile.rfind(os.sep)]) + 1):
            InvalidParameter(self.outputFile, None, -1, str="output", max="output file")
        elif self.checkAperture(self.values["radius"]) != True:
            InvalidParameter(self.leftBox.userParams["radius"].GetValue(), self, -1, str = self.radiusError)
        elif self.timeAndDateCheck(self.radioBox.userParams['ingress1'].GetValue(),
                                   self.radioBox.userParams['egress1'].GetValue(),
                                   self.radioBox.userParams['ingress'].GetValue(),
                                   self.radioBox.userParams['egress'].GetValue()) == True:
            try:
                list = ["smoothing", "zoom"]
                for string in list:
                    self.values[string] = int(self.leftBox.userParams[string].GetValue())
                    self.leftBox.userParams[string].SetValue(str(self.values[string]))

                self.paths.boxList[2].SetValue(masterFlat)
#                 self.paths.boxList[4].SetValue(regionsFile)
                self.paths.boxList[5].SetValue(self.outputFile)
                
                # This code here writes all the parameters to the init.par file.
                
                init = open(os.path.join(os.path.dirname(__file__),'init.par'), 'w')
                init.write("Path to Dark Frames: " + self.paths.boxList[1].GetValue() + "\n")
                init.write("Path to data images: " + self.paths.boxList[3].GetValue() + "\n")
                init.write("Path to Master-Flat Frame: " + self.paths.boxList[2].GetValue() + "\n")
                init.write("Path to regions file: " + self.paths.boxList[4].GetValue() + "\n")
                if not self.paths.boxList[5].GetValue().lower().endswith(".pkl"):
                    init.write("Output Path: " + self.paths.boxList[5].GetValue() + ".pkl\n")
                else:
                    init.write("Output Path: " + self.paths.boxList[5].GetValue() + "\n")
        
                self.parseTime(self.radioBox.userParams["ingress"].GetValue(),
                               self.radioBox.userParams["ingress1"].GetValue(), 'Ingress: ',  init, name="ingress")
                self.parseTime(self.radioBox.userParams["egress"].GetValue(),
                               self.radioBox.userParams["egress1"].GetValue(), 'Egress: ',  init, name="egress")
                if self.radioBox.userParams['trackPlot'].GetValue():
                    init.write("Plot Tracking: " + "on"+ "\n")
                else:
                    init.write("Plot Tracking: " + "off"+ "\n")
                if self.radioBox.userParams['photPlot'].GetValue():
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
                        if self.radioBox.userParams["flatType"].GetValue() == True:
                            wx.CallAfter(self.createFrame)

                else:
                    if self.loadFitError == False:
                        InvalidParameter("", self, -1, str="fitOpen")
                        self.loadFitError = True
            except ValueError:
                string2 = string
                if string2 == "smoothing":
                    string2 = "smoothing constant"
                InvalidParameter(self.leftBox.userParams[string].GetValue(),None,-1, str="leftbox", max=string2)
    
    def timeAndDateCheck(self, time1, time2, date1, date2):
        
        years = []
        months = []
        days = []
        hours = []
        minutes = []
        seconds = []
        
        for timeArray, value in [(time1.split(":"), time1),
                                 (time2.split(":"), time2)]:
            if len(timeArray) != 3:
                InvalidParameter(value, self, -1, str="dateTime", max = "time")
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
                        InvalidParameter(value, None, -1, str = "dateTime", max = "time")
                        return False
                    
                    if hour > 23 or hour < 0 or minute > 59 or minute < 0 or second > 59 or second < 0:
                        InvalidParameter(value, None, -1, str = "dateTime", max = "time")
                        return False
                    
                except ValueError:
                    InvalidParameter(value, self, -1, str = "dateTime", max = "time")
                    return False
                
        for dateArray,value in [(date1.split("/"),date1),
                                (date2.split("/"),date2)]:
            if len(dateArray) != 3:
                InvalidParameter(value, self, -1, str="dateTime", max = "date")
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
                        InvalidParameter(value, self, -1, str="dateTime", max = "date")
                        return False
                    minYear = datetime.date.today().year - 100
                    maxYear = datetime.date.today().year + 100
                    if year < minYear or year > maxYear or month > 12 or month < 0 or day > 31 or day < 0 or \
                       month == 0 or year == 0 or day == 0:
                        InvalidParameter(value, self, -1, str="dateTime", max = "date")
                        return False
                except ValueError:
                    InvalidParameter(value, self, -1, str="dateTime", max = "date")
                    return False

        if years[0] > years[1]:
            InvalidParameter(date1, self, -1, str = "logicalDate")
            return False
        elif years[0] == years[1]:
            if months[0] > months[1]:
                InvalidParameter(date1, self, -1, str = "logicalDate")
                return False
            elif months[0] == months[1]:
                if days[0] > days[1]:
                    InvalidParameter(date1, self, -1, str = "logicalDate")
                    return False
                elif days[0] == days[1]:
                    if hours[0] > hours[1]:
                        InvalidParameter(time1, self, -1, str = "logicalTime")
                        return False
                    elif hours[0] == hours[1]:
                        if minutes[0] > minutes[1]:
                            InvalidParameter(time1, self, -1, str = "logicalTime")
                            return False
                        elif minutes[0] == minutes[1]:
                            if seconds[0] >= seconds [1]:
                                InvalidParameter(time1, self, -1, str = "logicalTime")
                                return False
        return True
    
    def checkAperture(self, stringVal):
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
            min = splitString[0].strip()
            max = splitString[1].strip()
            stepSize = splitString[2].strip()
            try:
                min = float(min)
                max = float(max)
                stepSize = float(stepSize)
                if min == max:
                    self.radiusError = "radiusEqual"
                    return False
                elif min > max:
                    self.radiusError = "radiusLogic"
                    return False
                elif (max-min) < stepSize:
                    self.radiusError = "radiusStep"
                    return False
                
                if stepSize == 0:
                    self.radiusError = "radiusLogic"
                    return False
                elif min == 0 or max == 0:
                    self.radiusError = "radiusLogic"
                    return False
                self.values["radius"] = str(min) + "," + str(max) + "," + str(stepSize)
                self.leftBox.userParams["radius"].SetValue(str(min) + "," + str(max) + "," + str(stepSize))
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
                list = [("Path to Master-Flat Frame", 2),
                        ("Path to regions file", 4),
                        ("Ingress", "ingress"),("Egress", "egress"),
                        ("Radius", "radius"),("Tracking Zoom", "zoom"),
                        ("Plot Tracking", "trackPlot"),
                        ("Plot Photometry", "photPlot"),("Smoothing Constant", "smoothing"),
                        ("Output Path",5),("Path to Dark Frames", 1),("Path to data images", 3),
                        ("CCD Gain",""),("Exposure Time Keyword","")]
                
                for string,save in list:
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
                        elif name == "Path to Dark Frames" or name == "Path to data images":
                            tempArray = value.split(",")
                            tempArray[:] = [x.strip() for x in tempArray]
                            finalString = ""
                            for eachString in tempArray:
                                finalString += eachString + ","
                            self.paths.boxList[save].SetValue(finalString.rpartition(",")[0])
                        elif name == "Path to Master-Flat Frame" or name == "Path to regions file" or\
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
        setValueString = ""
        tempString = ""
        if boxValue == "":
            InvalidParameter(boxValue, self, -1, str="emptyReg")
            return False
        splitSets = boxValue.split(";")
        checkSet = self.paths.boxList[3].GetValue().strip().split(",")
        try:
            if len(splitSets[0].split(",")) == 1 and len(splitSets[1]) == 0 and len(splitSets) == 2:
                setValueString = splitSets[0].strip() + "," + self.paths.boxList[3].GetValue().split(",")[0].strip() + ";"
            elif splitSets[0].split(",")[1].strip() == "" and len(splitSets[1]) == 0 and len(splitSets) == 2:
                if splitSets[0].split(",")[0].strip().lower().endswith(".reg") != True or \
                   len(glob(splitSets[0].split(",")[0])) != 1:
                    InvalidParameter("\nRegions: "+ splitSets[0].split(",")[0]
                                     + "\nReference: " + splitSets[0].split(",")[1], self, -1, str="invalidReg")
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
                                InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, str="invalidReg")
                                return False
                            elif len(glob(tempRef)) != 1 or (tempRef.lower().endswith(".fits") == False and 
                                                             tempRef.lower().endswith(".fit") == False):
                                InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, str="invalidRef")
                                return False
                            elif all(tempRef != temp for temp in checkSet):
                                InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, str="invalidRefExist")
                                return False
                            setValueString += tempReg + "," + tempRef + ";"
                except IndexError:
                    if tempString == "tempReg":
                        tempReg = ""
                    elif tempString == "tempRef":
                        tempRef = ""
                    if len(eachSet.split(",")) == 1:
                        InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, str="outofbounds")
                        return False
        except IndexError:
            if splitSets[0].split(",")[0].strip().lower().endswith(".reg") != True or \
                   len(glob(splitSets[0].split(",")[0])) != 1:
                InvalidParameter("\nRegions: "+ splitSets[0].split(",")[0] 
                                 + "\nReference: " + splitSets[0].split(",")[1], self, -1, str="invalidReg")
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
                            InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, str="invalidReg")
                            return False
                        elif len(glob(tempRef)) != 1 or (tempRef.lower().endswith(".fits") == False and 
                                                         tempRef.lower().endswith(".fit") == False):
                            InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, str="invalidRef")
                            return False
                        elif all(tempRef != temp for temp in checkSet):
                            InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, str="invalidRefExist")
                            return False
                        setValueString += tempReg + "," + tempRef + ";"
            except IndexError:
                if tempString == "tempReg":
                    tempReg = ""
                elif tempString == "tempRef":
                    tempRef = ""
                if len(eachSet.split(",")) == 1:
                    InvalidParameter("\nRegions: "+tempReg + "\nReference: " + tempRef, self, -1, str="outofbounds")
                    return False
        array = []
        dict = {}
        for eachSet in setValueString.split(";"):
            if len(eachSet.split(",")) != 1:
                reg = eachSet.split(",")[0]
                ref = eachSet.split(",")[1]
                try:
                    temp = array.index(ref)
                    if dict[ref] != reg:
                        tempString = "\nRegions: " + reg + "\nReference: " + ref + "\nBecause ---" + "\nRegions: " + \
                        dict[ref] + "\nIs already associated with the reference file."
                        InvalidParameter(tempString, self, -1, str="referenceImageDup")
                        return False
                except ValueError:
                    array.append(ref)
                    dict[ref] = reg
        self.paths.boxList[4].SetValue(setValueString)
        return True
    
    def singularExistance(self, event, value, name):

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
                try:
                    import ephem
                    EphemerisFrame(self, -1)
                    self.loadEphFrame = True
                except ImportError:
                    InvalidParameter("", None, -1, str="importError")
            elif name == "ds9":
                if sys.platform == "win32":
                    errorType = WindowsError
                else:
                    errorType = OSError
                
                try:
                    subprocess.Popen([os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),
                                                   'extras','ds9',sys.platform,'ds9')])
                except errorType:
                    self.ds9Open = True
                    InvalidParameter("", self, -1, str="ds9")
            elif name == "extra":
                invalidDataImages = self.checkFileInputs(self.paths.boxList[3].GetValue(), saveNum=3)
                if invalidDataImages != "":
                    InvalidParameter(invalidDataImages, self, -1, str="fits", max="the path to Data Images")
                elif self.checkRegionsBox(self.paths.boxList[4].GetValue()) == True:
                    ExtraRegions(self,-1)
                    self.extraRegionsOpen = True
            elif name == "observatory":
                invalidDataImages = self.checkFileInputs(self.paths.boxList[3].GetValue(), saveNum=3)
                if invalidDataImages != "":
                    InvalidParameter(invalidDataImages, self, -1, str="fits", max="the path to Data Images")
                else:
                    ObservatoryFrame(self, -1)
                    self.loadObservatoryFrame = True
                
                    
    def parseTime(self, date, time, text, filename, name=""):
        
        dateArr = str(date).split('/')
        result = dateArr[0].strip() + '-' + dateArr[1].strip() + '-' + dateArr[2].strip() + ' ; '
        timeArr = str(time).split(":")
        result += timeArr[0].strip() + ":" + timeArr[1].strip() + ':' + timeArr[2].strip()
        filename.write(text + result + '\n')
        
        self.radioBox.userParams[name].SetValue(dateArr[0].strip() + '/' + dateArr[1].strip() + '/' + dateArr[2].strip())
        self.radioBox.userParams[name+"1"].SetValue(timeArr[0].strip() + ":" + timeArr[1].strip() + ':' +
                                                    timeArr[2].strip())
    
    def checkRB(self, button, text, filename):
        if button.GetValue() == True:
            filename.write(text + 'on\n')
        else:
            filename.write(text + 'off\n')

    def createFrame(self):
        if self.loadFittingOpen == False:
            if not self.outputFile.lower().endswith(".pkl"):
                FittingFrame(self, -1, self.outputFile + ".pkl")
                self.loadFittingOpen = True
            else:
                FittingFrame(self, -1, self.outputFile)
                self.loadFittingOpen = True

    def openLink(self, event, string):
        webbrowser.open_new_tab(string)
    
    def on_exit(self, event):
        self.Destroy()

class ObservatoryFrame(wx.Frame):

    def __init__(self, parent, id):

        if sys.platform == "win32":
            self.fontType = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        else: 
            self.fontType = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)

        wx.Frame.__init__(self, parent, id, "Change Observatory Parameters")
        self.panel = wx.Panel(self)
        self.parent = parent
        
        self.titlebox = wx.StaticText(self.panel, -1, "Observatory Parameters")
        self.titleFont = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.titlebox.SetFont(self.titleFont)
        
        list = [('ccd',"CCD Gain: ",
                 'Enter a decimal for the gain here.', self.parent.ccdGain)]
        
        
        header = pyfits.getheader(self.parent.paths.boxList[3].GetValue().split(",")[0]).keys()   
        
        bestKeyword, self.allKeys, acceptedKeys, conversion = \
            timeConversions.findKeyword(self.parent.paths.boxList[3].GetValue().split(",")[0])
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
        
        self.params = ParameterBox(self.panel, -1, list, rows=5, cols=2, vNum=10, hNum=10, font=self.fontType)
       
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
        self.parent.exposureTime = self.timeList.GetValue()
    
    def update(self, event):
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
        try:
            tempCCD = float(self.params.userParams["ccd"].GetValue())
            self.params.userParams["ccd"].SetValue(str(tempCCD))
            timeKey = self.timeList.GetValue().strip()
            if timeKey == "":
                InvalidParameter(timeKey, self, -1, str="emptyKeyword")
                return False
            elif not timeKey in self.allKeys:
                InvalidParameter(timeKey, self, -1, str="invalidKeyword")
                return False
            elif (not timeKey in self.unionKeys) and (timeKey in self.allKeys):
                InvalidParameter(timeKey, self, -1, str="emailKeyword")
                return False
            self.timeList.SetValue(timeKey)
        except ValueError:
            InvalidParameter(self.params.userParams["ccd"].GetValue(),None,-1, str="leftbox", max="ccd")
            return False
        return True

    def create_menu(self):
          
        menubar = wx.MenuBar()
        menu_file = wx.Menu()
        m_quit = menu_file.Append(wx.ID_EXIT, "Quit\tCtrl+Q", "Quit this application.")
        self.Bind(wx.EVT_MENU, self.on_exit, m_quit)
    
        menubar.Append(menu_file, "File")
        self.SetMenuBar(menubar)
    
    def on_exit(self,event):
        self.Destroy()

    def onDestroy(self,event):
        self.parent.loadObservatoryFrame = False

class ExtraRegions(wx.Frame):

    def __init__(self, parent, id):

        if sys.platform == "win32":
            self.fontType = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        else: 
            self.fontType = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)

        wx.Frame.__init__(self, parent, id, "Extra Regions Files")
        self.panel = wx.Panel(self)
        self.parent = parent
        
        self.titlebox = wx.StaticText(self.panel, -1, "Extra Regions Files")
        self.titleFont = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.titlebox.SetFont(self.titleFont)
        self.set1 = AddLCB(self.panel, -1, name="Path to Regions File: ,Path to Reference Image: ", rowNum=2, vNum=5,
                            hNum=5, str="Browse", boxName ="Set 1", font=self.fontType)
        self.set2 = AddLCB(self.panel, -1, name="Path to Regions File: ,Path to Reference Image: ", rowNum=2, vNum=5,
                             hNum=5, str="Browse", boxName="Set 2", font=self.fontType)
        self.set3 = AddLCB(self.panel, -1, name="Path to Regions File: ,Path to Reference Image: ", rowNum=2, vNum=5,
                             hNum=5, str="Browse", boxName="Set 3", font=self.fontType)
        self.set4 = AddLCB(self.panel, -1, name="Path to Regions File: ,Path to Reference Image: ", rowNum=2, vNum=5,
                            hNum=5, str="Browse", boxName="Set 4", font=self.fontType)
        self.set5 = AddLCB(self.panel, -1, name="Path to Regions File: ,Path to Reference Image: ", rowNum=2, vNum=5,
                            hNum=5, str="Browse", boxName="Set 5", font=self.fontType)
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
    
    def addSet(self,event, stringName):
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
                    if tempRef == reference and tempReg != regions:
                        uniqueRef = False
                        break

            if uniqueRef == False:
                tempString = "\nRegions: " + regions + "\nReference: " + reference + "\nBecause ---" + "\nRegions: " + \
                             tempReg + "\nIs already associated with the reference file."
                InvalidParameter(tempString, self, -1, str="referenceImageDup")
            elif all(reference != temp for temp in dataImages):
                InvalidParameter("\nRegions: "+ regions + "\nReference: " + reference, self, -1, str="invalidRefExist")
            else:
                regionsBox += setString + ";"
                self.parent.paths.boxList[4].SetValue(regionsBox)
                InvalidParameter("", self, -1, str="regionsUpdate")
    
    def SetCheck(self, reg, ref):
        if reg == "":
            InvalidParameter(reg, self, -1, str="regionsError1")
            return False
        elif ref == "":
            InvalidParameter(ref, self, -1, str="regionsError1")
            return False

        if len(glob(reg)) != 1:
            tempString = reg
            if len(reg.split(",")) > 1:
                tempString = ""
                for string in reg.split(","):
                    if string == "" and len(masterFlat.split(",")) == 2:
                        tempString += ","
                    else:
                        tempString += "\n" + string.strip()
            InvalidParameter(tempString, self, -1, str="regionsError2")
            return False
        elif len(glob(ref)) != 1:
            tempString = ref
            if len(ref.split(",")) > 1:
                tempString = ""
                for string in ref.split(","):
                    if string == "" and len(masterFlat.split(",")) == 2:
                        tempString += ","
                    else:
                        tempString += "\n" + string.strip()
            InvalidParameter(tempString, self, -1, str="regionsError2")
            return False
        elif reg.lower().endswith(".reg") == False:
            InvalidParameter(reg, self, -1, str="regionsError3")
            return False
        elif ref.lower().endswith(".fits") == False and ref.lower().endswith(".fit") == False:
            InvalidParameter(ref, self, -1, str="regionsError4")
            return False
        return True        

    def create_menu(self):
          
        menubar = wx.MenuBar()
        menu_file = wx.Menu()
        m_quit = menu_file.Append(wx.ID_EXIT, "Quit\tCtrl+Q", "Quit this application.")
        self.Bind(wx.EVT_MENU, self.on_exit, m_quit)
    
        menubar.Append(menu_file, "File")
        self.SetMenuBar(menubar)
    
    def on_exit(self,event):
        self.Destroy()

    def onDestroy(self,event):
        self.parent.extraRegionsOpen = False

class MasterFlatFrame(wx.Frame):
    def __init__(self, parent, id):
        
        wx.Frame.__init__(self, parent, id, "Master Flat Maker")
        self.panel = wx.Panel(self)
        self.parent = parent
        self.overWrite = False
        self.titlebox = wx.StaticText(self.panel, -1, 'OSCAAR: Master Flat Maker')
        self.titleFont = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.titlebox.SetFont(self.titleFont)
        
        self.path1 = AddLCB(self.panel, -1, name="Path to Flat Images: ", str="Browse", multFiles=True, saveType=None)
        self.path2 = AddLCB(self.panel, -1, name="Path to Dark Flat Images: ", str="Browse", multFiles=True, saveType=None)
        self.path3 = AddLCB(self.panel, -1, name="Path to Save Master Flat: ", str="Browse", saveType=wx.FD_SAVE)
        
        list = [('trackPlot',"","none",'')]
        self.plotBox = ParameterBox(self.panel,-1,list, name = "Plots")
        list = [('flatType',"","Standard","Twilight")]
        self.flatBox = ParameterBox(self.panel,-1,list, name = "Flat Type")
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
        
        path = self.path3.boxList[1].GetValue().strip()
        self.flatImages = self.checkFileInputs(self.path1.boxList[1].GetValue(), self.path1.boxList[1])
        self.darkFlatImages = self.checkFileInputs(self.path2.boxList[1].GetValue(), self.path2.boxList[1])
        if self.flatImages != "":
            InvalidParameter(self.flatImages, None, -1, str="flat1")
        elif self.darkFlatImages != "":
            InvalidParameter(self.darkFlatImages, None, -1, str="flat2")
        elif not path:
            InvalidParameter(str(path), None, -1, str="flat3")
        elif not os.path.isdir(path[path.rfind(os.sep)]) or \
             not len(path) > (len(path[:path.rfind(os.sep)]) + 1):
            InvalidParameter(path, None, -1, str="flat3")
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
            self.plotCheck = self.plotBox.userParams['trackPlot'].GetValue()
            if pathCorrected in glob(outfolder):
                if self.overWrite == False:
                    OverWrite(self, -1, "Overwrite Master Flat", pathCorrected, "MasterFlat")
                    self.overWrite = True
            else:
                if self.flatBox.userParams['flatType'].GetValue() == True:
                    systematics.standardFlatMaker(self.flatImages, self.darkFlatImages, self.path3.boxList[1].GetValue(),
                                              self.plotCheck)
                else:
                    systematics.twilightFlatMaker(self.flatImages, self.darkFlatImages, self.path3.boxList[1].GetValue(),
                                              self.plotCheck)
    def checkFileInputs(self,array,box):
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
          
        menubar = wx.MenuBar()
        menu_file = wx.Menu()
        m_quit = menu_file.Append(wx.ID_EXIT, "Quit\tCtrl+Q", "Quit this application.")
        self.Bind(wx.EVT_MENU, self.on_exit, m_quit)
    
        menubar.Append(menu_file, "File")
        self.SetMenuBar(menubar)
    
    def on_exit(self,event):
        self.Destroy()

    def onDestroy(self,event):
        self.parent.loadMasterFlat = False

class AboutFrame(wx.Frame):

    def __init__(self, parent, id):
        
        wx.Frame.__init__(self, parent, id, "About OSCAAR")
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

    def onDestroy(self,event):
        self.parent.aboutOpen = False

    def exit(self,event):
        self.Destroy()


class OverWrite(wx.Frame): 
     
    def __init__(self, parent, id, title, path, check):
        
        wx.Frame.__init__(self, parent, id, title)
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
        self.Bind(wx.EVT_BUTTON, self.onOkay, self.noButton)
        
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
        self.Destroy()
        self.parent.overWrite = False  
        os.remove(self.path)
        if self.parent.flatBox.userParams['flatType'].GetValue() == True:
            systematics.standardFlatMaker(self.parent.flatImages, self.parent.darkFlatImages, 
                                     self.parent.path3.boxList[1].GetValue(), self.parent.plotCheck)
        else:
            systematics.twilightFlatMaker(self.parent.flatImages, self.parent.darkFlatImages, 
                                     self.parent.path3.boxList[1].GetValue(), self.parent.plotCheck)
    def onOutputFile(self,event):
        self.Destroy()
        self.parent.overWrite = False
        diffPhotCall = "from oscaar import differentialPhotometry"
        subprocess.check_call(['python','-c',diffPhotCall])
        if self.parent.radioBox.userParams["flatType"].GetValue() == True:
            wx.CallAfter(self.parent.createFrame)

    def onOkay(self, event):
        self.parent.overWrite = False    
        self.Destroy()
        
    def doNothing(self,event):
        self.parent.overWrite = False
        pass


class EphemerisFrame(wx.Frame):

    def __init__(self, parent, id):

        wx.Frame.__init__(self, parent, id, "Ephemerides")
        
        self.panel = wx.Panel(self)
        self.parent = parent
        
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
        for file in obsList:
            for line in open(file,'r').read().splitlines():
                if line.split(":")[0] == "name":
                    self.nameList[line.split(":")[1].strip()] = file
        
        self.obsLabel = wx.StaticText(self.panel, -1, 'Select Observatory: ')
        self.obsLabel.SetFont(self.fontType)
        self.obsList = wx.ComboBox(self.panel, value = 'Observatories',
                                   choices = sorted(self.nameList.keys()) + ["Enter New Observatory"])
        self.obsList.Bind(wx.EVT_COMBOBOX, self.update)

        self.dropBox = wx.BoxSizer(wx.HORIZONTAL)
        self.dropBox.Add(self.obsLabel, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 10)
        self.dropBox.Add(self.obsList, 0, flag = wx.ALIGN_CENTER)
        
        list = [('observatoryName',"Name of Observatory: ","",""),
                ('fileName',"Enter File Name: ","",""),
                ('obsStart',"Start of Observation, UT (YYYY/MM/DD): ",
                 "Enter a date in the correct format here.",datetime.date.today().strftime("%Y/%m/%d")),
                ('obsEnd',"End of Observation, UT (YYYY/MM/DD): ",
                 "Enter a date in the correct format here.",(datetime.datetime.now()+datetime.timedelta(days=7)
                                                             ).strftime("%Y/%m/%d")),
                ('upperLimit',"Apparent Mag. Upper Limit: ","","0.0"),
                ('lowerLimit',"Depth Lower Limit: ","","0.0")]
        self.leftBox = ParameterBox(self.panel,-1,list, rows=6, cols=2, vNum = 5, hNum = 15, font = self.fontType)
        
        list = [("latitude","Latitude (deg:min:sec): ","","00:00:00"),
                ("longitude","Longitude (deg:min:sec): ","","00:00:00"),
                ("elevation","Observatory Elevation (m): ","","0.0"),
                ("temperature","Temperature ("u"\u00b0""C): ","","0.0"),
                ("lowerElevation","Lower Elevation Limit (deg:min:sec): ","","00:00:00"),
                ]
        self.leftBox2 = ParameterBox(self.panel, -1, list, rows=5, cols=2, vNum = 5, hNum = 15, font =self.fontType)
        
        self.twilightChoices = {}
        self.twilightChoices["Civil Twilight (-6"u"\u00b0"+")"] = "-6"
        self.twilightChoices["Nautical Twilight (-12"u"\u00b0"+")"] = "-12"
        self.twilightChoices["Astronomical Twilight (-18"u"\u00b0"")"] = "-18"
        
        self.twilightLabel = wx.StaticText(self.panel, -1, "Select Twilight Type: ")
        self.twilightLabel.SetFont(self.fontType)
        self.twilightList = wx.ComboBox(self.panel, value = "Civil Twilight (-6"u"\u00b0"+")", 
                                        choices = sorted(self.twilightChoices.keys()))
        
        self.dropBox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.dropBox2.Add(self.twilightLabel, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 10)
        self.dropBox2.Add(self.twilightList, 0, flag = wx.ALIGN_CENTER)       
        
        list = [('flatType',"","V","K")]
        self.band = ParameterBox(self.panel,-1,list, name = "Band Type")
        list = [('flatType',"","On","Off")]
        self.showLT = ParameterBox(self.panel,-1,list, name = "Show Local Times", other = False)
        
        self.botRadioBox = wx.BoxSizer(wx.HORIZONTAL)
        self.botRadioBox.Add(self.showLT, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 10)
        self.botRadioBox.Add(self.band, 0, flag = wx.ALIGN_CENTER | wx.LEFT, border = 15)
       
        list = [('flatType',"","True","False")]
        self.calcEclipseBox = ParameterBox(self.panel,-1,list, name = "Calculate Eclipses", other = False)
        list = [('flatType',"","True", "False")]
        self.htmlBox = ParameterBox(self.panel,-1,list, name = "HTML Out")
        list = [('flatType',"","True","False")]
        self.textBox = ParameterBox(self.panel,-1,list, name = "Text Out")
        list = [('flatType',"","True","False")]
        self.calcTransitsBox = ParameterBox(self.panel,-1,list, name = "Calculate Transits")
        

        self.radioBox = wx.BoxSizer(wx.VERTICAL)
        self.radioBox.Add(self.calcEclipseBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.radioBox.Add(self.htmlBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.radioBox.Add(self.textBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.radioBox.Add(self.calcTransitsBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        
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
        
        if self.parameterCheck() == True:
            
            if self.parent.singularOccurance == 0 and self.showLT.userParams["flatType"].GetValue():
                self.parent.singularOccurance = 1
                InvalidParameter("", self, -1, str = "warnError")
            else:
                outputPath = str(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),
                                              'extras','eph','ephOutputs','eventReport.html'))
                path = os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),
                                    'extras','eph','observatories', self.leftBox.userParams["fileName"].GetValue() + '.par')
                
                if not self.nameList.has_key(self.name):
                    self.nameList[self.name] = path
                    self.obsList.Append(self.name)
                
                self.saveFile(path)
                import oscaar.extras.eph.calculateEphemerides as eph
                eph.calculateEphemerides(path)
        
                if self.htmlBox.userParams["flatType"].GetValue() == True: 
                    webbrowser.open_new_tab("file:"+2*os.sep+outputPath)

    def parameterCheck(self):

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
            InvalidParameter(self.name, self, -1, str = "obsName")
            return False
        elif self.fileName == "" or self.fileName == "Enter the name of the file":
            InvalidParameter(self.fileName, self, -1, str ="obsFile")
            return False
        years = []
        months = []
        days = []
        for dateArray,value in [(self.startingDate.split("/"),self.startingDate),
                                (self.endingDate.split("/"),self.endingDate)]:
            if len(dateArray) != 3:
                InvalidParameter(value, self, -1, str="obsDate")
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
                        InvalidParameter(value, self, -1, str="obsDate")
                        return False
                    minYear = datetime.date.today().year - 100
                    maxYear = datetime.date.today().year + 100
                    if year < minYear or year > maxYear or month > 12 or month < 0 or day > 31 or day < 0 or \
                       month == 0 or year == 0 or day == 0:
                        InvalidParameter(value, self, -1, str="dateRange")
                        return False
                except ValueError:
                    InvalidParameter(value, self, -1, str="obsDate")
                    return False

        if years[0] > years[1]:
            InvalidParameter(self.startingDate, self, -1, str = "logicalDate")
            return False
        elif years[0] == years[1]:
            if months[0] > months[1]:
                InvalidParameter(self.startingDate, self, -1, str = "logicalDate")
                return False
            elif months[0] == months[1]:
                if days[0] >= days[1]:
                    InvalidParameter(self.startingDate, self, -1, str = "logicalDate")
                    return False
        
        for coordArray, value, type in [(self.latitude.split(":"),self.latitude, "lat"), 
                                  (self.longitude.split(":"),self.longitude, "long")]:
            if(len(coordArray) != 3):
                InvalidParameter(value, self, -1, str = "coordTime")
                return False
            else:
                try:
                    deg = float(coordArray[0].strip())
                    min = float(coordArray[1].strip())
                    sec = float(coordArray[2].strip())
                    if type == "lat":
                        self.latitude = str(deg) + ":" + str(min) + ":" + str(sec)
                        if abs(deg) > 90.0 or min >= 60 or min < 0.0 or sec >= 60 or sec < 0.0:
                            InvalidParameter(value, self, -1, str = "coordRange")
                            return False
                    elif type == "long":
                        self.longitude = str(deg) + ":" + str(min) + ":" + str(sec)
                        if abs(deg) > 180.0 or min >= 60 or min < 0.0 or sec >= 60 or sec < 0.0:
                            InvalidParameter(value, self, -1, str = "coordRange")
                            return False
                    if abs(deg) == 90 and type == "lat":
                        if min != 0 or sec != 0:
                            InvalidParameter(value, self, -1, str = "coordRange")
                            return False
                    elif abs(deg) == 180 and type == "long":
                        if min != 0 or sec != 0:
                            InvalidParameter(value, self, -1, str = "coordRange")
                            return False
                except ValueError:
                    InvalidParameter(value, self, -1, str = "coordTime")
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
            
            stripElevation = self.lowerElevation.split(":")

            if len(stripElevation) != 3:
                InvalidParameter(self.lowerElevation, self, -1, str = "lowerElevation")
                return False

            temp6 = int(stripElevation[0])
            temp7 = int(stripElevation[1])
            temp8 = int(stripElevation[2])
            
            if temp6 < 0.0 or temp6 > 90 or temp7 >= 60 or temp7 < 0.0 or temp8 >= 60 or temp8 < 0.0:
                InvalidParameter(self.lowerElevation, self, -1, str = "lowerElevation")
                return False
            elif temp6 == 90:
                if temp7 != 0 or temp8 != 0:
                    InvalidParameter(self.lowerElevation, self, -1, str = "lowerElevation")
                    return False
              
            self.lowerElevation = stripElevation[0].strip() + ":" + stripElevation[1].strip() + ":" +\
                                  stripElevation[2].strip()
            
            if temp1 < 0:
                InvalidParameter(self.elevation, self, -1, str = "tempElevNum", max = "elevation")
                return False
            
            elif temp2 < 0:
                InvalidParameter(self.temperature, self, -1, str = "tempElevNum", max = "temperature")
                return False
            
            elif temp4 < 0:
                InvalidParameter(self.lowerLimit, self, -1, str = "tempElevNum", max = "depth lower limit")
                return False

        except ValueError:
            if tempString == "temperature":
                InvalidParameter(self.temperature, self, -1, str = "tempElevNum", max = tempString)
            elif tempString == "apparent magnitude upper limit":
                InvalidParameter(self.upperLimit, self, -1, str = "tempElevNum", max = tempString)
            elif tempString == "depth lower limit":
                InvalidParameter(self.lowerLimit, self, -1, str = "tempElevNum", max = tempString)
            elif tempString == "lower elevation limit":
                InvalidParameter(self.lowerElevation, self, -1, str = "lowerElevation")
            else:
                InvalidParameter(self.elevation, self, -1, str = "tempElevNum", max = tempString)
            return False
        
        if all(self.twilight != temp for temp in ["Civil Twilight (-6"u"\u00b0"")",
                                         "Nautical Twilight (-12"u"\u00b0"")",
                                         "Astronomical Twilight (-18"u"\u00b0"")"]):
            InvalidParameter(self.twilight, self, -1, str = "twilight")
            return False
                
        return True
    
    def update(self, event):

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
                    list = [("name","observatoryName"),("min_horizon","lowerElevation"),("mag_limit","upperLimit"),
                            ("depth_limit","lowerLimit"),("latitude",""),("longitude",""),("elevation",""),
                            ("temperature",""),("twilight",""),("calc_transits",6),("calc_eclipses",0),
                            ("html_out",2),("text_out",4), ("show_lt","flatType"), ("band","flatType")]
                
                    for string,saveName in list:
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
        newObs.write("calc_eclipses: " + str(self.calcEclipseBox.userParams["flatType"].GetValue()) + "\n")
        newObs.write("html_out: " + str(self.htmlBox.userParams["flatType"].GetValue()) + "\n")
        newObs.write("text_out: " + str(self.textBox.userParams["flatType"].GetValue()) + "\n")
        newObs.write("calc_transits: " + str(self.calcTransitsBox.userParams["flatType"].GetValue()) + "\n")
        newObs.write("twilight: " + self.twilightChoices[self.twilight] + "\n")
        tempLT = str(self.showLT.userParams["flatType"].GetValue())
        if tempLT == "True":
            tempLT = "1"
        else:
            tempLT = "0"
        newObs.write("show_lt: " + tempLT + "\n")
        tempString = str(self.band.userParams["flatType"].GetValue())
        if tempString == "True":
            bandString = "V"
        else:
            bandString = "K"
        newObs.write("band: "+ bandString)
        newObs.close()

    def create_menu(self):
    
        # These commands create the menu bars that are at the top of the GUI.
    
        menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_save = menu_file.Append(wx.ID_SAVE, "Save\tCtrl+S", "Save data to a zip folder.")
        m_quit = menu_file.Append(wx.ID_EXIT, "Quit\tCtrl+Q", "Quit this application.")
        self.Bind(wx.EVT_MENU, self.on_exit, m_quit)
        self.Bind(wx.EVT_MENU, self.saveOutput, m_save)
        
        menubar.Append(menu_file, "File")
        self.SetMenuBar(menubar)

    def saveOutput(self, event):
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

    def onDestroy(self, event):
        self.parent.loadEphFrame = False
    
    def on_exit(self,event):
        self.parent.loadEphFrame = False
        self.Destroy()

class FittingFrame(wx.Frame):

    def __init__(self, parent, id, path = ''):
        
        self.path = path
        self.title = "Fitting Methods"
        self.loadMCMC = False
        wx.Frame.__init__(self, parent, id, self.title)
        
        self.panel = wx.Panel(self)
        self.parent = parent
        
        self.box = AddLCB(self.panel,-1,name="Path to Output File: ")
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.box, border=5, flag=wx.ALL)
        self.box.boxList[1].SetValue(self.path)
        
        #self.plotLSFitButton = wx.Button(self.panel,label="Least Squares Fit", size =(130,25))
        self.plotMCMCButton = wx.Button(self.panel,label="MCMC Fit", size = (130,25))
        
        #self.Bind(wx.EVT_BUTTON, self.plotLSFit, self.plotLSFitButton)
        self.Bind(wx.EVT_BUTTON, self.plotMCMC, self.plotMCMCButton)
        
        self.sizer0 = wx.FlexGridSizer(rows=2, cols=4)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)
        
        #self.sizer0.Add(self.plotLSFitButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotMCMCButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        
        self.pklPathTxt = self.box.boxList[1]
        self.create_menu()

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.hbox, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.vbox.AddSpacer(10)
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.Center()
        self.Show()

    def create_menu(self):
    
        # These commands create a drop down menu with the browse command, and exit command.
    
        self.menubar = wx.MenuBar()
    
        menu_file = wx.Menu()
        m_browse = menu_file.Append(-1,"Browse\tCtrl-O","Browse")
        self.Bind(wx.EVT_MENU,lambda event: self.browseButtonEvent(event,'Choose Path to Output File',self.pklPathTxt,
                                                                   False,wx.FD_OPEN),m_browse)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "Exit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
    
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def browseButtonEvent(self, event, message, textControl, fileDialog, saveDialog):                    
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
        if self.validityCheck():
            global pathText
            global loadLSFit
            pathText = self.pklPathTxt.GetValue()
            if loadLSFit == False:
                LeastSquaresFitFrame()
                loadLSFit = True
    
    def plotMCMC(self,event):
        if self.validityCheck():
            try:
                self.pathText = self.pklPathTxt.GetValue()
                self.data = IO.load(self.pathText)
                temp = self.data.apertureRadii
                if self.loadMCMC == False:
                    MCMCFrame(self, -1)
                    self.loadMCMC = True
            except AttributeError:
                InvalidParameter("", self, -1, str="oldPKL") 
     
    def validityCheck(self):
        pathName = self.pklPathTxt.GetValue()
        if pathName != "":
            if pathName.lower().endswith(".pkl"):
                if os.path.isfile(pathName) == False:
                   InvalidParameter(pathName, self, -1, str="path")
                   return False
            else:
                InvalidParameter(pathName, self, -1, str="path")
                return False 
        else:
            InvalidParameter(pathName, self, -1, str="path")
            return False
        return True
    
    def onDestroy(self, event):
        self.parent.loadFittingOpen = False
    
    def on_exit(self, event):
        self.Destroy()

class LoadOldPklFrame(wx.Frame):

    def __init__(self, parent, id):

        self.title = "Load An Old .pkl File"
        wx.Frame.__init__(self, parent, id, self.title)
        
        self.panel = wx.Panel(self)
        self.parent = parent
        self.loadGraphFrame = False
        self.data = ""
        
        self.box = AddLCB(self.panel,-1, parent2 = self, name="Path to Output File: ", updateRadii = True)    
         
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

        #self.Bind(wx.EVT_BUTTON, self.plotLightCurve, self.plotLightCurveButton)
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
        self.vbox.Fit(self)
        self.Center()
        self.Show()

    def create_menu(self):
    
        # These commands create a drop down menu with the browse command, and exit command.
    
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
                InvalidParameter("", self, -1, str="oldPKL") 
        
        dlg.Destroy()

    def plotLightCurve(self, event):
        if self.validityCheck() and self.radiusCheck():
            if self.tempNum[0][0] != self.apertureRadiusIndex:
                self.apertureRadiusIndex = self.tempNum[0][0]
            print 'Loading file: '+self.pklPathTxt.GetValue()
            
            commandstring = "import oscaar.IO; data=oscaar.IO.load('%s'); data.plotLightCurve(apertureRadiusIndex=%s)" \
                                % (self.pklPathTxt.GetValue(),self.apertureRadiusIndex)

            subprocess.Popen(['python','-c',commandstring])


    def plotRawFlux(self, event):
        if self.validityCheck() and self.radiusCheck():
            if self.tempNum[0][0] != self.apertureRadiusIndex:
                self.apertureRadiusIndex = self.tempNum[0][0]
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar.IO; data=oscaar.IO.load('%s'); data.plotRawFluxes(apertureRadiusIndex=%s)" \
                                % (self.pklPathTxt.GetValue(),self.apertureRadiusIndex)
                                
            subprocess.Popen(['python','-c',commandstring])

    def plotScaledFluxes(self, event):
        if self.validityCheck() and self.radiusCheck():
            if self.tempNum[0][0] != self.apertureRadiusIndex:
                self.apertureRadiusIndex = self.tempNum[0][0]
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar.IO; data=oscaar.IO.load('%s'); data.plotScaledFluxes(apertureRadiusIndex=%s)" \
                              % (self.pklPathTxt.GetValue(),self.apertureRadiusIndex)

            subprocess.Popen(['python','-c',commandstring])
    
    def plotCentroidPosition(self, event):
        if self.validityCheck():
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar.IO; data=oscaar.IO.load('%s'); data.plotCentroidsTrace()" \
                                % (self.pklPathTxt.GetValue())

            subprocess.Popen(['python','-c',commandstring])

    def plotComparisonStarWeightings(self, event):
        if self.validityCheck() and self.radiusCheck():
            if self.tempNum[0][0] != self.apertureRadiusIndex:
                self.apertureRadiusIndex = self.tempNum[0][0]
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar.IO; data=oscaar.IO.load('%s');" \
                            "data.plotComparisonWeightings(apertureRadiusIndex=%s)" \
                            % (self.pklPathTxt.GetValue(),self.apertureRadiusIndex)

            subprocess.Popen(['python','-c',commandstring])
    
    def plotInteractiveLightCurve(self, event):
        if self.validityCheck() and self.radiusCheck():
            if self.tempNum[0][0] != self.apertureRadiusIndex:
                self.apertureRadiusIndex = self.tempNum[0][0]
            if self.loadGraphFrame == False:   
                GraphFrame(self, -1)
                self.loadGraphFrame = True
            
    def validityCheck(self, throwException=True):
        pathName = self.pklPathTxt.GetValue()
        if pathName != "":
            if pathName.lower().endswith(".pkl"):
                if os.path.isfile(pathName) == False:
                    if throwException:
                        InvalidParameter(pathName, self, -1, str="path")
                    return False
            else:
                if throwException:
                    InvalidParameter(pathName, self, -1, str="path")
                return False 
        else:
            if throwException:
                InvalidParameter(pathName, self, -1, str="path")
            return False
        return True

    def radiusCheck(self):
        if len(self.apertureRadii) == 0:
            InvalidParameter(str(self.apertureRadii), self, -1, str = "radiusListError")
            return False
        elif self.radiusList.GetValue() == "":
            InvalidParameter(self.radiusList.GetValue(), self, -1, str = "radiusError")
            return False
        try:
            self.tempNum = np.where(self.epsilonCheck(self.apertureRadii,float(self.radiusList.GetValue())))
            if len(self.tempNum[0]) == 0:
                tempString = self.radiusList.GetValue() + " was not found in " + str(self.apertureRadii)
                InvalidParameter(tempString, self, -1, str = "radiusListError2")
                return False
        except ValueError:
            InvalidParameter(self.radiusList.GetValue(), self, -1, str = "radiusError")
            return False
        return True
    
    def updateRadiiList(self, event):
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
                InvalidParameter("", self, -1, str="oldPKL") 

    def epsilonCheck(self,a,b):
        ''' Check variables `a` and `b` are within machine precision of each other
            because otherwise we get machine precision difference errors when mixing
            single and double precion NumPy floats and pure Python built-in float types.
        '''
        return np.abs(a-b) < np.finfo(np.float32).eps

    def radiusIndexUpdate(self, event):
        self.apertureRadiusIndex = np.where(self.epsilonCheck(self.apertureRadii, float(self.radiusList.GetValue())))[0][0]
        #map(float,self.apertureRadii) == float(self.radiusList.GetValue()))[0][0]
        
    def onDestroy(self, event):
        self.parent.loadOldPklOpen = False
    
    def on_exit(self, event):
        self.Destroy()

class GraphFrame(wx.Frame):
    
    """ The main frame of the application
    """
    
    title = 'Light Curve Plot'

    def __init__(self, parent, id):
    
        # This initializes the wx.frame with the title.
        
        wx.Frame.__init__(self, parent, id, self.title, style = wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | 
                                                                                            wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        #wx.Frame(None, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        
        # This gets the location of the pkl file by using a global variable that is defined in the LoadOldPklFrame class.
        
        self.pT = parent.pklPathTxt.GetValue()
        self.parent = parent
        self.apertureRadiusIndex = self.parent.apertureRadiusIndex
        # The rest of these commands just create the window.
        
        self.create_menu()
        self.create_status_bar()
        self.create_main_panel()
        
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.Centre()
        self.Show()

    def create_menu(self):
    
        # These commands create a drop down menu with the save command, and exit command.
    
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

        self.panel = wx.Panel(self)
        self.init_plot()
        self.canvas = FigCanvas(self.panel, -1, self.fig)
        self.box = ScanParamsBox(self.panel,-1)

        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.box, border=5, flag=wx.ALL)
        self.okButton = wx.Button(self.panel,label = 'Plot')
        self.Bind(wx.EVT_BUTTON,self.draw_plot, self.okButton)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)  
        self.vbox.Add(self.hbox, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.okButton,0,flag=wx.ALIGN_CENTER|wx.TOP)
        self.vbox.AddSpacer(10)
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)

    def create_status_bar(self):
        self.statusbar = self.CreateStatusBar()

    def init_plot(self):

        # Initializes the first plot with a bin size of 10.
        
        # We make an instance of the dataBank class with all the paramters of the pkl file loaded.
        self.data = IO.load(self.pT)
        self.pointsPerBin = 10
        
        # Now we can use the plotLightCurve method from the dataBank.py class with minor modifications
        # to plot it.

        binnedTime, binnedFlux, binnedStd = medianBin(self.data.times,self.data.lightCurves[self.apertureRadiusIndex],
                                                      self.pointsPerBin)
        self.fig = pyplot.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
        self.dpi = 100
        self.axes = self.fig.add_subplot(111)
        self.axes.set_axis_bgcolor('white')
        self.axes.set_title('Light Curve', size=12)
        def format_coord(x, y):
            # '''Function to give data value on mouse over plot.'''
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

        """ Redraws the plot
        """
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
                 # '''Function to give data value on mouse over plot.'''
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
    
        # Saves the plot to a location of your choosing.

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

    def on_exit(self, event):
        self.Destroy()
    
    def flash_status_message(self, msg, flash_len_ms=1500):
        self.statusbar.SetStatusText(msg)
        self.timeroff = wx.Timer(self)
        self.Bind(
            wx.EVT_TIMER, 
            self.on_flash_status_off, 
            self.timeroff)
        self.timeroff.Start(flash_len_ms, oneShot=True)
    
    def on_flash_status_off(self, event):
        self.statusbar.SetStatusText('')
    
    def onDestroy(self, event):
        self.parent.loadGraphFrame = False

class LeastSquaresFitFrame(wx.Frame):
    
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
            InvalidParameter(self.box1.boxList[1].GetValue(), None,-1, str="planet")
        else:
            self.planet = self.box1.boxList[1].GetValue()
            [RpOverRs,AOverRs,per,inc,ecc] = returnSystemParams.transiterParams(self.planet)
            
            if RpOverRs == -1 or AOverRs == -1 or per == -1 or inc == -1 or ecc == -1:
                InvalidParameter(self.box1.boxList[1].GetValue(), None,-1, str="planet")
            else:
                self.box.userParams['Rp/Rs'].SetValue(str(RpOverRs))
                self.box.userParams['a/Rs'].SetValue(str(AOverRs))
                self.box.userParams['per'].SetValue(str(per))
                self.box.userParams['inc'].SetValue(str(inc))
                self.box.userParams['ecc'].SetValue(str(ecc))
                InvalidParameter("",None,-1, str="params")

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

class MCMCFrame(wx.Frame):
    
    title = "MCMC Fit"
    
    def __init__(self, parent, id):

        wx.Frame.__init__(self, parent, id, self.title)
        
        self.panel = wx.Panel(self)
        self.parent = parent
        self.pT = self.parent.pathText
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
        
        list = [('Rp/Rs',"Ratio of Radii (Rp/Rs):",
                 'Enter a ratio of the radii here.','0.11'),
                ('a/Rs',"a/Rs:",
                 'Enter a value for a/Rs here.','14.1'),
                ('inc',"Inclination:",
                 'Enter a value for the inclination here.','90.0'),
                ('t0',"t0:", 
                 'Enter a value for the mid transit time here.','2456427.9425593214')]
        
        self.box = ParameterBox(self.panel,-1,list,"Free Parameters",rows=4,cols=2)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.box, border=5, flag=wx.ALL)
        
        list = [('b-Rp/Rs',"Beta Rp/Rs:",
                 'Enter a beta for Rp/Rs here.','0.005'),
                ('b-a/Rs',"Beta a/Rs:",
                 'Enter a beta for a/Rs here.','0.005'),
                ('b-inc',"Beta Inclination:",
                 'Enter a beta for inclination here.','0.005'),   
                ('b-t0',"Beta t0:",
                 'Enter a beta for the mid transit time here.','0.005')]
        
        self.box2 = ParameterBox(self.panel,-1,list,"Beta's",rows=4,cols=2)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.box2, border=5, flag=wx.ALL)

        list = [('per',"Period:",
                 'Enter a value for the period here.','1.580400'),
                ('gamma1',"gamma1:", 
                 'Enter a value for gamma1 here.','0.23'),
                ('gamma2',"gamma2:", 
                 'Enter a value for gamma2 here.','0.3'),
                ('ecc',"Eccentricity:", 
                 'Enter a value for the eccentricity here.','0.0'),
                ('pericenter',"Pericenter:", 
                 'Enter a value for the pericenter here.','0.0')]
        
        self.box3 = ParameterBox(self.panel,-1,list,"Fixed Parameters")
        self.hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox3.Add(self.box3, border=5, flag=wx.ALL)        
        
        list = [('saveiteration',"Iteration to save:",
                 'Enter a number for the nth iteration to be saved.','10'),
                ('burnfrac',"Burn Fraction:",
                 'Enter a decimal for the burn fraction here.','0.20'),
                ('acceptance',"Acceptance:",
                 'Enter a value for the acceptance rate here.','0.30'),
                ('number', "Number of Steps:",
                 'Enter a value for the total steps here.','10000')]
        
        self.box4 = ParameterBox(self.panel,-1,list,"Fit Parameters")
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
    
        # These commands create a drop down menu with the exit command.
    
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_exit = menu_file.Append(-1, "E&xit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
        
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    def plot(self,event):
       list = [(self.box.userParams['Rp/Rs'].GetValue(),"Rp/Rs"),(self.box.userParams['a/Rs'].GetValue(),"a/Rs"),
            (self.box3.userParams['per'].GetValue(),"per"), (self.box.userParams['inc'].GetValue(),"inc"),
            (self.box3.userParams['ecc'].GetValue(),"ecc"), (self.box.userParams['t0'].GetValue(),"t0"),
            (self.box3.userParams['gamma1'].GetValue(),"gamma1"),(self.box3.userParams['gamma2'].GetValue(),"gamma2"),
            (self.box3.userParams['pericenter'].GetValue(),"pericenter"),(self.box4.userParams['saveiteration'].GetValue(),
            "saveiteration"), (self.box4.userParams['acceptance'].GetValue(),"acceptance"),
            (self.box4.userParams['burnfrac'].GetValue(),"burnfrac"), (self.box4.userParams['number'].GetValue(),"number")]
       
       if checkParams(self,list) == True and self.radiusCheck() == True:
            initParams = [float(self.box.userParams['Rp/Rs'].GetValue()),float(self.box.userParams['a/Rs'].GetValue()),
                          float(self.box3.userParams['per'].GetValue()), float(self.box.userParams['inc'].GetValue()),
                          float(self.box3.userParams['gamma1'].GetValue()),float(self.box3.userParams['gamma2'].GetValue()),
                          float(self.box3.userParams['ecc'].GetValue()),float(self.box3.userParams['pericenter'].GetValue()),
                          float(self.box.userParams['t0'].GetValue())]
            apertureRadius = 4.5
            nSteps = float(self.box4.userParams['number'].GetValue())
            initBeta = (np.zeros([4]) + 0.012).tolist()        
            ## << The .tolist() method type casts the Numpy ndarray into a python list
    #         initBeta = [int(self.box2.userParams['b-Rp/Rs'].GetValue()), int(self.box2.userParams['b-a/Rs'].GetValue()),
    #                     int(self.box2.userParams['b-inc'].GetValue()), int(self.box2.userParams['b-t0'].GetValue())]
            
            idealAcceptanceRate = float(self.box4.userParams['acceptance'].GetValue())
            interval = float(self.box4.userParams['saveiteration'].GetValue())
            burnFraction = float(self.box4.userParams['burnfrac'].GetValue())
            #mcmcinstance = oscaar.fitting.mcmcfit(self.pT,initParams,initBeta,nSteps,interval,idealAcceptanceRate,
            #burnFraction)
            #mcmcinstance.run(updatepkl=True)
            #mcmcinstance.plot()
            
            ## Spawn a new process to execute the MCMC run separately
            mcmcCall = 'import oscaar.fitting; mcmcinstance = oscaar.fitting.mcmcfit("%s",%s,%s,%s,%s,%s,%s); mcmcinstance.run(updatepkl=True, apertureRadiusIndex=%s); mcmcinstance.plot(num=%s)' % \
                        (self.pT,initParams,initBeta,nSteps,interval,idealAcceptanceRate,burnFraction,
                         self.apertureRadiusIndex,self.apertureRadiusIndex)
            subprocess.call(['python','-c',mcmcCall])

    def radiusCheck(self):
        if self.radiusList.GetValue() == "":
            InvalidParameter(self.radiusList.GetValue(), self, -1, str = "radiusError")
            return False
        try:
            #self.tempNum = np.where(self.epsilonCheck(self.data.apertureRadii,float(self.radiusList.GetValue())))
            condition = self.epsilonCheck(self.data.apertureRadii,float(self.radiusList.GetValue()))
            self.tempNum = np.array(self.data.apertureRadii)[condition]
            if len(self.tempNum) == 0:
                tempString = self.radiusList.GetValue() + " was not found in " + str(self.data.apertureRadii)
                InvalidParameter(tempString, self, -1, str = "radiusListError2")
                return False
        except ValueError:
            InvalidParameter(self.radiusList.GetValue(), self, -1, str = "radiusError")
            return False
        return True

    def update(self,event):
        if self.LCB.boxList[1].GetValue() == '':
            InvalidParameter(self.LCB.boxList[1].GetValue(), None,-1, str="planet")
        else:
            self.planet = self.LCB.boxList[1].GetValue()
            [RpOverRs,AOverRs,per,inc,ecc] = returnSystemParams.transiterParams(self.planet)
            
            if RpOverRs == -1 or AOverRs == -1 or per == -1 or inc == -1 or ecc == -1:
                InvalidParameter(self.LCB.boxList[1].GetValue(), None,-1, str="planet")
            else:
                self.box.userParams['Rp/Rs'].SetValue(str(RpOverRs))
                self.box.userParams['a/Rs'].SetValue(str(AOverRs))
                self.box3.userParams['per'].SetValue(str(per))
                self.box.userParams['inc'].SetValue(str(inc))
                self.box3.userParams['ecc'].SetValue(str(ecc))
                InvalidParameter("",None,-1, str="params")

    def epsilonCheck(self,a,b):
        ''' Check when elements of list `a` are within machine precision of float `b`
            because otherwise we get machine precision difference errors when mixing
            single and double precion NumPy floats and pure Python built-in float types.
        '''
    	a = np.array(a)
        return np.abs(a-b) < np.finfo(np.float32).eps

    def radiusUpdate(self, event):
        self.apertureRadiusIndex = np.where(self.epsilonCheck(self.data.apertureRadii,
                                                              float(self.radiusList.GetValue())))[0][0]
        
    def on_exit(self, event):
        self.Destroy()
    
    def onDestroy(self, event):
        self.parent.loadMCMC = False

class ParameterBox(wx.Panel):

        def __init__(self, parent, id,list,name="",rows=1,cols=10,vNum=0,hNum=0,font=wx.NORMAL_FONT, other=True):               
            wx.Panel.__init__(self,parent,id)
            box1 = wx.StaticBox(self, -1, name)
            sizer = wx.StaticBoxSizer(box1, wx.VERTICAL)
            self.userParams = {}
            sizer0 = wx.FlexGridSizer(rows=rows, cols=cols, vgap=vNum, hgap=hNum)
            sizer.Add(sizer0, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
            
            for (widget, labeltxt, ToolTip, value) in list:
                label = wx.StaticText(self, -1, labeltxt, style=wx.ALIGN_CENTER)
                sizer0.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
                label.SetFont(font)
                
                if widget == "observatoryName" or widget == "fileName":
                    self.userParams[widget] = wx.TextCtrl(self, -1, value = value, size = (220,wx.DefaultSize.GetHeight()))
                elif widget != 'trackPlot' and widget != 'photPlot' and widget != 'flatType':
                    self.userParams[widget] = wx.TextCtrl(self, -1, value = value)
 
                if widget == 'trackPlot' or widget == 'photPlot' or widget == 'flatType':
                    if widget == 'flatType':
                        label1 = ToolTip
                        label2 = value
                    else:
                        label1 = "On"
                        label2 = "Off"
                    self.userParams[widget] = wx.RadioButton(self, label = label1, style = wx.RB_GROUP)
                    sizer0.Add(self.userParams[widget], 0, wx.ALIGN_CENTRE|wx.ALL, 0)
                    if other == False:
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
            
        def __init__(self, parent, id, parent2=None, name='', str ="Browse\t (Cntrl-O)", multFiles=False, rowNum=1, colNum=3,
                     vNum=0, hNum=0, font=wx.NORMAL_FONT, updateRadii=False, boxName="", height=20, saveType=wx.FD_OPEN):
            
            wx.Panel.__init__(self,parent,id)
            box1 = wx.StaticBox(self, -1, boxName)
            box1.SetFont(font)
            sizer = wx.StaticBoxSizer(box1, wx.VERTICAL)
            self.parent = parent2
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
                        if str == "Browse\t (Cntrl-O)":
                            str = "Browse\t("+u'\u2318'"-O)"
                        self.buttonList[iterationNumber] = wx.Button(self, -1, str)
                    else:
                        self.buttonList[iterationNumber] = wx.Button(self, -1, str)
                    self.buttonList[iterationNumber].Bind(wx.EVT_BUTTON, lambda event, lambdaIter = iterationNumber,
                                                          lambdaMult = multFiles, lambdaSave = saveType:
                    self.browseButtonEvent(event, "Choose Path(s) to File(s)",self.boxList[lambdaIter], lambdaMult,
                                           lambdaSave, update=updateRadii))
                    sizer0.Add(self.buttonList[iterationNumber],0,wx.ALIGN_CENTRE|wx.ALL,0)         
            self.SetSizer(sizer)
            sizer.Fit(self)

        def browseButtonEvent(self, event, message, textControl, fileDialog, saveDialog, update=False):
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
                    InvalidParameter("", self, -1, str="oldPKL") 
                
            dlg.Destroy()

class ScanParamsBox(wx.Panel):
    
    def __init__(self,parent,id):

        # Create a box with all the parameters that the users can manipulate.
        
        wx.Panel.__init__(self,parent,id)
        
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
        if self.userinfo['bin'].GetValue() == '':
            InvalidParameter(self.userinfo['bin'].GetValue(), None, -1, max=str(self.max))
            return False
        else:
            try:
                self.var = int(self.userinfo['bin'].GetValue())
            except ValueError:
                InvalidParameter(self.userinfo['bin'].GetValue(), None, -1, max=str(self.max))
                return False
             
            if int(self.userinfo['bin'].GetValue()) <= 4 or int(self.userinfo['bin'].GetValue()) > self.max:
                InvalidParameter(self.userinfo['bin'].GetValue(), None,-1, max=str(self.max))
                return False
            else:
                return True

    def boxDiff(self):
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
    
    def setMax(self,len):
        self.max = len
    
    def update(self):
        self.newNum = self.userinfo['bin'].GetValue()
        self.newX = self.userinfo['xlabel'].GetValue()
        self.newY = self.userinfo['ylabel'].GetValue()
        self.newtitle = self.userinfo['title'].GetValue()

class InvalidParameter(wx.Frame):

    def __init__(self, num, parent, id, str='', max='0', columns=2):

        if sys.platform == "win32":
            wx.Frame.__init__(self, parent, id, 'Invalid Parameter', size = (500,110))
        else:
            wx.Frame.__init__(self, parent, id, 'Invalid Parameter', size = (500,100))
            self.create_menu()
            self.Bind(wx.EVT_CHAR_HOOK, self.onCharOkay)   
        
        self.parent = parent
        if str == "params":
            self.SetTitle("Updated Parameters")
            self.Bind(wx.EVT_CHAR_HOOK, self.onOkay)
        elif str == "ds9":
            self.SetTitle("DS9 Error")
        elif str == "fitOpen":
            self.SetTitle("Fitting Frame Open Error")
        elif str == "warnError":
            self.SetTitle("Warning about local times!")
        elif str == "regionsUpdate":
            self.SetTitle("Regions File Set Added!")

        self.panel = wx.Panel(self)
        self.string = "invalid"
        
        if max != '0':
            self.string = "The bin size must be between 5 and "+max+"."
        if str == "Rp/Rs":
            self.string = "The value for Rp over Rs must be between 0 and 1."
        elif str == "a/Rs":
            self.string = "The value for A over Rs must be greater than 1."
        elif str == "inc":
            self.string = "The value for the inclincation must be between 0 and 90."
        elif str == "t0":
            self.string = "The value for the mid-transit time, t0, must be greater than 0."
        elif str == "gamma1":
            self.string = "The value entered for gamma1 must be a number."
        elif str == "gamma2":
            self.string = "The value entered for gamma2 must be a number."
        elif str == "gamma":
            self.string = "The value for Gamma1 + Gamma2 must be less than or equal to 1."
        elif str == "per":
            self.string = "The value for the period must be greater than 0."
        elif str == "ecc":
            self.string = "The value for the eccentricity must be between 0 and 1."
        elif str == "pericenter":
            self.string = "The value for the pericenter must be greater than or equal to 0."
        elif str == "planet":
            self.string = "The name of the planet does not exist in the database."
        elif str == "limbdark":
            self.string = "The parameter for Limb-Darkening must be either 'False', 'linear', or 'quadratic'."
        elif str == "saveiteration":
            self.string = "The iterative step to be saved must be greater than or equal to 5."
        elif str == "acceptance":
            self.string = "The acceptance rate must be greater than 0."
        elif str == "burnfrac":
            self.string = "The burn number must be greater than 0 and less than or equal to 1."
        elif str == "number":
            self.string = "The number of total steps must be greater than or equal to 10."
        elif str == "mod":
            self.string = "The iterative step to be saved cannot be greater than the total number of steps."
        elif str == "flat1":
            self.string = "The path(s) to flat images must be fixed."
        elif str == "flat2":
            self.string = "The path(s) to dark flat images must be fixed."
        elif str == "flat3":
            self.string = "The path to save the master flat must be fixed."
        elif str == "fits":
            self.string = "One or more of the files in " + max + " need to be fixed."
        elif str == "master":
            self.string = "Either more than one file has been entered, or the file entered needs to be fixed in the " +max+ \
                          "."
        elif str == "output":
            self.string = "Either you entered a directory, or the specified path cannot be made for the " + max + "."
        elif str == "leftbox":
            self.string = "Please enter a number for the " + max + "."
        elif str == "dateTime":
            self.string = "Please check the format and values entered for the ingress or egress " + max + ".\n"
            if max == "date":
                self.string += "The year must be within 100 years of today, the month must be between 1 and 12\nand" +\
                               " the day must be between 1 and 31."
            elif max == "time":
                self.string += "The hour must be between 0 and 23, while both the minutes and seconds must be between"+\
                              " 0 and 59.\nThe format is hh:mm:ss."
        elif str == "obsName" or str == "obsFile":
            self.string = "The observatory name or file name must be fixed."
        elif str == "logicalDate":
            self.string = "The starting date must come before the ending date."
        elif str == "logicalTime":
            self.string = "The starting time must come before the ending time when the dates are equal."
        elif str == "obsDate":
            self.string = "The starting date and ending date both need to be in the format YYYY/MM/DD with integers."
        elif str == "dateRange":
            self.string = "The year must be within 100 years of today, the month must be between 1 and 12,\nand the"+\
                          " day must be between 1 and 31."
        elif str == "coordRange":
            self.string = "The latitude must be between 90 and -90 degrees, while the longitude must be \nbetween "+\
                          "0 and 180 degrees. Both must have min and sec in between 0 and 59."
        elif str == "coordTime":
            self.string = "The longitude and latitude must be in the format Deg:Min:Sec with numbers."
        elif str == "tempElevNum":
            if max == "apparent magnitude upper limit":
                self.string = "The " + max + " must be a number."
            else:
                self.string = "The " + max + " must be a number greater than or equal to 0."
        elif str == "twilight":
            self.string = "The twilight must be -6, -12, or -18. Please select one from the drop down menu."
        elif str == "lowerElevation":
            self.string = "The lower elevation limist needs to be in the format Deg:Min:Sec, "+\
                          "with min and sec\nbetween 0 and 59. The degrees must be between 0 and 90."
        elif str == "radiusNum":
            self.string = "The aperture radii values must be numbers."
        elif str == "radiusEqual":
            self.string = "The min and max aperture radii cannot be equal."
        elif str == "radiusStep":
            self.string = "The aperture radii step size cannot be smaller than the difference between the maximum\n" + \
                          "radius and the minimum radius. The format for this is \"min, max, stepsize\"."
        elif str == "radiusLogic":
            self.string = "The minimum aperture radius must be smaller than the maximum. None of the 3 parameters\n" + \
                          "can be equal to 0."
        elif str == "radiusLogic2":
            self.string = "None of the aperture radii can be equal to 0."
        elif str == "radiusError":
            self.string = "The radius you entered was empty or not a number. Please enter a valid number."
        elif str == "radiusListError":
            self.string = "The plotting methods rely on the aperture radii list from the .pkl file. You\n" + \
                          "must update the radii list to continue."
        elif str == "radiusListError2":
            self.string = "The radius you entered was not in the aperture radii list for this .pkl file.\n" + \
                          "Please pick a radius from the approved radii in the drop down menu."
        elif str == "utZone":
            self.string = "The time zone must be between -12 and 12. Please choose one from the drop down menu."
        elif str == "regionsError1":
            self.string = "Either the regions file or reference file for this set is empty. You cannot add an " + \
                          "extra\nregions file without a referenced data image."
        elif str == "regionsError2":
            self.string = "You have entered a filename that does not exist or more than one file. There can " + \
                          "only be one regions file\nand one reference file entered at a time for a set."
        elif str == "regionsError3":
            self.string = "The regions file must be a valid .reg file."
        elif str == "regionsError4":
            self.string = "The reference file must be a valid .fits or .fit file."
        elif str == "emptyReg":
            self.string = "You must enter a regions file. If you wish you can enter additional sets of regions " + \
                          "files\nafter at least one has been entered."
        elif str == "invalidReg":
            self.string = "This regions file was not found, or is not a vaild .reg file."
        elif str == "invalidRef":
            self.string = "This reference file was not found, or is not a valid .fits or .fit file."
        elif str == "invalidRefExist":
            self.string = "This reference file was not found in the list of data images. Please add it to the list of" + \
                          "data images and try again."
        elif str == "outofbounds":
            self.string = "You must enter extra regions files as sets with a reference file. The format is " + \
                          "\"regionsFiles,referenceFile;\"."
        elif str == "referenceImageDup":
            self.string = "The reference image you have listed in this set is already assigned to another regions file."
        elif str == "emptyKeyword":
            self.string = "The exposure time keyword cannot be empty. Please use a valid phrase, or choose from the drop" + \
                          "down menu."
        elif str == "invalidKeyword":
            self.string = "The keyword you entered was not found in the header of the first data image."
        elif str == "emailKeyword":
            self.string = "This keyword is in the header file of the first data image, but is not something we " + \
                          "have a conversion method for.\nPlease email us the keyword you are trying to use and we " + \
                          "will include it into our list of possible keywords."
        self.okButton = wx.Button(self.panel,label = "Okay", pos = (125,30))
        self.Bind(wx.EVT_BUTTON, self.onOkay, self.okButton)
        
        if str == "path":
            self.text = wx.StaticText(self.panel, -1, "The following is an invalid output path: " + num)
        elif str == "params":
            self.text = wx.StaticText(self.panel, -1, "The appropriate parameters have been updated.")
        elif str == "ds9":
            self.Bind(wx.EVT_WINDOW_DESTROY, self.ds9Error)
            self.text = wx.StaticText(self.panel, -1, 
                                       "It seems that ds9 may not have installed correctly, please try again.")
        elif str == "importError":
            self.text = wx.StaticText(self.panel, -1, "Failed to import ephem, please try again.")
        elif str == "fitOpen":
            self.Bind(wx.EVT_WINDOW_DESTROY, self.fitError)
            self.text = wx.StaticText(self.panel, -1, "Please close the fitting frame window and try again.")
        elif str == "warnError":
            self.Bind(wx.EVT_WINDOW_DESTROY, self.parent.calculate)
            self.text = wx.StaticText(self.panel, -1, "Please be careful. The local times are calculated using " + \
                                       "PyEphem's ephem.localtime(\"input\") method. Make sure\nthat this method " + \
                                       "produces the correct local time for yourself. If you don't know how to check " + \
                                       "this, please refer\nto the documentation from the help menu in the main frame. " + \
                                       "This message is shown once per GUI session,\nand will run the calculations " + \
                                       "for the current parameters as soon as you close this window.")
        elif str == "oldPKL":
            self.text = wx.StaticText(self.panel, -1, "This seems to be an outdated .pkl file, sorry. Try creating" + \
                                       " a new .pkl file from the main frame and try again.\nIf this .pkl file is" + \
                                       " important and cannot be recreated, talk to our developers for information on" + \
                                       " how to extract \nthe data from the file.")
        elif str == "regionsUpdate":
            self.text = wx.StaticText(self.panel, -1, "This set has been added to the list of regions sets in the main GUI.")
        else:
            self.text = wx.StaticText(self.panel, -1, self.string +"\nThe following is invalid: " + num)
        
        self.sizer0 = wx.FlexGridSizer(rows=2, cols=columns) 
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.text,0,wx.ALIGN_CENTER|wx.ALL,5)

        self.sizer0.Add(self.okButton,0,wx.ALIGN_CENTER|wx.ALL,5)

        self.panel.SetSizer(self.hbox)
        self.hbox.Fit(self)
        self.Center()
        self.Show()

    def ds9Error(self, event):
        self.parent.ds9Open = False

    def fitError(self, event):
        self.parent.loadFitError = False

    def create_menu(self):
        
        # These commands create a drop down menu with the exit command.
        
        self.menubar = wx.MenuBar()
        
        menu_file = wx.Menu()
        m_exit = menu_file.Append(-1, "Exit\tCntrl-X", "Exit")
        self.Bind(wx.EVT_MENU, self.onOkay, m_exit)
        
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)
    
    def onCharOkay(self,event):
        self.keycode = event.GetKeyCode()
        if self.keycode == wx.WXK_RETURN:
            self.Destroy()
    
    def onOkay(self, event):
        self.Destroy()
            

def checkParams(self,list):
    
    self.tempGamma1 = -1
    self.tempGamma2 = -1
    self.tempSaveIteration = -1
    self.tempNumber = -1
    
    for (number,string) in list:
        if number == '':
            InvalidParameter(number, None,-1, str=string)
            return False
        else:
            try:
                if string !="limbdark":
                    self.tmp = float(number)
            except ValueError:
                InvalidParameter(number, None,-1, str=string)
                return False
            if string == "Rp/Rs":
                if float(number)>1 or float(number)<0:
                    InvalidParameter(number, None,-1, str=string)
                    return False
            if string == "a/Rs":
                if float(number) <= 1:
                    InvalidParameter(number, None,-1, str=string)
                    return False
            if string == "per":
                if float(number) < 0:
                    InvalidParameter(number, None,-1, str=string)
                    return False
            if string == "inc":
                if float(number) < 0 or float(number) > 90:
                    InvalidParameter(number, None,-1, str=string)
                    return False
            if string == "t0":
                if float(number) < 0:
                    InvalidParameter(number, None,-1, str=string)
                    return False
            if string == "ecc":
                if float(number) < 0 or float(number) > 1:
                    InvalidParameter(number, None,-1, str=string)
                    return False
            if string == "pericenter":
                if float(number) < 0:
                    InvalidParameter(number, None,-1, str=string)
                    return False
            if string == "limbdark":
                if (number != "False"):
                    if (number != "linear"):
                        if(number != "quadratic"):
                            InvalidParameter(number,None,-1,str=string)
                            return False
            if string == 'gamma1':
                self.tempGamma1 = number
            if string == 'gamma2':
                self.tempGamma2 = number
            if string == "saveiteration":
                self.tempSaveIteration = float(number)
                if float(number) < 5:
                    InvalidParameter(number,None,-1,str=string)
                    return False
            if string == "number":
                self.tempNumber = float(number)
                if float(number) < 10:
                    InvalidParameter(number,None,-1,str=string)
                    return False
            if string == "acceptance":
                if float(number) <= 0:
                    InvalidParameter(number,None,-1,str=string)
                    return False
            if string == "burnfrac":
                if float(number) > 1 or float(number) <= 0:
                    InvalidParameter(number,None,-1,str=string)
                    return False
    
    if(self.tempNumber != -1) and (self.tempSaveIteration != -1):
        if (self.tempNumber % self.tempSaveIteration) != 0:
            tempString = str(self.tempSaveIteration)+" < "+str(self.tempNumber)
            InvalidParameter(tempString,None,-1,str="mod")
            return False
    
    self.totalGamma = float(self.tempGamma1) + float(self.tempGamma2)
    self.totalString = str(self.totalGamma)
    if self.totalGamma > 1:
        InvalidParameter(self.totalString, None,-1, str="gamma")
        return False

    return True

app = wx.App(False)
#### Runs the GUI ####
OscaarFrame()
app.MainLoop()
