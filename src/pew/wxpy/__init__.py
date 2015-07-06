import wx

def run_on_main_thread(func, *args, **kwargs):
    wx.CallAfter(func, *args, **kwargs)

app = None
def get_app():
    return app

class PEWApp(wx.App):
    def OnInit(self):
        global app
        app = self
        self.setUp()
        return True

    def shutdown(self):
        self.ExitMainLoop()

    def run(self):
        self.MainLoop()

from webview import *