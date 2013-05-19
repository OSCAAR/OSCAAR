import threading
import wx
import os
import sys
from glob import glob
from time import strftime
import webbrowser
import subprocess
from os.path import expanduser

def homeDir():
    '''Look for the `.homeDir file` in the current directory. If it is in
       in the current working directory, do nothing. Otherwise, go up a 
       level through parent directories until the `.homeDir` file is in the
       current working directory. If it is never reached, go back 
       to the original current working directory and prompt the user. '''
    originalDirectory = os.getcwd()
    userHomeDirectory = expanduser("~")    
    ## This is the user's home directory. Assume that they will not put the oscaar
    ## working directory at any levels higher than this.
    
    while len(glob('./.homeDir'))  == 0 and len(os.getcwd()) > len(userHomeDirectory):
        os.chdir(os.pardir)
    if len(os.getcwd()) == len(userHomeDirectory):
        print '\n******************************************************************\n'+\
                'WARNING: oscaar.homeDir() has walked backward through to your user  \n'+\
                'home directory and has not found the top-level directory for OSCAAR. \n'+\
                'The current working directory will now be changed back to the \n'+\
                'current working directory before oscaar.homeDir() was called. \n'+\
                'This error can be caused by deleting the OSCAAR/.homeDir file, \n'+\
                'which indicates the top-level oscaar directory. It is permissible\n'+\
                'to change the name of the OSCAAR directory as long as .homeDir is\n'+\
                'still located in that directory.\n'+\
                '******************************************************************\n'
        os.chdir(originalDirectory)


#os.chdir(os.path.join(os.path.dirname(__file__),'code'))
#if os.getcwd() not in sys.path:
#    sys.path.insert(0, os.getcwd())
import oscaar.code.oscaar as oscaarx

APP_EXIT = 1

class OscaarFrame(wx.Frame): ##Defined a class extending wx.Frame for the GUI
    def __init__(self, *args, **kwargs):
        super(OscaarFrame, self).__init__(*args, **kwargs)
        self.InitUI()

    #### Creates and initializes the GUI ####
    def InitUI(self):
        #### Defines the menubar ####
        global masterFlatOpen
        global ephGUIOpen
        global aboutOpen
        masterFlatOpen = False
        ephGUIOpen = False
        aboutOpen = False
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
        self.logo = wx.Image(os.path.join(os.path.dirname(__file__),'code/oscaar/images/logo4.png'), wx.BITMAP_TYPE_ANY)
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
        self.ephButton = wx.Button(self,-1, 'Ephemeris')
        self.notesField = wx.TextCtrl(self, value = 'Enter notes to be saved here', size = (220, 48), style = wx.TE_MULTILINE)
        self.notesLabel = wx.StaticText(self, label = 'Notes')
        self.notesLabel.SetFont(self.labelFont)
        self.outPathBtn = wx.Button(self, -1, 'Browse')
        self.outputTxt = wx.TextCtrl(self, value = 'outputs', size = textCtrlSize)
    
        ##### Add items to sizer for organization #####
        self.addPathChoice(2, self.darkPathTxt, self.darkPathBtn, wx.StaticText(self, -1, 'Path to Dark Frames: '), 'Choose Path to Dark Frames', False, None)
        self.addPathChoice(3, self.flatPathTxt, self.flatPathBtn, wx.StaticText(self, -1, 'Path to Master Flat: '), 'Choose Path to Flat Frames', True, wx.FD_OPEN)
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
        self.sizer.Add(self.ephButton, (12,3),wx.DefaultSpan,wx.ALIGN_CENTER, 7)
        self.ephButton.Bind(wx.EVT_BUTTON, self.openEphGUI)
        self.sizer.Add(self.ds9Button,(12,5), wx.DefaultSpan, wx.ALIGN_CENTER, 7)
        self.ds9Button.Bind(wx.EVT_BUTTON, self.openDS9)
        self.sizer.Add(self.masterFlatButton, (12,4), wx.DefaultSpan, wx.ALIGN_CENTER, 7)
        self.masterFlatButton.Bind(wx.EVT_BUTTON, self.openMasterFlatGUI)
        self.sizer.Add(self.notesField, (11, 1), (2,2), wx.ALIGN_CENTER, 7)
        self.sizer.Add(self.notesLabel, (11, 0 ), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.setDefaults(None, os.path.join(os.path.dirname(__file__),'code/init.par'))

        # Code to make Run button default for main window
        self.run = wx.Button(self, -1, 'Run')
        #setDefault(self.run)
        #self.run.SetFocus()
        
        self.sizer.Add(self.run, (12,6), wx.DefaultSpan, wx.ALIGN_CENTER, 7)
        self.run.Bind(wx.EVT_BUTTON, self.runOscaar)
        self.sizer.SetDimension(5, 5, 550, 500)
        self.SetSizer(self.sizer)
        self.bestSize = self.GetBestSizeTuple()
        setSize = (self.bestSize[0]+20,self.bestSize[1]+20) ##Not sure if this looks okay on os x and linux.
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
        ds9 = os.path.join(os.path.dirname(__file__),'extras/ds9')
        ds9Loc = ds9 + '/' + sys.platform + '/ds9'
        regionsName =  ds9 + '/testFits.fit'  ##if it is beneficial, we could use glob to get the users actual image here
        subprocess.Popen([ds9Loc, regionsName])
        
    def openMasterFlatGUI(self, event):
        global masterFlatOpen
        if masterFlatOpen == False:
            masterFlatOpen = True
            MasterFlatFrame(None)
        
    def openEphGUI(self,event):
        global ephGUIOpen
        if ephGUIOpen == False:
            ephGUIOpen = True
            EphFrame(None)
            

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
        os.chdir(os.path.join(os.path.dirname(__file__),'code'))
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
        if not self.containsFit(flatFrames) and self.flatFits!='None':
            if commaNeeded:
                invalidsString += ", "
            invalidsString += "Flat Frames"
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
        global aboutOpen
        if aboutOpen == False:
            AboutFrame(parent = None, id = -1)
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
                oscaarx.standardFlatMaker(self.flatpaths, self.flatdarkpaths, self.masterFlatPathCtrl.GetValue(), self.plotsRadioBox.GetSelection() == 0)
            else: 
                oscaarx.twilightFlatMaker(self.flatpaths, self.flatdarkpaths, self.masterFlatPathCtrl.GetValue(), self.plotsRadioBox.GetSelection() == 0)
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
        wx.Frame.__init__(self, parent, id, 'About oscaar')
        if(sys.platform == 'darwin' or sys.platform == 'linux2'):
            self.SetSize((525, 440))
        else: self.SetSize((460,440))
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        self.SetBackgroundColour(wx.Colour(227,227,227))
        self.static_bitmap = wx.StaticBitmap(parent = self, pos = (0,0), style=wx.ALIGN_CENTER)
        homeDir()
        self.logo = wx.Image(os.getcwd()+'/code/oscaar/images/logo4noText.png', wx.BITMAP_TYPE_ANY)
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
                     'Luuk Visser (Leiden University/TU Delft)'])
        
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
        homeDir()
        os.chdir(os.path.join(os.path.dirname(__file__),'code'))
        execfile('differentialPhotometry.py')

class PlotThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        homeDir()
        os.chdir(os.path.join(os.path.dirname(__file__),'code'))
        execfile('plotPickle.py')
        
class EphFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(EphFrame, self).__init__(*args, **kwargs)
        self.initUI()
    
    def initUI(self):
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDestroy)
        if(sys.platform == 'darwin' or sys.platform == 'linux2'):
            self.labelFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        else: self.labelFont = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.titleFont = wx.Font(17, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.SetTitle('Ephemerides')
        self.ctrlList = []
        self.ephSizer = wx.GridBagSizer(5,5)
        homeDir()
        obsList = glob(os.path.join(os.path.dirname(__file__),'extras') + os.sep + 'eph' + os.sep + 'observatories'+os.sep+'*')
        nameList = []
        #for i in obsList:
        #    nameList.insert(0,i[i.rfind(os.sep)+1:i.rfind('.')])
        for file in obsList:        ## Gather all available observatory names
            openfile = open(file,'r').read().splitlines()
            for line in openfile: 
                if line.split(':')[0] == 'name':
                    nameList.append(line.split(':')[1].strip())
        nameList += ['Enter New Observatory']
        self.observatory = wx.ComboBox(self, value = 'Observatories', choices = nameList, name = 'Observatories', size = (235,25))
        self.observatory.Bind(wx.EVT_COMBOBOX, self.enterNewObs)
        self.title = wx.StaticText(self, -1, 'Ephemerides Calculator')
        self.title.SetFont(self.titleFont)
        self.name = wx.TextCtrl(self, value = 'Name', size = (205,25))
        self.filename = wx.TextCtrl(self, value = 'Filename', size = (205,25))
        self.startSemTime = wx.TextCtrl(self, value = '00:00:00')
        self.endSemDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
        self.endSemTime = wx.TextCtrl(self, value = '00:00:00')
        self.latitude = wx.TextCtrl(self, value = 'deg:min:sec')
        self.longitude = wx.TextCtrl(self, value = 'deg:min:sec')
        self.elevation = wx.TextCtrl(self, value = '0.0')
        self.temp = wx.TextCtrl(self, value = '0.0')
        self.v_limit = wx.TextCtrl(self, value = '0.0')
        self.depth_limit = wx.TextCtrl(self, value = '0.0')
        self.selectObsLbl = wx.StaticText(self, -1, 'Select Observatory: ')
        self.selectObsLbl.SetFont(self.labelFont)
        self.html_out = wx.RadioBox(self, -1, label = 'Html Out', choices = ['True', 'False'])
        self.text_out = wx.RadioBox(self, -1, label = 'Text Out', choices = ['True', 'False'])
        self.calc_transits = wx.RadioBox(self, -1, label = 'Calc Transits', choices = ['True', 'False'])
        self.calc_eclipses = wx.RadioBox(self, -1, label = 'Calc Eclipses', choices = ['True', 'False'])
        self.twilightType = wx.TextCtrl(self,-1, value = '0')
        self.min_horizon = wx.TextCtrl(self,-1,value = 'deg:min:sec')
        self.calcButton = wx.Button(self,-1,label = 'Calculate', size = (110,25))
        self.startSemDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
        
        self.ephSizer.Add(self.title, (0,0), (1,2), wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(self.selectObsLbl, (1,0), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(self.observatory, (1,1), (1,2), wx.TOP | wx.LEFT, 7)
        
        self.addTextCtrl(2,0, self.name, wx.StaticText(self,-1,'Name of Observatory: '), (1,2))
        self.addTextCtrl(3,0, self.filename, wx.StaticText(self,-1,'Enter File Name: '), (1,2))
        self.addDateCtrl(4,0, self.startSemDate, self.startSemTime,wx.StaticText(self, -1, "Beginning of Obs, UT (YYYY/MM/DD): "))
        self.addDateCtrl(5,0, self.endSemDate, self.endSemTime,wx.StaticText(self, -1, "End of Obs, UT (YYYY/MM/DD): "))
        self.addTextCtrl(6,0, self.latitude, wx.StaticText(self, -1, 'Lattitude (deg:min:sec):'), wx.DefaultSpan)
        self.addTextCtrl(7,0, self.longitude, wx.StaticText(self, -1, 'Longitude (deg:min:sec):'), wx.DefaultSpan)
        self.addTextCtrl(8,0, self.elevation, wx.StaticText(self, -1, 'Observatory Elevation: '), wx.DefaultSpan)
        self.addTextCtrl(9,0, self.temp, wx.StaticText(self, -1, 'Temperature (Celcius): '), wx.DefaultSpan)
        self.addTextCtrl(10,0, self.v_limit, wx.StaticText(self,-1, 'v_limit: '), wx.DefaultSpan)
        self.addTextCtrl(11,0, self.depth_limit, wx.StaticText(self,-1,'Depth Limit: '), wx.DefaultSpan)
        self.addTextCtrl(12,0, self.twilightType, wx.StaticText(self,-1, 'Twilight Type: '), wx.DefaultSpan)
        self.addTextCtrl(13,0, self.min_horizon, wx.StaticText(self,-1, 'Minimum Horizon: '), wx.DefaultSpan)
        self.addRadioBox(6,3, self.html_out)
        self.addRadioBox(8,3, self.text_out)
        self.addRadioBox(10,3, self.calc_transits)
        self.addRadioBox(12,3, self.calc_eclipses)

        self.addButton(1,1, self.calcButton)
        self.Bind(wx.EVT_BUTTON, self.calculate)
        
        self.bestSize = self.GetBestSizeTuple()
        self.SetSize((self.bestSize[0]+20,self.bestSize[1]+20))

        self.SetBackgroundColour(wx.Colour(233,233,233))
        self.SetSizer(self.ephSizer)
        self.bestSize = self.GetBestSizeTuple()
        self.SetSize((self.bestSize[0]+20,self.bestSize[1]+20))
        self.Centre()
        self.Show()
        
    def addDateCtrl(self, row, colStart, dateCtrl, timeCtrl, label):
        label.SetFont(self.labelFont)
        self.ephSizer.Add(label, (row, colStart), (1,2), wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(dateCtrl, (row, colStart+2), wx.DefaultSpan, wx.TOP , 7)
        self.ephSizer.Add(timeCtrl, (row, colStart+3), wx.DefaultSpan, wx.TOP, 7)
        
    def addTextCtrl(self, row, colStart, textCtrl, label, span):
        label.SetFont(self.labelFont)
        self.ephSizer.Add(label, (row, colStart), (1,2), wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(textCtrl, (row, colStart+2), span, wx.TOP, 7)
        
    def addButton(self, row, colStart, button):
        self.ephSizer.Add(button, (row, colStart+2), wx.DefaultSpan, wx.TOP | wx.RIGHT, 7)
        
    def addRadioBox(self, row, colStart, radioBox):
        self.ephSizer.Add(radioBox, (row, colStart), (2,1), wx.LEFT | wx.TOP, 20)
        
    def enterNewObs(self, event):
        if self.observatory.GetValue() == 'Enter New Observatory':
            self.filename.SetValue('Enter Filename for Observatory')
            self.name.SetValue('Enter Name of Observatory')
        else:
            homeDir()
            '''This is a hack so as to display the observatory names in the drop down menu but to
               open files using the glob() retrieved paths. It could be cleaned up. -BM'''
            obsList = glob(os.path.join(os.path.dirname(__file__),'extras') + os.sep + 'eph' + os.sep + 'observatories'+os.sep+'*')
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
            obsPath = os.getcwd() +os.sep+ openFile
            self.loadValues(obsPath)
    def loadValues(self, obsPath):
        obsFilename = obsPath[obsPath.rfind(os.sep)+1:obsPath.rfind('.')]
        self.filename.SetValue(obsFilename)
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
                elif line[0] == 'start_date':
                    if line[1].split('#')[0].strip() != '':
                        dateArr = line[1].split('#')[0].strip().split('(')[1].split(')')[0].split(',')
                        self.startSemDate.SetValue(dateArr[0]+'/'+dateArr[1]+'/'+dateArr[2])
                        if len(dateArr) > 3:
                            self.startSemTime.SetValue(dateArr[3]+':'+dateArr[4]+':'+dateArr[5])
                elif line[0] == 'end_date':
                    if line[1].split('#')[0].strip() != '':
                        dateArr = line[1].split('#')[0].strip().split('(')[1].split(')')[0].split(',')
                        self.endSemDate.SetValue(dateArr[0]+'/'+dateArr[1]+'/'+dateArr[2])
                        if len(dateArr) > 3:
                            self.endSemTime.SetValue(dateArr[3]+':'+dateArr[4]+':'+dateArr[5])
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
        semtimeArr = self.startSemTime.GetValue().split(':')
        enddateArr = self.endSemDate.GetValue().split('/')
        endtimeArr = self.endSemTime.GetValue().split(':')
        newobs = open(filename, 'w')
        newobs.write('name: ' + self.name.GetValue() + '\n')
        newobs.write('latitude: ' + self.latitude.GetValue() + '\n')
        newobs.write('longitude: ' + self.longitude.GetValue() + '\n')
        newobs.write('elevation: ' + self.elevation.GetValue() + '\n')
        newobs.write('temperature: ' + self.temp.GetValue() + '\n')
        newobs.write('min_horizon: ' + self.min_horizon.GetValue() + '\n')
        newobs.write('start_date: ' + '(' + semdateArr[0] + ',' + semdateArr[1] + ',' + semdateArr[2] + ',' + semtimeArr[0] + ',' + semtimeArr[1] + ',' + semtimeArr[2] + ')' + '\n')
        newobs.write('end_date: ' + '(' + enddateArr[0] + ',' + enddateArr[1] + ',' + enddateArr[2] + ',' + endtimeArr[0] + ',' + endtimeArr[1] + ',' + endtimeArr[2] + ')' + '\n')
        newobs.write('v_limit: ' + self.v_limit.GetValue() + '\n')
        newobs.write('depth_limit: ' + self.depth_limit.GetValue() + '\n')
        newobs.write('calc_transits: ' + str(self.calc_transits.GetSelection()==0) + '\n')
        newobs.write('calc_eclipses: ' + str(self.calc_eclipses.GetSelection()==0) + '\n')
        newobs.write('html_out: ' + str(self.html_out.GetSelection()==0) + '\n')
        newobs.write('text_out: ' + str(self.text_out.GetSelection()==0) + '\n')
        newobs.write('twilight: ' + self.twilightType.GetValue() + '\n')
        newobs.close()
        
    def calculate(self, event):
        path = str(os.path.join(os.path.dirname(__file__),'extras') + os.sep + 'eph' + os.sep + 'observatories' +os.sep+ self.filename.GetValue() + '.par')
        self.saveFile(str(path))
        namespace = {}
        execfile(os.path.join(os.path.dirname(__file__),'extras') + os.sep + 'eph' + os.sep + 'calculateEphemerides.py',namespace)
        globals().update(namespace)
        rootPath = str(os.path.join(os.path.dirname(__file__),'extras') + os.sep + 'eph' + os.sep)
        calculateEphemerides(path,rootPath)
        outputPath = str(os.path.join(os.path.dirname(__file__),'extras') + os.sep + 'eph' + os.sep + 'eventReport.html')
        if self.html_out.GetSelection() == 0: webbrowser.open_new_tab("file:"+2*os.sep+outputPath)
        self.Destroy()
        
    def onDestroy(self, event):
        global ephGUIOpen
        ephGUIOpen = False

app = wx.App(False)
#### Runs the GUI ####
OscaarFrame(None)
app.MainLoop()
