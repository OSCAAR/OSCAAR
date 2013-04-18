import wx
import sys

class EphFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(EphFrame, self).__init__(*args, **kwargs)
        self.initUI()
    
    def initUI(self):
        if(sys.platform == 'darwin' or sys.platform == 'linux2'):
            self.labelFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        else: self.labelFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.titleFont = wx.Font(15, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.bestSize = self.GetBestSizeTuple()
        self.SetSize((self.bestSize[0]+20,self.bestSize[1]+20))
        self.SetTitle('Ephemerides')

        self.ephSizer = wx.GridBagSizer(7,7)
        self.title = wx.StaticText(self, -1, 'Ephemerides Calculator')
        self.title.SetFont(self.titleFont)
        self.startSemDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
        self.startSemTime = wx.TextCtrl(self, value = '00:00:00')
        self.endSemDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
        self.endSemTime = wx.TextCtrl(self, value = '00:00:00')
        self.latitude = wx.TextCtrl(self, value = 'deg:min:sec')
        self.elevation = wx.TextCtrl(self, value = '0.0')
        
        
        self.ephSizer.Add(self.title, (0,0), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.addDateCtrl(1,0, self.startSemDate, self.startSemTime,wx.StaticText(self, -1, "Beginning of Obs, UT (YYYY/MM/DD): "))
        self.addDateCtrl(2,0, self.endSemDate, self.endSemTime,wx.StaticText(self, -1, "End of Obs, UT (YYYY/MM/DD): "))
        self.addTextCtrl(3,0, self.latitude, wx.StaticText(self, -1, 'Lattitude (deg:min:sec):'))
        self.addTextCtrl(4,0, self.elevation, wx.StaticText(self, -1, 'Observatory Elevation: '))

        self.SetBackgroundColour(wx.Colour(233,233,233))
        self.SetSizer(self.ephSizer)
        self.Centre()
        self.Show()
        
        
    def addDateCtrl(self, row, colStart, dateCtrl, timeCtrl, label):
        label.SetFont(self.labelFont)
        self.ephSizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(dateCtrl, (row, colStart+1), wx.DefaultSpan, wx.TOP , 7)
        self.ephSizer.Add(timeCtrl, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)
        
    def addTextCtrl(self, row, colStart, textCtrl, label):
        label.SetFont(self.labelFont)
        self.ephSizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(textCtrl, (row, colStart+1), wx.DefaultSpan, wx.TOP, 7)
        
app = wx.App(False)
#### Runs the GUI ####
EphFrame(None)
app.MainLoop()
        