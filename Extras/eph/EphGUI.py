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
        else: self.labelFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.titleFont = wx.Font(17, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        
        self.SetTitle('Ephemerides')
        self.ctrlList = []
        self.ephSizer = wx.GridBagSizer(7,7)
        obsList = glob('observatories'+os.sep+'\*')
        nameList = []
        for i in obsList:
            nameList.insert(0,i[i.rfind(os.sep)+1:i.rfind('.')])
        nameList += ['Enter New Observatory']
        self.observatory = wx.ComboBox(self, value = 'Observatories', choices = nameList, name = 'Observatories')
        self.observatory.Bind(wx.EVT_COMBOBOX, self.enterNewObs)
        self.title = wx.StaticText(self, -1, 'Ephemerides Calculator')
        self.title.SetFont(self.titleFont)
        
        self.selectObsLbl = wx.StaticText(self, -1, 'Select Observatory: ')
        self.selectObsLbl.SetFont(self.labelFont)
        
        self.ephSizer.Add(self.title, (0,0), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(self.selectObsLbl, (1,0), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(self.observatory, (1,1), wx.DefaultSpan, wx.TOP, 7)

        self.SetBackgroundColour(wx.Colour(233,233,233))
        self.SetSizer(self.ephSizer)
        self.bestSize = self.GetBestSizeTuple()
        self.SetSize((self.bestSize[0]+20,self.bestSize[1]+20))
        self.Centre()
        self.Show()
        
        
    def addDateCtrl(self, row, colStart, dateCtrl, timeCtrl, label):
        label.SetFont(self.labelFont)
        self.ctrlList += [label]
        self.ephSizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(dateCtrl, (row, colStart+1), wx.DefaultSpan, wx.TOP , 7)
        self.ephSizer.Add(timeCtrl, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)
        
    def addTextCtrl(self, row, colStart, textCtrl, label):
        self.ctrlList += [label]
        label.SetFont(self.labelFont)
        self.ephSizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(textCtrl, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
        
    def enterNewObs(self, event):
        if self.observatory.GetValue() == 'Enter New Observatory':
            self.startSemDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
            self.startSemTime = wx.TextCtrl(self, value = '00:00:00')
            self.endSemDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
            self.endSemTime = wx.TextCtrl(self, value = '00:00:00')
            self.latitude = wx.TextCtrl(self, value = 'deg:min:sec')
            self.elevation = wx.TextCtrl(self, value = '0.0')
            self.temp = wx.TextCtrl(self, value = '0.0')
            self.ctrlList = [self.startSemDate,self.startSemTime,self.endSemDate,self.endSemTime,self.elevation,self.latitude,self.temp]
            self.addDateCtrl(2,0, self.startSemDate, self.startSemTime,wx.StaticText(self, -1, "Beginning of Obs, UT (YYYY/MM/DD): "))
            self.addDateCtrl(3,0, self.endSemDate, self.endSemTime,wx.StaticText(self, -1, "End of Obs, UT (YYYY/MM/DD): "))
            self.addTextCtrl(4,0, self.latitude, wx.StaticText(self, -1, 'Lattitude (deg:min:sec):'))
            self.addTextCtrl(5,0, self.elevation, wx.StaticText(self, -1, 'Observatory Elevation: '))
            self.addTextCtrl(6,0, self.temp, wx.StaticText(self, -1, 'Temperature (Celcius): '))
            self.bestSize = self.GetBestSizeTuple()
            self.SetSize((self.bestSize[0]+20,self.bestSize[1]+20))
            self.Centre()
            
        else:
            for i in self.ctrlList:
                try:
                    i.Destroy()
                except wx.PyDeadObjectError:
                    pass
            ctrlList = []
            self.bestSize = self.GetBestSizeTuple()
            self.SetSize((self.bestSize[0]+20,self.bestSize[1]+20))
            self.Centre()
        
app = wx.App(False)
#### Runs the GUI ####
EphFrame(None)
app.MainLoop()
        