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
import oscaar
import random
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
    def __init__(self, *args, **kwargs):
        super(OscaarFrame, self).__init__(*args, **kwargs)
        self.InitUI()

    #### Creates and initializes the GUI ####
    def InitUI(self):
        #### Defines the menubar ####
        global masterFlatOpen ##Global variables to ensure one instance of each frame open at a time
        global ephGUIOpen
        global aboutOpen
        global loadOldPklOpen
        masterFlatOpen = False
        ephGUIOpen = False
        aboutOpen = False
        loadOldPklOpen = False
	
        self.menubar = wx.MenuBar() ##This is the main menubar where all menus are attached
        self.fileMenu = wx.Menu()  ##File menu for quit
        self.oscaarMenu = wx.Menu()  ##Menu for oscaar features
        self.helpMenu = wx.Menu()
	
	##Append menu options to different menus:
        menuExit = self.fileMenu.Append(wx.ID_EXIT, 'Quit\tCtrl+Q', 'Quit application') ##provides a way to quit
        self.menubar.Append(self.fileMenu, '&File')
        self.menubar.Append(self.helpMenu, '&Help')
        self.menubar.Append(self.oscaarMenu, '&Oscaar')
        self.Bind(wx.EVT_MENU, self.OnQuit, menuExit) ##Bind with OnQuit function, which closes the application
	##Initialize and menu items and bind them to a function
        self.linkToPredictions = self.oscaarMenu.Append(-1, 'Transit time predictions...', 'Transit time predictions...')
        self.Bind(wx.EVT_MENU, self.predictions, self.linkToPredictions)
        self.aboutOscaarButton = self.oscaarMenu.Append(-1, 'About oscaar', 'About oscaar')
        self.Bind(wx.EVT_MENU, self.aboutOscaar, self.aboutOscaarButton)
        self.helpItem = self.helpMenu.Append(wx.ID_HELP, 'Help', 'Help')
        self.Bind(wx.EVT_MENU, self.helpPressed, self.helpItem)
        self.loadPklItem = self.oscaarMenu.Append(-1, "&Load old output\tCtrl-L", "Load old output")
        self.Bind(wx.EVT_MENU, self.loadOldPklPressed, self.loadPklItem)

        self.SetMenuBar(self.menubar)
        self.sizer = wx.GridBagSizer(7, 7) ##The sizer organizes gui items in a grid, all items are added to the sizer        
        self.static_bitmap = wx.StaticBitmap(parent = self, pos = (0,0), size = (130,50))
	##Adds logo image to the gui
        self.logo = wx.Image(os.path.join(os.path.dirname(__file__),'images','logo4.png'), wx.BITMAP_TYPE_ANY)
        self.bitmap = wx.BitmapFromImage(self.logo)
        self.static_bitmap.SetBitmap(self.bitmap)
        self.SetBackgroundColour(wx.Colour(233,233,233))
        if(sys.platform == 'darwin' or sys.platform == 'linux2'):
            self.labelFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        else: self.labelFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        
        #### CONTROL BUTTON DECLARATIONS ####
        self.radioTrackPlotOn = wx.RadioButton(self, label = "On", style = wx.RB_GROUP)
        self.radioTrackPlotOff = wx.RadioButton(self, label = "Off")
        
        textCtrlSize = (555,25) ##Tuple defining default TextCtrl size
	
	##Dark images path displayed in darkPathTxt TextCtrl, size is set to default size
        self.darkPathTxt = wx.TextCtrl(self, size = textCtrlSize)
	##Defines browse button for dark images path
        self.darkPathBtn = wx.Button(self, -1, 'Browse')
        self.flatPathTxt = wx.TextCtrl(self, size = textCtrlSize)
        self.flatPathBtn = wx.Button(self, -1, 'Browse')
        self.imagPathTxt = wx.TextCtrl(self, size = textCtrlSize)
        self.imagPathBtn = wx.Button(self, -1, 'Browse')
        self.regPathTxt = wx.TextCtrl(self, size = textCtrlSize)
        self.regPathBtn = wx.Button(self, -1, 'Browse')
	
	##Text Control and RadioButton declarations
        self.smoothingConstTxt = wx.TextCtrl(self, value = '0')
        self.radiusTxt = wx.TextCtrl(self, value = '0')
        self.trackZoomTxt = wx.TextCtrl(self, value = '0')
        self.ccdGainTxt = wx.TextCtrl(self, value = '0')
        self.photPlotsOn = wx.RadioButton(self, label = 'On', style = wx.RB_GROUP) ##Only one button from each "RB_GROUP" can be selected
        self.photPlotsOff = wx.RadioButton(self, label = 'Off')
        self.ingressDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
        self.ingressTime = wx.TextCtrl(self, value = '00:00:00')
        self.egressDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
        self.egressTime = wx.TextCtrl(self, value = '00:00:00') ## TimeCtrl to pick the egress time
        self.ds9Button = wx.Button(self, -1, 'Open DS9', size = (90, 25)) ## Button to open ds9
        self.masterFlatButton = wx.Button(self, -1, 'Master Flat Maker', size = (130,25), pos = (505, 433)) ## Open master flat maker GUI
        self.ephButton = wx.Button(self,-1, 'Ephemeris')  ## Open Ephemeris GUI
	##Large TextCtrl that allows you to enter notes for a transit
        self.notesField = wx.TextCtrl(self, value = 'Enter notes to be saved here', size = (220, 48), style = wx.TE_MULTILINE)
        self.notesLabel = wx.StaticText(self, label = 'Notes')
        self.notesLabel.SetFont(self.labelFont)
        self.outPathBtn = wx.Button(self, -1, 'Browse')
        self.outputTxt = wx.TextCtrl(self, value = 'outputs', size = textCtrlSize)
	self.valid_text = [None, None, wx.StaticText(self,-1, 'INVALID'), wx.StaticText(self,-1, 'INVALID'), wx.StaticText(self,-1, 'INVALID'), wx.StaticText(self,-1, 'INVALID')]
	self.sizer.Add(self.valid_text[2], (2,7), wx.DefaultSpan, wx.TOP, 12)
	self.sizer.Add(self.valid_text[3], (3,7), wx.DefaultSpan, wx.TOP, 12)
	self.sizer.Add(self.valid_text[4], (4,7), wx.DefaultSpan, wx.TOP, 12)
	self.sizer.Add(self.valid_text[5], (5,7), wx.DefaultSpan, wx.TOP, 12)

    
        ##### Add items to sizer for organization #####
	## First parameter is always the row in which the item is placed
	## Second to last parameter of addPathChoice represents whether there will be single file select, if it is false there will be multiple
        self.addPathChoice(2, self.darkPathTxt, self.darkPathBtn, wx.StaticText(self, -1, 'Path to Dark Frames: '), 'Choose Path to Dark Frames', False, None)
        self.addPathChoice(3, self.flatPathTxt, self.flatPathBtn, wx.StaticText(self, -1, 'Path to Master Flat: '), 'Choose Path to Flat Frames', True, wx.FD_OPEN)
        self.addPathChoice(4, self.imagPathTxt, self.imagPathBtn, wx.StaticText(self, -1, 'Path to Data Images: '), 'Choose Path to Data Images', False, None)
        self.addPathChoice(5, self.regPathTxt, self.regPathBtn, wx.StaticText(self, -1, 'Path to Regions File: '), 'Choose Path to Regions File', True, wx.FD_OPEN)
        self.addPathChoice(6, self.outputTxt, self.outPathBtn, wx.StaticText(self, -1, 'Output Path'), 'Choose Output Name', True, wx.FD_SAVE)
	self.darkPathTxt.Bind(wx.EVT_TEXT, lambda event: self.checkValid(event, 2, self.darkPathTxt.GetValue(), None))
	self.flatPathTxt.Bind(wx.EVT_TEXT, lambda event: self.checkValid(event, 3, self.flatPathTxt.GetValue(), None))
	self.imagPathTxt.Bind(wx.EVT_TEXT, lambda event: self.checkValid(event, 4, self.imagPathTxt.GetValue(), None))
	self.regPathTxt.Bind(wx.EVT_TEXT, lambda event: self.checkValid(event, 5, self.regPathTxt.GetValue(), True))
        self.addButtonPair(7, 4, self.radioTrackPlotOn, self.radioTrackPlotOff, wx.StaticText(self, -1, 'Tracking Plots: '))
        self.addButtonPair(8, 4, self.photPlotsOn, self.photPlotsOff, wx.StaticText(self, -1, 'Photometry Plots:     '))
        self.addTextCtrl(7,0, self.trackZoomTxt, wx.StaticText(self, -1, 'Track Zoom: '))
        self.addTextCtrl(8,0, self.ccdGainTxt, wx.StaticText(self, -1, 'CCD Gain: '))
        self.addTextCtrl(9,0, self.radiusTxt, wx.StaticText(self, -1, 'Aperture Radius: '))
        self.addTextCtrl(10,0, self.smoothingConstTxt, wx.StaticText(self, -1, 'Smoothing Constant: '))
        self.addDateCtrl(9,4, self.ingressDate, self.ingressTime, wx.StaticText(self, -1, 'Ingress, UT (YYYY/MM/DD):       '))
        self.addDateCtrl(10,4, self.egressDate, self.egressTime, wx.StaticText(self, -1, 'Egress, UT (YYYY/MM/DD):       '))
        self.sizer.Add(self.ephButton, (12,3),wx.DefaultSpan,wx.ALIGN_CENTER, 7)
        self.ephButton.Bind(wx.EVT_BUTTON, self.openEphGUI)
        self.sizer.Add(self.ds9Button,(12,5), wx.DefaultSpan, wx.ALIGN_CENTER, 7)
        self.ds9Button.Bind(wx.EVT_BUTTON, self.openDS9)
        self.sizer.Add(self.masterFlatButton, (12,4), wx.DefaultSpan, wx.ALIGN_CENTER, 7)
        self.masterFlatButton.Bind(wx.EVT_BUTTON, self.openMasterFlatGUI)
        self.sizer.Add(self.notesField, (11, 1), (2,2), wx.ALIGN_CENTER, 7)
        self.sizer.Add(self.notesLabel, (11, 0 ), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.setDefaults(None, os.path.join(os.path.dirname(__file__),'init.par'))

        # Code to make Run button default for main window
        self.run = wx.Button(self, -1, 'Run')
        #setDefault(self.run)
        #self.run.SetFocus()
        
	## Add the run button to the sizer ##
        self.sizer.Add(self.run, (12,6), wx.DefaultSpan, wx.ALIGN_CENTER, 7)
        self.run.Bind(wx.EVT_BUTTON, self.runOscaar)
	## Set the sizer's dimensions ##
        self.sizer.SetDimension(5, 5, 550, 500)
	## Set OscaarFrame's sizer to the sizer all the items are added to ##
        self.SetSizer(self.sizer)
        self.bestSize = self.GetBestSizeTuple() ##These three lines set the frame size to be appropriate regardless of os
        setSize = (self.bestSize[0]+20,self.bestSize[1]+20) 
        self.SetSize(setSize)
        self.SetMinSize(setSize) ##Set minimum size so that all gui items are always visible
        self.SetTitle('OSCAAR') ##Set the frame's title
        iconloc = os.path.join(os.path.dirname(__file__),'images','logo4noText.ico')
        icon1 = wx.Icon(iconloc, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon1) ##Set frame's icon
        self.Centre()
        self.Show(True)

    def checkValid(self, event, row, text, isRegion):
	valid = False
	if isRegion:
	    for path in text.split(','):
		if path in glob(path[:path.rfind(os.sep)] + os.sep + '*') and path.endswith('.reg'):
		    valid = True
		else:
		    for fil in (glob(path)):
			if fil.endswith('.fit') or fil.endswith('.fits'):
			    valid = True
	else:
	    for path in text.split(','):
		if path in glob(path[:path.rfind(os.sep)] + os.sep + '*') and (path.endswith('.fit') or path.endswith('.fits')):
		    valid = True
		else:
		    for fil in (glob(path)):
			if fil.endswith('.fit') or fil.endswith('.fits'):
			    valid = True
	if valid: self.updateImage(True, row)
	else: self.updateImage(False, row)
			
    def updateImage(self, on, row):
	if on == True:
	    self.valid_text[row].SetLabel('O')
	    self.valid_text[row].SetForegroundColour(wx.Colour(20,220,20))
	else:
	    self.valid_text[row].SetLabel('X')
	    self.valid_text[row].SetForegroundColour(wx.Colour(255,0,0))

    #### Allows quitting from the file menu. (Fixes cmd-Q on OS X), Bound to the exit menu item ####
    def OnQuit(self, e): 
        self.Close()

    #### Neater creation of control items ####
    #### All control items (TextCtrls, Buttons, etc.) are passed into these functions to be added to sizer ####
    def addButtonPair(self, row, colStart, button1, button2, label):
        label.SetFont(self.labelFont) ##Set font type for each button created
        self.sizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7) ##border of 8 pixels on the top and left
        self.sizer.Add(button1, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
        self.sizer.Add(button2, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)

    def addTextCtrl(self, row, colStart, textCtrl, label):
        label.SetFont(self.labelFont)
        self.sizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7) ##Adds a text field and a label to the sizer
        self.sizer.Add(textCtrl, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
        textCtrl.SetForegroundColour(wx.Colour(120,120,120)) ##Set Color of TextCtrl text
        textCtrl.Bind(wx.EVT_TEXT, lambda event: self.updateColor(textCtrl)) ##Updates color if text is changed.

    def addPathChoice(self, row, textCtrl, button, label, message, fileDialog, saveDialog):
        label.SetFont(self.labelFont)
        self.sizer.Add(label, (row, 0), wx.DefaultSpan, wx.LEFT | wx.TOP, 7) ##Add label to sizer
        self.sizer.Add(textCtrl, (row, 1), (1,5), wx.TOP, 7) ##Add TextCtrl to sizer
        self.sizer.Add(button, (row, 6), (1,1), wx.TOP, 7)
        textCtrl.SetForegroundColour(wx.Colour(120,120,120)) ##Set text color
	## Bind the browse button to browseButtonEvent with parameters entered
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
	if saveDialog == wx.SAVE:
	    dlg.SetFilename('outputName')
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

    #####Opens DS9 to create a regions file when button is pressed#####
    def openDS9(self, event):
        ds9 = os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'extras','ds9',sys.platform,'ds9')
        #ds9Loc = ds9 + '/' + sys.platform + '/ds9'
        #regionsName =  ds9 + '/testFits.fit'  ##if it is beneficial, we could use glob to get the users actual image here
        #subprocess.Popen([ds9Loc, regionsName])
        subprocess.Popen([ds9])
        
    #### Bound to the masterFlatButton button, opens the MasterFlatFrame
    def openMasterFlatGUI(self, event):
        global masterFlatOpen
        if masterFlatOpen == False:
            masterFlatOpen = True
            MasterFlatFrame(self)
        
    #### Bound to the openEphGui button, opens the Ephemeris GUI
    def openEphGUI(self,event):
        global ephGUIOpen
        if ephGUIOpen == False:
	    try:
		import ephem
	    except ImportError:
		WarnFrame(self)
	    else:
		ephGUIOpen = True
		EphFrame(self)
            
    #####Opens the webpage for the documentation when help is pressed#####
    def helpPressed(self, event):
        documentationURL = 'https://github.com/OSCAAR/OSCAAR/tree/master/docs/documentationInProgress'
        webbrowser.open_new_tab(documentationURL)

	#####Opens the webpage for the documentation when help is pressed#####
    def loadOldPklPressed(self, event):
        global loadOldPklOpen
        if loadOldPklOpen == False:
            LoadOldPklFrame()
            loadOldPklOpen = True
		        
    #####Runs the photom script with the values entered into the gui when 'run' is pressed#####
    def runOscaar(self, event):
        global worker ##Declaration of the worker thread
        worker = None ##initialize threads to None
        notes = open(os.path.join(os.path.dirname(__file__),'outputs','notes.txt'), 'w')
        notes.write('\n\n\n------------------------------------------'+\
                    '\nRun initiated (LT): '+strftime("%a, %d %b %Y %H:%M:%S"))

	##Only write notes if the notes field has been changed
        if self.notesField.GetValue() == 'Enter notes to be saved here':
            notes.write('\nNo notes entered.')
        else: 
            notes.write('\nNotes: '+str(self.notesField.GetValue()))
        
        notes.close()
        init = open(os.path.join(os.path.dirname(__file__),'init.par'), 'w')
        ##Write to init.par
	##init.par is parsed by the photometry script for the initial parameters
	##Copy image path fields from gui to init.par
        self.darkFits = self.addStarFits(init, 'Path to Dark Frames: ', self.darkPathTxt.GetValue())
        self.imgFits = self.addStarFits(init, 'Path to data images: ', self.imagPathTxt.GetValue())
        self.flatFits = self.addStarFits(init, 'Path to Master-Flat Frame: ', self.flatPathTxt.GetValue())
        self.regFits = self.addStarFits(init, 'Path to regions file: ', self.regPathTxt.GetValue())
        init.write('Output Path: ' + self.outputTxt.GetValue() + '\n')
	##Write the ingress and egress time with the correct format to init.par
        self.parseTime(self.ingressDate.GetValue(), self.ingressTime.GetValue(), 'Ingress: ',  init)
        self.parseTime(self.egressDate.GetValue(), self.egressTime.GetValue(), 'Egress: ', init)
        self.checkRB(self.radioTrackPlotOn, 'Plot Tracking: ', init)
        self.checkRB(self.photPlotsOn, 'Plot Photometry: ', init)
	##Copy all TextCtrl fields into init.par
        init.write('Smoothing Constant: ' + self.smoothingConstTxt.GetValue() + '\n')
        init.write('CCD Gain: ' + self.ccdGainTxt.GetValue() + '\n')
        init.write('Radius: ' + self.radiusTxt.GetValue() + '\n')
        init.write('Tracking Zoom: ' + self.trackZoomTxt.GetValue() + '\n')
        init.write('Init GUI: on')
        init.close()
        init = open(os.path.join(os.path.dirname(__file__),'init.par'), 'r').read().splitlines()
	##Calls validity check, which opens a frame if fields are entered improperly
        if self.validityCheck():
	    ##If it is valid and you are going to overwrite other output, it will allow you to back out
            if self.outputOverwriteCheck(self.outputTxt.GetValue()):
		##destroy oscaarFrame and run photometry script in separate thread to avoid freezing up the GUI
                self.Destroy()
                if not worker:
                    worker = WorkerThread()
    
    ##This function takes a field and paths separated by commas and writes the field name and the comma separated list of paths
    def addStarFits(self, init, field, path):
        pathList = []
        for impath in path.split(','):
            newpath = impath
            if os.path.isdir(impath) and not (impath.endswith(os.sep)):
                newpath += os.sep
            if newpath.endswith(os.sep):
                newpath += '*.fits'
            pathList += glob(newpath)
        initText = ''
        for i in range(0,len(pathList)):
            if i == len(pathList)-1:
                initText += pathList[i]
            else:
                initText += (pathList[i]+',')
        init.write(field + initText + '\n')
        return pathList
    
    ##Checks to make sure the user has entered valid parameters
    def validityCheck(self):
        darkFrames = self.darkFits
        imageFiles = self.imgFits
        regionsFile = self.regFits
        flatFrames = self.flatFits
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
        if not self.containsReg(regionsFile):
            if commaNeeded:
                invalidsString += ", "
            invalidsString += "Regions"
        try:
            float(self.smoothingConstTxt.GetValue())
            float(self.radiusTxt.GetValue())
            float(self.trackZoomTxt.GetValue())
            float(self.ccdGainTxt.GetValue())
        except ValueError:
            if commaNeeded:
                invalidsString += ", "
            invalidsString += "Value Error"
            commaNeeded = True
        if invalidsString == "":
            return True
        else:
            InvalidPath(invalidsString, None, -1)
            return False
    
    ##Checks to see if output is going to be overwritten. If so it returns false
    def outputOverwriteCheck(self, path):
        pathCorrected = path.replace('/', os.sep)
        outfolder = pathCorrected[:pathCorrected.rfind(os.sep)] + os.sep + '*'
        if pathCorrected + '.pkl' in glob(outfolder):
            OverWriteFrame(pathCorrected, self, -1)
            return False
        return True
                 
    ##Checks to see if an array contains any .fit or .fits files
    def containsFit(self, ary):
        for i in ary:
            if str(i).endswith('.fit') or str(i).endswith('.fits'):
                return True
        return False

    ##Checks to see if an array contains any .reg files
    def containsReg(self, ary):
        for i in ary:
            if str(i).endswith('.reg'):
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
                if inline[0] == 'Path to Dark Frames':  self.darkPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()).replace('/', os.sep))
                if inline[0] == 'Path to Master-Flat Frame':  self.flatPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()).replace('/',os.sep))
                if inline[0] == 'Path to data images':  self.imagPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()).replace('/', os.sep))
                if inline[0] == 'Path to regions file': self.regPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()).replace('/', os.sep))
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
		self.checkValid(None, 2, self.darkPathTxt.GetValue(), False)
		self.checkValid(None, 3, self.imagPathTxt.GetValue(), False)
		self.checkValid(None, 4, self.flatPathTxt.GetValue(), False)
		self.checkValid(None, 5, self.regPathTxt.GetValue(), True)



    #####Opens the webpage for transit time predictions from Czech Astronomical Society#####
    def predictions(self, event):
        webbrowser.open_new_tab("http://var2.astro.cz/ETD/predictions.php") ##Change to documentation

    def aboutOscaar(self, event):
        global aboutOpen
        if aboutOpen == False:
            AboutFrame(parent = self, id = -1)
            aboutOpen = True

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

class WarnFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
	super(WarnFrame, self).__init__(*args, **kwargs)
	self.SetTitle('Install PyEphem')
	self.SetSize((290,120))
        self.SetBackgroundColour(wx.Colour(227,227,227))
        self.warningText = wx.StaticText(parent = self, id = -1, label = 'You must install PyEphem to use this feature', pos = (15,7), style = wx.ALIGN_CENTER)
        self.okButton = wx.Button(parent = self, id = -1, label = 'Okay', pos = (100,50))
        self.okButton.Bind(wx.EVT_BUTTON, self.destroy)
        self.Centre()
        self.Show()
    def destroy(self, event):
	self.Destroy()

class MasterFlatFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MasterFlatFrame, self).__init__(*args, **kwargs)
        self.frameSizer = wx.GridBagSizer(7,7)
        
        ###Variable Declarations###
        pathCtrlSize = (325,25)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.destroyed)
        self.SetBackgroundColour(wx.Colour(227,227,227))
        self.flatImagesPathCtrl = wx.TextCtrl(self, size = pathCtrlSize)
        self.flatDarksPathCtrl = wx.TextCtrl(self, size = pathCtrlSize)
        self.masterFlatPathCtrl = wx.TextCtrl(self, size = pathCtrlSize)
        self.plotsRadioBox = wx.RadioBox(self,-1, "Plots", (10,10), wx.DefaultSize, ["On", "Off"], wx.RA_SPECIFY_COLS)
        self.flatRadioBox = wx.RadioBox(self,-1, "Flat Type", (10,10), wx.DefaultSize, ["Standard", "Twilight"], wx.RA_SPECIFY_COLS)
        self.flatBrowse = wx.Button(self, -1, 'Browse')
        self.darkBrowse = wx.Button(self, -1, 'Browse')
        self.masterPathBrowse = wx.Button(self, -1, 'Browse')
        self.title = wx.StaticText(self, -1, 'OSCAAR: Master Flat Maker')
        self.titleFont = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.title.SetFont(self.titleFont)
        self.runButton = wx.Button(self, -1, 'Run')
        self.runButton.Bind(wx.EVT_BUTTON, self.runMasterFlatMaker)

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

    def destroyed(self, event):
        global masterFlatOpen
        masterFlatOpen = False

    def addPathChoice(self, sizer, row, label, btn, textCtrl, message):
        sizer.Add(label, (row, 0), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        sizer.Add(textCtrl, (row, 1), (1,4), wx.TOP, 7)
        sizer.Add(btn, (row, 5), (1,1), wx.TOP, 7)
        btn.Bind(wx.EVT_BUTTON, lambda event: self.openDirDialog(event, message, textCtrl))

    def addButtonPair(self, row, colStart, button1, button2, label):
        label.SetFont(self.labelFont)
        self.frameSizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7) ##border of 8 pixels on the top and left
        self.frameSizer.Add(button1, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
        self.frameSizer.Add(button2, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)

    #####Button Press Event Functions#####
    def openDirDialog(self, event, message, textControl):
        dlg = wx.FileDialog(self, message = message, style = wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            filenames = dlg.GetPaths()
            textControl.Clear()
            for i in range(0,len(filenames)):
                if i != len(filenames)-1:
                    textControl.WriteText(filenames[i] + ',')
                else:
                    textControl.WriteText(filenames[i])
        dlg.Destroy()

    def runMasterFlatMaker(self, event):
        path = self.masterFlatPathCtrl.GetValue()
        self.flatpaths = []
        for impath in self.flatImagesPathCtrl.GetValue().split(','):
            self.flatpaths += glob(impath)
        self.flatdarkpaths = []
        for dpath in self.flatDarksPathCtrl.GetValue().split(','):
            self.flatdarkpaths += glob(dpath)
        if not path.endswith('.fits') and not path.endswith('.fit'):
            path += '.fits'
        pathCorrected = path.replace('/', os.sep)
        outfolder = pathCorrected[:pathCorrected.rfind(os.sep)] + os.sep + '*'
        self.standardFlat = (self.flatRadioBox.GetSelection() == 0)
        if pathCorrected in glob(outfolder):
            OverwFlatFrame(pathCorrected,self,-1)
        else:
            if self.standardFlat:
                oscaar.standardFlatMaker(self.flatpaths, self.flatdarkpaths, self.masterFlatPathCtrl.GetValue(), self.plotsRadioBox.GetSelection() == 0)
            else: 
                oscaar.twilightFlatMaker(self.flatpaths, self.flatdarkpaths, self.masterFlatPathCtrl.GetValue(), self.plotsRadioBox.GetSelection() == 0)
            self.Destroy()

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
        if self.parent.standardFlat:
#        if self.standardFlat.GetValue():
            oscaarx.standardFlatMaker(self.parent.flatpaths, self.parent.flatdarkpaths, self.parent.masterFlatPathCtrl.GetValue(), self.parent.plotsRadioBox.GetSelection() == 0)
        else: 
            oscaarx.twilightFlatMaker(self.parent.flatpaths, self.parent.flatdarkpaths, self.parent.masterFlatPathCtrl.GetValue(), self.parent.plotsRadioBox.GetSelection() == 0)

        self.parent.Destroy()
        
### "About" panel ###
class AboutFrame(wx.Frame):
    def __init__(self, parent, id):
        self.parent = parent
        wx.Frame.__init__(self, parent, id, 'About OSCAAR')
        if(sys.platform == 'darwin' or sys.platform == 'linux2'):
            self.SetSize((525, 525))
        else: self.SetSize((410,460))
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.SetBackgroundColour(wx.Colour(227,227,227))
        self.static_bitmap = wx.StaticBitmap(parent = self, pos = (0,0), style=wx.ALIGN_CENTER)
        self.logo = wx.Image(os.path.join(os.path.dirname(os.path.abspath(__file__)),'images/logo4noText.png'), wx.BITMAP_TYPE_ANY)
        self.bitmap = wx.BitmapFromImage(self.logo)
        self.static_bitmap.SetBitmap(self.bitmap)
        if(sys.platform == 'darwin' or sys.platform == 'linux2'):
            self.labelFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        else: self.labelFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)

        ### WARNING: Do not post your name here or remove someone elses without consulting Brett Morris.
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
        
        self.titleText = wx.StaticText(parent = self, id = -1, label = titleText, pos=(0,75),style = wx.ALIGN_CENTER)
        self.viewRepoButton = wx.Button(parent = self, id = -1, label = 'Open Code Repository (GitHub)')
        self.viewRepoButton.Bind(wx.EVT_BUTTON, self.openRepo)
        
        self.contribText = wx.StaticText(parent = self, id = -1, label = contribText,style = wx.ALIGN_CENTER)
        self.exitButton = wx.Button(parent = self, id = -1, label = 'Close')
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
    
    def onDestroy(self,event):
        global aboutOpen
        aboutOpen = False
    def exit(self,event):
        self.Destroy()
    def openRepo(self, event):
        webbrowser.open_new_tab("https://github.com/OSCAAR/OSCAAR")


#### Checks if the dark frames are valid ####

class InvalidPath(wx.Frame):
    def __init__(self, path, parent, id):
        wx.Frame.__init__(self, parent, id, 'Invalid Parameter')
        self.SetSize((350,100))
        self.SetBackgroundColour(wx.Colour(227,227,227))
        self.paths = wx.StaticText(self, -1, "The following is invalid: " + path)
        self.okButton = wx.Button(self, -1, 'Okay', pos = (125,30))
        self.okButton.Bind(wx.EVT_BUTTON, self.onOkay)
        self.Centre()
        self.Show()
        
    def onOkay(self, event):
        self.Destroy()

#### Launches worker processes ####
        
class WorkerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        diffPhotCall = "from oscaar import differentialPhotometry"
        subprocess.call(['python','-c',diffPhotCall])
class PlotThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        os.chdir(os.path.join(os.path.dirname(__file__)))
        execfile('plotPickle.py')
        
class EphFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(EphFrame, self).__init__(*args, **kwargs)
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
        newobs.write('start_date: ' + '(' + semdateArr[0] + ',' + semdateArr[1] + ',' + semdateArr[2] + ',0,0,0)\n')
        newobs.write('end_date: ' + '(' + enddateArr[0] + ',' + enddateArr[1] + ',' + enddateArr[2] + ',0,0,0)\n')
        newobs.write('v_limit: ' + self.v_limit.GetValue() + '\n')
        newobs.write('depth_limit: ' + self.depth_limit.GetValue() + '\n')
        newobs.write('calc_transits: ' + str(self.calc_transits.GetSelection()==0) + '\n')
        newobs.write('calc_eclipses: ' + str(self.calc_eclipses.GetSelection()==0) + '\n')
        newobs.write('html_out: ' + str(self.html_out.GetSelection()==0) + '\n')
        newobs.write('text_out: ' + str(self.text_out.GetSelection()==0) + '\n')
        newobs.write('twilight: ' + self.twilightType.GetValue() + '\n')
        newobs.close()
        
    def calculate(self, event):
        path = os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'extras','eph','observatories',self.filename.GetValue() + '.par')
        self.saveFile(str(path))
        namespace = {}
        execfile(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'extras','eph','calculateEphemerides.py'),namespace)
        globals().update(namespace)
        rootPath = str(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'extras','eph','ephOutputs'))
        calculateEphemerides(path,rootPath)
        outputPath = str(os.path.join(os.path.dirname(os.path.abspath(oscaar.__file__)),'extras','eph','ephOutputs','eventReport.html'))
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
        global ephGUIOpen
        ephGUIOpen = False

