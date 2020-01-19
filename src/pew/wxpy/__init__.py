import logging
import wx

from .. import get_app_name


def run_on_main_thread(func, *args, **kwargs):
    wx.CallAfter(func, *args, **kwargs)


app = None


def choose_file(callback):
    picked_file = None
    if app and app.GetTopWindow():
        def call_file_dialog(callback):
            dlg = wx.FileDialog(app.GetTopWindow(), "Select a file to open")
            result = dlg.ShowModal()
            if result != wx.ID_CANCEL:
                callback(dlg.GetPath())
            else:
                callback(None)
        run_on_main_thread(call_file_dialog, callback)
    else:
        logging.warning("choose_file called without a fully initialized app")

    return picked_file


def show_save_file_dialog(options, callback):
    if app and app.GetTopWindow():
        def call_file_dialog(options, callback):

            wildcards = []
            if 'types' in options:
                types = options['types']
                for type_name in types:
                    wildcards.append("{}(*.{})|*.{}".format(type_name, types[type_name], types[type_name]))
            wildcard = '|'.join(wildcards)
            logging.debug("wildcard = {}".format(wildcard))
            dlg = wx.FileDialog(app.GetTopWindow(), "Save file as...", defaultFile="", wildcard = wildcard, style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
            result = dlg.ShowModal()
            if result != wx.ID_CANCEL:
                callback(dlg.GetPath())
            else:
                callback(None)
        run_on_main_thread(call_file_dialog, options, callback)
    else:
        logging.warning("choose_file called without a fully initialized app")



def get_app():
    return app


def set_fullscreen():
    if app and hasattr(app, 'webview'):
        app.webview.set_fullscreen()


class NativePEWApp(wx.App):
    def OnInit(self):
        global app
        app = self
        self.SetAppName(get_app_name())
        self.setUp()
        return True

    def shutdown(self):
        self.ExitMainLoop()

    def run(self):
        self.MainLoop()

from .menus import *

try:
    from .webview_chromium import *
except Exception as e:
    import traceback
    logging.warning(traceback.format_exc())
    logging.warning("Chromium not found, loading wxWebView instead.")
    from .webview import *
