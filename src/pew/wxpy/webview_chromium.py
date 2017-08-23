import atexit
import logging
import platform
import sys
import threading

import wx

from cefpython3 import cefpython
WindowUtils = cefpython.WindowUtils()

chrome_settings = {
    "debug": True,
    "log_severity": cefpython.LOGSEVERITY_INFO,
    "log_file": "debug.log",
#    "log_severity": cefpython.LOGSEVERITY_INFO,
#    "release_dcheck_enabled": True, # Enable only when debugging.
#    "browser_subprocess_path": "%s/%s" % (
#        cefpython.GetModuleDirectory(), "subprocess")
}

class ClientHandler:
    # --------------------------------------------------------------------------
    # RequestHandler
    # --------------------------------------------------------------------------
    onload_handled = False
    def OnBeforeBrowse(self, browser, frame, request, is_redirect):
        # - frame.GetUrl() returns current url
        # - request.GetUrl() returns new url
        # - Return true to cancel the navigation or false to allow
        # the navigation to proceed.
        if self.callback is not None:
            return not self.callback(request.GetUrl())
        return False


@atexit.register
def ShutDown():
    logging.info("Shutting down")
    cefpython.Shutdown()

logging.info("Initializing WebView?")

PEWThread = threading.Thread


class NativeWebView(object):
    def __init__(self, name="WebView", size=(1024, 768)):
        cefpython.Initialize(chrome_settings)

        self.browser_panel = self.view = wx.Frame(None, -1, name, size=size)
        
        # self.browser_panel = wx.Panel(self.view, style=wx.WANTS_CHARS)
        self.browser_panel.Bind(wx.EVT_SIZE, self.OnSize)
        self.browser_panel.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)

        window_info = cefpython.WindowInfo()
        (width, height) = self.browser_panel.GetClientSize().Get()
        window_info.SetAsChild(self.browser_panel.GetHandle(),
                               [0, 0, size[0], size[1]])
        self.webview = cefpython.CreateBrowserSync(window_info,
                                             url="about:blank")

        client = ClientHandler()
        self.webview.SetClientHandler(client)
        client.callback = self.HandleURL

        self.timer = None
        self.create_timer()

        self.view.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnSize(self, event):
        logging.info("OnSize called...")
        if not self.webview:
            return
        if platform.system() == "Windows":
            WindowUtils.OnSize(self.browser_panel.GetHandle(),
                               0, 0, 0)
        elif platform.system() == "Linux":
            (x, y) = (0, 0)
            (width, height) = self.browser_panel.GetSize().Get()
            self.webview.SetBounds(x, y, width, height)
        self.webview.NotifyMoveOrResizeStarted()

    def OnSetFocus(self, _):
        if not self.webview:
            return
        if platform.system() == "Windows":
            WindowUtils.OnSetFocus(self.browser_panel.GetHandle(),
                                   0, 0, 0)
        self.webview.SetFocus(True)

    def create_timer(self):
        # See also "Making a render loop":
        # http://wiki.wxwidgets.org/Making_a_render_loop
        # Another way would be to use EVT_IDLE in MainFrame.
        self.timer = wx.Timer(self.view, -1)
        self.view.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(10)  # 10ms timer

    def on_timer(self, event):
        cefpython.MessageLoopWork()

    def show(self):
        self.view.Show()

    def set_fullscreen(self, enable=True):
        self.view.ShowFullScreen(enable)

    def load_url(self, url):
        self.webview.LoadUrl(url)

    def get_user_agent(self):
        return ""

    def set_user_agent(self, user_agent):
        pass

    def evaluate_javascript(self, js):
        self.webview.GetBrowser().GetMainFrame().ExecuteJavascript(js)

    def OnClose(self, event):
        logging.info("OnClose called...")
        if self.timer:
            self.timer.Stop()
        if self.webview:
            self.webview.ParentWindowWillClose()
            self.webview = None

        self.shutdown()
        event.Skip()

    def HandleURL(self, url):
        #self.evaluate_javascript("$('#search_bar').val('%s');" % url)
        return self.webview_should_start_load(self, url, None)

    def OnLoadComplete(self, event):
        return self.webview_did_finish_load(self)

    def OnLoadStateChanged(self, event):
        if event.GetState() == wx.webkit.WEBKIT_STATE_STOP:
            return self.OnLoadComplete(event)
