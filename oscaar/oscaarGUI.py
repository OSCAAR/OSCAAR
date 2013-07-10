import threading
import wx
import os
import sys
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
import transiterFit
import systematics
import IO
from matplotlib import pyplot
import matplotlib
from oscaar.extras.knownSystemParameters import returnSystemParams
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas, \
    NavigationToolbar2WxAgg as NavigationToolbar
import numpy as np
import pylab

APP_EXIT = 1

class OscaarFrame(wx.Frame): ##Defined a class extending wx.Frame for the GUI
    
    def __init__(self):
        
        self.aboutOpen = False
        self.loadOldPklOpen = False
        self.loadFittingOpen = False
        self.loadMCMC = False
        self.loadMasterFlat = False
        self.overWrite = False
        self.ds9Open = False
        self.loadFitError = False
        self.loadEphFrame = False
        self.title = "OSCAAR"
        wx.Frame.__init__(self,None,-1, self.title)
        self.panel = wx.Panel(self)
                
        if sys.platform == "win32":
            self.fontType = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
            self.row = 1
        else: 
            self.fontType = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
            self.row = 5
        
        self.static_bitmap = wx.StaticBitmap(self.panel)
        self.logo = wx.Image(os.path.join(os.path.dirname(__file__),'images','logo4.png'), wx.BITMAP_TYPE_ANY)
        self.bitmap = wx.BitmapFromImage(self.logo)
        self.static_bitmap.SetBitmap(self.bitmap)
        
        self.paths = AddLCB(self.panel, -1, name = "mainGUI", str = "Browse", rowNum=self.row, vNum = 15, hNum = 5, font = self.fontType)
        self.topBox = wx.BoxSizer(wx.HORIZONTAL)
        self.topBox.Add(self.paths, border = 5, flag = wx.ALL)

        list = [('zoom',"Track Zoom: ",
                 'Enter a number for the zoom here.','15'),
                ('ccd',"CCD Gain: ",
                 'Enter a decimal for the gain here.','1.0'),
                ('radius',"Aperture Radius: ",
                 'Enter a decimal for the radius here.','4.5'),
                ('smoothing',"Smoothing Constant: ", 
                 'Enter an integer for smoothing here.','3'),
                ('notes',"Notes: ","",'Enter notes to be saved here.')]
        
        if sys.platform == "win32":
            self.row = 4
        
        self.leftBox = ParameterBox(self.panel,-1,list,rows=self.row,cols=2, vNum=10, hNum=10, font=self.fontType)
        
        list = [('trackPlot',"Tracking Plots: ","none",''),
                ('photPlot',"Photometry Plots: ","none",''),
                ('ingress',"Ingress, UT (YYYY/MM/DD)",
                 "Enter a date in the correct format here.","YYYY/MM/DD"),
                ('egress',"Egress, UT (YYYY/MM/DD)",
                 "Enter a date in the correct format here.","YYYY/MM/DD")]
        
        if sys.platform == "win32":
            self.row = 2
        else:
            self.row = 4
            
        self.radioBox = ParameterBox(self.panel,-1,list, rows = self.row, cols = 3, vNum = 10, hNum = 10, font = self.fontType)
        
        self.sizer0 = wx.FlexGridSizer(rows=1, cols=4)
        self.buttonBox = wx.BoxSizer(wx.HORIZONTAL)
        self.buttonBox.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)

        self.ephButton = wx.Button(self.panel,label="Ephemeris")
        self.masterFlatButton = wx.Button(self.panel, label = "Master Flat Maker")
        self.ds9Button = wx.Button(self.panel, label = "Open DS9")
        self.runButton = wx.Button(self.panel, label = "Run")
        
        self.Bind(wx.EVT_BUTTON, lambda evt: self.singularExistance(evt, self.loadEphFrame, "ephemeris"), self.ephButton)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.singularExistance(evt, self.loadMasterFlat, "masterFlat"),
                  self.masterFlatButton)
        self.Bind(wx.EVT_BUTTON, lambda evt: self.singularExistance(evt, self.ds9Open, "ds9"), self.ds9Button)
        self.Bind(wx.EVT_BUTTON, self.runOscaar, self.runButton)
   
        self.sizer0.Add(self.ephButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.masterFlatButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.ds9Button,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.runButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        
        self.rightBox = wx.BoxSizer(wx.VERTICAL)
        self.rightBox.Add(self.radioBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)
        self.rightBox.Add(self.buttonBox, 0, flag = wx.ALIGN_CENTER | wx.ALL, border = 5)

        self.bottomBox = wx.BoxSizer(wx.HORIZONTAL)
        self.bottomBox.Add(self.leftBox, 0, flag = wx.ALIGN_CENTER)
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
        m_loadOld = menu_oscaar.Append(-1, "Load old output\tCtrl+L", "Load an old output file for further analysis.")
        m_loadFitting = menu_oscaar.Append(-1, "Fitting Routines\tCtrl-F", 
                                              "Different fitting methods for analysis of an old .pkl file.")
        m_about = menu_oscaar.Append(-1, "About", "Contributors of OSCAAR.")
        self.Bind(wx.EVT_MENU, lambda evt: self.openLink(evt, "http://var2.astro.cz/ETD/predictions.php"), m_ttp)
        self.Bind(wx.EVT_MENU, lambda evt: self.singularExistance(evt, self.aboutOpen, "about"), m_about)
        self.Bind(wx.EVT_MENU, lambda evt: self.singularExistance(evt, self.loadOldPklOpen, "loadOld"), m_loadOld)
        self.Bind(wx.EVT_MENU, lambda evt: self.singularExistance(evt, self.loadFittingOpen, "loadFitting"), m_loadFitting)

        menubar.Append(menu_file, "File")
        menubar.Append(menu_help, "Help")
        menubar.Append(menu_oscaar, "Oscaar")
        self.SetMenuBar(menubar)       

    def runOscaar(self, event):
        notes = open(os.path.join(os.path.dirname(__file__),'outputs','notes.txt'), 'w')
        notes.write('\n\n\n------------------------------------------'+\
                    '\nRun initiated (LT): '+strftime("%a, %d %b %Y %H:%M:%S"))
        if self.leftBox.userParams['notes'].GetValue() == 'Enter notes to be saved here.':
            notes.write('\nNo notes entered.')
        else:
            notes.write('\nNotes: '+ self.leftBox.userParams['notes'].GetValue())
        notes.close()
        
        invalidDarkFrames = self.checkArray(self.paths.boxes[0].GetValue(), "fit")
        masterFlat = self.paths.boxes[1].GetValue()
        invalidDataImages = self.checkArray(self.paths.boxes[2].GetValue(), "fit")
        regionsFile = self.paths.boxes[3].GetValue()
        self.outputFile = self.paths.boxes[4].GetValue()
                
        if invalidDarkFrames != "": 
            InvalidParameter(invalidDarkFrames, None, -1, str="fits", max="the path to Dark Frames")
        elif os.path.isfile(masterFlat) != True:
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
        elif os.path.isfile(regionsFile) != True or regionsFile.endswith(".reg") != True:
            tempString = regionsFile
            if len(regionsFile.split(",")) > 1:
                tempString = ""
                for string in regionsFile.split(","):
                    if string == "" and len(regionsFile.split(",")) == 2:
                        tempString += ","
                    else:
                        tempString += "\n" + string.strip()
            InvalidParameter(tempString, None, -1, str="master", max="path to Regions File")
        elif not os.path.isdir(self.outputFile[self.outputFile.rfind(os.sep)]) or \
             not len(self.outputFile) > (len(self.outputFile[:self.outputFile.rfind(os.sep)]) + 1):
            InvalidParameter(self.outputFile, None, -1, str="output", max="output file")
        
        elif self.timeAndDateCheck(self.radioBox.userParams['ingress1'].GetValue(),
                                   self.radioBox.userParams['egress1'].GetValue(),
                                   self.radioBox.userParams['ingress'].GetValue(),
                                   self.radioBox.userParams['egress'].GetValue()) == True:
            try:
                values = {}
                list = ["smoothing", "zoom"]
                for string in list:
                    values[string] = int(self.leftBox.userParams[string].GetValue())
                list = ["radius","ccd"]
                for string in list:
                    values[string] = float(self.leftBox.userParams[string].GetValue())

                # This code here writes all the parameters to the init.par file.
                
                init = open(os.path.join(os.path.dirname(__file__),'init.par'), 'w')
                self.darkFits = self.addFits(init, "Path to Dark Frames: ", self.paths.boxes[0].GetValue())
                self.imagFits = self.addFits(init, "Path to data images: ", self.paths.boxes[2].GetValue())
                init.write("Path to Master-Flat Frame: " + self.paths.boxes[1].GetValue() + "\n")
                init.write("Path to regions file: " + self.paths.boxes[3].GetValue() + "\n")
                if not self.paths.boxes[4].GetValue().endswith(".pkl"):
                    init.write("Output Path: " + self.paths.boxes[4].GetValue() + ".pkl\n")
                else:
                    init.write("Output Path: " + self.paths.boxes[4].GetValue() + "\n")
        
                self.parseTime(self.radioBox.userParams["ingress"].GetValue(),
                               self.radioBox.userParams["ingress1"].GetValue(), 'Ingress: ',  init)
                self.parseTime(self.radioBox.userParams["egress"].GetValue(),
                               self.radioBox.userParams["egress1"].GetValue(), 'Egress: ',  init)
                if self.radioBox.userParams['trackPlot'].GetValue():
                    init.write("Plot Tracking: " + "on"+ "\n")
                else:
                    init.write("Plot Tracking: " + "off"+ "\n")
                if self.radioBox.userParams['photPlot'].GetValue():
                    init.write("Plot Photometry: " + "on"+ "\n")
                else:
                    init.write("Plot Photometry: " + "off"+ "\n")
                
                init.write("Smoothing Constant: " + str(values["smoothing"]) + '\n')
                init.write("CCD Gain: " + str(values["ccd"]) + '\n')
                init.write("Radius: " + str(values["radius"]) + '\n')
                init.write("Tracking Zoom: " + str(values["zoom"]) + '\n')
                init.write("Init GUI: on")
                init.close()
                if self.loadFittingOpen == False:
                    if os.path.isfile(self.outputFile) or os.path.isfile(self.outputFile + '.pkl'):
                        if self.overWrite == False:
                            OverWrite(self, -1, "Overwrite Output File", self.outputFile, "Output File")
                            self.overWrite = True
                    else:
                        diffPhotCall = "from oscaar import differentialPhotometry"
                        subprocess.check_call(['python','-c',diffPhotCall])
                        wx.CallAfter(self.createFrame)

                else:
                    if self.loadFitError == False:
                        InvalidParameter("", self, -1, str="fitOpen")
                        self.loadFitError = True
            except ValueError:
                string2 = string
                if string2 == "ccd":
                    string2 = "ccd gain"
                elif string2 == "smoothing":
                    string2 = "smoothing constant"
                InvalidParameter(self.leftBox.userParams[string].GetValue(),None,-1, str="leftbox", max=string2)
    
    def timeAndDateCheck(self, time1, time2, date1, date2):
        timeCheck = False
        dateCheck = False
        for eachTime in [time1,time2]:
            if len(eachTime.split(":")) != 3:
                InvalidParameter(eachTime, None, -1, str = "dateTime", max = "time")
                return False
            for num in eachTime.split(":"):
                num = num.strip()
                if len(num) > 2:
                    InvalidParameter(eachTime, None, -1, str = "dateTime", max = "time")
                    return False
                try:
                    int(num)
                except ValueError:
                    InvalidParameter(eachTime, None, -1, str = "dateTime", max = "time")
                    return False
        for eachDate in [date1,date2]:
            if len(eachDate.split("/")) != 3:
                InvalidParameter(eachDate, None, -1, str = "dateTime", max = "date")
                return False
            dateArray = eachDate.split("/")
            dateArray = [x.strip() for x in dateArray]
            if len(dateArray[0]) > 4 or len(dateArray[1]) > 2 or len(dateArray[2]) > 2:
                InvalidParameter(eachDate, None, -1, str = "dateTime", max = "date")
                return False
            try:
                for num in dateArray:
                    int(num)
            except ValueError:
                InvalidParameter(eachDate, None, -1, str = "dateTime", max = "date")
                return False
            
        return True
    
    def setDefaults(self):
        oscaarpath = os.path.dirname(os.path.abspath(oscaar.__file__))
        init = open(os.path.join(oscaarpath,'init.par'), 'r').read().splitlines()
        for line in init:
            if len(line.split()) > 1:
                inline = line.split(':', 1)
                name = inline[0].strip()
                value = str(inline[1].strip())
                list = [("Path to Master-Flat Frame", 1),
                        ("Path to regions file", 3),
                        ("Ingress", "ingress"),("Egress", "egress"),
                        ("Radius", "radius"),("Tracking Zoom", "zoom"),
                        ("CCD Gain", "ccd"),("Plot Tracking", "trackPlot"),
                        ("Plot Photometry", "photPlot"),("Smoothing Constant", "smoothing"),
                        ("Output Path",4),("Path to Dark Frames", 0),("Path to data images", 2)]
                
                for string,save in list:
                    if string == name:
                        if name == "Smoothing Constant" or name == "Radius" or name == "Tracking Zoom" or name == "CCD Gain":
                            self.leftBox.userParams[save].SetValue(value)
                        elif name == "Plot Photometry" or name == "Plot Tracking":
                            if value == "off":
                                save += "1"
                            self.radioBox.userParams[save].SetValue(True)
                        elif name == "Path to Dark Frames" or name == "Path to Master-Flat Frame" or \
                        name == "Path to data images" or name == "Path to regions file" or name == "Output Path":
                            self.paths.boxes[save].SetValue(value)
                        else:
                            date = value.split(";")[0].strip().replace("-","/")
                            time = value.split(";")[1].strip()
                            self.radioBox.userParams[save].SetValue(date)
                            self.radioBox.userParams[save+"1"].SetValue(time)
            
    def addFits(self, init, field, path):
        pathList = []
        for impath in path.split(','):
            newpath = impath
            if os.path.isdir(impath) and not (impath.endswith(os.sep)):
                newpath += os.sep
            if newpath.endswith(os.sep):
                newpath += '*.fits'
            pathList += glob(newpath)
            
        initText = ''
        for path in range(len(pathList)):
            initText += pathList[path]
            if path != len(pathList)-1:
                initText += ","
        init.write(field + initText + '\n')
        return pathList
                
    def checkArray(self,array,param1):
        errorString = ""
        if param1 == 'fit':
            for element in array.split(","):
                if not element.endswith('.fit') and not element.endswith('.fits'):
                    errorString += "\n" + element
        else:
            for element in array.split(","):
                if not element.endswith('.reg'):
                    return False
        if not array:
            return "No Values Entered"
        else:
            return errorString   
    
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
                    EphFrame(self)
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

    def parseTime(self, date, time, text, filename):
        
        dateArr = str(date).split('/')
        result = str(dateArr[0]).strip() + '-' + str(dateArr[1]).strip() + '-' + str(dateArr[2]).strip() + ' ; '
        result += str(time)
        filename.write(text + result + '\n')
    
    def checkRB(self, button, text, filename):
        if button.GetValue() == True:
            filename.write(text + 'on\n')
        else:
            filename.write(text + 'off\n')

    def createFrame(self):
        if self.loadFittingOpen == False:
            if not self.outputFile.endswith(".pkl"):
                FittingFrame(self, -1, self.outputFile + ".pkl")
                self.loadFittingOpen = True
            else:
                FittingFrame(self, -1, self.outputFile)
            self.loadFittingOpen = True

    def openLink(self, event, string):
        webbrowser.open_new_tab(string)
    
    def on_exit(self, event):
        self.Destroy()

class MasterFlatFrame(wx.Frame):
    def __init__(self, parent, id):
        
        wx.Frame.__init__(self, parent, id, "Master Flat Maker")
        self.panel = wx.Panel(self)
        self.parent = parent
        self.overWrite = False
        self.titlebox = wx.StaticText(self.panel, -1, 'OSCAAR: Master Flat Maker')
        self.titleFont = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.titlebox.SetFont(self.titleFont)
        
        self.path1 = AddLCB(self.panel, -1, "Path to Flat Images: ","Browse")
        self.path2 = AddLCB(self.panel, -1, "Path to Dark Flat Images: ","Browse")
        self.path3 = AddLCB(self.panel, -1, "Path to Save Master Flat: ","Browse")
        
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
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.Center()
        self.Show()
        
    def onDestroy(self,event):
        self.parent.loadMasterFlat = False

    def run(self,event):
        
        path = self.path3.txtbox.GetValue()
        self.flatImages = []
        self.darkFlatImages = []
        for pathname in self.path1.txtbox.GetValue().split(','):
            self.flatImages += glob(pathname)
        for pathname in self.path2.txtbox.GetValue().split(','):
            self.darkFlatImages += glob(pathname)
        if not self.flatImages:
            InvalidParameter(str(self.path1.txtbox.GetValue()), None, -1, str="flat1")
        elif not self.darkFlatImages:
            InvalidParameter(str(self.path2.txtbox.GetValue()), None, -1, str="flat2")
        elif not path:
            InvalidParameter(str(path), None, -1, str="flat3")
        elif not os.path.isdir(path[path.rfind(os.sep)]) or \
             not len(path) > (len(path[:path.rfind(os.sep)]) + 1):
            InvalidParameter(path, None, -1, str="flat3")
        else:
            if not path.endswith('.fits') and not path.endswith('.fit'):
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
                    systematics.standardFlatMaker(self.flatImages, self.darkFlatImages, self.path3.txtbox.GetValue(),
                                              self.plotCheck)
                else:
                    systematics.twilightFlatMaker(self.flatImages, self.darkFlatImages, self.path3.txtbox.GetValue(),
                                              self.plotCheck)

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
        self.Bind(wx.EVT_BUTTON, lambda evt: self.parent.openLink(evt, "https://github.com/OSCAAR/OSCAAR"), self.viewRepoButton)
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
        self.paths = wx.StaticText(self.panel, -1, "Are you sure you want to overwrite\n" + self.path + "?")
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
        self.sizer0.Add(self.paths,0,wx.ALIGN_CENTER|wx.ALL,5)
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
                                     self.parent.path3.txtbox.GetValue(), self.parent.plotCheck)
        else:
            systematics.twilightFlatMaker(self.parent.flatImages, self.parent.darkFlatImages, 
                                     self.parent.path3.txtbox.GetValue(), self.parent.plotCheck)
    def onOutputFile(self,event):
        self.Destroy()
        self.parent.overWrite = False
        diffPhotCall = "from oscaar import differentialPhotometry"
        subprocess.check_call(['python','-c',diffPhotCall])
        wx.CallAfter(self.parent.createFrame)

    def onOkay(self, event):
        self.parent.overWrite = False    
        self.Destroy()
        
    def doNothing(self,event):
        pass
        