class BrowseBox(wx.Panel):
            
        def __init__(self, parent,id):
            wx.Panel.__init__(self,parent,id)
            
            box1 = wx.StaticBox(self, -1)
            sizer = wx.StaticBoxSizer(box1, wx.VERTICAL)

            sizer0 = wx.FlexGridSizer(rows=1, cols=3)
            sizer.Add(sizer0, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

            self.label = wx.StaticText(self, -1, "Path to Output File: ", style=wx.ALIGN_CENTER)
            sizer0.Add(self.label, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
            self.txtbox = wx.TextCtrl(self, -1, size=(500,20))
            sizer0.Add(self.txtbox, 0, wx.ALIGN_CENTRE|wx.ALL, 0)
            
            if sys.platform == 'win32':
                self.browseButton = wx.Button(self, -1, "Browse\t (Cntrl-B)")
            else:
                self.browseButton = wx.Button(self, -1, "Browse\t("+u'\u2318'"-B)")
            
            self.Bind(wx.EVT_BUTTON, lambda event:self.browseButtonEvent(event,"Choose Path to Output File",
                                                                         self.txtbox,True,wx.FD_OPEN))
            sizer0.Add(self.browseButton,0,wx.ALIGN_CENTRE|wx.ALL,0)
            
            self.SetSizer(sizer)
            sizer.Fit(self)

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

class LoadOldPklFrame(wx.Frame):

    def __init__(self):
        self.title = "Load An Old .pkl File"
        wx.Frame.__init__(self, None,-1, self.title)
        
        self.panel = wx.Panel(self)
        
        self.box = BrowseBox(self.panel,-1)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.box, border=5, flag=wx.ALL)

        self.plotLightCurveButton = wx.Button(self.panel,label = 'Plot Light Curve', size = (130,25)) 
        self.plotRawFluxButton = wx.Button(self.panel,label = 'Plot Raw Fluxes', size = (130,25))
        self.plotScaledFluxesButton = wx.Button(self.panel,label = 'Plot Scaled Fluxes', size = (130,25))
        
        if sys.platform == 'win32':
            self.plotCentroidPositionsButton = wx.Button(self.panel, label = 'Trace Stellar Centroid Positions', size = (170,25))
            self.plotComparisonStarWeightingsButton = wx.Button(self.panel,label = 'Plot Comparison\nStar Weightings', size = (110,37))   
            self.plotInteractiveLightCurveButton = wx.Button(self.panel,label = 'Plot Interactive Light Curve', size = (170,25))        
        else:
            self.plotCentroidPositionsButton = wx.Button(self.panel,-1,label = 'Trace Stellar\nCentroid Positions', size = (150,40))
            self.plotComparisonStarWeightingsButton = wx.Button(self.panel,-1,label = 'Plot Comparison\nStar Weightings', size = (150,40))
            self.plotInteractiveLightCurveButton = wx.Button(self.panel,-1,label = 'Plot Interactive Light Curve', size = (190,25))
        
        self.plotLSFitButton = wx.Button(self.panel,label="Least Squares Fit", size =(130,25))
        self.Bind(wx.EVT_BUTTON, self.plotLightCurve,self.plotLightCurveButton)
        self.Bind(wx.EVT_BUTTON, self.plotRawFlux, self.plotRawFluxButton)     
        self.Bind(wx.EVT_BUTTON, self.plotCentroidPosition, self.plotCentroidPositionsButton)
        self.Bind(wx.EVT_BUTTON, self.plotScaledFluxes,self.plotScaledFluxesButton)
        self.Bind(wx.EVT_BUTTON, self.plotComparisonStarWeightings, self.plotComparisonStarWeightingsButton)
        self.Bind(wx.EVT_BUTTON, self.plotInteractiveLightCurve, self.plotInteractiveLightCurveButton)    
        self.Bind(wx.EVT_BUTTON,self.plotLSFit, self.plotLSFitButton)
        
        self.sizer0 = wx.FlexGridSizer(rows=1, cols=7)
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)

        self.sizer0.Add(self.plotLightCurveButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotRawFluxButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotCentroidPositionsButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotScaledFluxesButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotComparisonStarWeightingsButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotInteractiveLightCurveButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.plotLSFitButton,0,wx.ALIGN_CENTER|wx.ALL,5)
         
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
        m_browse = menu_file.Append(-1,"Browse\tCtrl-B","Browse")
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
            commandstring = "import oscaar; data=oscaar.load('"+self.pklPathTxt.GetValue()+"'); data.plotLightCurve()"
            subprocess.Popen(['python','-c',commandstring])

    def plotRawFlux(self, event):
        if self.validityCheck():
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar; data=oscaar.load('"+self.pklPathTxt.GetValue()+"'); data.plotRawFluxes()"

            subprocess.Popen(['python','-c',commandstring])

    def plotScaledFluxes(self, event):
        if self.validityCheck():
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar; data=oscaar.load('"+self.pklPathTxt.GetValue()+"'); data.plotScaledFluxes()"

            subprocess.Popen(['python','-c',commandstring])
    
    def plotCentroidPosition(self, event):
        if self.validityCheck():
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar; data=oscaar.load('"+self.pklPathTxt.GetValue()+"'); data.plotCentroidsTrace()"

            subprocess.Popen(['python','-c',commandstring])

    def plotComparisonStarWeightings(self, event):
        if self.validityCheck():
            print 'Loading file: '+self.pklPathTxt.GetValue() 

            commandstring = "import oscaar; data=oscaar.load('"+self.pklPathTxt.GetValue()+"'); data.plotComparisonWeightings()"

            subprocess.Popen(['python','-c',commandstring])
    
    def plotInteractiveLightCurve(self, event):
        if self.validityCheck():
            global pathText
            pathText = self.pklPathTxt.GetValue()
            GraphFrame()

    def plotLSFit(self,event):
        if self.validityCheck():
            global pathText
            pathText = self.pklPathTxt.GetValue()
            LeastSquaresFitFrame()
            
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
        global loadOldPklOpen
        loadOldPklOpen = False
    
    def on_exit(self, event):
        self.Destroy()

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
        self.data = oscaar.load(self.pT)
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

