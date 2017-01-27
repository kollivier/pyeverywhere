import logging
import threading

import objc
objc.setVerbose(True)
import AppKit
import Foundation
import PyObjCTools.AppHelper
import WebKit


PEWThread = threading.Thread


class WebViewDelegate(AppKit.NSObject):
    def webView_addMessageToConsole_(self, webview, message):
        logging.error("JSError: %r" % message)

    def consoleLog_(self, message):
        logging.info("JSLog: %r" % message)

    def isSelectorExcludedFromWebScript_(self, aSel):
        if aSel.startswith('consoleLog'):
            return False

        return True

    def webView_didFinishLoadForFrame_(self, webview, frame):
        print("self.webview = %r" % self.webview)
        if frame == frame.findFrameNamed_("_top"):
            scriptObject = webview.windowScriptObject()
            scriptObject.setValue_forKey_(self, "PEWApp")
            scriptObject.evaluateWebScript_("console = { log: function(msg) { window.PEWApp.consoleLog_(msg); } }")

        self.webview.webview_did_finish_load(self.webview)


class NativeWebView(object):
    def __init__(self, name="WebView", size=(1024, 768)):
        self.app = AppKit.NSApplication.sharedApplication()
        self.view = AppKit.NSWindow.alloc()
        frame = ((200.0, 300.0), size)
        self.view.initWithContentRect_styleMask_backing_defer_(frame, 15, 2, 0)
        self.view.setTitle_('HelloWorld')
        self.view.setLevel_(3)
        self.webview = WebKit.WebView.alloc().initWithFrame_(frame)
        self.webviewDelegate = WebViewDelegate.alloc().init()
        self.webviewDelegate.webview = self
        self.webview.setUIDelegate_(self.webviewDelegate)
        self.webview.setFrameLoadDelegate_(self.webviewDelegate)
        self.view.setContentView_(self.webview)

    def show(self):
        print("Calling show")
        self.view.display()
        self.view.orderFrontRegardless()

    def load_url(self, url):
        PyObjCTools.AppHelper.callAfter(self._load_url, url)

    def _load_url(self, url):
        nsurl = Foundation.NSURL.URLWithString_(url)
        req = Foundation.NSURLRequest.requestWithURL_(nsurl)
        self.webview.mainFrame().loadRequest_(req)

    def evaluate_javascript(self, js):
        js = js.encode('utf8')
        PyObjCTools.AppHelper.callAfter(self.webview.stringByEvaluatingJavaScriptFromString_, js)
