import logging
import sys
import urllib
import urlparse

platform = None

class BaseWebViewDelegate(object):
    def __init__(self, protocol, delegate):
        self.protocol = protocol
        self.delegate = delegate
    
    def parse_message(self, url):
        if not url.startswith(self.protocol):
            return False

        logging.debug("parsing url: %r" % (url,))
        parts = urlparse.urlparse(url)
        command = "%s(" % parts.netloc

        query = parts.query
        if not query:
            query = parts.path
        if query:
            args = parts.query.split("&")
            for arg in args:
                pieces = arg.split("=")
                if len(pieces) == 2:
                    argname =  ulrlib.unquote(pieces[0]).replace("\\u", "\u").decode('unicode_escape')
                    argvalue = urllib.unquote(pieces[1]).replace("\\u", "\u").decode('unicode_escape')
                    command += "%s=\"%s\"" % (argname, argvalue)
                else:
                    command += "u\"%s\"" % urllib.unquote(arg).replace("\\u", "\u").decode('unicode_escape')
        command += ")"

        command = "self.delegate.%s" % command
        logging.debug("calling: %s" % command)
        eval(command)

        return True
    
    def shutdown(self):
        self.delegate.shutdown()

    def webview_should_start_load(self, webview, url, nav_type):
        #self.evaluate_javascript("$('#search_bar').val('%s');" % url)
        return not self.parse_message(url)

    def webview_did_start_load(self, webview, url=None):
        pass
    def webview_did_finish_load(self, webview, url=None):
        webview.evaluate_javascript("bridge.setProtocol('%s')" % self.protocol)
        self.delegate.load_complete()
    
    def webview_did_fail_load(self, webview, error_code, error_msg):
        pass


try:
    from pythonista_webview import *
    platform = 'ios'
except:
    pass

try:
    from kivy_webview import *
    platform = 'android'

except:
    pass

try:
    from wx_webview import *
    platform = sys.platform
except Exception, e:
    pass

if platform == None:
    raise Exception("PyEverywhere does not currently support this platform.")