class LeastSquaresFitFrame(wx.Frame):
    
    title = "Least Squares Fit"
    
    def __init__(self):
        
        wx.Frame.__init__(self, None,-1, self.title)
        
        self.panel = wx.Panel(self)
        
        self.pT = pathText
        self.data = oscaar.load(self.pT)
        
        self.box = ScanBox(self.panel,-1)
        self.hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox.Add(self.box, border=5, flag=wx.ALL)
        
        self.okButton = wx.Button(self.panel,label = 'Plot')
        self.Bind(wx.EVT_BUTTON,self.onOkPress, self.okButton)
        self.updateButton = wx.Button(self.panel,label = 'Update Parameters')
        self.Bind(wx.EVT_BUTTON, self.update, self.updateButton)

        self.sizer0 = wx.FlexGridSizer(rows=1, cols=10)
        
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.sizer0,0, wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.okButton,0,wx.ALIGN_CENTER|wx.ALL,5)
        self.sizer0.Add(self.updateButton,0,wx.ALIGN_CENTER|wx.ALL,5)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.hbox, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_CENTER | wx.TOP)
        
        self.box.userParams['t0'].SetValue(str(oscaar.transiterFit.calcMidTranTime(self.data.times,self.data.lightCurve)))
        
        self.vbox.AddSpacer(10)
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
        self.Center()
        self.Show()

    def onOkPress(self,event):

        if self.checkParams() == True:
            oscaar.transiterFit.run_LMfit(self.data.getTimes(),self.data.lightCurve, self.data.lightCurveError,
                                          float(self.box.GetRatio()),float(self.box.GetRatio2()),float(self.box.GetInc()),
                                          float(self.box.GetT0()),float(self.box.GetGamma1()),float(self.box.GetGamma2()),
                                          float(self.box.GetPeriod()),float(self.box.GetEcc()), float(self.box.GetPericenter()),
                                          fitLimbDark='quadratic', plotting=True)
    def checkParams(self):

        list = [(self.box.GetRatio(),"ratio"),(self.box.GetRatio2(),"ratio2"),(self.box.GetInc(),"inc"),
                (self.box.GetT0(),"t0"),(self.box.GetGamma1(),"gamma1"),(self.box.GetGamma2(),"gamma2"),
                (self.box.GetPeriod(),"per"),(self.box.GetEcc(),"ecc"),(self.box.GetPericenter(),"pericenter")]
        for (number,string) in list:
            if number == '':
                InvalidParameter(number, None,-1, str=string)
                return False
            else:
                try:
                    self.tmp = float(number)
                except ValueError:
                    InvalidParameter(number, None,-1, str=string)
                    return False
                if string == "ratio":
                    if float(number)>1 or float(number)<0:
                        InvalidParameter(number, None,-1, str=string)
                        return False
                if string == "ratio2":
                    if float(number) <= 1:
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
                if string == "per":
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
        self.totalGamma = float(self.box.GetGamma1()) + float(self.box.GetGamma2())
        self.totalString = str(self.totalGamma)
        if self.totalGamma > 1:
            InvalidParameter(self.totalString, None,-1, str="gamma")
            return False
        return True

    def update(self,event):
        if self.box.GetPlanet() == '':
            InvalidParameter(self.box.GetPlanet(), None,-1, str="planet")
        else:
            self.planet = self.box.GetPlanet()
            try:
                [ratio,ratio2,per,inc,ecc] = returnSystemParams.transiterParams(self.planet)
            except ValueError:
                InvalidParameter(self.box.GetPlanet(), None,-1, str="planet")
            
            self.box.userParams['ratio'].SetValue(str(ratio))
            self.box.userParams['ratio2'].SetValue(str(ratio2))
            self.box.userParams['per'].SetValue(str(per))
            self.box.userParams['inc'].SetValue(str(inc))
            self.box.userParams['ecc'].SetValue(str(ecc))
            InvalidParameter("",None,-1, str="params")

