import threading
import wx
import os
import sys
from wx.lib.masked import TimeCtrl
import calendar
from time import strftime
from time import strptime
import glob
from scipy import ndimage
import numpy as np
import math
import webbrowser
import time
import subprocess
execfile('oscmds.py')

APP_EXIT = 1

class OscaarFrame(wx.Frame): ##Defined a class extending wx.Frame for the GUI
    def __init__(self, *args, **kwargs):

        super(OscaarFrame, self).__init__(*args, **kwargs)
        self.InitUI()

    def InitUI(self): ##InitUI provides code for creating and showing all items in the interface
        ##Menu Bar:
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        menuExit = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application') ##provides a way to quit
        menubar.Append(fileMenu, '&File')
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.OnQuit, menuExit) ##Bind with OnQuit function, which closes the application
        self.menuDefaults = fileMenu.Append(-1, 'Set Defaults', 'Set Defaults')
        self.Bind(wx.EVT_MENU, self.setDefaults, self.menuDefaults)
        
        
        ##Control Buttons Var Declarations:
        self.sizer = wx.GridBagSizer(7, 3)
        
        self.static_bitmap = wx.StaticBitmap(parent = self, pos = (0,-10), size = (144, 72))
        self.logo = wx.Image('OscaarLogo.png', wx.BITMAP_TYPE_ANY)
        self.bitmap = wx.BitmapFromImage(self.logo)
        self.static_bitmap.SetBitmap(self.bitmap)

        
        self.radioTrackingOn = wx.RadioButton(self, label = "On", style = wx.RB_GROUP) ##On is always set to default, can be changed
        self.radioTrackingOff = wx.RadioButton(self, label = "Off")
        self.radioTrackPlotOn = wx.RadioButton(self, label = "On", style = wx.RB_GROUP)
        self.radioTrackPlotOff = wx.RadioButton(self, label = "Off")
        self.radioAperOn = wx.RadioButton(self, label = "On", style = wx.RB_GROUP)
        self.radioAperOff = wx.RadioButton(self, label = "Off")
        self.radialStarWidth = wx.TextCtrl(self, value = '0')
        self.radialStarWidth.SetMaxLength(6)
        self.darkPathTxt = wx.TextCtrl(self, size = (265,30))
        self.darkPathBtn = wx.Button(self, -1, 'Browse')
        self.flatPathTxt = wx.TextCtrl(self, size = (265,30))
        self.flatPathBtn = wx.Button(self, -1, 'Browse')
        self.imagPathTxt = wx.TextCtrl(self, size = (265, 30))
        self.imagPathBtn = wx.Button(self, -1, 'Browse')
        self.regPathTxt = wx.TextCtrl(self, size = (265, 30))
        self.regPathBtn = wx.Button(self, -1, 'Browse')
        self.smoothingConstTxt = wx.TextCtrl(self, value = '0')
        self.radiusTxt = wx.TextCtrl(self, value = '0')
        self.ccdSatTxt = wx.TextCtrl(self, value = '0')
        self.ccdGainTxt = wx.TextCtrl(self, value = '0')
        self.diffPhotomOn = wx.RadioButton(self, label = 'On', style = wx.RB_GROUP)
        self.diffPhotomOff = wx.RadioButton(self, label = 'Off')
        self.showPlotsOn = wx.RadioButton(self, label = 'On', style = wx.RB_GROUP)
        self.showPlotsOff = wx.RadioButton(self, label = 'Off')
        self.ingressDate = wx.DatePickerCtrl(self)
        self.ingressTime = TimeCtrl(self)
        self.egressDate = wx.DatePickerCtrl(self)
        self.egressTime = TimeCtrl(self)

        self.ds9Button = wx.Button(self, -1, 'Open DS9', size = (90, 30))

        ##Add items to sizer for organization
        self.createPathChoice(2, self.darkPathTxt, self.darkPathBtn, wx.StaticText(self, -1, 'Path to Dark Frames: '), 'Choose Path to Dark Frames')
        self.createPathChoice(3, self.flatPathTxt, self.flatPathBtn, wx.StaticText(self, -1, 'Path to Flat Frames: '), 'Choose Path to Flat Frames')
        self.createPathChoice(4, self.imagPathTxt, self.imagPathBtn, wx.StaticText(self, -1, 'Path to Data Images: '), 'Choose Path to Data Images')
        self.createPathChoice(5, self.regPathTxt, self.regPathBtn, wx.StaticText(self, -1, 'Path to Regions Img: '), 'Choose Path to Regions Img')
        self.createButtonPair(6, 2, self.radioTrackingOn, self.radioTrackingOff, wx.StaticText(self, -1, 'Star Tracking Algorithm: '))
        self.createButtonPair(7, 2, self.radioTrackPlotOn, self.radioTrackPlotOff, wx.StaticText(self, -1, 'Plot Gaussian Fits: '))
        self.createButtonPair(8, 2, self.radioAperOn, self.radioAperOff, wx.StaticText(self, -1, 'Aperture Photomentry: '))
        self.createButtonPair(9, 2, self.diffPhotomOn, self.diffPhotomOff, wx.StaticText(self, -1, 'Differential Photometry:'))
        self.createButtonPair(10, 2, self.showPlotsOn, self.showPlotsOff, wx.StaticText(self, -1, 'Show Plots: '))
        self.createTextCtrl(6,0, self.ccdSatTxt, wx.StaticText(self, -1, 'CCD Saturation: '))
        self.createTextCtrl(7,0, self.ccdGainTxt, wx.StaticText(self, -1, 'CCD Gain: '))
        self.createTextCtrl(8,0, self.radiusTxt, wx.StaticText(self, -1, 'Aperture Radius: '))
        self.createTextCtrl(9,0, self.radialStarWidth, wx.StaticText(self, -1, 'Radial star width: '))
        self.createTextCtrl(10,0, self.smoothingConstTxt, wx.StaticText(self, -1, 'Smoothing Constant: '))
        self.createDateCtrl(11,0, self.ingressDate, self.ingressTime, wx.StaticText(self, -1, 'Ingress: '))
        self.createDateCtrl(12,0, self.egressDate, self.egressTime, wx.StaticText(self, -1, 'Egress: '))
        self.sizer.Add(self.ds9Button, (5,4), wx.DefaultSpan, wx.TOP | wx.LEFT, 7)
        self.ds9Button.Bind(wx.EVT_BUTTON, self.openDS9)

        #Set Default Values
        init = open('init.par', 'r').read().splitlines()
        for i in range(0, len(init)):
            if len(init[i].split()) > 1 and init[i][0] != '#':
                inline = init[i].split(":")
                inline[0] = inline[0].strip()
                if inline[0] == 'Path to Dark Frames':  self.darkPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Path to Flat Frames':  self.flatPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Path to data images':  self.imagPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Path to regions file': self.regPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Star Tracking':    
                    if inline[1].split('#')[0].strip() == 'off': 
                        self.radioTrackingOn.SetValue(False)
                        self.radioTrackingOff.SetValue(True)
                if inline[0] == 'Aper':
                    if inline[1].split('#')[0].strip() == 'off': 
                        self.radioAperOn.SetValue(False)
                        self.radioAperOff.SetValue(True)
                if inline[0] == 'Radius':   self.radiusTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'CCD Saturation Limit':   self.ccdSatTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'CCD Gain':   self.ccdGainTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Show Plots':
                    if inline[1].split('#')[0].strip() == 'off': 
                        self.showPlotsOn.SetValue(False)
                        self.showPlotsOff.SetValue(True)
                if inline[0] == 'Perform Differential Photometry': 
                    if inline[1].split('#')[0].strip() == 'off': 
                        self.diffPhotomOn.SetValue(False)
                        self.diffPhotomOff.SetValue(True)
                if inline[0] == 'Trackplot':
                    if inline[1].split('#')[0].strip() == 'off': 
                        self.radioTrackPlotOn.SetValue(False)
                        self.radioTrackPlotOff.SetValue(True)
                if inline[0] == 'Smoothing Constant': self.smoothingConstTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Ingress': ingressUt = str(inline[1]) + ':' + str(inline[2]) + ':' + str(inline[3].split('#')[0].strip())
                if inline[0] == 'Egress': egressUt = str(inline[1]) + ':' + str(inline[2]) + ':' + str(inline[3].split('#')[0].strip()) ##inline is split at colon so these lines are a bit different
                if inline[0] == 'Init GUI': initGui = inline[1].split('#')[0].strip()

        self.run = wx.Button(self, -1, 'Run')
        self.help = wx.Button(self, -1, 'Help')
        self.sizer.Add(self.help, (12, 3), wx.DefaultSpan, wx.TOP, 7)
        self.sizer.Add(self.run, (12,4), wx.DefaultSpan, wx.TOP, 7)
        #self.run.SetDimensions(x = 

        self.help.Bind(wx.EVT_BUTTON, self.helpFunc)
        self.run.Bind(wx.EVT_BUTTON, self.runOscaar)

        self.sizer.SetDimension(5, 5, 550, 500)
        self.SetSizer(self.sizer)
        self.SetSize((660, 535))
        self.SetMinSize((660, 535))
        self.SetTitle('OSCAAR')
        self.Centre()
        self.Show(True)

    def OnQuit(self, e): ##defined for quitting using the file menu
        self.Close()

    def createButtonPair(self, row, colStart, button1, button2, label): ##defined for neater creation of control items
        self.sizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7) ##border of 8 pixels on the top and left
        self.sizer.Add(button1, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
        self.sizer.Add(button2, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)

    def createTextCtrl(self, row, colStart, textCtrl, label):
        self.sizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.sizer.Add(textCtrl, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
        textCtrl.SetForegroundColour(wx.Colour(180,180,180))
        textCtrl.Bind(wx.EVT_TEXT, lambda event: self.updateColor(textCtrl))

    def createPathChoice(self, row, textCtrl, button, label, message):
        self.sizer.Add(label, (row, 0), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.sizer.Add(textCtrl, (row, 1), (1,2), wx.TOP, 7)
        self.sizer.Add(button, (row, 3), (1,1), wx.TOP, 7)
        textCtrl.SetForegroundColour(wx.Colour(180,180,180))
        button.Bind(wx.EVT_BUTTON, lambda event: self.browseButtonEvent(event, message, textCtrl))
        textCtrl.Bind(wx.EVT_TEXT, lambda event: self.updateColor(textCtrl))

    def createDateCtrl(self, row, colStart, dateCtrl, timeCtrl, label):
        self.sizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.sizer.Add(dateCtrl, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
        self.sizer.Add(timeCtrl, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)

    def updateColor(event,ctrl):
        ctrl.SetForegroundColour(wx.Colour(0,0,0))

    ##Functions for event handling
    def browseButtonEvent(self, event, message, textControl):
        dlg = wx.DirDialog(self, message = message,  style = wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            textControl.Clear()
            textControl.WriteText(dlg.GetPath())
        dlg.Destroy()

    def openDS9(self, event):
        ds9Loc = os.getcwd() + '/ds9'
        cd()
        regionsName = os.getcwd() + '/tres1-020.fit'
        subprocess.Popen([ds9Loc, regionsName])

    def helpFunc(self, event):
        webbrowser.open_new_tab("http://www.astro.umd.edu/") ##Change to documentation

    def runOscaar(self, event):
        init = open('init.par', 'w')
        #Write to init.par
        init.write('Path to Dark Frames: ' + self.darkPathTxt.GetValue() + '\n')
        init.write('Path to data images: ' + self.imagPathTxt.GetValue() + '\n')
        init.write('Path to Flat Frames: ' + self.flatPathTxt.GetValue() + '\n')
        init.write('Path to regions file: ' + self.regPathTxt.GetValue() + '\n')
        self.checkRB(self.radioTrackingOn, 'Star Tracking: ', init)
        init.write('Radial Star Width: ' + self.radialStarWidth.GetValue() + '\n')
        self.checkRB(self.radioTrackPlotOn, 'Trackplot: ', init)
        init.write('Smoothing Constant: ' + self.smoothingConstTxt.GetValue() + '\n')
        self.checkRB(self.radioAperOn, 'Aper: ', init)
        init.write('CCD Saturation Limit: ' + self.ccdSatTxt.GetValue() + '\n')
        init.write('CCD Gain: ' + self.ccdGainTxt.GetValue() + '\n')
        init.write('Radius: ' + self.radiusTxt.GetValue() + '\n')
        self.checkRB(self.showPlotsOn, 'Show Plots: ', init)
        self.checkRB(self.diffPhotomOn, 'Perform Differential Photometry: ', init)
        self.checkRB(self.radioTrackingOn, 'Star Tracking: ', init)
        init.write('GUI: off\n')
        self.parseTime(self.ingressDate.GetValue(), self.ingressTime.GetValue(), 'Ingress: ',  init)
        self.parseTime(self.egressDate.GetValue(), self.egressTime.GetValue(), 'Egress: ', init)
        init.write('Init GUI: on')
        init.close()
        init = open('init.par', 'r').read().splitlines()
        for i in range(0, len(init)):
            if len(init[i].split()) > 1 and init[i][0] != '#':
                inline = init[i].split(":")
                inline[0] = inline[0].strip()
                if inline[0] == 'Path to Dark Frames': darkLoc = str(inline[1].split('#')[0].strip()) ##Everything after # on a line in init.par is ignored
                if inline[0] == 'Path to Flat Frames': flatLoc = str(inline[1].split('#')[0].strip())
                if inline[0] == 'Path to data images':  imagLoc = str(inline[1].split('#')[0].strip())
                if inline[0] == 'Path to regions file': regsLoc = str(inline[1].split('#')[0].strip())
                if inline[0] == 'Star Tracking':    track = inline[1].split('#')[0].strip()
                if inline[0] == 'Aper':  aper = inline[1].split('#')[0].strip()
                if inline[0] == 'Radius':   aprad = float(inline[1].split('#')[0].strip())
                if inline[0] == 'CCD Saturation Limit':   satur = float(inline[1].split('#')[0].strip())
                if inline[0] == 'CCD Gain':    Kccd = float(inline[1].split('#')[0].strip())
                if inline[0] == 'Show Plots': aperplot = inline[1].split('#')[0].strip()
                if inline[0] == 'Perform Differential Photometry':    diffonoff = inline[1].split('#')[0].strip()
                if inline[0] == 'GUI': gui = inline[1].split('#')[0].strip()
                if inline[0] == 'Trackplot': trackplot = inline[1].split('#')[0].strip()
                if inline[0] == 'Smoothing Constant': smoothConst = float(inline[1].split('#')[0].strip())
                if inline[0] == 'Ingress': ingressUt = str(inline[1]) + ':' + str(inline[2]) + ':' + str(inline[3].split('#')[0].strip())
                if inline[0] == 'Egress': egressUt = str(inline[1]) + ':' + str(inline[2]) + ':' + str(inline[3].split('#')[0].strip()) ##inline is split at colon so these lines are a bit different
                if inline[0] == 'Init GUI': initGui = inline[1].split('#')[0].strip()
        overwcheckDict = {'track_out':track, 'aper_out':aper, 'diff10': diffonoff, 'time_out': aper, 'diff_out':diffonoff}
        self.Destroy()
        guiOverwcheck(overwcheckDict)
       
    def checkRB(self, button, text, filename):
        if button.GetValue() == True:
            filename.write(text + 'on\n')
        else:
            filename.write(text + 'off\n')

    def parseTime(self, date, time, text, filename):
        fullTime = (str(date) +  ' ' + str(time)).split()
        d = dict((v,k) for k,v in enumerate(calendar.month_abbr))
        result = str(fullTime[3]) + '-' + str(d.get(fullTime[2])) + '-' + str(fullTime[1])   + ';'
        result += strftime('%H:%M:%S', strptime((fullTime[7]+fullTime[8]), '%I:%M:%S%p'))
        filename.write(text + result + '\n')

    def setDefaults(self, event):
        init = open('init.par', 'r').read().splitlines()
        for i in range(0, len(init)):
            if len(init[i].split()) > 1 and init[i][0] != '#':
                inline = init[i].split(":")
                inline[0] = inline[0].strip()
                if inline[0] == 'Path to Dark Frames':  self.darkPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Path to Flat Frames':  self.flatPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Path to data images':  self.imagPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Path to regions file': self.regPathTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Star Tracking':    
                    if inline[1].split('#')[0].strip() == 'off': 
                        self.radioTrackingOn.SetValue(False)
                        self.radioTrackingOff.SetValue(True)
                if inline[0] == 'Aper':
                    if inline[1].split('#')[0].strip() == 'off': 
                        self.radioAperOn.SetValue(False)
                        self.radioAperOff.SetValue(True)
                if inline[0] == 'Radius':   self.radiusTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'CCD Saturation Limit':   self.ccdSatTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'CCD Gain':   self.ccdGainTxt.ChangeValue(str(inline[1].split('#')[0].strip()))
                if inline[0] == 'Show Plots':
                    if inline[1].split('#')[0].strip() == 'off': 
                        self.showPlotsOn.SetValue(False)
                        self.showPlotsOff.SetValue(True)
                if inline[0] == 'Perform Differential Photometry': 
                    if inline[1].split('#')[0].strip() == 'off': 
                        self.diffPhotomOn.SetValue(False)
                        self.diffPhotomOff.SetValue(True)
                if inline[0] == 'Trackplot':
                    if inline[1].split('#')[0].strip() == 'off': 
                        self.radioTrackPlotOn.SetValue(False)
                        self.radioTrackPlotOff.SetValue(True)
                if inline[0] == 'Smoothing Constant': self.smoothingConstTxt.ChangeValue(str(inline[1].split('#')[0].strip()))

class Overwcheck(wx.Frame): #Defines and organizes the Overwrite checking window
    def __init__(self, fileDict, index,  *args, **kwargs):
        self.worker = None
        fileList = fileDict.keys()
        super(Overwcheck, self).__init__(*args, **kwargs)
        sizer = wx.GridBagSizer(4,4)
        sizer.Add(wx.StaticText(self, -1, 'Would you like to overwrite ' + fileList[index] + '?'), (0,2), (1,4), wx.TOP, 13)
        yesButton = wx.Button(self, -1, 'Yes')
        self.Bind(wx.EVT_BUTTON, lambda event: self.yesCheck(event, fileDict, index), yesButton)
        sizer.Add(yesButton, (2,2))
        noButton = wx.Button(self, -1, 'No')
        self.Bind(wx.EVT_BUTTON, lambda event: self.noCheck(event, fileDict, index), noButton)
        sizer.Add(noButton, (2,4))
        self.SetSizer(sizer)
        self.Centre()
        self.SetSize((305, 100))
        self.Show(True)

    def yesCheck(self, event, fileDict, filenum):
        global worker
        worker = None
        fileList = fileDict.keys()
        os.system('rm -r ' +  fileList[filenum])
        self.Close()
        files = glob.glob('*')
        index = filenum + 1
        if index < len(fileList):
            while (fileList[index] not in files or fileDict.get(fileList[index]) != 'on') and index < len(fileList)-1:
                index = index + 1
            Overwcheck(parent = None, fileDict = fileDict, index = index)
        else:
            results = ResultsFrame(None, -1)
            global doneThread
            doneThread = None
            if not worker:
                worker = WorkerThread()
                #while not doneThread:
                #    time.sleep(1)
                worker.join()
                results.Close()
                GraphFrame(None)
                

    def noCheck(self, event, fileDict, filenum):
        fileList = fileDict.keys()
        index = filenum + 1
        self.Destroy()
        while (filesList[index] not in files or fileDict.get(fileList[index]) != 'on') and index < len(fileList)-1:
            index = index + 1
        if index < len(fileList):
            Overwcheck(parent = None, fileDict = fileDict, index = index)
        else:
            #ResultsFrame(None, -1)
            if not worker:
                worker = WorkerThread()
                worker.join()
                GraphFrame(None)

    def validityCheck(self, event):
        var = False
        ##Implement to make sure fields are filled out in a valid manner

    

class ResultsFrame(wx.Frame):
    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, 'Oscaar')
        self.loading = wx.StaticText(self, -1, 'Oscaar is currently running, please wait...')
        self.loading.Centre()

        self.SetSize((825,625))
        self.Centre()
        self.Show(True)
        
class WorkerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        execfile('photom16irSimplified.py')
        wx.CallAfter(doneThreading)

def doneThreading():
    print "done threading"
    doneThread = True

class GraphFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(GraphFrame, self).__init__(*args, **kwargs)
        self.graphIndex = 0
        self.graphList = ['plots/jdRNF.png', 'plots/goodnessOfFit.png', 'plots/lightCurve.png']
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
        self.Centre()
        self.SetSize((850, 625))
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
        

def createGraphFrame():
    GraphFrame(None)

def guiOverwcheck(fileDict):
    filesOverwritten = fileDict.keys()
    files = glob.glob('*')
    index = 0
    worker = None
    while (filesOverwritten[index] not in files or fileDict.get(filesOverwritten[index]) != 'on') and index < len(filesOverwritten)-1:
        index = index + 1
    if index < len(filesOverwritten) - 1:
        Overwcheck(parent = None, fileDict = fileDict, index = index)
    else:
        #ResultsFrame(None, -1)
        if not worker:
            worker = WorkerThread()
            worker.join()
            GraphFrame(None)

app = wx.App(False)
OscaarFrame(None) ##Run the GUI
app.MainLoop()



