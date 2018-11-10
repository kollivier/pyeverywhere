"""
The PyEverywhere (pew) module acts as a bridge layer between the Python app logic
and an HTML/CSS/JS-based front end.
"""


__version__ = "0.9.2"

HOST = "127.0.0.1"
PORT = 8456
MSG_PORT = 8128

import copy
import json
import logging
import os
import six.moves.BaseHTTPServer as BaseHTTPServer
import six.moves.SimpleHTTPServer as SimpleHTTPServer
import six.moves.socketserver as socketserver
import sys
import threading
import time

import six
from six.moves.BaseHTTPServer import BaseHTTPRequestHandler
from six.moves.urllib.parse import urlparse, unquote

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


message_thread = None
message_delegate = None


def start_message_server(delegate, host=HOST, port=MSG_PORT):
    """
    Messages sent to the server at the specified host and port will be parsed as URLs
    and converted to Python methods called upon the delegate object, which must be a
    PEWMessageHandler-derived object.

    Returns the root URL to the started server.
    """

    global message_thread
    message_thread = PEWThread(target=start_message_server_thread, args=(delegate, host, port))
    message_thread.daemon = True
    message_thread.start()
    return "http://%s:%s/" % (host, port)


def start_message_server_thread(delegate, host=HOST, port=MSG_PORT):
    from BaseHTTPServer import HTTPServer
    global message_delegate
    message_delegate = delegate
    server = HTTPServer((host, port), PEWMessageRequestHandler)
    logging.info("message server initialized at http://%s:%s/" % (host, port))
    try:
        server.serve_forever()
    except Exception as e:
        import traceback
        logging.info("Server disconnected")
        logging.info("Reason: %s" % traceback.format_exc())
    logging.info("Finished.")


def start_local_server(url_root, host=HOST, port=PORT, callback=None):
    """
    Starts a local HTTP server with the site root pointing to the directory passed in
    as url_root. This function does not return - if using this in a GUI app, make sure
    to call this in a thread. If the host and port are not passed in, they default to
    "%s" and %s, respectively.

    If there's a callback function, it will call that once it starts the server. This is
    useful for taking an action like opening the site in a web browser once it is loaded.
    """ % (HOST, PORT)

    http_handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    logging.info("Starting local server")

    httpd = socketserver.TCPServer((HOST, PORT), http_handler)
    try:
        root = os.path.abspath(url_root)
        os.chdir(root)
        hostname = HOST
        if HOST == "":
            hostname = "localhost"
        url = "http://%s:%d/" % (hostname, PORT)

        if callback:
            logging.info("callback being called")
            timer = threading.Timer(1.0, callback, (url,))
            timer.start()

        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.socket.close()


class PEWMessageRequestHandler(BaseHTTPRequestHandler):
    handler = None

    def do_GET(self):
        global message_delegate
        if message_delegate and run_on_main_thread(message_delegate.parse_message, self.path):
            self.send_response(200)
        else:
            self.send_response(500)


class PEWMessageHandler:
    def __init__(self, webview, delegate):
        self.webview = webview
        self.delegate = delegate
        self.js_value = None
        self.message_received = False

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

        parts = urlparse(url)
        query = parts.query

        # On Android at least, Python puts the ?whatever part in path rather than query
        path = parts.path.split("?")
        if len(path) == 2 and not query:
            query = path[1]
        path = path[0][1:]

        func_name = parts.netloc
        if path != "":
            func_name += path.replace("/", ".")
        command = "%s" % func_name

        func_args = []
        func_kwargs = {}
        if query:
            args = query.split("&")
            for arg in args:
                arg = unquote(arg.encode('ascii'))
                logging.debug("arg = %s" % arg)
                #arg = arg.replace("\\", "\\\\")
                #arg = arg.replace("\\u", "\u")
                arg = arg.decode('utf-8')
                name = None
                value = arg

                if arg.find("=") != -1:
                    name, value = arg.split("=")

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

        try:
            function = eval(command)
            function(*func_args, **func_kwargs)
        except Exception as e:
            import traceback
            logging.error(traceback.format_exc())
            return False

        self.message_received = True
        return True

def get_app_dir():
    return os.path.dirname(sys.argv[0])

def get_files_dir():
    return os.path.join(get_app_dir(), 'files')

def get_user_dir():
    """
    Returns the user's home directory.
    """
    return os.getenv('EXTERNAL_STORAGE') or os.path.expanduser("~")

def get_user_path(app_name="python"):
    """
    Returns the folder where user data can be stored.
    """
    root = get_user_dir()
    ios = False
    try:
        import console
        import ui
        ios = True
    except:
        pass
    if not ios:
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
    global app_name

    if sys.platform.startswith("darwin"):
        return os.path.join(get_user_dir(), "Library", "Application Support", app_name)
    elif sys.platform.startswith("win"):
        app_files_dir = os.getenv('APPDATA')
        if app_files_dir is not None and os.path.exists(app_files_dir):
            return os.path.join(app_files_dir, app_name)
        else:
            return os.path.join(get_user_dir(), "Application Data", spp_name)

    # iOS and Android store documents inside their own special folders, 
    # so the directory is already app-specific
    return get_user_path(app_name)