class ScanBox(wx.Panel):
        'create box for scan parameters'
        # Create a box with all the parameters that the users can manipulate.
        def __init__(self, parent,id):
            wx.Panel.__init__(self,parent,id)
            
            box1 = wx.StaticBox(self, -1, "Descriptive information")
            sizer = wx.StaticBoxSizer(box1, wx.VERTICAL)
            self.userParams = {}
            sizer0 = wx.FlexGridSizer(rows=1, cols=10)
            sizer.Add(sizer0, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
            
            for (widget,label,ToolTip) in [
                ('ratio',"Ratio of Radii (R_p/R_s):",
                 'Enter a ratio of the radii here.'),
                ('ratio2',"A over R_s:",
                 'Enter a value for A over R_s here.'),
                ('per',"Period:",
                 'Enter a value for the period here.'),
                ('inc',"Inclination:",
                 'Enter a value for the inclination here.'),
                ('ecc',"Eccentricity: ", 
                 'Enter a value for the eccentricity here.')
                ]:
                label = wx.StaticText(self, -1, label, style=wx.ALIGN_CENTER)
                sizer0.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
                self.userParams[widget] = wx.TextCtrl(self, -1)
                self.userParams[widget].SetToolTipString(ToolTip)
                sizer0.Add(self.userParams[widget], 0, wx.ALIGN_CENTRE|wx.ALL, 0)
 
            sizer0 = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(sizer0, 0, wx.ALIGN_CENTER|wx.ALL, 5)
            label = wx.StaticText(self, -1, "", style=wx.ALIGN_CENTER)
            sizer0.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
            for (widget,label,ToolTip) in [
                ('planet',"Planet Name:",
                 'Enter a planet name from the exoplanet.org database here.'),
                ('t0',"t0:",
                 'Enter a value for t0 here.'),
                ('gamma1',"Gamma 1:",
                 'Enter a value for gamma 1 here.'),
                ('gamma2'," Gamma 2:",
                 'Enter a value for gamma 2 here.'),
                ('pericenter',"Pericenter:",
                 'Enter an arguement for the pericenter here.'),
                ]:
                label = wx.StaticText(self, -1, label, style=wx.ALIGN_CENTER)
                sizer0.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 3)
                if widget == 'pericenter':
                    self.userParams[widget] = wx.TextCtrl(self, -1, size = (100,20), value='0.0')
                else:
                    self.userParams[widget] = wx.TextCtrl(self, -1, size=(100,20))
                self.userParams[widget].SetToolTipString(ToolTip)
                sizer0.Add(self.userParams[widget], 0, wx.ALIGN_CENTRE|wx.ALL, 0)
            
            self.SetSizer(sizer)
            sizer.Fit(self)
        def GetPlanet(self):
            return self.userParams['planet'].GetValue()
        def GetRatio(self):
            return self.userParams['ratio'].GetValue()
        def GetRatio2(self):
            return self.userParams['ratio2'].GetValue()
        def GetPeriod(self):
            return self.userParams['per'].GetValue()
        def GetInc(self):
            return self.userParams['inc'].GetValue()
        def GetEcc(self):
            return self.userParams['ecc'].GetValue()
        def GetT0(self):
            return self.userParams['t0'].GetValue()
        def GetGamma1(self):
            return self.userParams['gamma1'].GetValue()
        def GetGamma2(self):
            return self.userParams['gamma2'].GetValue()
        def GetPericenter(self):
            return self.userParams['pericenter'].GetValue()