class EphFrame(wx.Frame):
     def __init__(self, *args, **kwargs):
         super(EphFrame, self).__init__(*args, **kwargs)
         self.parent = args[0]
         self.initUI()
     
     def initUI(self):
         self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
         if(sys.platform == 'darwin' or sys.platform == 'linux2'):
             self.labelFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
         else: self.labelFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
         self.titleFont = wx.Font(17, wx.DEFAULT, wx.NORMAL, wx.BOLD)
         self.subTitleFont = wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.BOLD)
         self.SetTitle('Ephemerides')
         self.ctrlList = []
         self.ephSizer = wx.GridBagSizer(5,5)
         obsList = glob(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'extras','eph','observatories','*.par'))
         nameList = []
         for file in obsList:        ## Gather all available observatory names
             openfile = open(file,'r').read().splitlines()
             for line in openfile: 
                 if line.split(':')[0] == 'name':
                     nameList.append(line.split(':')[1].strip())
         nameList += ['Enter New Observatory']
     
         self.menuBar = wx.MenuBar()
         self.fileMenu = wx.Menu()
         self.menuBar.Append(self.fileMenu, '&File')
         self.save = self.fileMenu.Append(-1, 'Save', 'Save')
         self.SetMenuBar(self.menuBar)
         self.Bind(wx.EVT_MENU, self.saveOutput, self.save)
     
         self.observatory = wx.ComboBox(self, value = 'Observatories', choices = nameList, name = 'Observatories', size = (320,25))
         self.observatory.Bind(wx.EVT_COMBOBOX, self.enterNewObs)
         self.title = wx.StaticText(self, -1, 'Ephemeris Calculator')
         self.title.SetFont(self.titleFont)
         self.name = wx.TextCtrl(self, value = 'Name', size = (205,25))
         self.filename = wx.TextCtrl(self, value = 'Filename', size = (205,25))
         self.startSemDate = wx.TextCtrl(self, value = datetime.datetime.now().strftime("%Y/%m/%d"))
         self.endSemDate = wx.TextCtrl(self, value = (datetime.datetime.now()+datetime.timedelta(days=7)).strftime("%Y/%m/%d"))
         self.latitude = wx.TextCtrl(self, value = 'deg:min:sec')
         self.longitude = wx.TextCtrl(self, value = 'deg:min:sec')
         self.elevation = wx.TextCtrl(self, value = '0.0')
         self.temp = wx.TextCtrl(self, value = '0.0')
         self.v_limit = wx.TextCtrl(self, value = '0.0')
         self.depth_limit = wx.TextCtrl(self, value = '0.0')
         self.selectObsLbl = wx.StaticText(self, -1, 'Select Observatory: ')
         self.selectObsLbl.SetFont(self.labelFont)
         self.html_out = wx.RadioBox(self, -1, label = 'HTML Out', choices = ['True', 'False'])
         self.text_out = wx.RadioBox(self, -1, label = 'Text Out', choices = ['True', 'False'])
         self.calc_transits = wx.RadioBox(self, -1, label = 'Calc Transits', choices = ['True', 'False'])
         self.calc_eclipses = wx.RadioBox(self, -1, label = 'Calc Eclipses', choices = ['True', 'False'])
         self.twilightType = wx.TextCtrl(self,-1, value = '0')
         self.min_horizon = wx.TextCtrl(self,-1,value = 'deg:min:sec')
         self.calcButton = wx.Button(self,-1,label = 'Calculate', size = (110,25))
         self.advancedOptions = wx.StaticText(self, -1, 'Advanced Options')
         self.advancedOptions.SetFont(self.subTitleFont)
         self.ephSizer.Add(self.title, (0,0), (1,2), wx.LEFT | wx.TOP, 7)
         self.ephSizer.Add(self.selectObsLbl, (1,0), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
         self.ephSizer.Add(self.observatory, (1,1), (1,3), wx.TOP | wx.LEFT, 7)
         self.ephSizer.Add(self.advancedOptions, (6,0), (1,2), wx.TOP | wx.LEFT, 7)
             
         self.addTextCtrl(2,0, self.name, wx.StaticText(self,-1,'Name of Observatory: '), (1,2))
         self.addTextCtrl(3,0, self.filename, wx.StaticText(self,-1,'Enter File Name: '), (1,2))
         self.addDateCtrl(4,0, self.startSemDate,wx.StaticText(self, -1, "Start of Obs, UT (YYYY/MM/DD): "))
         self.addDateCtrl(5,0, self.endSemDate, wx.StaticText(self, -1, "End of Obs, UT (YYYY/MM/DD): "))
         self.addTextCtrl(7,0, self.latitude, wx.StaticText(self, -1, 'Latitude (deg:min:sec):'), wx.DefaultSpan)
         self.addTextCtrl(8,0, self.longitude, wx.StaticText(self, -1, 'Longitude (deg:min:sec):'), wx.DefaultSpan)
         self.addTextCtrl(9,0, self.elevation, wx.StaticText(self, -1, 'Observatory Elevation (m): '), wx.DefaultSpan)
         self.addTextCtrl(10,0, self.temp, wx.StaticText(self, -1, 'Temperature (Celcius): '), wx.DefaultSpan)
         self.addTextCtrl(4,3, self.v_limit, wx.StaticText(self,-1, '     V upper limit: '), wx.DefaultSpan)
         self.addTextCtrl(5,3, self.depth_limit, wx.StaticText(self,-1,'     Depth Lower Limit: '), wx.DefaultSpan)
         self.addTextCtrl(11,0, self.twilightType, wx.StaticText(self,-1, 'Twilight Type (Default = -6): '), wx.DefaultSpan)
         self.addTextCtrl(12,0, self.min_horizon, wx.StaticText(self,-1, 'Lower Elevation Limit (deg:min:sec): '), wx.DefaultSpan)
         self.addRadioBox(7,3, self.html_out)
         self.addRadioBox(9,3, self.text_out)
         self.addRadioBox(11,3, self.calc_transits)
         self.addRadioBox(2,4, self.calc_eclipses)
 
         self.addButton(1,3, self.calcButton)
         self.Bind(wx.EVT_BUTTON, self.calculate)
         
         self.bestSize = self.GetBestSizeTuple()
         self.SetSize((self.bestSize[0]+20,self.bestSize[1]+20))
 
         self.SetBackgroundColour(wx.Colour(233,233,233))
         self.SetSizer(self.ephSizer)
         self.bestSize = self.GetBestSizeTuple()
         self.SetSize((self.bestSize[0]+20,self.bestSize[1]+20))
         self.Centre()
         self.Show()
         
     def addDateCtrl(self, row, colStart, dateCtrl, label):
         label.SetFont(self.labelFont)
         self.ephSizer.Add(label, (row, colStart), (1,2), wx.LEFT | wx.TOP, 7)
         self.ephSizer.Add(dateCtrl, (row, colStart+2), wx.DefaultSpan, wx.TOP , 7)
         
     def addTextCtrl(self, row, colStart, textCtrl, label, span):
         label.SetFont(self.labelFont)
         self.ephSizer.Add(label, (row, colStart), (1,2), wx.LEFT | wx.TOP, 7)
         self.ephSizer.Add(textCtrl, (row, colStart+2), span, wx.TOP, 7)
         
     def addButton(self, row, colStart, button):
         self.ephSizer.Add(button, (row, colStart+2), (1,2), wx.TOP | wx.RIGHT, 7)
         
     def addRadioBox(self, row, colStart, radioBox):
         self.ephSizer.Add(radioBox, (row, colStart), (2,2), wx.LEFT | wx.TOP, 12)
         
     def enterNewObs(self, event):
         if self.observatory.GetValue() == 'Enter New Observatory':
             self.filename.SetValue('Enter Filename for Observatory')
             self.name.SetValue('Enter Name of Observatory')
         else:
             '''This is a hack so as to display the observatory names in the drop down menu but to
                open files using the glob() retrieved paths. It could be cleaned up. -BM'''
             obsList = glob(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'extras','eph','observatories','*.par'))
             nameList = []
             #for i in obsList:
             #    nameList.insert(0,i[i.rfind(os.sep)+1:i.rfind('.')])
             for file in obsList:        ## Gather all available observatory names
                 openfile = open(file,'r').read().splitlines()
                 for line in openfile: 
                     if line.split(':')[0] == 'name':
                         nameList.append(line.split(':')[1].strip())
             
             for ind in range(0,len(nameList)):
                 if nameList[ind] == self.observatory.GetValue(): openFile = obsList[ind]
             obsPath = os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),openFile)
             self.loadValues(obsPath)
    
     def loadValues(self, obsPath):
         filename = os.path.split(obsPath)
         self.filename.SetValue(filename[1].split('.')[0])
         obsPath = file(obsPath, 'r')
         for line in obsPath:
             if line.split(':',1) > 1 and line[0] != '#':
                 line = line.split(':',1)
                 if line[0] == 'name':  self.name.SetValue(str(line[1].split('#')[0].strip()))
                 elif line[0] == 'latitude':  self.latitude.SetValue(str(line[1].split('#')[0].strip()))
                 elif line[0] == 'longitude':  self.longitude.SetValue(str(line[1].split('#')[0].strip()))
                 elif line[0] == 'elevation':   self.elevation.SetValue(str(line[1].split('#')[0].strip()))
                 elif line[0] == 'temperature':   self.temp.SetValue(str(line[1].split('#')[0].strip()))
                 elif line[0] == 'min_horizon':    self.min_horizon.SetValue(str(line[1].split('#')[0].strip()))
                 elif line[0] == 'v_limit': self.v_limit.SetValue(str(line[1].split('#')[0].strip()))
                 elif line[0] == 'depth_limit': self.depth_limit.SetValue(str(line[1].split('#')[0].strip()))
                 elif line[0] == 'calc_transits':
                     if bool(line[1].split('#')[0].strip()):
                         self.calc_transits.SetSelection(0)
                     else:
                         self.calc_transits.SetSelection(1)
                 elif line[0] == 'calc_eclipses':
                     if bool(line[1].split('#')[0].strip()):
                         self.calc_eclipses.SetSelection(0)
                     else:
                         self.calc_eclipses.SetSelection(1)
                 elif line[0] == 'html_out':
                     if bool(line[1].split('#')[0].strip()):
                         self.html_out.SetSelection(0)
                     else:
                         self.html_out.SetSelection(1)
                 elif line[0] == 'text_out':
                     if bool(line[1].split('#')[0].strip()):
                         self.text_out.SetSelection(0)
                     else:
                         self.text_out.SetSelection(1)
                 elif line[0] == 'twilight': self.twilightType.SetValue(str(line[1].split('#')[0].strip()))
         obsPath.close()
         
     def saveFile(self, filename):
         semdateArr = self.startSemDate.GetValue().split('/')
         enddateArr = self.endSemDate.GetValue().split('/')
         newobs = open(filename, 'w')
         newobs.write('name: ' + self.name.GetValue() + '\n')
         newobs.write('latitude: ' + self.latitude.GetValue() + '\n')
         newobs.write('longitude: ' + self.longitude.GetValue() + '\n')
         newobs.write('elevation: ' + self.elevation.GetValue() + '\n')
         newobs.write('temperature: ' + self.temp.GetValue() + '\n')
         newobs.write('min_horizon: ' + self.min_horizon.GetValue() + '\n')
         newobs.write('start_date: ' + '(' + str(int(semdateArr[0])) + ',' + str(int(semdateArr[1])) + ',' + str(int(semdateArr[2])) + ',0,0,0)\n')
         newobs.write('end_date: ' + '(' + str(int(enddateArr[0])) + ',' + str(int(enddateArr[1])) + ',' + str(int(enddateArr[2])) + ',0,0,0)\n')
         newobs.write('v_limit: ' + self.v_limit.GetValue() + '\n')
         newobs.write('depth_limit: ' + self.depth_limit.GetValue() + '\n')
         newobs.write('calc_transits: ' + str(self.calc_transits.GetSelection()==0) + '\n')
         newobs.write('calc_eclipses: ' + str(self.calc_eclipses.GetSelection()==0) + '\n')
         newobs.write('html_out: ' + str(self.html_out.GetSelection()==0) + '\n')
         newobs.write('text_out: ' + str(self.text_out.GetSelection()==0) + '\n')
         newobs.write('twilight: ' + self.twilightType.GetValue() + '\n')
         newobs.close()
         
     def calculate(self, event):
         outputPath = str(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'extras','eph','ephOutputs','eventReport.html'))
         path = os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'extras','eph','observatories',self.filename.GetValue() + '.par')
         self.saveFile(path)
         import oscaar.extras.eph.calculateEphemerides as eph
         eph.calculateEphemerides(path)
         if self.html_out.GetSelection() == 0: webbrowser.open_new_tab("file:"+2*os.sep+outputPath)
         self.Destroy()
         
     def saveOutput(self, event):
         dlg = wx.FileDialog(self, message = "Save your output...", style = wx.SAVE)
         if dlg.ShowModal() == wx.ID_OK:
             outputPath = dlg.GetPath()
             self.calculate(None)
             shutil.copytree(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'extras','eph','ephOutputs'), outputPath)
             outputArchive = zipfile.ZipFile(outputPath+'.zip', 'w')
             for name in glob(outputPath+os.sep+'*'):
                 outputArchive.write(name, os.path.basename(name), zipfile.ZIP_DEFLATED)
             shutil.rmtree(outputPath)
             outputArchive.close()
 
     def onDestroy(self, event):
         self.parent.loadEphFrame = False

