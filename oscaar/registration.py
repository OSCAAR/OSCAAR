import wx
import os
import webbrowser

class RegistrationFrame(wx.Frame):
    
    def __init__(self):
         
        self.title = "OSCAAR Registration"
        wx.Frame.__init__(self,None,-1, self.title)
        self.panel = wx.Panel(self)
        
        self.logo = wx.Image(os.path.join(os.path.dirname(__file__),'images','registration2_2.png'), wx.BITMAP_TYPE_ANY)
        self.bmp = wx.BitmapFromImage(self.logo)
        self.button = wx.BitmapButton(self.panel, -1, self.bmp, size=(self.bmp.GetWidth(),self.bmp.GetHeight()))
        self.button.Bind(wx.EVT_BUTTON, self.openLink)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.button, 0, wx.ALL, 0)
        self.panel.SetSizer(self.vbox)
        self.vbox.Fit(self)
         
        iconloc = os.path.join(os.path.dirname(__file__),'images','logo4noText.ico')
        icon1 = wx.Icon(iconloc, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon1)       
         
        self.Center()
        self.Show()

    def openLink(self, event):
        webbrowser.open_new_tab("https://docs.google.com/forms/d/1JYJo2eDY-X4KgUgc1rtRbxyiK82rJB9QZ0Y199djxrE/viewform")
        self.Destroy()

app = wx.App(False)
#### Runs the GUI ####
RegistrationFrame()
app.MainLoop()