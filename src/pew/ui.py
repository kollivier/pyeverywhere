import logging
import six
import warnings

import pew.options as options


def check_platforms():
    errors = {}
    platforms = []

    try:
        import console
        import ui
        platforms.append('ios')
    except Exception as e:
        # Note that there is a strange issue in packaged apps where a global traceback
        # import is sometimes not seen in an except handler. So we import traceback
        # directly inside it to address this.
        import traceback
        errors['pythonista'] = traceback.format_exc()

    try:
        import jnius
        platforms.append('android')
    except Exception as e:
        import traceback
        errors['android'] = traceback.format_exc()

    try:
        import objc
        platforms.append('pyobjc')
    except Exception as e:
        import traceback
        errors['pyobjc'] = traceback.format_exc()

    try:
        import wx
        platforms.append('wx')
    except Exception as e:
        import traceback
        errors['wx'] = traceback.format_exc()

    try:
        import wx
        import cefpython3
        platforms.append('chromium')
    except Exception as e:
        import traceback
        errors['chromium'] = traceback.format_exc()

    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('WebKit2', '4.0')
        from gi.repository import Gtk, WebKit2
        platforms.append('gtk')
    except Exception as e:
        import traceback
        errors['gtk'] = traceback.format_exc()

    if len(platforms) == 0:
        message = "PyEverywhere could not load a browser for this platform."
        logging.error(message)
        for platform in errors:
            logging.error("Error loading {}".format(platform))
            logging.error(errors[platform])

        raise Exception(message)

    # reorder the platforms list so that preferred platforms come first
    if len(options.preferred_platforms) > 0:
        preferred = options.preferred_platforms
        preferred.reverse()
        for platform in options.preferred_platforms:
            if platform in platforms:
                platforms.insert(0, platforms.pop(platforms.index(platform)))

    return platforms

# we must load during init to create the native subclasses
platforms = check_platforms()

logging.debug("Found platforms: {}".format(platforms))
loaded = False
for platform in platforms:
    try:
        if platform == 'ios':
            from .pythonista import *
        elif platform == 'android':
            from .kivy_pew import *
        elif platform == 'pyobjc':
            from .pyobjc_pew import *
        elif platform in ['wx', 'chromium']:
            from .wxpy import *
        elif platform in ['gtk']:
            from .pygobject_gtk import *
        loaded = True
        break
    except Exception as e:
        import traceback
        logging.warning("Failed to load platform {}".format(platform))
        logging.warning(traceback.format_exc())

if not loaded:
    raise Exception("Error attempting to load a native web browser. See logs for details.")


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

    # Unique application ID
    # Set this to a value like "com.example.Application" in a subclass.
    application_id = None

    # Set to true if this application will accept file open requests from the
    # system.
    handles_open_file_uris = False

    def __init__(self):
        super(PEWApp, self).__init__()

    def init_ui(self):
        """
        Called by the application when it is ready to initialize the app's UI.

        Your subclass must implement this method and initialize a main window using `pew.ui.WebUIView`.

        It is expected that you will have a visible WebUIView by the time this method
        completes. If not, some platforms may shut down the app.
        """

        pass

    def handle_command_line(self, argv):
        """
        Implement command line processing for the application here.

        On some platforms, additional command line arguments may be passed to
        the application after it starts. This function runs before init_ui.
        Raising an Exception or SystemExit, such as with argparse, causes the
        application to exit early.
        """

        pass

    def handle_open_file_uris(self, files):
        """
        Implement file opening for the application here.

        On some platforms, additional file URIs may be passed to the application
        after it starts.
        """

        pass

    def setUp(self):
        self.init_ui()

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

    def __init__(self, name, url=None, protocol=None, delegate=None, size=(1024, 768)):
        """
        Creates a native WebUIView and accompanying UI window.

        :param name: window name, will show in the titlebar of platforms that have one
        :param url: URL of the HTML document containing the app's UI
        :param protcol: string designating the app protocol to use, e.g. myapp will result in myapp://message messages
        :param delegate: a Python object that will receive the messages sent from the web UI
        """
        super(WebUIView, self).__init__(name, size)

        self.protocol = protocol
        if protocol is not None:
            url = url + "?protocol=" + protocol
            if not "://" in protocol:
                self.protocol += "://"
        self.delegate = delegate

        self.page_loaded = False
        self.current_url = None

        # a list of JS calls made since app start so that we can do playback in a browser for testing.
        self.js_session_script = ""

        if url is not None:
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
        self.current_url = url
        super(WebUIView, self).load_url(url)

    def present_window(self):
        """
        Ask the desktop environment to bring this window to the user's attention.
        """
        super(WebUIView, self).present_window()

    def get_view_state(self):
        """
        Get any view or app state that was natively persisted by pause / resume actions.

        :return: A dictionary of persisted view or app state properties.
        """

        # not all backends implement this, so check that NativeWebView.get_persisted_state exists first
        if hasattr(self, 'get_persisted_state'):
            return self.get_persisted_state()

        return {}

    def show(self):
        """
        Makes the web view visible on screen.
        """
        super(WebUIView, self).show()

    def close(self):
        """
        Closes the webview, on platforms which support it.
        """
        super(WebUIView, self).close()

    def set_title(self, name):
        try:
            super(WebUIView, self).set_title(name)
        except:
            raise
        self.webview.set_user_agent(self.webview.get_user_agent() + " / " + name)

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
            if isinstance(arg, six.string_types):
                arg = "'%s'" % arg.replace("'", "\\'").encode("utf-8")
            else:
                arg = "%s" % str(arg)
            args.append(arg)

        js = "%s(%s);" % (function_name, ','.join(args))
        self.js_session_script += js + "\n"

        self.evaluate_javascript(js)

    def get_js_session_script(self):
        return self.js_session_script

    def shutdown(self):
        if self.delegate is not None:
            self.delegate.shutdown()

    def webview_should_start_load(self, webview, url, nav_type):
        if self.protocol is not None and self.delegate is not None and url.startswith(self.protocol):
            return not self.delegate.parse_message(url)

        if self.delegate and hasattr(self.delegate, "should_load_url"):
            return self.delegate.should_load_url(url)

        return True

    def webview_did_start_load(self, webview, url=None):
        pass

    def webview_did_finish_load(self, webview, url=None):
        if not self.page_loaded:
            logging.info("Page loaded = %r, url = %r, current_url = %r" % (self.page_loaded, url, self.current_url))
            self.page_loaded = True
            if self.protocol is not None:
                webview.evaluate_javascript("bridge.setProtocol('%s')" % self.protocol)
            if self.delegate and hasattr(self.delegate, 'load_complete'):
                self.delegate.load_complete()

        if self.delegate and hasattr(self.delegate, "page_loaded"):
            self.delegate.page_loaded(url)

    def webview_did_fail_load(self, webview, error_code, error_msg):
        self.page_loaded = True  # make sure we don't wait forever if the page fails to load
