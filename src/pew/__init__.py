"""
The PyEverywhere (pew) module acts as a bridge layer between the Python app logic
and an HTML/CSS/JS-based front end. 
"""


__version__ = "0.9.1"

import copy
import json
import logging
import os
import sys
import threading
import time
import unittest
import urllib
import urllib2
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
    """
    Sets the app name. In addition to being used for name display, it is used
    when creating app data subdirectories in common locations.
    """
    global app_name
    app_name = name


def get_app_name():
    """
    Returns the app name.
    """
    global app_name
    return app_name


class PEWTimeoutError(Exception):
    """
    Exception thrown when PEW times out waiting to retrieve a JS value.
    """
    
    pass


class PEWApp(NativePEWApp):
    """
    Class for managing the native application. You must create a subclass of 
    this class, initialize it and call its run method to start the app.
    """
    
    def __init__(self):
        super(PEWApp, self).__init__()
    
    def setUp(self):
        """
        Performs application setup. Your application should override this 
        method and perform its own setup steps. 
        
        It is expected that you will have a visible WebUIView before this method
        completes. If not, some platforms may shut down the app.
        """
        pass
        
    def run(self):
        """
        Starts the application's main loop.
        """
        super(PEWApp, self).run()
        
    def shutdown(self):
        """
        Runs any shutdown handling code. Your application should override
        this method if you need to run any custom shutdown code. Be sure
        to call the base shutdown method as well.
        """
        super(PEWApp, self).shutdown()


class WebUIView(NativeWebView):
    """
    WebUIView is a wrapper around the native platform's embedded web browser 
    engine. It constructs a native window and fills the entire window with 
    the contents of the web view.
    """
    def __init__(self, name, url, protocol, delegate, size=(1024, 768)):
        """
        Creates a native WebUIView and accompanying UI window.
        
        :param name: window name, will show in the titlebar of platforms that have one 
        :param url: URL of the HTML document containing the app's UI
        :param protcol: string designating the app protocol to use, e.g. myapp will result in myapp://message messages
        :param delegate: a Python object that will receive the messages sent from the web UI
        """
        super(WebUIView, self).__init__(name, size)

        self.protocol = protocol
        if not "://" in protocol:
            self.protocol += "://" 
        self.delegate = delegate

        self.page_loaded = False
        self.js_value = None
        self.message_received = False

        self.load_url(url)
    
    def _wait_for_js_value(self, variable, timeout=1):
        """
        Waits for the UI to send back the requested variable. Returns the variable
        if retrieved before timeout, otherwise throws a PEWTimeoutError.
        
        Params:
            :param variable: variable whose value we are trying to retrieve 
            :param timeout: time in seconds to wait before timing out
        """
        total_time = 0
        sleep_time = 0.05
        while self.js_value is None:
            total_time += sleep_time
            time.sleep(sleep_time)
            if total_time > timeout:
                raise PEWTimeoutError("Timed out attempting to retrieve value for '%s'" % variable)

        value = copy.copy(self.js_value)
        self.js_value = None
        return value

    def load_url(self, url):
        """
        Loads the document at the specified URL into the app's main web view. Note
        that this will effectively replace your UI view.
        
        Params:
            :param url: URL to load, if loading a local file be sure to use the file:// protocol
        """
        super(WebUIView, self).load_url(url)

    def show(self):
        """
        Makes the web view visible on screen. 
        """
        super(WebUIView, self).show()

    def call_js_function(self, function_name, *a):
        """
        Calls a JavaScript function from Python. 
        
        :param function_name: name of function to call 
        :param a: series of arguments to function 
        
        Example:
            webview.call_js_function("show_address_form", "123 Main Street", "Santa Claus", "IN")
        """
        args = []
        for arg in a:
            args.append("'%s'" % arg.replace("'", "\\'").encode("utf-8"))

        js = "%s(%s);" % (function_name, ','.join(args))

        self.evaluate_javascript(js)

    def get_value_from_js(self, value):
        self.js_value = value.replace("%", "%%")

    def get_js_value(self, variable, timeout=1):
        """
        Gets the value of a property, variable or function in JavaScript. 
        
        Javascript in many browsers runs asynchronously and cannot directly return a value, but
        sometimes an app cannot proceed until a value is retrieved, e.g. tests, so this method
        sends a message asking for the value and waits until JS sends back the value.
 
        This method causes the app to sleep and should be avoided for any time-sensitive operation.

        :param variable: the property or variable you want the value of 
        :param timeout: how many seconds to wait before giving up on retrieving the value
        """
        self.evaluate_javascript("bridge.getJSValue('%s');" % variable)
        return self._wait_for_js_value(variable, timeout)

    def clear_message_received_flag(self):
        """
        Clears the message received flag. This is mostly used for unit testing, so that we can wait on an async response after triggering a UI action.
        """
        self.message_received = False

    def parse_message(self, url):
        """
        Processes a message received from the JavaScript bridge and calls the
        corresponding Python delegate method. Internal use only.
        """
        if not url.startswith(self.protocol):
            return False

        logging.debug("parsing url: %r" % (url,))
        parts = urlparse.urlparse(url)
        query = parts.query

        # On Android at least, Python puts the ?whatever part in path rather than query
        path = parts.path.split("?")
        if len(path) == 2 and not query:
            query = path[1]
        path = path[0]

        func_name = parts.netloc
        if path != "":
            func_name += path.replace("/", ".")
        command = u"%s" % func_name

        func_args = []
        func_kwargs = {}
        if query:
            args = query.split("&")
            for arg in args:
                arg = urllib2.unquote(arg.encode('ascii'))
                logging.debug("arg = %s" % arg)
                #arg = arg.replace("\\", "\\\\")
                #arg = arg.replace("\\u", "\u")
                arg = arg.decode('utf-8')
                name = None
                value = None
                pieces = arg.split("=")
                if len(pieces) == 2:
                    name = pieces[0]
                    value = pieces[1]
                else:
                    value = pieces[0]
                if value == "empty_string":
                    value = ""
                    
                try:
                    value = json.loads(value)
                except:
                    pass
                
                if name is not None:
                    func_kwargs[name] = value
                else:
                    func_args.append(value)
        
        if func_name.startswith("get_value_from_js"):
            command = "self.%s" % func_name
        else:
            command = "self.delegate.%s" % func_name
        
        logging.debug("calling: %s" % command)    
        function = eval(command)
        function(*func_args, **func_kwargs)

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
    """
    Returns the user's home directory.
    """
    return os.getenv('EXTERNAL_STORAGE') or os.path.expanduser("~")

def get_user_path(app_name="python"):
    """ 
    Returns the folder where user data can be stored. 
    """
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
    """
    Returns the location where the application's support files should be stored.
    """
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