import threading
import wx
import os
import sys
import datetime
import calendar
from time import strftime
from time import strptime
from glob import glob
from scipy import ndimage
import numpy as np
import math
import webbrowser
import time
import subprocess

def homeDir():
    """Set the current directory to oscaar's home directory"""
    ### BM: changed the split() argument to '/' rather than '\\'.
    ### DG: added a platform check
    if sys.platform == 'win32':
        splitChar = '\\'
    else:
        splitChar = '/'
    if 'OSCAAR' in os.getcwd().split(splitChar):
        while os.getcwd().split(splitChar)[len(os.getcwd().split(splitChar))-1] != 'OSCAAR':
            os.chdir(os.pardir)

os.chdir(os.pardir)
os.chdir('Code')
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())


APP_EXIT = 1

class OscaarFrame(wx.Frame): ##Defined a class extending wx.Frame for the GUI
    def __init__(self, *args, **kwargs):

        super(OscaarFrame, self).__init__(*args, **kwargs)
        self.InitUI()

    #### Creates and initializes the GUI ####
    
    def InitUI(self):
        #### Defines the menubar ####
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        self.oscaarMenu = wx.Menu()
        self.helpMenu = wx.Menu()
        menuExit = fileMenu.Append(wx.ID_EXIT, 'Quit\tCtrl+Q', 'Quit application') ##provides a way to quit
        menubar.Append(fileMenu, '&File')
        menubar.Append(self.helpMenu, '&Help')
        menubar.Append(self.oscaarMenu, '&Oscaar')
        self.Bind(wx.EVT_MENU, self.OnQuit, menuExit) ##Bind with OnQuit function, which closes the application
        self.menuDefaults = self.oscaarMenu.Append(-1, 'Set Defaults', 'Set Defaults')
        self.Bind(wx.EVT_MENU, lambda event: self.setDefaults(event, '../Code/init.par'), self.menuDefaults)
        self.linkToPredictions = self.oscaarMenu.Append(-1, 'Transit time predictions...', 'Transit time predictions...')
        self.Bind(wx.EVT_MENU, self.predictions, self.linkToPredictions)
        self.helpItem = self.helpMenu.Append(wx.ID_HELP, 'Help', 'Help')
        self.Bind(wx.EVT_MENU, self.helpFunc, self.helpItem)
        self.save = fileMenu.Append(wx.ID_SAVE, '&Save Settings\tCtrl+S', 'Save')
        self.Bind(wx.EVT_MENU, self.saveParFile, self.save)
        self.load = fileMenu.Append(wx.ID_OPEN, 'Load', 'Load')
        self.Bind(wx.EVT_MENU, self.loadFunction, self.load)
        self.SetMenuBar(menubar)

        
        self.sizer = wx.GridBagSizer(7, 7)        
        self.static_bitmap = wx.StaticBitmap(parent = self, pos = (0,0), size = (130,50))
        self.logo = wx.Image(os.pardir+ '/Docs/OscaarLogo.png', wx.BITMAP_TYPE_ANY)
        self.bitmap = wx.BitmapFromImage(self.logo)
        self.static_bitmap.SetBitmap(self.bitmap)
        self.SetBackgroundColour(wx.Colour(233,233,233))
        self.labelFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        
        #### CONTROL BUTTON DECLARATIONS ####
        self.radioTrackPlotOn = wx.RadioButton(self, label = "On", style = wx.RB_GROUP)
        self.radioTrackPlotOff = wx.RadioButton(self, label = "Off")
        
        textCtrlSize = (510,25)
        
        self.darkPathTxt = wx.TextCtrl(self, size = textCtrlSize)
        self.darkPathBtn = wx.Button(self, -1, 'Browse')
        self.flatPathTxt = wx.TextCtrl(self, size = textCtrlSize)
        self.flatPathBtn = wx.Button(self, -1, 'Browse')
        self.imagPathTxt = wx.TextCtrl(self, size = textCtrlSize)
        self.imagPathBtn = wx.Button(self, -1, 'Browse')
        self.regPathTxt = wx.TextCtrl(self, size = textCtrlSize)
        self.regPathBtn = wx.Button(self, -1, 'Browse')
        self.smoothingConstTxt = wx.TextCtrl(self, value = '0')
        self.radiusTxt = wx.TextCtrl(self, value = '0')
        self.trackZoomTxt = wx.TextCtrl(self, value = '0')
        self.ccdGainTxt = wx.TextCtrl(self, value = '0')
        self.photPlotsOn = wx.RadioButton(self, label = 'On', style = wx.RB_GROUP)
        self.photPlotsOff = wx.RadioButton(self, label = 'Off')
        #self.ingressDate = wx.DatePickerCtrl(self)
        self.ingressDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
        self.ingressTime = wx.TextCtrl(self, value = '00:00:00')
        #self.egressDate = wx.DatePickerCtrl(self) ## DatePicker to pick the egress date
        self.egressDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')

        self.egressTime = wx.TextCtrl(self, value = '00:00:00') ## TimeCtrl to pick the egress time
        self.ds9Button = wx.Button(self, -1, 'Open DS9', size = (90, 25)) ## Button to open ds9
        self.masterFlatButton = wx.Button(self, -1, 'Flat Maker', size = (90,25))
        self.notesField = wx.TextCtrl(self, value = 'Enter notes to be saved here', size = (220, 48), style = wx.TE_MULTILINE)
        self.notesLabel = wx.StaticText(self, label = 'Notes')
        self.notesLabel.SetFont(self.labelFont)
    

        ##### Add items to sizer for organization #####
        self.addPathChoice(2, self.darkPathTxt, self.darkPathBtn, wx.StaticText(self, -1, 'Path to Dark Frames: '), 'Choose Path to Dark Frames', False)
        self.addPathChoice(3, self.flatPathTxt, self.flatPathBtn, wx.StaticText(self, -1, 'Path to Flat Frames: '), 'Choose Path to Flat Frames', False)
        self.addPathChoice(4, self.imagPathTxt, self.imagPathBtn, wx.StaticText(self, -1, 'Path to Data Images: '), 'Choose Path to Data Images', False)
        self.addPathChoice(5, self.regPathTxt, self.regPathBtn, wx.StaticText(self, -1, 'Path to Regions File: '), 'Choose Path to Regions File', True)
        self.addButtonPair(6, 4, self.radioTrackPlotOn, self.radioTrackPlotOff, wx.StaticText(self, -1, 'Tracking Plots: '))
        self.addButtonPair(7, 4, self.photPlotsOn, self.photPlotsOff, wx.StaticText(self, -1, 'Photometry Plots:     '))
        self.addTextCtrl(6,0, self.trackZoomTxt, wx.StaticText(self, -1, 'Track Zoom: '))
        self.addTextCtrl(7,0, self.ccdGainTxt, wx.StaticText(self, -1, 'CCD Gain: '))
        self.addTextCtrl(8,0, self.radiusTxt, wx.StaticText(self, -1, 'Aperture Radius: '))
        self.addTextCtrl(9,0, self.smoothingConstTxt, wx.StaticText(self, -1, 'Smoothing Constant: '))
        self.addDateCtrl(8,4, self.ingressDate, self.ingressTime, wx.StaticText(self, -1, 'Ingress, UT (YYYY/MM/DD):       '))
        self.addDateCtrl(9,4, self.egressDate, self.egressTime, wx.StaticText(self, -1, 'Egress, UT (YYYY/MM/DD):       '))
        self.sizer.Add(self.ds9Button,(11,5), wx.DefaultSpan, wx.ALIGN_CENTER, 7)
        self.ds9Button.Bind(wx.EVT_BUTTON, self.openDS9)
        self.sizer.Add(self.masterFlatButton, (11,4), wx.DefaultSpan, wx.ALIGN_CENTER, 7)
        self.masterFlatButton.Bind(wx.EVT_BUTTON, self.openMasterFlatGUI)
        self.sizer.Add(self.notesField, (10, 1), (2,2), wx.ALIGN_CENTER, 7)
        self.sizer.Add(self.notesLabel, (10, 0 ), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        
        self.setDefaults(None, '../Code/init.par')
        self.run = wx.Button(self, -1, 'Run')
        self.sizer.Add(self.run, (11,6), wx.DefaultSpan, wx.ALIGN_CENTER, 7)
        self.run.Bind(wx.EVT_BUTTON, self.runOscaar)

        self.sizer.SetDimension(5, 5, 550, 500)
        self.SetSizer(self.sizer)
        setSize = (900, 500) ##Made the size bigger so the items fit in all os
        self.SetSize(setSize)
        self.SetMinSize(setSize)
        self.SetTitle('OSCAAR')
        self.Centre()
        self.Show(True)

    #### Allows quitting from the file menu. (Fixes cmd-Q on OS X) ####
    def OnQuit(self, e): 
        self.Close()

    #### Neater creation of control items ####
    def addButtonPair(self, row, colStart, button1, button2, label):
        label.SetFont(self.labelFont)
        self.sizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7) ##border of 8 pixels on the top and left
        self.sizer.Add(button1, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
        self.sizer.Add(button2, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)

    def addTextCtrl(self, row, colStart, textCtrl, label):
        label.SetFont(self.labelFont)
        self.sizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.sizer.Add(textCtrl, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
        textCtrl.SetForegroundColour(wx.Colour(180,180,180))
        textCtrl.Bind(wx.EVT_TEXT, lambda event: self.updateColor(textCtrl))

    def addPathChoice(self, row, textCtrl, button, label, message, fileDialog):
        label.SetFont(self.labelFont)
        self.sizer.Add(label, (row, 0), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.sizer.Add(textCtrl, (row, 1), (1,5), wx.TOP, 7)
        self.sizer.Add(button, (row, 6), (1,1), wx.TOP, 7)
        textCtrl.SetForegroundColour(wx.Colour(180,180,180))
        button.Bind(wx.EVT_BUTTON, lambda event: self.browseButtonEvent(event, message, textCtrl, fileDialog))
        textCtrl.Bind(wx.EVT_TEXT, lambda event: self.updateColor(textCtrl))

    def addDateCtrl(self, row, colStart, dateCtrl, timeCtrl, label):
        label.SetFont(self.labelFont)
        self.sizer.Add(label, (row, colStart), wx.DefaultSpan, wx.ALIGN_RIGHT | wx.TOP, 7)
        self.sizer.Add(dateCtrl, (row, colStart+1), wx.DefaultSpan, wx.TOP , 7)
        self.sizer.Add(timeCtrl, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)

    def updateColor(event,ctrl):
        ctrl.SetForegroundColour(wx.Colour(0,0,0))

    #####Functions for event handling#####
    def browseButtonEvent(self, event, message, textControl, fileDialog):
        if fileDialog:
            dlg = wx.FileDialog(self, message = message, style = wx.OPEN)
        else: dlg = wx.DirDialog(self, message = message,  style = wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            textControl.Clear()
            if fileDialog == False:
                textControl.WriteText(dlg.GetPath()+"*.fit*")
            else: textControl.WriteText(dlg.GetPath())
        dlg.Destroy()

    #####Opens DS9 to create a regions file when button is pressed#####
    def openDS9(self, event):
        ds9 = os.pardir + '/Extras/ds9'
        ds9Loc = ds9 + '/' + sys.platform + '/ds9'
        #print(ds9Loc)
        regionsName =  ds9 + '/testFits.fit'  ##if it is beneficial, we could use glob to get the users actual image here
        subprocess.Popen([ds9Loc, regionsName])
        
    def openMasterFlatGUI(self, event):
        MasterFlatFrame(None)

    #####Opens the webpage for the documentation when help is pressed#####
    def helpFunc(self, event):
        #oscaar.homeDir()
        homeDir()
        #oscaar.cd('Docs')
        os.chdir('Docs')
        if sys.platform == 'linux2' or sys.platform == 'darwin': ##Haven't tested this
            os.system("/usr/bin/xdg-open OscaarDocumentation-20110917.pdf")
        elif sys.platform == 'win32':
            os.startfile('OscaarDocumentation-20110917.pdf')
        #webbrowser.open_new_tab("https://github.com/OSCAAR/OSCAAR/") ##Change to documentation
        
    #####Runs the photom script with the values entered into the gui when 'run' is pressed#####
    def runOscaar(self, event):
        #oscaar.homeDir()
        homeDir()
        os.chdir('Code')
        #oscaar.cd('Code')
        global worker
        worker = None
        if self.notesField.GetValue() != 'Enter notes to be saved here':
            notes = open('../outputs/notes.txt', 'w') ##Not exactly sure where where the notes should go.
            notes.write(str(self.notesField.GetValue()))
        
        init = open('../Code/init.par', 'w')
        #Write to init.par
        init.write('Path to Dark Frames: ' + self.darkPathTxt.GetValue() + '\n')
        init.write('Path to data images: ' + self.imagPathTxt.GetValue() + '\n')
        init.write('Path to Master-Flat Frame: ' + self.flatPathTxt.GetValue() + '\n')
        init.write('Path to regions file: ' + self.regPathTxt.GetValue() + '\n')
        self.parseTime(self.ingressDate.GetValue(), self.ingressTime.GetValue(), 'Ingress: ',  init)
        self.parseTime(self.egressDate.GetValue(), self.egressTime.GetValue(), 'Egress: ', init)
        self.checkRB(self.radioTrackPlotOn, 'Plot Tracking: ', init)
        self.checkRB(self.photPlotsOn, 'Plot Photometry: ', init)
        init.write('Smoothing Constant: ' + self.smoothingConstTxt.GetValue() + '\n')
        init.write('CCD Gain: ' + self.ccdGainTxt.GetValue() + '\n')
        init.write('Radius: ' + self.radiusTxt.GetValue() + '\n')
        init.write('Tracking Zoom: ' + self.trackZoomTxt.GetValue() + '\n')
        init.write('Init GUI: on')
        init.close()
        init = open('../Code/init.par', 'r').read().splitlines()
        #overwcheckDict = {'track_out':track, 'aper_out':aper, 'diff10': diffonoff, 'time_out': aper, 'diff_out':diffonoff}
        if self.validityCheck():
            self.Destroy()
            if not worker:
               worker = WorkerThread()

        
        #self.guiOverwcheck(overwcheckDict)
        
    ####NOT YET IMPLEMENTED Checks that the filenames entered are valid####
    def validityCheck(self):
        darkFrames = glob(self.darkPathTxt.GetValue())
        imageFiles = glob(self.imagPathTxt.GetValue())
        regionsFile = glob(self.regPathTxt.GetValue())
        flatFrames = glob(self.flatPathTxt.GetValue())
        for i in flatFrames:
            print str(i).endswith('.fits')
        invalidsString = ""
        commaNeeded = False
        if not self.containsFit(darkFrames):
            invalidsString += "Dark Frames"
            commaNeeded = True
        if not self.containsFit(imageFiles):
            if commaNeeded:
                invalidsString += ", "
            invalidsString += "Image Files"
            commaNeeded = True
        if not self.containsFit(flatFrames):
            if commaNeeded:
                invalidsString += ", "
            invalidsString += "Flat Frames"
        if invalidsString == "":
            return True
        else:
            InvalidPath(invalidsString, None, -1)
        
             
    def containsFit(self, ary):
        for i in ary:
            if str(i).endswith('.fit') or str(i).endswith('.fits'):
                return True
        return False

    ##### Used to set radiobutton values to init more easily #####
    def checkRB(self, button, text, filename):
        if button.GetValue() == True:
            filename.write(text + 'on\n')
        else:
            filename.write(text + 'off\n')

    #### Converts datePicker and timeCtrl to string form for init.par ####
    def parseTime(self, date, time, text, filename):
        dateArr = str(self.ingressDate.GetValue()).split('/')
        result = str(dateArr[0]).strip() + '-' + str(dateArr[1]).strip() + '-' + str(dateArr[2]).strip() + ';'
        result += str(time)
        filename.write(text + result + '\n')
        
    def saveParFile(self, event):
        dlg = wx.FileDialog(self, message = 'choose a location to save your .par file', style = wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            parFile = open(dlg.GetPath(), 'w')
            parFile.write('Path to Dark Frames: ' + self.darkPathTxt.GetValue() + '\n')
            parFile.write('Path to data images: ' + self.imagPathTxt.GetValue() + '\n')
            parFile.write('Path to Master-Flat Frame: ' + self.flatPathTxt.GetValue() + '\n')
            parFile.write('Path to regions file: ' + self.regPathTxt.GetValue() + '\n')
            self.parseTime(self.ingressDate.GetValue(), self.ingressTime.GetValue(), 'Ingress: ',  parFile)
            self.parseTime(self.egressDate.GetValue(), self.egressTime.GetValue(), 'Egress: ', parFile)
            self.checkRB(self.radioTrackPlotOn, 'Plot Tracking: ', parFile)
            self.checkRB(self.photPlotsOn, 'Plot Photometry: ', parFile)
            parFile.write('Smoothing Constant: ' + self.smoothingConstTxt.GetValue() + '\n')
            parFile.write('CCD Gain: ' + self.ccdGainTxt.GetValue() + '\n')
            parFile.write('Radius: ' + self.radiusTxt.GetValue() + '\n')
            parFile.write('Tracking Zoom: ' + self.trackZoomTxt.GetValue() + '\n')
            parFile.write('Init GUI: on')
            parFile.close()
    
    def loadFunction(self, event):
        dlg = wx.FileDialog(self, message = 'choose a file to load', style = wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.setDefaults(None, dlg.GetPath())
            

    ####Sets default values to the values currently written to init.par####
    def setDefaults(self, event, filename):
        init = open(filename, 'r').read().splitlines()
        for i in range(0, len(init)):
            if len(init[i].split()) > 1 and init[i][0] != '#':
                inline = init[i].split(":", 1)
                inline[0] = inline[0].strip()
                if inline[0] == 'Path to Dark Frames':  self.darkPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Path to Master-Flat Frame':  self.flatPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Path to data images':  self.imagPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Path to regions file': self.regPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Radius':   self.radiusTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Tracking Zoom':   self.trackZoomTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'CCD Gain':   self.ccdGainTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Plot Photometry': 
                    if inline[1].split('#')[0].strip() == 'off': 
                        self.photPlotsOn.SetValue(False)
                        self.photPlotsOff.SetValue(True)
                    else:
                        self.photPlotsOn.SetValue(True)
                        self.photPlotsOff.SetValue(False)
                if inline[0] == 'Plot Tracking':
                    if inline[1].split('#')[0].strip() == 'off': 
                        self.radioTrackPlotOn.SetValue(False)
                        self.radioTrackPlotOff.SetValue(True)
                    else:
                        self.radioTrackPlotOn.SetValue(True)
                        self.radioTrackPlotOff.SetValue(False)
                if inline[0] == 'Smoothing Constant': self.smoothingConstTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Ingress':
                    ingArray = inline[1].split(';')[0].split('-')
                    ingDate = '/'.join(map(str,ingArray))#[ingArray[1],ingArray[2],ingArray[0]]))#wx.DateTimeFromDMY(int(ingArray[2]), int(ingArray[1])-1, int(ingArray[0]))
                    self.ingressDate.SetValue(ingDate)
                    timeString = inline[1].split(';')[1].split('#')[0].strip()
                    self.ingressTime.SetValue(timeString)
                if inline[0] == 'Egress':
                    egrArray = inline[1].split(';')[0].split('-')
                    egrDate = '/'.join(map(str,ingArray))#[egrArray[1],egrArray[2],egrArray[0]]))#wx.DateTimeFromDMY(int(egrArray[2]), int(egrArray[1])-1, int(egrArray[0]))
                    self.egressDate.SetValue(egrDate)
                    timeString = inline[1].split(';')[1].split('#')[0].strip()
                    self.egressTime.SetValue(timeString)
                if inline[0] == 'Init GUI': initGui = inline[1].split('#')[0].strip()

    #####Opens the webpage for transit time predictions from Czech Astronomical Society#####
    def predictions(self, event):
        webbrowser.open_new_tab("http://var2.astro.cz/ETD/predictions.php") ##Change to documentation

class MasterFlatFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MasterFlatFrame, self).__init__(*args, **kwargs)
        self.frameSizer = wx.GridBagSizer(7,7)
        
        ###Variable Declarations###
        pathCtrlSize = (325,25)
        self.SetBackgroundColour(wx.Colour(227,227,227))
        self.flatImagesPathCtrl = wx.TextCtrl(self, size = pathCtrlSize)
        self.flatDarksPathCtrl = wx.TextCtrl(self, size = pathCtrlSize)
        self.masterFlatPathCtrl = wx.TextCtrl(self, size = pathCtrlSize)
        self.plotsOn = wx.RadioButton(self, -1, 'On')
        self.plotsOff = wx.RadioButton(self, -1, 'Off')
        self.flatBrowse = wx.Button(self, -1, 'Browse')
        self.darkBrowse = wx.Button(self, -1, 'Browse')
        self.masterPathBrowse = wx.Button(self, -1, 'Browse')
        self.title = wx.StaticText(self, -1, 'OSCAAR: Master Flat Maker')
        self.titleFont = wx.Font(15, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
        self.title.SetFont(self.titleFont)
        self.runButton = wx.Button(self, -1, 'Run')
        self.runButton.Bind(wx.EVT_BUTTON, self.runMasterFlatMaker)

        ######Add to sizer######
        self.frameSizer.Add(self.runButton, (5,5), wx.DefaultSpan) 
        self.frameSizer.Add(self.title, (0,0), (1,2), wx.LEFT | wx.TOP, 7)
        self.addPathChoice(self.frameSizer, 1, wx.StaticText(self, -1, 'Path to Flat Images:'), 
                           self.flatBrowse, self.flatImagesPathCtrl, 'Choose Path to Flats...')
        self.addPathChoice(self.frameSizer, 2, wx.StaticText(self, -1, 'Path to Dark Flat Images:'), 
                           self.darkBrowse, self.flatDarksPathCtrl, 'Choose Path to Darks...')
        self.addPathChoice(self.frameSizer, 3, wx.StaticText(self, -1, 'Path to Save Master Flat:'), 
                           self.masterPathBrowse, self.masterFlatPathCtrl, 'Choose Path to Save Master Flat...')
        self.addButtonPair(self.frameSizer, 0, 2, wx.StaticText(self, -1, 'Plots: '), self.plotsOn, self.plotsOff)

        ###Set GUI Frame Attributes###
        frameSize = (625, 245)
        self.SetSizer(self.frameSizer)
        self.SetSize(frameSize)
        self.SetMinSize(frameSize)
        self.SetTitle('Master Flat Maker')
        self.Centre()
        self.Show(True)

    def addPathChoice(self, sizer, row, label, btn, textCtrl, message):
        sizer.Add(label, (row, 0), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        sizer.Add(textCtrl, (row, 1), (1,4), wx.TOP, 7)
        sizer.Add(btn, (row, 5), (1,1), wx.TOP, 7)
        btn.Bind(wx.EVT_BUTTON, lambda event: self.openDirDialog(event, message, textCtrl))

    def addButtonPair(self, sizer, row, colStart, label, button1, button2): ##defined for neater insertion of control items
        sizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 12) ##border of 12 pixels on the top and left
        sizer.Add(button1, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
        sizer.Add(button2, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)

    #####Button Press Event Functions#####
    def openDirDialog(self, event, message, textControl):
        dlg = wx.DirDialog(self, message = message, style = wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            textControl.Clear()
            textControl.WriteText(dlg.GetPath())
        dlg.Destroy()

    def runMasterFlatMaker(self, event):
        masterFlatMaker(self.flatImagesPathCtrl.GetValue, self.flatDarksPathCtrl.GetValue, 
                        self.masterFlatPathCtrl.GetValue, self.plotsOn.GetValue)

#### Checks if the dark frames are valid ####

class InvalidPath(wx.Frame):
    def __init__(self, path, parent, id):
        wx.Frame.__init__(self, parent, id, 'Check Path names')
        self.SetSize((250,100))
        self.SetBackgroundColour(wx.Colour(227,227,227))
        self.paths = wx.StaticText(self, -1, "The following paths are invalid: " + path)
        self.Centre()
        self.Show()

#### Shows the 'please wait' dialog while OSCAAR runs ####

class LoadingFrame(wx.Frame):
    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, 'Oscaar')
        self.loadingText = wx.StaticText(self, -1, 'Oscaar is currently running, please wait...')
        self.loadingText.Centre()
        
        self.SetSize((275,75))
        self.Centre()
        self.Show(True)

#### Launches worker processes ####
        
class WorkerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        homeDir()
        #oscaar.homeDir()
        #print os.getcwd()
        os.chdir('Code')
        execfile('differentialPhotometry.py')

#class JoinThread(threading.Thread):
#    def __init__(self, toJoin):
#        threading.Thread.__init__(self)
#        self.toJoin = toJoin
#        self.start()
#
#    def run(self):
#        self.toJoin.join()
#        wx.CallAfter(doneThreading)

#def doneThreading():
    #GraphFrame(None)
#    loading.Close()


#### Shows the graphs and outputs after OSCAAR completes ####

class GraphFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(GraphFrame, self).__init__(*args, **kwargs)
        self.graphIndex = 0
        self.graphList = [os.pardir + '/Outputs/Plots/jdRNF.png', os.pardir + 'Outputs/plots/goodnessOfFit.png', os.pardir + 'Outputs/plots/lightCurve.png']
        self.staticBitmap = wx.StaticBitmap(parent = self, pos = (20, 15), size = (800, 600))
        self.graph = wx.Image(self.graphList[self.graphIndex], wx.BITMAP_TYPE_ANY)
        self.graphIndex += 1
        self.bitmap = wx.BitmapFromImage(self.graph)
        self.staticBitmap.SetBitmap(self.bitmap)
        self.nextButton = wx.Button(parent = self, label = 'Next Graph', pos = (750, 585), size = (90, 35))
        self.Bind(wx.EVT_BUTTON, self.nextGraph, self.nextButton)
        self.prevButton = wx.Button(parent = self, label = 'Prev Graph', pos = (5, 585), size = (90, 35))
        self.Bind(wx.EVT_BUTTON, self.prevGraph, self.prevButton)
        self.prevButton.Hide()
        self.SetBackgroundColour('White')
        self.SetSize((850, 625))
        self.Centre()
        self.Show(True)

    def nextGraph(self, event):
        if self.graphIndex == len(self.graphList)-1:
            self.nextButton.SetLabel('Close')
        if self.graphIndex == len(self.graphList):
            self.Destroy()
            return
        if self.graphIndex == 1:
            self.prevButton.Show()
        self.graph = wx.Image(self.graphList[self.graphIndex], wx.BITMAP_TYPE_ANY)
        self.bitmap = wx.BitmapFromImage(self.graph)
        self.staticBitmap.SetBitmap(self.bitmap)
        self.graphIndex += 1

    def prevGraph(self, event):
        self.graphIndex -= 1
        if self.graphIndex == len(self.graphList)-2:
            self.nextButton.SetLabel('Next Graph')
        if self.graphIndex == 1:
            self.prevButton.Hide()
        self.graph = wx.Image(self.graphList[self.graphIndex-1], wx.BITMAP_TYPE_ANY)
        self.bitmap = wx.BitmapFromImage(self.graph)
        self.staticBitmap.SetBitmap(self.bitmap)
        
app = wx.App(False)
#### Runs the GUI ####
OscaarFrame(None)
app.MainLoop()

