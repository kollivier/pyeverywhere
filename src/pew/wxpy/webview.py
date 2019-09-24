import logging
import sys
import threading

import wx
import wx.html2

useWebKitCtrl = False
try:
    import wx.webkit
    useWebKitCtrl = True
except Exception as e:
    if sys.platform.startswith('darwin'):
        logging.warning("Unable to load WebKitCtrl wrapper")


logging.info("Initializing WebView?")

PEWThread = threading.Thread


class NativeWebView(object):
    def __init__(self, name="WebView", size=(1024, 768)):
        self.view = wx.Frame(None, -1, name, size=size)

        if useWebKitCtrl:
            self.webview = wx.webkit.WebKitCtrl(self.view, -1)
            self.webview.Bind(wx.webkit.EVT_WEBKIT_STATE_CHANGED, self.OnLoadStateChanged)
            self.webview.Bind(wx.webkit.EVT_WEBKIT_BEFORE_LOAD, self.OnBeforeLoad)
        else:
            self.webview = wx.html2.WebView.New(self.view)
            self.webview.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.OnBeforeLoad)
            self.webview.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.OnLoadComplete)

        self.view.Bind(wx.EVT_CLOSE, self.OnClose)

    def createMacEditMenu(self):
        """
        When using WebKit on OS X, the copy and paste keyboard shortcuts will not work
        unless we have a menubar with shortcuts for them defined.
        """
        menu = wx.MenuBar()
        editMenu = wx.Menu()
        editMenu.Append(wx.ID_CUT, "Cut\tCTRL+X")
        editMenu.Append(wx.ID_COPY, "Copy\tCTRL+C")
        editMenu.Append(wx.ID_PASTE, "Paste\tCTRL+V")
        menu.Append(editMenu, "Edit")
        return menu

    def show(self):
        self.view.Show()

    def close(self):
        self.view.Close()

    def set_fullscreen(self, enable=True):
        self.view.ShowFullScreen(enable)

    def set_menubar(self, menubar):
        self.view.SetMenuBar(menubar.native_object)

    def load_url(self, url):
        wx.CallAfter(self.webview.LoadURL, url)

    def get_user_agent(self):
        return ""

    def set_user_agent(self, user_agent):
        pass

    def evaluate_javascript(self, js):
        js = js.encode('utf8')
        wx.CallAfter(self.webview.RunScript, js)

    def OnClose(self, event):
        self.shutdown()
        event.Skip()

    def OnBeforeLoad(self, event):
        #self.evaluate_javascript("$('#search_bar').val('%s');" % url)
        return self.webview_should_start_load(self, event.URL, None)

    def OnLoadComplete(self, event):
        return self.webview_did_finish_load(self)

    def OnLoadStateChanged(self, event):
        if event.GetState() == wx.webkit.WEBKIT_STATE_STOP:
            return self.OnLoadComplete(event)
