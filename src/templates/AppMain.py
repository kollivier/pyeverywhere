import os
import sys
import urllib

import mobilepy

thisdir = os.path.dirname(os.path.abspath(__file__))

class Application(object):
    def run(self):
        """
        Start your UI and app run loop here.
        """
        index = os.path.abspath(os.path.join(thisdir, "files", "www", "index.html"))
        url = "file://%s" % urllib.quote(index)
        if not os.path.exists(index):
            #print sys.path
            print os.listdir(thisdir)
            #print os.listdir(os.path.dirname(index))
            url = "http://www.kosoftworks.com"
        self.delegate = mobilepy.ui.BaseWebViewDelegate("pe", self)
        self.webview = mobilepy.ui.NativeWebView(self.delegate)
        self.webview.load_url(url)
        self.webview.show()
        return 0

    def get_main_window(self):
        return self.webview

    def search_key_up(self, value):
        mobilepy.ui.show_alert('search_key_up called with value:' + value)
        self.webview.evaluate_javascript("$('#search_bar').val('%s');" % value)