class FittingFrame(wx.Frame):

    def __init__(self, parent, id, path = ''):
        
        self.path = path
        self.title = "Fitting Methods"
        
        wx.Frame.__init__(self, parent, id, self.title)
        
        self.panel = wx.Panel(self)
        self.parent = parent
        
        self.box = AddLCB(self.panel,-1,name="Path to Output File: ")
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.box, border=5, flag=wx.ALL)
        self.box.txtbox.SetValue(self.path)
        
        #self.plotLSFitButton = wx.Button(self.panel,label="Least Squares Fit", size =(130,25))
        self.plotMCMCButton = wx.Button(self.panel,label="MCMC Fit", size = (130,25))
        
        #self.Bind(wx.EVT_BUTTON, self.plotLSFit, self.plotLSFitButton)
        self.Bind(wx.EVT_BUTTON, self.plotMCMC, self.plotMCMCButton)
        
        self.sizer0 = wx.FlexGridSizer(rows=2, cols=4)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)
        
        #self.sizer0.Add(self.plotLSFitButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotMCMCButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        
        self.pklPathTxt = self.box.txtbox
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
        self.Bind(wx.EVT_MENU,lambda event: self.browseButtonEvent(event,'Choose Path to Output File',self.pklPathTxt,True,wx.FD_OPEN),m_browse)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "Exit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
    
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    #####Functions for event handling#####
    def browseButtonEvent(self, event, message, textControl, fileDialog, saveDialog):
        if fileDialog:
            dlg = wx.FileDialog(self, message = message, style = saveDialog)
        else: dlg = wx.FileDialog(self, message = message,  style = wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
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
            self.pathText = self.pklPathTxt.GetValue()
            if self.parent.loadMCMC == False:
                MCMCFrame(self, -1)
                self.parent.loadMCMC = True
     
    def validityCheck(self):
        invalidString = ""
        pathTxt = self.pklPathTxt.GetValue()
        if pathTxt:
            if not self.correctOutputFile(pathTxt):
                invalidString += pathTxt;
            if invalidString == "":
                return True
            else:
                 InvalidParameter(invalidString, None, -1, str='path')
            return False
        else:
            InvalidParameter(invalidString, None, -1, str='path')

    def correctOutputFile(self, pathname):
        if pathname == '':
            return False
        if pathname.endswith('.pkl'):
            return True
        return False
    
    def onDestroy(self, event):
        self.parent.loadFittingOpen = False
    
    def on_exit(self, event):
        self.Destroy()

class LoadOldPklFrame(wx.Frame):

    def __init__(self, parent, id):
        
        global loadGraphFrame
        loadGraphFrame = False

        self.title = "Load An Old .pkl File"
        wx.Frame.__init__(self, parent, id, self.title)
        
        self.panel = wx.Panel(self)
        self.parent = parent
        self.box = AddLCB(self.panel,-1,name="Path to Output File")
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.box, border=5, flag=wx.ALL)
        
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
        self.hbox2.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)

        self.sizer0.Add(self.plotLightCurveButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotRawFluxButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotScaledFluxesButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotCentroidPositionsButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotComparisonStarWeightingsButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotInteractiveLightCurveButton,0,wx.ALIGN_CENTER|wx.ALL,5)
         
        self.pklPathTxt = self.box.txtbox
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
        self.Bind(wx.EVT_MENU,lambda event: self.browseButtonEvent(event,'Choose Path to Output File',self.pklPathTxt,True,wx.FD_OPEN),m_browse)
        menu_file.AppendSeparator()
        m_exit = menu_file.Append(-1, "Exit\tCtrl-Q", "Exit")
        self.Bind(wx.EVT_MENU, self.on_exit, m_exit)
    
        self.menubar.Append(menu_file, "&File")
        self.SetMenuBar(self.menubar)

    #####Functions for event handling#####
    def browseButtonEvent(self, event, message, textControl, fileDialog, saveDialog):
        if fileDialog:
            dlg = wx.FileDialog(self, message = message, style = saveDialog)
        else: dlg = wx.FileDialog(self, message = message,  style = wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            filenames = dlg.GetPaths()
            textControl.Clear()
            for i in range(0,len(filenames)):
                if i != len(filenames)-1:
                    textControl.WriteText(filenames[i] + ',')
                else:
                    textControl.WriteText(filenames[i])
        dlg.Destroy()

    def plotLightCurve(self, event):
        if self.validityCheck():
            print 'Loading file: '+self.pklPathTxt.GetValue() 
            commandstring = "import oscaar.IO; data=oscaar.IO.load('"+self.pklPathTxt.GetValue()+"'); data.plotLightCurve()"
            subprocess.Popen(['python','-c',commandstring])

    def plotRawFlux(self, event):
        if self.validityCheck():
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar.IO; data=oscaar.IO.load('"+self.pklPathTxt.GetValue()+"'); data.plotRawFluxes()"

            subprocess.Popen(['python','-c',commandstring])

    def plotScaledFluxes(self, event):
        if self.validityCheck():
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar.IO; data=oscaar.IO.load('"+self.pklPathTxt.GetValue()+"'); data.plotScaledFluxes()"

            subprocess.Popen(['python','-c',commandstring])
    
    def plotCentroidPosition(self, event):
        if self.validityCheck():
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar.IO; data=oscaar.IO.load('"+self.pklPathTxt.GetValue()+"'); data.plotCentroidsTrace()"

            subprocess.Popen(['python','-c',commandstring])

    def plotComparisonStarWeightings(self, event):
        if self.validityCheck():
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar.IO; data=oscaar.IO.load('"+self.pklPathTxt.GetValue()+"'); data.plotComparisonWeightings()"

            subprocess.Popen(['python','-c',commandstring])
    
    def plotInteractiveLightCurve(self, event):
        if self.validityCheck():
            global pathText
            global loadGraphFrame
            pathText = self.pklPathTxt.GetValue()
            if loadGraphFrame == False:   
                GraphFrame()
                loadGraphFrame = True
            
    def validityCheck(self):
        invalidString = ""
        pathTxt = self.pklPathTxt.GetValue()
        if pathTxt:
            if not self.correctOutputFile(pathTxt):
                invalidString += pathTxt;
            if invalidString == "":
                return True
            else:
                 InvalidParameter(invalidString, None, -1, str='path')
            return False
        else:
            InvalidParameter(invalidString, None, -1, str='path')

    def correctOutputFile(self, pathname):
        if pathname == '':
            return False
        if pathname.endswith('.pkl'):
            return True
        return False
            
    def onDestroy(self, event):
        self.parent.loadOldPklOpen = False
    
    def on_exit(self, event):
        self.Destroy()

class GraphFrame(wx.Frame):
    
    """ The main frame of the application
    """
    
    title = 'Light Curve Plot'

    def __init__(self):
    
        # This initializes the wx.frame with the title.
        
        wx.Frame.__init__(self, None, -1, self.title, style = wx.DEFAULT_FRAME_STYLE & ~ (wx.RESIZE_BORDER | wx.RESIZE_BOX | wx.MAXIMIZE_BOX))
        #wx.Frame(None, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        
        # This gets the location of the pkl file by using a global variable that is defined in the LoadOldPklFrame class.
        
        self.pT = pathText
        
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

        binnedTime, binnedFlux, binnedStd = medianBin(self.data.times,self.data.lightCurve,self.pointsPerBin)
        self.fig = pyplot.figure(num=None, figsize=(10, 8), facecolor='w',edgecolor='k')
        self.dpi = 100
        self.axes = self.fig.add_subplot(111)
        self.axes.set_axis_bgcolor('white')
        self.axes.set_title('Light Curve', size=12)
        def format_coord(x, y):
            # '''Function to give data value on mouse over plot.'''
            return 'JD=%1.5f, Flux=%1.4f' % (x, y)
        self.axes.format_coord = format_coord 
        self.axes.errorbar(self.data.times,self.data.lightCurve,yerr=self.data.lightCurveError,fmt='k.',ecolor='gray')
        self.axes.errorbar(binnedTime, binnedFlux, yerr=binnedStd, fmt='rs-', linewidth=2)
        self.axes.axvline(ymin=0,ymax=1,x=self.data.ingress,color='k',ls=':')
        self.axes.axvline(ymin=0,ymax=1,x=self.data.egress,color='k',ls=':')
        self.axes.set_title('Light Curve')
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
            
            binnedTime, binnedFlux, binnedStd = medianBin(self.data.times,self.data.lightCurve,self.pointsPerBin)
           
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
            self.axes.errorbar(self.data.times,self.data.lightCurve,yerr=self.data.lightCurveError,fmt='k.',ecolor='gray')
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
        global loadGraphFrame
        loadGraphFrame = False

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
                     str(transiterFit.calcMidTranTime(self.data.times,self.data.lightCurve))),
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
            
            fit, success = transiterFit.run_LMfit(self.data.getTimes(),self.data.lightCurve, self.data.lightCurveError,
                              float(self.box.userParams['Rp/Rs'].GetValue()),float(self.box.userParams['a/Rs'].GetValue()),
                              float(self.box.userParams['inc'].GetValue()),float(self.box.userParams['t0'].GetValue()),
                              float(self.box.userParams['gamma1'].GetValue()),float(self.box.userParams['gamma2'].GetValue()),
                              float(self.box.userParams['per'].GetValue()),float(self.box.userParams['ecc'].GetValue()),
                              float(self.box.userParams['pericenter'].GetValue()),fitLimbDark=self.tempLimbDark, plotting=True)
            n_iter = 300
