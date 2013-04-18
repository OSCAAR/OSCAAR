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
        
        textCtrlSize = (530,25)
        setSize = (800,400)
        self.SetSize(setSize)
        self.SetMinSize(setSize)
        self.SetTitle('Ephemerides')

        self.ephSizer = wx.GridBagSizer(7,7)
        self.startSemDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
        self.startSemTime = wx.TextCtrl(self, value = '00:00:00')
        self.endSemDate = wx.TextCtrl(self, value = 'YYYY/MM/DD')
        self.endSemTime = wx.TextCtrl(self, value = '00:00:00')
        
        self.addDateCtrl(1,0, self.startSemDate, self.startSemTime,wx.StaticText(self, -1, "Beginning of Obs, UT (YYYY/MM/DD): "))
        self.addDateCtrl(2,0, self.endSemDate, self.endSemTime,wx.StaticText(self, -1, "End of Obs, UT (YYYY/MM/DD): "))

        
        self.SetBackgroundColour(wx.Colour(233,233,233))

        self.SetSizer(self.ephSizer)
        self.Centre()
        self.Show()
        
        
    def addDateCtrl(self, row, colStart, dateCtrl, timeCtrl, label):
        label.SetFont(self.labelFont)
        self.ephSizer.Add(label, (row, colStart), wx.DefaultSpan, wx.LEFT | wx.TOP, 7)
        self.ephSizer.Add(dateCtrl, (row, colStart+1), wx.DefaultSpan, wx.TOP , 7)
        self.ephSizer.Add(timeCtrl, (row, colStart+2), wx.DefaultSpan, wx.TOP, 7)
        
app = wx.App(False)
#### Runs the GUI ####
EphFrame(None)
app.MainLoop()
        