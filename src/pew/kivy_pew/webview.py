import atexit
import logging
import threading

import jnius

logging.info("Starting pew_p4a...?")

from jnius import autoclass, JavaClass, PythonJavaClass, MetaJavaClass, java_method, JavaMethod
from runnable import run_on_ui_thread

WebView = autoclass('android.webkit.WebView')
WebViewClient = autoclass('android.webkit.WebViewClient')
PythonWebViewClient = autoclass('org.kosoftworks.pyeverywhere.PEWebViewClient')
PythonActivity = autoclass('org.kivy.android.PythonActivity')
activity = PythonActivity.mActivity


@run_on_ui_thread
def set_fullscreen():
    Context = PythonActivity.mActivity
    view_instance = Context.getWindow().getDecorView()
    View = autoclass('android.view.View')
    flag = View.SYSTEM_UI_FLAG_LAYOUT_STABLE \
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION \
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN \
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION \
                | View.SYSTEM_UI_FLAG_FULLSCREEN \
                | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
    view_instance.setSystemUiVisibility(flag)


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
        except Exception as e:
            import traceback
            if hasattr(self, "target"):
                logging.error("Error occurred in %r thread. Error details:" % self.target)
            logging.error(traceback.format_exc(e))
        finally:
            self.clean_up()

    def clean_up(self):
        jnius.detach()


class PEWebViewClientInterface(PythonJavaClass):
    __javainterfaces__ = ['org/kosoftworks/pyeverywhere/WebViewCallbacks']
    __javacontext__ = 'app'

    def __init__(self, delegate):
        self.delegate = delegate
        self.webview = None
        self.load_complete = False
        super(PEWebViewClientInterface, self).__init__()

    def setWebView(self, webview):
        self.webview = webview

    @java_method('(Landroid/webkit/WebView;Ljava/lang/String;)Z')
    def shouldLoadURL(self, view, url):
        return not self.delegate.webview_should_start_load(self.webview, url, None)

    @java_method('(Landroid/webkit/WebView;Ljava/lang/String;)V')
    def pageLoadComplete(self, view, url):
        if not self.load_complete:
            self.load_complete = True
            activity.removeLoadingScreen()
        self.delegate.webview_did_finish_load(self.webview, url)


class AndroidWebView(object):
    def __init__(self, **kwargs):
        super(AndroidWebView, self).__init__()
        self.initialized = False
        self.webview = None
        self.client = kwargs['client']
        self.create_webview()
        self.url = None

    @run_on_ui_thread
    def load_url(self, url):
        self.url = url
        if self.initialized:
            self.webview.loadUrl(url)

    @run_on_ui_thread
    def reload(self):
        self.webview.reload()

    @run_on_ui_thread
    def go_back(self):
        self.webview.goBack()

    @run_on_ui_thread
    def go_forward(self):
        self.webview.goForward()

    @run_on_ui_thread
    def clear_history(self):
        self.webview.clearHistory()

    @run_on_ui_thread
    def get_url(self):
        return self.webview.getUrl()

    @run_on_ui_thread
    def evaluate_javascript(self, js):
        self.webview.loadUrl('javascript:' + js, None)

    def get_user_agent(self):
        settings = self.webview.getSettings()
        return settings.getUserAgentString()

    def set_user_agent(self, user_agent):
        settings = self.webview.getSettings()
        settings.setUserAgentString(user_agent)

    @run_on_ui_thread
    def create_webview(self, *args):
        self.webview = PythonActivity.mWebView  # WebView(activity)
        self.webview.setWebContentsDebuggingEnabled(True)
        settings = self.webview.getSettings()
        settings.setJavaScriptEnabled(True)
        settings.setAllowFileAccessFromFileURLs(True)
        settings.setAllowUniversalAccessFromFileURLs(True)
        settings.setMediaPlaybackRequiresUserGesture(False)
        settings.setDomStorageEnabled(True)
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

    def get_persisted_state(self):
        state = {}
        if PythonActivity.mSavedURL:
            state['URL'] = PythonActivity.mSavedURL

        return state

    @run_on_ui_thread
    def show(self):
        pass

    def close(self):
        pass

    def set_menubar(self, menubar):
        pass

    def set_user_agent(self, user_agent):
        self.webview.set_user_agent(user_agent)

    def get_user_agent(self):
        return self.webview.get_user_agent()

    @run_on_ui_thread
    def load_url(self, url):
        self.webview.load_url(url)

    @run_on_ui_thread
    def evaluate_javascript(self, js):
        self.webview.evaluate_javascript(js)