#             Rp,aRs,inc,t0,gam1,gam2=oscaar.transiterFit.run_MCfit(n_iter,self.data.getTimes(),
#                 self.data.lightCurve, self.data.lightCurveError,fit,success,
#                 float(self.box.GetPeriod()),float(self.box.GetEcc()),
#                 float(self.box.GetPericenter()),float(self.box.GetGamma1()),float(self.box.GetGamma2()), plotting=False)

    def update(self,event):
        if self.box1.txtbox.GetValue() == '':
            InvalidParameter(self.box1.txtbox.GetValue(), None,-1, str="planet")
        else:
            self.planet = self.box1.txtbox.GetValue()
            [RpOverRs,AOverRs,per,inc,ecc] = returnSystemParams.transiterParams(self.planet)
            
            if RpOverRs == -1 or AOverRs == -1 or per == -1 or inc == -1 or ecc == -1:
                InvalidParameter(self.box1.txtbox.GetValue(), None,-1, str="planet")
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
        
        self.pT = parent.pathText
        self.data = IO.load(self.pT)
        
        self.LCB = AddLCB(self.panel,-1,name="planet")
        self.Bind(wx.EVT_BUTTON,self.update,self.LCB.updateButton)
        self.topBox = wx.BoxSizer(wx.HORIZONTAL)
        self.topBox.Add(self.LCB, border=5, flag=wx.ALL)
        
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
        
    def on_exit(self, event):
        self.Destroy()
    
    def onDestroy(self, event):
        global loadMCMC
        loadMCMC = False

    def plot(self,event):
       list = [(self.box.userParams['Rp/Rs'].GetValue(),"Rp/Rs"),(self.box.userParams['a/Rs'].GetValue(),"a/Rs"),
            (self.box3.userParams['per'].GetValue(),"per"), (self.box.userParams['inc'].GetValue(),"inc"),
            (self.box3.userParams['ecc'].GetValue(),"ecc"), (self.box.userParams['t0'].GetValue(),"t0"),
            (self.box3.userParams['gamma1'].GetValue(),"gamma1"),(self.box3.userParams['gamma2'].GetValue(),"gamma2"),
            (self.box3.userParams['pericenter'].GetValue(),"pericenter"),(self.box4.userParams['saveiteration'].GetValue(),
            "saveiteration"), (self.box4.userParams['acceptance'].GetValue(),"acceptance"),
            (self.box4.userParams['burnfrac'].GetValue(),"burnfrac"), (self.box4.userParams['number'].GetValue(),"number")]
       
       if checkParams(self,list) == True:
            path = self.pT
            initParams = [float(self.box.userParams['Rp/Rs'].GetValue()),float(self.box.userParams['a/Rs'].GetValue()),
                          float(self.box3.userParams['per'].GetValue()), float(self.box.userParams['inc'].GetValue()),
                          float(self.box3.userParams['gamma1'].GetValue()),float(self.box3.userParams['gamma2'].GetValue()),
                          float(self.box3.userParams['ecc'].GetValue()),float(self.box3.userParams['pericenter'].GetValue()),
                          float(self.box.userParams['t0'].GetValue())]
            
            nSteps = float(self.box4.userParams['number'].GetValue())
            initBeta = (np.zeros([4]) + 0.012).tolist()        ## << The .tolist() method type casts the Numpy ndarray into a python list
    #         initBeta = [int(self.box2.userParams['b-Rp/Rs'].GetValue()), int(self.box2.userParams['b-a/Rs'].GetValue()),
    #                     int(self.box2.userParams['b-inc'].GetValue()), int(self.box2.userParams['b-t0'].GetValue())]
            
            idealAcceptanceRate = float(self.box4.userParams['acceptance'].GetValue())
            interval = float(self.box4.userParams['saveiteration'].GetValue())
            burnFraction = float(self.box4.userParams['burnfrac'].GetValue())
            #mcmcinstance = oscaar.fitting.mcmcfit(self.pT,initParams,initBeta,nSteps,interval,idealAcceptanceRate,burnFraction)
            #mcmcinstance.run(updatepkl=True)
            #mcmcinstance.plot()
            
            ## Spawn a new process to execute the MCMC run separately
            mcmcCall = 'import oscaar.fitting; mcmcinstance = oscaar.fitting.mcmcfit("%s",%s,%s,%s,%s,%s,%s); mcmcinstance.run(updatepkl=True); mcmcinstance.plot()' % \
                        (self.pT,initParams,initBeta,nSteps,interval,idealAcceptanceRate,burnFraction)
            subprocess.call(['python','-c',mcmcCall])

    def update(self,event):
        if self.LCB.txtbox.GetValue() == '':
            InvalidParameter(self.LCB.txtbox.GetValue(), None,-1, str="planet")
        else:
            self.planet = self.LCB.txtbox.GetValue()
            [RpOverRs,AOverRs,per,inc,ecc] = returnSystemParams.transiterParams(self.planet)
            
            if RpOverRs == -1 or AOverRs == -1 or per == -1 or inc == -1 or ecc == -1:
                InvalidParameter(self.LCB.txtbox.GetValue(), None,-1, str="planet")
            else:
                self.box.userParams['Rp/Rs'].SetValue(str(RpOverRs))
                self.box.userParams['a/Rs'].SetValue(str(AOverRs))
                self.box3.userParams['per'].SetValue(str(per))
                self.box.userParams['inc'].SetValue(str(inc))
                self.box3.userParams['ecc'].SetValue(str(ecc))
                InvalidParameter("",None,-1, str="params")

