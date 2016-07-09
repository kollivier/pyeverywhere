from objc_util import *

app = None


def get_app():
    return app


# unlike Android and wx, there is no main App class in Pythonista
class NativePEWApp(object):
    @on_main_thread
    def run(self):
        global app
        app = self
        return self.setUp()

    def shutdown(self):
        pass  # closing the app programmatically isn't supported in Pythonista

from webview import *
