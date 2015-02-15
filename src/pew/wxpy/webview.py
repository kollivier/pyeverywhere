import wx
import wx.webkit

import logging

logging.info("Initializing WebView?")

class NativeWebView(object):
    def __init__(self, delegate):
        self.view = wx.Frame(None, -1, "WebView", size=(700, 500))
        self.webview = wx.webkit.WebKitCtrl(self.view, -1)
        self.webview.Bind(wx.webkit.EVT_WEBKIT_STATE_CHANGED, self.OnLoadStateChanged)
        self.webview.Bind(wx.webkit.EVT_WEBKIT_BEFORE_LOAD, self.OnBeforeLoad)
        self.delegate = delegate

        self.view.Bind(wx.EVT_CLOSE, self.OnClose)

    def show(self):
        self.view.Show()

    def load_url(self, url):
        self.webview.LoadURL(url)

    def evaluate_javascript(self, js):
        js = js.encode('utf8');
        logging.info("Running %s" % js)
        wx.CallAfter(self.webview.RunScript, js)

    def OnClose(self, event):
        self.delegate.shutdown()
        event.Skip()

    def OnBeforeLoad(self, event):
        #self.evaluate_javascript("$('#search_bar').val('%s');" % url)
        return self.delegate.webview_should_start_load(self, event.URL, None)

    def OnLoadStateChanged(self, event):
        if event.GetState() == wx.webkit.WEBKIT_STATE_STOP:
            return self.delegate.webview_did_finish_load(self)