class ParameterBox(wx.Panel):

        def __init__(self, parent, id,list,name="",rows=1,cols=10,vNum=0,hNum=0,font=wx.NORMAL_FONT):               
            wx.Panel.__init__(self,parent,id)
            box1 = wx.StaticBox(self, -1, name)
            sizer = wx.StaticBoxSizer(box1, wx.VERTICAL)
            self.userParams = {}
            sizer0 = wx.FlexGridSizer(rows=rows, cols=cols, vgap=vNum, hgap=hNum)
            sizer.Add(sizer0, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
            
            for (widget, labeltxt, ToolTip, value) in list:
                label = wx.StaticText(self, -1, labeltxt, style=wx.ALIGN_CENTER)
                if widget != 'notes':
                    sizer0.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
                else:
                    sizer0.Add(label, 0, (wx.ALIGN_CENTER_HORIZONTAL) | wx.ALL, 0)
                label.SetFont(font)
                
                if widget == 'notes':
                    self.userParams[widget] = wx.TextCtrl(self, -1, value = value, size = (220, 48), style = wx.TE_MULTILINE)
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
                    self.userParams[widget+"1"] = wx.RadioButton(self, label = label2)
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
            
        def __init__(self, parent,id,name='',str="Browse\t (Cntrl-O)",rowNum=1,colNum=3,vNum=0,hNum=0, font = wx.NORMAL_FONT):
            wx.Panel.__init__(self,parent,id)
            
            box1 = wx.StaticBox(self, -1)
            sizer = wx.StaticBoxSizer(box1, wx.VERTICAL)

            sizer0 = wx.FlexGridSizer(rows=rowNum, cols=colNum, vgap=vNum, hgap=hNum)
            sizer.Add(sizer0, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
            
            if name != "mainGUI":
                if name == 'planet':
                    self.label = wx.StaticText(self, -1, "Planet Name", style=wx.ALIGN_CENTER)
                    self.txtbox = wx.TextCtrl(self, -1, value='GJ 1214 b')
                    self.txtbox.SetToolTipString('Enter the name of a planet from the exoplanet.org database here.')
                else:
                    self.label = wx.StaticText(self, -1, name, style=wx.ALIGN_CENTER)
                    self.txtbox = wx.TextCtrl(self, -1, size=(500,20))
                sizer0.Add(self.label, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
                sizer0.Add(self.txtbox, 0, wx.ALIGN_CENTRE|wx.ALL, 0)
                
                if name == 'planet':
                    self.updateButton = wx.Button(self, -1, "Update Parameters")
                    sizer0.Add(self.updateButton,0,wx.ALIGN_CENTER|wx.ALL,0)
                else:
                    if sys.platform != 'win32':
                        if str == "Browse\t (Cntrl-O)":
                            str = "Browse\t("+u'\u2318'"-O)"
                        self.browseButton = wx.Button(self, -1, str)
                    else:
                        self.browseButton = wx.Button(self, -1, str)
                    
                    self.Bind(wx.EVT_BUTTON, lambda event:self.browseButtonEvent(event,"Choose Path to Output File",
                                                                                 True,wx.FD_OPEN,textControl = self.txtbox))
                    sizer0.Add(self.browseButton,0,wx.ALIGN_CENTRE|wx.ALL,0)
            else:
                list = ["Path to Dark Frames: ", "Path to Master Flat: ", "Path to Data Images: ", "Path to Regions File: ",
                        "Output Path: "]
                if sys.platform == "win32":
                    tempSize = 25
                else:
                    tempSize = 35
                box0 = wx.TextCtrl(self, -1, size=(500,tempSize), style = wx.TE_RICH)
                box1 = wx.TextCtrl(self, -1, size=(500,25), style = wx.TE_RICH)
                box2 = wx.TextCtrl(self, -1, size=(500,tempSize), style = wx.TE_RICH)
                box3 = wx.TextCtrl(self, -1, size=(500,25), style = wx.TE_RICH)
                box4 = wx.TextCtrl(self, -1, size=(500,25))
                self.boxes = [box0,box1,box2,box3,box4]
               
                list = [("Path to Dark Frames: ",0), ("Path to Master Flat: ",1), ("Path to Data Images: ",2),
                        ("Path to Regions File: ",3), ("Output Path: ",4)]
                
                for (name,num) in list:
                    box = self.boxes[num]
                    self.label = wx.StaticText(self, -1, name, style=wx.ALIGN_CENTER)
                    self.label.SetFont(font)
                    sizer0.Add(self.label, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
                    sizer0.Add(box, 0, wx.ALIGN_CENTRE|wx.ALL, 0)
                    button = wx.Button(self, -1, "Browse")
                    if name == "Path to Dark Frames: ":
                        button.Bind(wx.EVT_BUTTON, lambda evt: self.browseButtonEvent(evt,"Choose "+name,
                                                                                      False,None,textControlNum = 0))
                    elif name == "Path to Master Flat: ":
                        button.Bind(wx.EVT_BUTTON, lambda evt: self.browseButtonEvent(evt,"Choose "+name,
                                                                                      True,wx.FD_OPEN,textControlNum = 1))
                    elif name == "Path to Data Images: ":
                        button.Bind(wx.EVT_BUTTON, lambda evt: self.browseButtonEvent(evt,"Choose "+name,
                                                                                      False,None,textControlNum = 2))
                    elif name == "Path to Regions File: ":
                        button.Bind(wx.EVT_BUTTON, lambda evt: self.browseButtonEvent(evt,"Choose "+name,
                                                                                      True,wx.FD_OPEN,textControlNum = 3))
                    elif name == "Output Path: ":
                        button.Bind(wx.EVT_BUTTON, lambda evt: self.browseButtonEvent(evt,"Choose "+name,
                                                                                      True,wx.FD_SAVE,textControlNum = 4))
                    sizer0.Add(button,0,wx.ALIGN_CENTRE|wx.ALL,0)
                    
            self.SetSizer(sizer)
            sizer.Fit(self)

        def browseButtonEvent(self, event, message, fileDialog, saveDialog, textControl = '', textControlNum = -1):
            if textControlNum != -1:
                textControl = self.boxes[textControlNum]
            if fileDialog:
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

        self.panel = wx.Panel(self)
        self.string = "Incorrect"
        self.ds9 = False
        self.fitError = False
        
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
            self.string = "Either more than one file has been entered, or the file entered needs to be fixed in the " + max + "."
        elif str == "output":
            self.string = "Either you entered a directory, or the specified path cannot be made for the " + max + "."
        elif str == "leftbox":
            self.string = "Please enter a number for the " + max + "."
        elif str == "dateTime":
            self.string = "Please check the format and values entered for the ingress or egress " + max + "."

        self.okButton = wx.Button(self.panel,label = "Okay", pos = (125,30))
        self.Bind(wx.EVT_BUTTON, self.onOkay, self.okButton)
        
        if str == "path":
            self.paths = wx.StaticText(self.panel, -1, "The following is an invalid output path: " + num)
        elif str == "params":
            self.paths = wx.StaticText(self.panel, -1, "The appropriate parameters have been updated.")
        elif str == "ds9":
            self.ds9 = True
            self.paths = wx.StaticText(self.panel, -1, 
                                       "It seems that ds9 may not have installed correctly, please try again.")
        elif str == "importError":
            self.paths = wx.StaticText(self.panel, -1, "Failed to import ephem, please try again.")
        elif str == "fitOpen":
            self.fitError = True
            self.paths = wx.StaticText(self.panel, -1, "Please close the fitting frame window and try again.")
        else:
            self.paths = wx.StaticText(self.panel, -1, self.string +"\nThe following is invalid: " + num)
        
        self.sizer0 = wx.FlexGridSizer(rows=2, cols=columns) 
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.paths,0,wx.ALIGN_CENTER|wx.ALL,5)

        self.sizer0.Add(self.okButton,0,wx.ALIGN_CENTER|wx.ALL,5)

        self.panel.SetSizer(self.hbox)
        self.hbox.Fit(self)
        self.Center()
        self.Show()
    
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
        if self.ds9:
            self.parent.ds9Open = False
        elif self.fitError:
            self.parent.loadFitError = False
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
