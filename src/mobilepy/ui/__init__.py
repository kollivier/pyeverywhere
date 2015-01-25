import logging
import urlparse

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
                    argname = pieces[0]
                    argvalue = pieces[1]
                    command += "%s=\"%s\"" % (argname, argvalue)
                else:
                    command += "\"%s\"" % arg
        command += ")"

        command = "self.delegate.%s" % command
        logging.debug("calling: %s" % command)
        eval(command)

        return True
    
    def webview_should_start_load(self, webview, url, nav_type):
        #self.evaluate_javascript("$('#search_bar').val('%s');" % url)
        return not self.parse_message(url)

    def webview_did_start_load(self, webview, url=None):
        pass
    def webview_did_finish_load(self, webview, url=None):
        webview.evaluate_javascript("bridge.setProtocol('%s')" % self.protocol)
    
    def webview_did_fail_load(self, webview, error_code, error_msg):
        pass


try:
    from pythonista_webview import *
except:
    pass

try:
    from kivy_webview import *
except:
    raise