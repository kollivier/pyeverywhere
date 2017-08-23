import logging
import wx

def run_on_main_thread(func, *args, **kwargs):
    wx.CallAfter(func, *args, **kwargs)

app = None
def get_app():
    return app

class NativePEWApp(wx.App):
    def OnInit(self):
        global app
        app = self
        self.setUp()
        return True

    def shutdown(self):
        self.ExitMainLoop()

    def run(self):
        self.MainLoop()

try:
    from webview_chromium import *
except Exception, e:
    import traceback
    logging.warning(traceback.format_exc(e))
    logging.warn("Chromium not found, loading wxWebView instead.")
    from webview import *
