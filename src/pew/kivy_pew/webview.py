import atexit
import logging
import threading

import jnius
import kivy

logging.info("Starting kivy...?")

from kivy.lang import Builder
from kivy.utils import platform
from kivy.uix.widget import Widget
from kivy.clock import Clock
from jnius import autoclass, JavaClass, PythonJavaClass, MetaJavaClass, java_method, JavaMethod
from android.runnable import run_on_ui_thread

WebView = autoclass('android.webkit.WebView')
WebViewClient = autoclass('android.webkit.WebViewClient')
PythonWebViewClient = autoclass('org.kosoftworks.pyeverywhere.PEWebViewClient')
activity = autoclass('org.renpy.android.PythonActivity').mActivity


def show_alert(title, message=""):
    logging.info("Alert: %s %s" % (title, message))


class PEWThread(threading.Thread):
    """
    PEWThread is a subclass of the Python threading.Thread object that allows it 
    to work with some native platforms that require additional handling when interacting
    with the GUI. The API for PEWThread mimics threading.Thread exactly, so please refer 
    to that for API documentation.
    """
    def __init__(self, group=None, target=None, name=None, args=(), kwargs={}):
        super(PEWThread, self).__init__(group, target, name, args, kwargs)

    def run(self):
        try:
            super(PEWThread, self).run()
        except Exception, e:
            import traceback
            logging.error("Error occurred in %r thread. Error details:" % self.target)
            logging.error(traceback.format_exc(e))
        finally:
            self.clean_up()

    @atexit.register
    def clean_up(self):
        jnius.detach()


class PEWebViewClientInterface(PythonJavaClass):
    __javainterfaces__ = ['org/kosoftworks/pyeverywhere/WebViewCallbacks']
    __javacontext__ = 'app'

    def __init__(self, delegate):
        self.delegate = delegate
        self.webview = None
        super(PEWebViewClientInterface, self).__init__()

    def setWebView(self, webview):
        self.webview = webview

    @java_method('(Landroid/webkit/WebView;Ljava/lang/String;)Z')
    def shouldLoadURL(self, view, url):
        logging.debug("shouldOverrideUrlLoading called with url %s" % url)
        return not self.delegate.webview_should_start_load(self.webview, url, None)

    @java_method('(Landroid/webkit/WebView;Ljava/lang/String;)V')
    def pageLoadComplete(self, view, url):
        logging.debug("onPageFinished called with url %s" % url)
        self.delegate.webview_did_finish_load(self.webview, url)


class AndroidWebView(Widget):
    def __init__(self, **kwargs):
        super(AndroidWebView, self).__init__(**kwargs)
        self.initialized = False
        self.webview = None
        self.client = kwargs['client']
        self.create_webview()
        self.url = None

    def load_url(self, url):
        self.url = url
        if self.initialized:
            self.webview.loadUrl(url)

    def evaluate_javascript(self, js):
        self.webview.evaluateJavascript(js, None)

    @run_on_ui_thread
    def create_webview(self, *args):
        self.webview = WebView(activity)
        settings = self.webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setAllowFileAccessFromFileURLs(True)
        settings.setAllowUniversalAccessFromFileURLs(True)
        activity.setContentView(self.webview)
        self.webview.setWebContentsDebuggingEnabled(True)
        self.webview.setWebViewClient(self.client)
        self.initialized = True
        self.load_url(self.url)


class NativeWebView(object):
    def __init__(self, name="WebView", size=None):
        self.initialize()

    def initialize(self):
        self.callback = PEWebViewClientInterface(self)
        self.client = PythonWebViewClient()
        self.client.setWebViewCallbacks(self.callback)
        self.webview = AndroidWebView(client=self.client)
        self.callback.setWebView(self.webview)

    @run_on_ui_thread
    def show(self):
        pass

    @run_on_ui_thread
    def load_url(self, url):
        self.webview.load_url(url)

    @run_on_ui_thread
    def evaluate_javascript(self, js):
        self.webview.evaluate_javascript(js)
