import logging

import console
import ui

from objc_util import *

NSURLRequest = ObjCClass('NSURLRequest')
WKWebView = ObjCClass('WKWebView')
WKWebViewConfiguration = ObjCClass('WKWebViewConfiguration')

USE_WKWEBKIT = False


@ui.in_background
def show_alert(title, message=""):
    console.alert(title, message)


class PEWThread(object):
    """
    PEWThread is a subclass of the Python threading.Thread object that allows it
    to work with some native platforms that require additional handling when interacting
    with the GUI. The API for PEWThread mimics threading.Thread exactly, so please refer
    to that for API documentation.
    """
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        self.target = target
        self.args = args
        self.kwargs = kwargs

    def start(self):
        self.run()

    @ui.in_background
    def run(self):
        self.target(*self.args, **self.kwargs)


class NativeWebView(object):
    def __init__(self, name="WebView", size=None):
        self.view = ui.View()
        self.view.name = name
        self.view.background_color = 'white'
        if USE_WKWEBKIT:
            self.nativeView = ObjCInstance(self.view._objc_ptr)
            self.config = WKWebViewConfiguration.new().autorelease()
            self.config.requiresUserActionForMediaPlayback = False
            self.webview = WKWebView.alloc().initWithFrame_configuration_(self.nativeView.bounds(), self.config)

            # self.webview = WKWebView.new().autorelease()
            flex_width, flex_height = (1 << 1), (1 << 4)
            self.webview.setAutoresizingMask_(flex_width | flex_height)
            self.nativeView.addSubview_(self.webview)
        else:
            self.webview = ui.WebView()
            ObjCInstance(self.webview).webView().setMediaPlaybackRequiresUserAction_(False)
            self.webview.delegate = self
            self.webview.flex = 'WH'
            self.view.add_subview(self.webview)

    def show(self):
        self.view.present('fullscreen', hide_title_bar=True)

    @on_main_thread
    def load_url(self, url):
        if USE_WKWEBKIT:
            if url.lower().startswith("file://"):
                urldir = url
                lastslash = url.rfind('/')
                lastpart = url[lastslash:]
                if len(lastpart) > 0 and lastpart.find(".") != -1:
                    urldir = url[:lastslash]
                self.webview.loadFileURL_allowingReadAccessToURL_(nsurl(url), nsurl(urldir))
            else:
                self.webview.loadRequest_(NSURLRequest.requestWithURL_(nsurl(url)))
        else:
            self.webview.load_url(url)

    def get_user_agent(self):
        return ""

    def set_user_agent(self, user_agent):
        pass

    def evaluate_javascript(self, js):
        if USE_WKWEBKIT:
            self.webview.evaluateJavaScript_completionHandler_(js, 0)
        else:
            self.webview.evaluate_javascript(js)

    def webview_should_start_load(self, webview, url, nav_type):
        #self.evaluate_javascript("$('#search_bar').val('%s');" % url)
        return self.webview_should_start_load(self, url, nav_type)

    def webview_did_start_load(self, webview):
        return self.webview_did_start_load(self)

    def webview_did_finish_load(self, webview):
        return self.webview_did_finish_load(self)

    def webview_did_fail_load(self, webview, error_code, error_msg):
        return self.webview_did_fail_load(self, error_code, error_msg)
