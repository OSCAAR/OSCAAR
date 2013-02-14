import wx
import photPack

class MasterFlatFrame(wx.Frame):

    def __init__(self, *args, **kwargs):
        super(MasterFlatFrame, self).__init__(*args, **kwargs)
        self.frameSizer = wx.GridBagSizer(7,7)
        
        ###Variable Declarations###
        pathCtrlSize = (325,25)
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
        photPack.masterFlatMaker(self.flatImagesPathCtrl.GetValue, self.flatDarksPathCtrl.GetValue, 
                                 self.masterFlatPathCtrl.GetValue, self.plotsOn.GetValue)

app = wx.App(False)
MasterFlatFrame(None)
app.MainLoop()
