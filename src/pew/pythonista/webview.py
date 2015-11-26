import logging

import console
import ui


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
        self.view = ui.View()                                      # [1]
        self.view.name = name                                    # [2]
        self.view.background_color = 'white'                       # [3]
        self.webview = ui.WebView()
        self.webview.delegate = self
        self.webview.flex = 'WH'
        self.view.add_subview(self.webview)                              # [8]

    def show(self):
        self.view.present('fullscreen', hide_title_bar=True)

    def load_url(self, url):
        self.webview.load_url(url)

    def evaluate_javascript(self, js):
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
