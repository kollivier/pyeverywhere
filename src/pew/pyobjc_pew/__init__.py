import logging

import objc

import AppKit
import PyObjCTools.AppHelper


def run_on_main_thread(func, *args, **kwargs):
    PyObjCTools.AppHelper.callAfter(func, *args, **kwargs)

app = None


def get_app():
    return app


def get_resource_url(url):
    return "file://%s" % url


class AppDelegate (AppKit.NSObject):
    def applicationDidFinishLaunching_(self, aNotification):
        pass


class NativePEWApp(object):
    def __init__(self):
        global app
        app = self
        self.nativeApp = AppKit.NSApplication.sharedApplication()
        self.setUp()

    def run(self):
        self.nativeApp.run()

    def shutdown(self):
        pass  # I don't think this is supported natively with Kivy

    def on_pause(self):
        logging.info("on_pause called...")
        # Here you can save data if needed
        return True

    def on_stop(self):
        logging.info("on_stop called...")
        self.shutdown()

    def on_resume(self):
        # Here you can check if any data needs replacing (usually nothing)
        pass


from webview import *
