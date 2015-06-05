__version__ = "0.9.1"

import copy
import logging
import os
import sys
import threading
import time
import unittest
import urllib
import urlparse

platform = None

try:
    import console
    import ui
    from pythonista import *
    platform = 'ios'
except:
    pass

try:
    import kivy
    import jnius
    from kivy_pew import *
    platform = 'android'
except Exception, e:
    import traceback
    logging.warning("Failure when loading kivy")
    logging.warning(traceback.format_exc(e))

try:
    from wxpy import *
    # Match the platform names used for pew commands for consistency
    if sys.platform == "darwin":
        platform = "mac"
    elif sys.platform.startswith("win"):
        platform = "win"
    else:
        platform = sys.platform
except Exception, e:
    pass

if platform == None:
    raise Exception("PyEverywhere does not currently support this platform.")

app_name = "python"

def set_app_name(name):
    global app_name
    app_name = name

def get_app_name():
    global app_name
    return app_name

class PEWTimeoutError(Exception):
    pass

class PEWTestCase(unittest.TestCase):
    def setUp(self):
        self.app = get_app()
        self.webview = self.app.get_main_window()

    def waitForResponse(self, timeout=10):
        time_waited = 0
        sleep_time = 0.05
        while time_waited < timeout:
            time_waited += sleep_time
            time.sleep(sleep_time)
            if self.webview.message_received:
                break

    def simulatePress(self, elementID):
        self.webview.clear_message_received_flag()
        self.webview.evaluate_javascript("$(\"%s\").simulate('click')" % elementID)

    def simulateTextInput(self, id, text):
        self.webview.clear_message_received_flag()
        self.webview.evaluate_javascript("$(\"#%s\").val('%s')" % (id, text))

class WebUIView(NativeWebView):
    def __init__(self, name, url, protocol, delegate):
        super(WebUIView, self).__init__(name)

        self.protocol = protocol
        self.delegate = delegate

        self.page_loaded = False
        self.js_value = None
        self.message_received = False

        self.load_url(url)
    
    def wait_for_js_value(self, timeout=1):
        total_time = 0
        sleep_time = 0.05
        while self.js_value is None:
            total_time += sleep_time
            time.sleep(sleep_time)
            if total_time > timeout:
                raise PEWTimeoutError()

        value = copy.copy(self.js_value)
        self.js_value = None
        return value

    def call_js_function(self, function_name, *a):
        args = []
        for arg in a:
            args.append("'%s'" % arg.replace("'", "\\'").encode("utf-8"))

        js = "%s(%s);" % (function_name, ','.join(args))

        self.evaluate_javascript(js)

    def get_value_from_js(self, value):
        self.js_value = value.replace("%", "%%")

    def get_js_value(self, property, timeout=1):
        """
        Javascript in many browsers runs asynchronously and cannot directly return a value, but
        sometimes an app cannot proceed until a value is retrieved, e.g. tests, so this method

 
        This method causes the app to sleep and should be avoided for any time-sensitive operation.

        """
        self.evaluate_javascript("bridge.getJSValue('%s');" % property)
        return self.wait_for_js_value(timeout)

    def clear_message_received_flag(self):
        """
        This is mostly used for unit testing, so that we can wait on an async response after triggering a UI action.
        """
        self.message_received = False

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
                arg = urllib.unquote(arg).replace("\\", "\\\\").replace("\\u", "\u").decode('unicode_escape')
                pieces = arg.split("=")
                if len(pieces) == 2:
                    command += "%s=u\"%s\"" % (pieces[0], pieces[1])
                else:
                    if arg == "empty_string":
                        arg = ""
                    command += "u\"%s\"" % arg
                command += ","
            command = command[:-1] # strip the last comma
        command += ")"
        
        if command.startswith("get_value_from_js"):
            command = "self.%s" % command
        else:
            command = "self.delegate.%s" % command
        logging.debug("calling: %r" % command)
        eval(command)

        self.message_received = True
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
            self.page_loaded = True
            webview.evaluate_javascript("bridge.setProtocol('%s')" % self.protocol)
            self.delegate.load_complete()
    
    def webview_did_fail_load(self, webview, error_code, error_msg):
        self.page_loaded = True # make sure we don't wait forever if the page fails to load

def get_user_dir():
    return os.getenv('EXTERNAL_STORAGE') or os.path.expanduser("~")

def get_user_path(app_name="python"):
    """ Return the folder to where user data can be stored """
    global platform
    root = get_user_dir()
    if platform != "ios":
        return os.path.join(root, ".%s" % app_name.replace(" ", "_").lower())
    else:
        # iOS does not seems to allow for sub-folder creation?
        # Documents seems to the the place to put it
        # https://groups.google.com/forum/#!topic/kivy-users/sQXAOecthmE
        return os.path.join(root, "Documents")

def get_app_files_dir():
    global platform
    global app_name

    if platform == "mac":
        return os.path.join(get_user_dir(), "Library", "Application Support", app_name)
    elif platform == "win":
        app_files_dir = os.getenv('APPDATA')
        if app_files_dir is not None and os.path.exists(app_files_dir):
            return app_files_dir
        else:
            return os.path.join(get_user_dir(), "Application Data")

    # iOS and Android store documents inside their own special folders, 
    # so the directory is already app-specific
    return get_user_path(app_name)