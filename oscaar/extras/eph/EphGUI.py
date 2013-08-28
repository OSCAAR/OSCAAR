import sys
if not hasattr(sys, 'real_prefix'):
    import wx
from glob import glob
import os

class EphFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(EphFrame, self).__init__(*args, **kwargs)
        self.initUI()
    
    def initUI(self):
        if(sys.platform == 'darwin' or sys.platform == 'linux2'):
            self.labelFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        else: self.labelFont = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
        self.titleFont = wx.Font(17, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.SetTitle('Ephemerides')
        self.ctrlList = []
        self.ephSizer = wx.GridBagSizer(5,5)
        obsList = glob('..'+os.sep+'eph'+'observatories'+os.sep+'*')
        nameList = []
        for i in obsList:
            nameList.insert(0,i[i.rfind(os.sep)+1:i.rfind('.')])
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
        self.addRadioBox(10,3, self.calc_eclipses)
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
            HomeDir()
            obsPath = os.getcwd() + 'Extras' + os.sep + 'eph' + 'observatories' + os.sep + self.observatory.GetValue() + '.par'
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
        newobs = file(filename, 'w')
        newobs.write('name: ' + self.name.GetValue() + '\n')
        newobs.write('longitude: ' + self.longitude.GetValue() + '\n')
        newobs.write('elevation: ' + self.elevation.GetValue() + '\n')
        newobs.write('temperature: ' + self.temp.GetValue() + '\n')
        newobs.write('min_horizon: ' + self.min_horizon.GetValue() + '\n')
        newobs.write('start_date: ' + '(' + semdateArr[0] + ',' + semdateArr[1] + ',' + semdateArr[2] + ',' + semtimeArr[0] + ',' + semtimeArr[1] + ',' + semtimeArr[2] + ')' + '\n')
        newobs.write('end_date: ' + '(' + enddateArr[0] + ',' + enddateArr[1] + ',' + enddateArr[2] + ',' + endtimeArr[0] + ',' + endtimeArr[1] + ',' + endtimeArr[2] + ')' + '\n')
        newobs.write('v_limit: ' + self.v_limit.GetValue() + '\n')
        newobs.write('depth_limit: ' + self.depth_limit.GetValue() + '\n')
        newobs.write('calc_eclipses: ' + str(self.calc_eclipses.GetSelection()==0) + '\n')
        newobs.write('html_out: ' + str(self.html_out.GetSelection()==0) + '\n')
        newobs.write('text_out: ' + str(self.text_out.GetSelection()==0) + '\n')
        newobs.write('twilight: ' + self.twilightType.GetValue() + '\n')
        newobs.close()
        
    def calculate(self, event):
        path = 'observatories' + os.sep + self.filename.GetValue() + '.par'
        self.saveFile(path)


app = wx.App(False)
#### Runs the GUI ####
EphFrame(None)
app.MainLoop()
        