import wx
import sys
from glob import glob
import os

class EphFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(EphFrame, self).__init__(*args, **kwargs)
        self.initUI()
    
    def initUI(self):
        if(sys.platform == 'darwin' or sys.platform == 'linux2'):
            self.labelFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        else: self.labelFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.titleFont = wx.Font(17, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.SetTitle('Ephemerides')
        self.ctrlList = []
        self.ephSizer = wx.GridBagSizer(5,5)
        obsList = glob('observatories'+os.sep+'*')
        nameList = []
        for i in obsList:
            nameList.insert(0,i[i.rfind(os.sep)+1:i.rfind('.')])
        nameList += ['Enter New Observatory']
        self.observatory = wx.ComboBox(self, value = 'Observatories', choices = nameList, name = 'Observatories', size = (205,25))
        self.observatory.Bind(wx.EVT_COMBOBOX, self.enterNewObs)
        self.title = wx.StaticText(self, -1, 'Ephemerides Calculator')
        self.title.SetFont(self.titleFont)
        self.startSemTime = wx.TextCtrl(self, value = '00:00:00')
        self.endSemDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
        self.endSemTime = wx.TextCtrl(self, value = '00:00:00')
        self.latitude = wx.TextCtrl(self, value = 'deg:min:sec')
        self.elevation = wx.TextCtrl(self, value = '0.0')
        self.temp = wx.TextCtrl(self, value = '0.0')
        self.v_limit = wx.TextCtrl(self, value = '0.0')
        self.depth_limit = wx.TextCtrl(self, value = '0.0')
        self.selectObsLbl = wx.StaticText(self, -1, 'Select Observatory: ')
        self.selectObsLbl.SetFont(self.labelFont)
        self.html_out = wx.RadioBox(self, -1, label = 'Html Out', choices = ['True', 'False'])
        self.text_out = wx.RadioBox(self, -1, label = 'Text Out', choices = ['True', 'False'])
        self.calc_eclipses = wx.RadioBox(self, -1, label = 'Calc Eclipses', choices = ['True', 'False'])
        self.twilightType = wx.TextCtrl(self,-1, value = '0')
        self.calcButton = wx.Button(self,-1,'Calculate')
        
        self.ephSizer.Add(self.title, (0,0), (1,2), wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(self.selectObsLbl, (1,0), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(self.observatory, (1,1), (1,2), wx.TOP, 7)
        self.startSemDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
            
        self.addDateCtrl(2,0, self.startSemDate, self.startSemTime,wx.StaticText(self, -1, "Beginning of Obs, UT (YYYY/MM/DD): "))
        self.addDateCtrl(3,0, self.endSemDate, self.endSemTime,wx.StaticText(self, -1, "End of Obs, UT (YYYY/MM/DD): "))
        self.addTextCtrl(4,0, self.latitude, wx.StaticText(self, -1, 'Lattitude (deg:min:sec):'))
        self.addTextCtrl(5,0, self.elevation, wx.StaticText(self, -1, 'Observatory Elevation: '))
        self.addTextCtrl(6,0, self.temp, wx.StaticText(self, -1, 'Temperature (Celcius): '))
        self.addTextCtrl(7,0, self.v_limit, wx.StaticText(self,-1, 'v_limit: '))
        self.addTextCtrl(8,0, self.depth_limit, wx.StaticText(self,-1,'Depth Limit: '))
        self.addTextCtrl(9,0, self.twilightType, wx.StaticText(self,-1, 'Twilight Type: '))
        self.addRadioBox(10,0, self.html_out)
        self.addRadioBox(10,1, self.text_out)
        self.addRadioBox(10,2, self.calc_eclipses)
        self.addButton(10,3, self.calcButton)
        
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
        
    def addTextCtrl(self, row, colStart, textCtrl, label):
        label.SetFont(self.labelFont)
        self.ephSizer.Add(label, (row, colStart), (1,2), wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(textCtrl, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)
        
    def addButton(self, row, colStart, button):
        self.ephSizer.Add(button, (row, colStart+2), wx.DefaultSpan, wx.TOP, 30)
        
    def addRadioBox(self, row, colStart, radioBox):
        self.ephSizer.Add(radioBox, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        
    def enterNewObs(self, event):
        if self.observatory.GetValue() == 'Enter New Observatory':
            pass
        else:
            obsPath = os.getcwd() + os.sep + 'observatories' + os.sep + self.observatory.GetValue() + '.par'
            self.loadValues(obsPath)
    def loadValues(self, obsPath):
        obsPath = file(obsPath, 'r')
        for line in obsPath:
            if line.split(':',1) > 1 and line[0] != '#':
                line = line.split(':',1)
                if line[0] == 'name':  str(line[1].split('#')[0].strip())
                elif line[0] == 'latitude':  self.latitude.SetValue(str(line[1].split('#')[0].strip()))
                #elif inline[0] == 'longitude':  self.egress = ut2jd(str(inline[1].split('#')[0].strip()))
                #elif inline[0] == 'elevation':   self.apertureRadius = float(inline[1].split('#')[0].strip())
                ##elif inline[0] == 'temperature':   self.trackingZoom = float(inline[1].split('#')[0].strip())
                #elif inline[0] == 'min_horizon':    self.ccdGain = float(inline[1].split('#')[0].strip())
                #elif inline[0] == 'start_date': self.gui = inline[1].split('#')[0].strip()
                #elif inline[0] == 'end_date': self.trackPlots = True if inline[1].split('#')[0].strip() == 'on' else False
                #elif inline[0] == 'v_limit': self.photPlots = True if inline[1].split('#')[0].strip() == 'on' else False
                #elif inline[0] == 'depth_limit': self.smoothConst = float(inline[1].split('#')[0].strip())
                #elif inline[0] == 'calc_eclipses': self.initGui = inline[1].split('#')[0].strip()
                #elif inline[0] == 'html_out': self.outputPath = inline[1].split('#')[0].strip()
               # elif inline[0] == 'text_out': self.outputPath = inline[1].split('#')[0].strip()
                #elif inline[0] == 'twilight': self.outputPath = inline[1].split('#')[0].strip()

app = wx.App(False)
#### Runs the GUI ####
EphFrame(None)
app.MainLoop()
        