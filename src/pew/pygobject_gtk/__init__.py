import logging

import gi
gi.require_version('Gio', '2.0')
gi.require_version('Gtk', '3.0')
from gi.repository import Gio, Gtk


def run_on_main_thread(func, *args, **kwargs):
    return func(*args, **kwargs)


app = None


def choose_file(callback):
    print("choose_file", callback)


def show_save_file_dialog(options, callback):
    print("show_save_file_dialog", options, callbacK)


def get_app():
    return app


def set_fullscreen():
    if app and hasattr(app, 'webview'):
        app.webview.set_fullscreen()


class NativePEWApp(object):
    def __init__(self):
        global app
        app = self

        self.gtk_application = Gtk.Application()
        self.gtk_application.connect('activate', self.__on_activate)

        quit_action = Gio.SimpleAction.new('quit', None)
        quit_action.connect('activate', self.__on_quit_action_activate)
        self.gtk_application.add_action(quit_action)
        self.gtk_application.set_accels_for_action('app.quit', ['<Primary>q'])

        self.setUp()

    def shutdown(self):
        self.gtk_application.quit()

    def run(self):
        self.gtk_application.register()
        if self.view:
            self.gtk_application.add_window(self.view.window)
        self.gtk_application.run()

    def __on_activate(self, application):
        print("__on_activate", application)

    def __on_quit_action_activate(self, action, parameter):
        for window in self.windows:
            window.close()

from .menus import *
from .webview import *
