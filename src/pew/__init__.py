__version__ = "0.9.1"

import logging
import os
import sys
import threading
import urllib
import urlparse

platform = None

try:
    from pythonista import *
    platform = 'ios'
except:
    pass

try:
    from kivy import *
    import jnius
    platform = 'android'
except:
    pass

try:
    from wxpy import *
    platform = sys.platform
except Exception, e:
    pass

if platform == None:
    raise Exception("PyEverywhere does not currently support this platform.")

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
        super(PEWThread, self).run()
        if platform == "android":
            jnius.detach()

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
            # On Android at least, Python puts the ?whatever part in path rather than query
            query = parts.path
            if query and len(query) > 0 and query[0] == "?":
                query = query[1:]
        if query:
            args = query.split("&")
            for arg in args:
                pieces = arg.split("=")
                if len(pieces) == 2:
                    argname =  ulrlib.unquote(pieces[0]).replace("\\u", "\u").decode('unicode_escape')
                    argvalue = urllib.unquote(pieces[1]).replace("\\u", "\u").decode('unicode_escape')
                    command += "%s=\"%s\"" % (argname, argvalue)
                else:
                    command += "u\"%s\"" % urllib.unquote(arg).replace("\\u", "\u").decode('unicode_escape')
                command += ","
            command = command[:-1] # strip the last comma
        command += ")"

        command = "self.delegate.%s" % command
        logging.debug("calling: %r" % command)
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
        if url is None or url.startswith("file://") and "index.html" in url:
            webview.evaluate_javascript("bridge.setProtocol('%s')" % self.protocol)
            self.delegate.load_complete()
    
    def webview_did_fail_load(self, webview, error_code, error_msg):
        pass

def get_user_path():
    """ Return the folder to where user data can be stored """
    global platform
    root = os.getenv('EXTERNAL_STORAGE') or os.path.expanduser("~")
    if platform != "ios":
        return os.path.join(root, ".python")
    else:
        # iOS does not seems to allow for sub-folder creation?
        # Documents seems to the the place to put it
        # https://groups.google.com/forum/#!topic/kivy-users/sQXAOecthmE
        return os.path.join(root, "Documents")