class InvalidParameter(wx.Frame):

    def __init__(self, num, parent, id, str='', max='0'):

        if sys.platform == "win32":
            wx.Frame.__init__(self, parent, id, 'Invalid Parameter', size = (500,110))
        else:
            wx.Frame.__init__(self, parent, id, 'Invalid Parameter', size = (500,100))
            self.create_menu()
            self.Bind(wx.EVT_CHAR_HOOK, self.onCharOkay)        
        if str == "params":
            self.SetTitle("Updated Parameters")
            self.Bind(wx.EVT_CHAR_HOOK, self.onOkay)
        self.panel = wx.Panel(self)
        self.string = "Incorrect"

        if max != '0':
            self.string = "The bin size must be between 5 and "+max+"."
        if str == "ratio":
            self.string = "The value for Rp over Rs must be between 0 and 1."
        elif str == "ratio2":
            self.string = "The value for A over Rs must be greater than 1."
        elif str == "inc":
            self.string = "The value for the inclincation must be between 0 and 90."
        elif str == "t0":
            self.string = "The value for the mid-transit time, t0, must be greater than 0."
        elif str == "gamma" or str == "gamma1" or str == "gamma2":
            self.string = "The value for Gamma1 + Gamma2 must be less than or equal to 1."
        elif str == "per":
            self.string = "The value for the period must be greater than 0."
        elif str == "ecc":
            self.string = "The value for the eccentricity must be between 0 and 1."
        elif str == "pericenter":
            self.string = "The value for the pericenter must be greater than 0."
        elif str == "planet":
            self.string = "The name of the planet does not exist in the database."

        if str == "path":
            self.paths = wx.StaticText(self.panel, -1,"The following is an invalid output path: " + num)
        elif str == "params":
            self.paths = wx.StaticText(self.panel, -1,"The appropriate parameters have been updated.")
        else:           
            self.paths = wx.StaticText(self.panel, -1, self.string +"\nThe following is invalid: " + num)
        
        self.okButton = wx.Button(self.panel,label = 'Okay', pos = (125,30))
        self.Bind(wx.EVT_BUTTON, self.onOkay, self.okButton)

        self.sizer0 = wx.FlexGridSizer(rows=2, cols=2)        
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
        self.Destroy()

app = wx.App(False)
#### Runs the GUI ####
OscaarFrame(None)
app.MainLoop()
