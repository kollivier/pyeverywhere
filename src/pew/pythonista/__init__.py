import urllib

from objc_util import *

# This is used by pew when creating launch image Info.plist entries, as
# it needs a separate entry for each device using that device's dimensions
# more info here:
# http://stackoverflow.com/questions/25926661/how-do-i-create-launch-images-for-iphone-6-6-plus-landscape-only-apps
device_sizes = {
    'iPhone 6': (1334, 750),
    'iPhone 6 Plus': (2208, 1242),
}

app = None


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

from webview import *
