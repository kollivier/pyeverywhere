import os
import urlparse

import console
import ui

@ui.in_background
def show_alert(title, message=""):
    console.alert(title, message)

class NativeWebView(object):
    def __init__(self, delegate):
        self.view = ui.View()                                      # [1]
        self.view.name = 'WebView'                                    # [2]
        self.view.background_color = 'white'                       # [3]
        self.webview = ui.WebView()
        self.delegate = delegate
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
        return self.delegate.webview_should_start_load(self, url, nav_type)

    def webview_did_start_load(self, webview):
        return self.delegate.webview_did_start_load(self)

    def webview_did_finish_load(self, webview):
        show_alert('finish load called')
        return self.delegate.webview_did_finish_load(self)
    
    def webview_did_fail_load(self, webview, error_code, error_msg):
        return self.delegate.webview_did_fail_load(self, error_code, error_msg)