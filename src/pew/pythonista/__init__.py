import urllib

from objc_util import *

app = None


def set_fullscreen():
    pass


@on_main_thread
def run_on_main_thread(func, *args, **kwargs):
    func(*args, **kwargs)


def get_app():
    return app


def get_resource_url(resource_path):
    resource_dir = str(ObjCClass('NSBundle').mainBundle().resourcePath())
    return "file://%s" % urllib.quote(os.path.join(resource_dir, resource_path))


# unlike Android and wx, there is no main App class in Pythonista
class NativePEWApp(object):
    @on_main_thread
    def run(self):
        global app
        app = self
        return self.setUp()

    def shutdown(self):
        pass  # closing the app programmatically isn't supported in Pythonista

from .menus import *
from .webview import *
