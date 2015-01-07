import kivy                                                                                                                                                            
from kivy.lang import Builder                                                                   
from kivy.utils import platform                                                                 
from kivy.uix.widget import Widget                                                              
from kivy.clock import Clock                                                                    
from jnius import autoclass, JavaClass, PythonJavaClass, MetaJavaClass, java_method, JavaMethod
from android.runnable import run_on_ui_thread                                                   

WebView = autoclass('android.webkit.WebView')                                                 
WebViewClient = autoclass('android.webkit.WebViewClient')                                       
activity = autoclass('org.renpy.android.PythonActivity').mActivity

def show_alert(title, message):
    pass

class PythonWebViewClient(JavaClass):
    __metaclass__ = MetaJavaClass
    __javaclass__ = 'android/webkit/WebViewClient'

    shouldOverrideUrlLoading = JavaMethod('(Landroid/webkit/WebView,Ljava/lang/String;)Z;')
    onPageFinished = JavaMethod('(Landroid/webkit/WebView,Ljava/lang/String;)V;')

class PEWebViewClient2(PythonWebViewClient):
    __metaclass__ = MetaJavaClass
    __javaclass__ = 'android/webkit/WebViewClient'

    def __init__(self, delegate):
        self.delegate = delegate
        super(PEWebViewClient2, self).__init__()

    @java_method('(Ljava/lang/object;Ljava/lang/String)Z;')
    def shouldOverrideUrlLoading(self, view, url):
        logging.info("shouldOverrideUrlLoading called with url %s" % url)
        return self.delegate.webview_should_start_load(url)

    @java_method('(Ljava/lang/object;Ljava/lang/String)V;')
    def onPageFinished(self, view, url):
        logging.info("onPageFinished called with url %s" % url)
        self.delegate.webview_did_finish_load(url)                           

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

    @run_on_ui_thread                                                                         
    def create_webview(self, *args):                                                            
        self.webview = WebView(activity)                                                             
        self.webview.getSettings().setJavaScriptEnabled(True)                                                                                                                                                                
        activity.setContentView(self.webview)             
        self.webview.setWebViewClient(self.client)
        self.initialized = True
        self.load_url(self.url)

class NativeWebView(object):
    def __init__(self, delegate):
        self.delegate = delegate
        self.initialize()

    def initialize(self):
        self.client = PEWebViewClient2(self.delegate)
        self.webview = AndroidWebView(client=self.client)

    @run_on_ui_thread
    def show(self):
        pass
    
    @run_on_ui_thread
    def load_url(self, url):
        self.webview.load_url(url)

    @run_on_ui_thread
    def evaluate_javascript(self, js):
        self.webview.webview.evaluateJavascript(js)

