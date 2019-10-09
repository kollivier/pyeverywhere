import logging

import console
import ui

from objc_util import *

NSURLCache = ObjCClass('NSURLCache')
NSURLRequest = ObjCClass('NSURLRequest')
NSUserDefaults = ObjCClass('NSUserDefaults')
UIColor = ObjCClass('UIColor')
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
        self.view.background_color = 'black'
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
            cache = NSURLCache.alloc().initWithMemoryCapacity_diskCapacity_diskPath_(0, 0, None)
            NSURLCache.setSharedURLCache_(cache)

            NSUserDefaults.standardUserDefaults().setInteger_forKey_(0, "WebKitCacheModelPreferenceKey")
            NSUserDefaults.standardUserDefaults().synchronize()
            # NSUserDefaults.standardUserDefaults().setBool_forKey_(False, "WebKitDiskImageCacheEnabled")
            # //    [[NSUserDefaults standardUserDefaults] setBool:NO forKey:@"WebKitOfflineWebApplicationCacheEnabled"];
            self.webview = ui.WebView()
            self.nativeView = ObjCInstance(self.webview).webView()
            self.nativeView.setMediaPlaybackRequiresUserAction_(False)
            self.nativeView.backgroundColor = UIColor.colorWithRed_green_blue_alpha_(0.0, 0.0, 0.0, 1.0)
            self.nativeView.setOpaque_(False)
            self.webview.delegate = self
            self.webview.flex = 'WH'
            self.view.add_subview(self.webview)

    def show(self):
        self.view.present('fullscreen', hide_title_bar=True)

    def close(self):
        pass

    @on_main_thread
    def load_url(self, url):
        if USE_WKWEBKIT:
            if url.lower().startswith("file://"):
                # Sadly, this does not appear to work. I'm leaving the code in place
                # in case someone can figure this out, but so far all the googling
                # I've done suggests loadFileURL is at least somewhat broken.
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

    def get_url(self):
        return self.webview.mainFrameURL()

    def set_menubar(self, menubar):
        pass

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
