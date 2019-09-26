import logging
import threading

import objc
objc.setVerbose(True)
import AppKit
import Foundation
import PyObjCTools.AppHelper
import WebKit


from . import dialogs


PEWThread = threading.Thread


class ApplicationDelegate(AppKit.NSObject):
    def applicationShouldTerminateAfterLastWindowClosed_(self, app):
        return True


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
        self.webview.webview_did_finish_load(self.webview)

    def webView_runOpenPanelForFileButtonWithResultListener_(self, webview, listener):
        def result(filename):
            listener.chooseFilename_(filename)

        dialogs.open_file_dialog(result)

class NativeWebView(object):
    def __init__(self, name="WebView", size=(1024, 768)):
        self.app = AppKit.NSApplication.sharedApplication()
        self.appDelegate = ApplicationDelegate.alloc().init()
        self.app.setDelegate_(self.appDelegate)

        self.view = AppKit.NSWindow.alloc()
        frame = ((200.0, 300.0), size)
        self.view.initWithContentRect_styleMask_backing_defer_(frame, 15, 2, 0)
        self.view.setTitle_(name)
        self.webview = WebKit.WebView.alloc().initWithFrame_(frame)
        self.webviewDelegate = WebViewDelegate.alloc().init()
        self.webviewDelegate.webview = self
        self.webview.setUIDelegate_(self.webviewDelegate)
        self.webview.setFrameLoadDelegate_(self.webviewDelegate)
        self.view.setContentView_(self.webview)

    def show(self):
        print("Calling show")
        self.view.makeKeyAndOrderFront_(None)
        self.view.contentView().setNeedsDisplay_(True)
        self.app.activateIgnoringOtherApps_(True)

    def close(self):
        self.view.close()

    def reload(self):
        self.webview.reload()

    def go_back(self):
        self.webview.goBack()

    def go_forward(self):
        self.webview.goForward()

    def clear_history(self):
        # setting this to false clears the existing one.
        self.webview.setMaintainsBackForwardList_(False)
        self.webview.setMaintainsBackForwardList_(True)

    def load_url(self, url):
        PyObjCTools.AppHelper.callAfter(self._load_url, url)

    def _load_url(self, url):
        nsurl = Foundation.NSURL.URLWithString_(url)
        req = Foundation.NSURLRequest.requestWithURL_(nsurl)
        self.webview.mainFrame().loadRequest_(req)

    def evaluate_javascript(self, js):
        js = js.encode('utf8')
        PyObjCTools.AppHelper.callAfter(self.webview.stringByEvaluatingJavaScriptFromString_, js)
