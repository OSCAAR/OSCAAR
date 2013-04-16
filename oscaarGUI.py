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
#import oscaar

def homeDir():
    """Set the current directory to oscaar's home directory"""
    ### BM: changed the split() argument to '/' rather than '\\'.
    ### DG: added a platform check
    splitChar = os.sep
    if 'OSCAAR' in os.getcwd().split(splitChar):
        while os.getcwd().split(splitChar)[len(os.getcwd().split(splitChar))-1] != 'OSCAAR':
            os.chdir(os.pardir)

os.chdir('code')
if os.getcwd() not in sys.path:
    sys.path.insert(0, os.getcwd())
import oscaar


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
        self.Bind(wx.EVT_MENU, lambda event: self.setDefaults(event, 'code/init.par'), self.menuDefaults)
        self.linkToPredictions = self.oscaarMenu.Append(-1, 'Transit time predictions...', 'Transit time predictions...')
        self.Bind(wx.EVT_MENU, self.predictions, self.linkToPredictions)
        self.aboutOscaarButton = self.oscaarMenu.Append(-1, 'About oscaar', 'About oscaar')
        self.Bind(wx.EVT_MENU, self.aboutOscaar, self.aboutOscaarButton)
        self.helpItem = self.helpMenu.Append(wx.ID_HELP, 'Help', 'Help')
        self.Bind(wx.EVT_MENU, self.helpPressed, self.helpItem)
        self.SetMenuBar(menubar)
        self.sizer = wx.GridBagSizer(7, 7)        
        self.static_bitmap = wx.StaticBitmap(parent = self, pos = (0,0), size = (130,50))
        homeDir()
        #print os.getcwd()
        self.logo = wx.Image(os.getcwd()+ '/code/oscaar/logo4.png', wx.BITMAP_TYPE_ANY)
        self.bitmap = wx.BitmapFromImage(self.logo)
        self.static_bitmap.SetBitmap(self.bitmap)
        self.SetBackgroundColour(wx.Colour(233,233,233))
        if(sys.platform == 'darwin' or sys.platform == 'linux2'):
            self.labelFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        else: self.labelFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        
        #### CONTROL BUTTON DECLARATIONS ####
        self.radioTrackPlotOn = wx.RadioButton(self, label = "On", style = wx.RB_GROUP)
        self.radioTrackPlotOff = wx.RadioButton(self, label = "Off")
        
        textCtrlSize = (530,25)
        
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
        self.ingressDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
        self.ingressTime = wx.TextCtrl(self, value = '00:00:00')
        self.egressDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
        self.egressTime = wx.TextCtrl(self, value = '00:00:00') ## TimeCtrl to pick the egress time
        self.ds9Button = wx.Button(self, -1, 'Open DS9', size = (90, 25)) ## Button to open ds9
        self.masterFlatButton = wx.Button(self, -1, 'Master Flat Maker', size = (130,25), pos = (505, 433))
        self.notesField = wx.TextCtrl(self, value = 'Enter notes to be saved here', size = (220, 48), style = wx.TE_MULTILINE)
        self.notesLabel = wx.StaticText(self, label = 'Notes')
        self.notesLabel.SetFont(self.labelFont)
        self.outPathBtn = wx.Button(self, -1, 'Browse')
        self.outputTxt = wx.TextCtrl(self, value = 'outputs', size = textCtrlSize)
    
        ##### Add items to sizer for organization #####
        self.addPathChoice(2, self.darkPathTxt, self.darkPathBtn, wx.StaticText(self, -1, 'Path to Dark Frames: '), 'Choose Path to Dark Frames', False, None)
        self.addPathChoice(3, self.flatPathTxt, self.flatPathBtn, wx.StaticText(self, -1, 'Path to Master Flat: '), 'Choose Path to Flat Frames', False, None)
        self.addPathChoice(4, self.imagPathTxt, self.imagPathBtn, wx.StaticText(self, -1, 'Path to Data Images: '), 'Choose Path to Data Images', False, None)
        self.addPathChoice(5, self.regPathTxt, self.regPathBtn, wx.StaticText(self, -1, 'Path to Regions File: '), 'Choose Path to Regions File', True, wx.FD_OPEN)
        self.addPathChoice(6, self.outputTxt, self.outPathBtn, wx.StaticText(self, -1, 'Output Path'), 'Choose Output Directory', True, wx.FD_SAVE)
        self.addButtonPair(7, 4, self.radioTrackPlotOn, self.radioTrackPlotOff, wx.StaticText(self, -1, 'Tracking Plots: '))
        self.addButtonPair(8, 4, self.photPlotsOn, self.photPlotsOff, wx.StaticText(self, -1, 'Photometry Plots:     '))
        self.addTextCtrl(7,0, self.trackZoomTxt, wx.StaticText(self, -1, 'Track Zoom: '))
        self.addTextCtrl(8,0, self.ccdGainTxt, wx.StaticText(self, -1, 'CCD Gain: '))
        self.addTextCtrl(9,0, self.radiusTxt, wx.StaticText(self, -1, 'Aperture Radius: '))
        self.addTextCtrl(10,0, self.smoothingConstTxt, wx.StaticText(self, -1, 'Smoothing Constant: '))
        self.addDateCtrl(9,4, self.ingressDate, self.ingressTime, wx.StaticText(self, -1, 'Ingress, UT (YYYY/MM/DD):       '))
        self.addDateCtrl(10,4, self.egressDate, self.egressTime, wx.StaticText(self, -1, 'Egress, UT (YYYY/MM/DD):       '))
        self.sizer.Add(self.ds9Button,(12,5), wx.DefaultSpan, wx.ALIGN_CENTER, 7)
        self.ds9Button.Bind(wx.EVT_BUTTON, self.openDS9)
        self.sizer.Add(self.masterFlatButton, (12,4), wx.DefaultSpan, wx.ALIGN_CENTER, 7)
        self.masterFlatButton.Bind(wx.EVT_BUTTON, self.openMasterFlatGUI)
        self.sizer.Add(self.notesField, (11, 1), (2,2), wx.ALIGN_CENTER, 7)
        self.sizer.Add(self.notesLabel, (11, 0 ), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.setDefaults(None, 'code/init.par')

        # Code to make Run button default for main window
        run = wx.Button(self, -1, 'Run')
                #setDefault(self.run)
                #self.run.SetFocus()
        
        self.sizer.Add(self.run, (12,6), wx.DefaultSpan, wx.ALIGN_CENTER, 7)
        self.run.Bind(wx.EVT_BUTTON, self.runOscaar)
        self.sizer.SetDimension(5, 5, 550, 500)
        self.SetSizer(self.sizer)
        if(sys.platform == 'darwin'):
            setSize = (900, 475) ## Sizes for Mac
        elif(sys.platform == 'linux2'):
            setSize = (975, 500)
        else:  setSize = (900, 535) ##Made the size bigger so the items fit in all os
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

    def addPathChoice(self, row, textCtrl, button, label, message, fileDialog, saveDialog):
        label.SetFont(self.labelFont)
        self.sizer.Add(label, (row, 0), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.sizer.Add(textCtrl, (row, 1), (1,5), wx.TOP, 7)
        self.sizer.Add(button, (row, 6), (1,1), wx.TOP, 7)
        textCtrl.SetForegroundColour(wx.Colour(180,180,180))
        button.Bind(wx.EVT_BUTTON, lambda event: self.browseButtonEvent(event, message, textCtrl, fileDialog, saveDialog))
        textCtrl.Bind(wx.EVT_TEXT, lambda event: self.updateColor(textCtrl))

    def addDateCtrl(self, row, colStart, dateCtrl, timeCtrl, label):
        label.SetFont(self.labelFont)
        self.sizer.Add(label, (row, colStart), wx.DefaultSpan, wx.ALIGN_RIGHT | wx.TOP, 7)
        self.sizer.Add(dateCtrl, (row, colStart+1), wx.DefaultSpan, wx.TOP , 7)
        self.sizer.Add(timeCtrl, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)

    def updateColor(event,ctrl):
        ctrl.SetForegroundColour(wx.Colour(0,0,0))

    #####Functions for event handling#####
    def browseButtonEvent(self, event, message, textControl, fileDialog, saveDialog):
        if fileDialog:
            dlg = wx.FileDialog(self, message = message, style = saveDialog)
        else: dlg = wx.DirDialog(self, message = message,  style = wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            textControl.Clear()
            if fileDialog == False:
                textControl.WriteText(dlg.GetPath().replace(os.sep, '/'))
            else: textControl.WriteText(dlg.GetPath().replace(os.sep, '/'))
        dlg.Destroy()

    #####Opens DS9 to create a regions file when button is pressed#####
    def openDS9(self, event):
        ds9 = os.pardir + '/OSCAAR/extras/ds9'
        ds9Loc = ds9 + '/' + sys.platform + '/ds9'
        regionsName =  ds9 + '/testFits.fit'  ##if it is beneficial, we could use glob to get the users actual image here
        subprocess.Popen([ds9Loc, regionsName])
        
    def openMasterFlatGUI(self, event):
        MasterFlatFrame(None)

    #####Opens the webpage for the documentation when help is pressed#####
    def helpPressed(self, event):
        homeDir()
        os.chdir('docs')
        if sys.platform == 'linux2': ##Haven't tested this
            os.system("/usr/bin/xdg-open OscaarDocumentation-20110917.pdf")
        elif sys.platform == 'darwin':
            os.system("open OscaarDocumentation-20110917.pdf")
        elif sys.platform == 'win32':
            os.startfile('OscaarDocumentation-20110917.pdf')
        
    #####Runs the photom script with the values entered into the gui when 'run' is pressed#####
    def runOscaar(self, event):
        homeDir()
        os.chdir('code')
        global worker
        worker = None
        notes = open('outputs/notes.txt', 'a')
        notes.write('\n\n\n------------------------------------------'+\
                    '\nRun initiated (LT): '+strftime("%a, %d %b %Y %H:%M:%S"))

        if self.notesField.GetValue() == 'Enter notes to be saved here':
            notes.write('\nNo notes entered.')
        else: 
            notes.write('\nNotes: '+str(self.notesField.GetValue()))
        
        notes.close()
        init = open('init.par', 'w')
        #Write to init.par
        self.darkFits = self.addStarFits(init, 'Path to Dark Frames: ', self.darkPathTxt.GetValue())
        self.imgFits = self.addStarFits(init, 'Path to data images: ', self.imagPathTxt.GetValue())
        self.flatFits = self.addStarFits(init, 'Path to Master-Flat Frame: ', self.flatPathTxt.GetValue())
        self.regFits = self.addStarFits(init, 'Path to regions file: ', self.regPathTxt.GetValue())
        init.write('Output Path: ' + self.outputTxt.GetValue() + '\n')
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
        init = open('init.par', 'r').read().splitlines()
        if self.validityCheck():
            if self.outputOverwriteCheck(self.outputTxt.GetValue()):
                self.Destroy()
                if not worker:
                    worker = WorkerThread()
    
    def addStarFits(self, init, field, path):
        fitsPath = path
        if os.path.isdir(fitsPath) and not (fitsPath.endswith(os.sep)):
            fitsPath += os.sep
        if path.endswith(os.sep):
            fitsPath += '*.fits'
        init.write(field + fitsPath + '\n')
        return fitsPath
        
    def validityCheck(self):
        darkFrames = glob(self.darkFits)
        imageFiles = glob(self.imgFits)
        regionsFile = glob(self.regFits)
        flatFrames = glob(self.flatFits)
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
        if not self.containsFit(flatFrames) and self.flatFits!='None':
            if commaNeeded:
                invalidsString += ", "
            invalidsString += "Flat Frames"
        if invalidsString == "":
            return True
        else:
            InvalidPath(invalidsString, None, -1)
    
    def outputOverwriteCheck(self, path):
        pathCorrected = path.replace('/', os.sep)
        outfolder = pathCorrected[:pathCorrected.rfind(os.sep)] + os.sep + '*'
        if pathCorrected + '.pkl' in glob(outfolder):
            OverWriteFrame(pathCorrected, self, -1)
            return False
        return True
                 
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
        if(time.count(":") is 1):
            time += ":00"
        result += str(time)
        filename.write(text + result + '\n')    

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
                if inline[0] == 'Output Path': self.outputTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
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

    def aboutOscaar(self, event):
        AboutFrame(None,-1)

class OverWriteFrame(wx.Frame):
    def __init__(self, path, parent, id):
        self.parent = parent
        wx.Frame.__init__(self, parent, id, 'Overwrite outputs?')
        self.SetSize((280,120))
        self.SetBackgroundColour(wx.Colour(227,227,227))
        self.warningText = wx.StaticText(parent = self, id = -1, label = 'Are you sure you want to overwrite\n ' + path + '?', pos = (35,7), style = wx.ALIGN_CENTER)
        self.yesButton = wx.Button(parent = self, id = -1, label = 'Yes', pos = (35,50))
        self.noButton = wx.Button(parent = self, id = -1, label = 'No', pos = (145,50))
        self.yesButton.Bind(wx.EVT_BUTTON, self.onYes)
        self.noButton.Bind(wx.EVT_BUTTON, self.onNo)
        self.Centre()
        self.Show()
    def onNo(self, event):
        self.Destroy()
    def onYes(self, event):
        self.parent.Destroy()
        worker = WorkerThread()

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
        #self.plotsOn = wx.RadioButton(self, -1, 'On')
        #self.plotsOff = wx.RadioButton(self, -1, 'Off')
        self.plotsRadioBox = wx.RadioBox(self,-1, "Plots", (10,10), wx.DefaultSize, ["On", "Off"], wx.RA_SPECIFY_COLS)
        self.flatRadioBox = wx.RadioBox(self,-1, "Flat Type", (10,10), wx.DefaultSize, ["Standard", "Twilight"], wx.RA_SPECIFY_COLS)
        #self.standardFlat = wx.RadioButton(self, -1, 'Standard')
        #self.twilightFlat = wx.RadioButton(self, -1, 'Twilight')
        self.flatBrowse = wx.Button(self, -1, 'Browse')
        self.darkBrowse = wx.Button(self, -1, 'Browse')
        self.masterPathBrowse = wx.Button(self, -1, 'Browse')
        self.title = wx.StaticText(self, -1, 'OSCAAR: Master Flat Maker')
        self.titleFont = wx.Font(15, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
        self.title.SetFont(self.titleFont)
        self.runButton = wx.Button(self, -1, 'Run')
        self.runButton.Bind(wx.EVT_BUTTON, self.runMasterFlatMaker)

        ## Set some defaults:
        #self.standardFlat.SetValue(True)
        #self.plotsOn.SetValue(True)
        self.labelFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        ######Add to sizer######
        self.frameSizer.Add(self.runButton, (4,5), wx.DefaultSpan, wx.TOP, 15) 
        self.frameSizer.Add(self.title, (0,0), (1,2), wx.LEFT | wx.TOP, 7)
        self.addPathChoice(self.frameSizer, 1, wx.StaticText(self, -1, 'Path to Flat Images:'), 
                           self.flatBrowse, self.flatImagesPathCtrl, 'Choose Path to Flats...')
        self.addPathChoice(self.frameSizer, 2, wx.StaticText(self, -1, 'Path to Dark Flat Images:'), 
                           self.darkBrowse, self.flatDarksPathCtrl, 'Choose Path to Darks...')
        self.addPathChoice(self.frameSizer, 3, wx.StaticText(self, -1, 'Path to Save Master Flat:'), 
                           self.masterPathBrowse, self.masterFlatPathCtrl, 'Choose Path to Save Master Flat...')
        self.frameSizer.Add(self.plotsRadioBox, (4,0), wx.DefaultSpan)
        self.frameSizer.Add(self.flatRadioBox, (4,1), (1,4))
        ###Set GUI Frame Attributes###
        if sys.platform == 'Win32':
            frameSize = (640, 260)
        elif sys.platform == 'darwin':
            frameSize = (700, 220)
        else: frameSize = (625, 245)
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

#    def addButtonPair(self, sizer, row, colStart, label, button1, button2): ##defined for neater insertion of control items
#        sizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 12) ##border of 12 pixels on the top and left
#        sizer.Add(button1, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
#        sizer.Add(button2, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)

    def addButtonPair(self, row, colStart, button1, button2, label):
        label.SetFont(self.labelFont)
        self.frameSizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7) ##border of 8 pixels on the top and left
        self.frameSizer.Add(button1, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
        self.frameSizer.Add(button2, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)

    #####Button Press Event Functions#####
    def openDirDialog(self, event, message, textControl):
        dlg = wx.DirDialog(self, message = message, style = wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            textControl.Clear()
            textControl.WriteText(dlg.GetPath())
        dlg.Destroy()

    def runMasterFlatMaker(self, event):
        #print self.plotsRadioBox.GetSelection() == 0
        path = self.masterFlatPathCtrl.GetValue()
        if(not path.endswith(".fits")):
            path += ".fits"
        pathCorrected = path.replace('/', os.sep) + '.fits'
        outfolder = pathCorrected[:pathCorrected.rfind(os.sep)] + os.sep + '*'
        if pathCorrected in glob(outfolder):
            global standardFlat
            standardFlat = self.self.flatRadioBox.GetSelection() == 0
            OverwFlatFrame(pathCorrected,self,-1)
        else:
            if self.standardFlat.GetValue():
                oscaar.standardFlatMaker(glob(self.flatImagesPathCtrl.GetValue()), glob(self.flatDarksPathCtrl.GetValue()), self.masterFlatPathCtrl.GetValue(), self.plotsRadioBox.GetSelection() == 0)
            else: 
                oscaar.twilightFlatMaker(glob(self.flatImagesPathCtrl.GetValue()), glob(self.flatDarksPathCtrl.GetValue()), self.masterFlatPathCtrl.GetValue(), self.plotsRadioBox.GetSelection() == 0)
            self.Destroy()
        
    def overWriteFlat(self):
        path = self.masterFlatPathCtrl.GetValue()
        pathCorrected = path.replace('/', os.sep) + '.fits'
        outfolder = pathCorrected[:pathCorrected.rfind(os.sep)] + os.sep + '*'
        if pathCorrected in glob(outfolder):
            return True
        else: return False

class OverwFlatFrame(wx.Frame):
    def __init__(self, path, parent, id):
        self.parent = parent
        self.path = path
        wx.Frame.__init__(self, parent, id, 'Overwrite master flat?')
        self.SetSize((360,120))
        self.SetBackgroundColour(wx.Colour(227,227,227))
        self.warningText = wx.StaticText(parent = self, id = -1, label = 'Are you sure you want to overwrite\n ' + path + '?', pos = (15,7), style = wx.ALIGN_CENTER)
        self.yesButton = wx.Button(parent = self, id = -1, label = 'Yes', pos = (60,50))
        self.noButton = wx.Button(parent = self, id = -1, label = 'No', pos = (190,50))
        self.yesButton.Bind(wx.EVT_BUTTON, self.onYes)
        self.noButton.Bind(wx.EVT_BUTTON, self.onNo)
        self.Centre()
        self.Show()
    def onNo(self, event):
        self.Destroy()
    def onYes(self, event):
        os.remove(self.path)
#        oscaar.standardFlatMaker(glob(self.parent.flatImagesPathCtrl.GetValue()), glob(self.parent.flatDarksPathCtrl.GetValue()), self.parent.masterFlatPathCtrl.GetValue(), self.parent.plotsOn.GetValue())
        #print self.parent.standardFlat.GetValue()
        if self.parent.standardFlat.GetValue():
#        if self.standardFlat.GetValue():
            oscaar.standardFlatMaker(glob(self.parent.flatImagesPathCtrl.GetValue()), glob(self.parent.flatDarksPathCtrl.GetValue()), self.parent.masterFlatPathCtrl.GetValue(), self.parent.plotsOn.GetValue())
        else: 
            oscaar.twilightFlatMaker(glob(self.parent.flatImagesPathCtrl.GetValue()), glob(self.parent.flatDarksPathCtrl.GetValue()), self.parent.masterFlatPathCtrl.GetValue(), self.parent.plotsOn.GetValue())

        self.parent.Destroy()
        
### "About" panel ###
class AboutFrame(wx.Frame):
    def __init__(self, parent, id):
        self.parent = parent
        wx.Frame.__init__(self, parent, id, 'About oscaar')
        if(sys.platform == 'darwin' or sys.platform == 'linux2'):
            self.SetSize((525, 440))
        else: self.SetSize((600,500))
        self.SetBackgroundColour(wx.Colour(227,227,227))
        self.static_bitmap = wx.StaticBitmap(parent = self, pos = (0,0), style=wx.ALIGN_CENTER)
        homeDir()
        self.logo = wx.Image(os.getcwd()+'/code/oscaar/logo4.png', wx.BITMAP_TYPE_ANY)
        self.bitmap = wx.BitmapFromImage(self.logo)
        self.static_bitmap.SetBitmap(self.bitmap)
        if(sys.platform == 'darwin' or sys.platform == 'linux2'):
            self.labelFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        else: self.labelFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        ### WARNING: Do not post your name here or remove someone elses without consulting Brett Morris.
        titleText = '\n'.join(['oscaar v2.0beta',\
                     'Open Source differential photometry Code for Amateur Astronomical Research',\
                     'Created by Brett Morris (NASA GSFC/UMD)\n'])
        contribText = '\n'.join(['Other Contributors:',\
                     'Nolan Matthews (UMD)',\
                     'Harley Katz (UMD)',\
                     'Daniel Galdi (UMD)',\
                     'Sam Gross (UMD)',\
                     'Naveed Chowdhury (UMD)',\
                     'Jared King (UMD)',\
                     'Steven Knoll (UMD)',\
                     'Luuk Visser (Leiden University)'])
        
        self.titleText = wx.StaticText(parent = self, id = -1, label = titleText, pos=(0,75),style = wx.ALIGN_CENTER)
        self.viewRepoButton = wx.Button(parent = self, id = -1, label = 'Open Code Repository (GitHub)', style = wx.ALIGN_CENTER)
        self.viewRepoButton.Bind(wx.EVT_BUTTON, self.openRepo)
        
        self.contribText = wx.StaticText(parent = self, id = -1, label = contribText,style = wx.ALIGN_CENTER)
        self.exitButton = wx.Button(parent = self, id = -1, label = 'Close', style = wx.ALIGN_CENTER)
        self.exitButton.Bind(wx.EVT_BUTTON, self.exit)
        self.frameSizer = wx.GridBagSizer(7,7)
        self.frameSizer.Add(self.static_bitmap, (0,0), wx.DefaultSpan, wx.ALL | wx.ALIGN_CENTER,7) 
        self.frameSizer.Add(self.titleText, (1,0) , wx.DefaultSpan, wx.ALL | wx.ALIGN_CENTER,7)
        self.frameSizer.Add(self.viewRepoButton, (2,0) , wx.DefaultSpan, wx.ALL | wx.ALIGN_CENTER,7)        
        self.frameSizer.Add(self.contribText, (3,0) , wx.DefaultSpan, wx.ALL | wx.ALIGN_CENTER,7)
        self.frameSizer.Add(self.exitButton,(4,0) , wx.DefaultSpan, wx.ALL | wx.ALIGN_CENTER,7)

        self.SetSizer(self.frameSizer)
        self.Centre()
        self.Show()
        
    def exit(self,event):
        self.Destroy()
    def openRepo(self, event):
        webbrowser.open_new_tab("https://github.com/OSCAAR/OSCAAR")





#### Checks if the dark frames are valid ####

class InvalidPath(wx.Frame):
    def __init__(self, path, parent, id):
        wx.Frame.__init__(self, parent, id, 'Check Path names')
        self.SetSize((250,100))
        self.SetBackgroundColour(wx.Colour(227,227,227))
        self.paths = wx.StaticText(self, -1, "The following paths are invalid: " + path)
        self.okButton = wx.Button(self, -1, 'Okay', pos = (self.GetPos()[0]/2,self.GetPos()[1]/2))
        self.Centre()
        self.Show()

#### Launches worker processes ####
        
class WorkerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        homeDir()
        os.chdir('code')
        execfile('differentialPhotometry.py')

class PlotThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        homeDir()
        os.chdir('code')
        execfile('plotPickle.py')

app = wx.App(False)
#### Runs the GUI ####
OscaarFrame(None)
app.MainLoop()
