import logging
import marshal

import gi
gi.require_version('Gio', '2.0')
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk


app = None


def run_on_main_thread(func, *args, **kwargs):
    def source_fn(*args, **kwargs):
        func(*args, **kwargs)
        return False

    data = (args, kwargs)
    main_context = GLib.MainContext.default()
    main_context.invoke_full(GLib.PRIORITY_DEFAULT, source_fn, *args, **kwargs)
    return None


def choose_file(callback):
    if app:
        top_window = app.get_top_window()
    else:
        top_window = None

    if not top_window:
        logging.warning("choose_file called without a fully initialized app")

    def run_open_file_dialog(callback):
        file_chooser = Gtk.FileChooserNative.new(
            "Open File", top_window, Gtk.FileChooserAction.OPEN, None, None
        )
        response = file_chooser.run()
        if response == Gtk.ResponseType.ACCEPT:
            callback(file_chooser.get_filename())
        else:
            callback(None)

    run_on_main_thread(run_open_file_dialog, callback)


def show_save_file_dialog(options, callback):
    if app:
        top_window = app.get_top_window()
    else:
        top_window = None

    if not top_window:
        logging.warning("show_save_file_dialog called without a fully initialized app")

    def run_save_file_dialog(options, callback):
        file_chooser = Gtk.FileChooserNative.new(
            "Save File", top_window, Gtk.FileChooserAction.SAVE, None, None
        )
        types = options.get('types', {})
        for type_name, type_extension in types.items():
            file_filter = Gtk.FileFilter.new()
            file_filter.set_name(type_name)
            file_filter.add_pattern('*.{}'.format(type_extension))
            file_chooser.add_filter(file_filter)
        response = file_chooser.run()
        if response == Gtk.ResponseType.ACCEPT:
            callback(file_chooser.get_filename())
        else:
            callback(None)

    run_on_main_thread(run_save_file_dialog, options, callback)


def get_app():
    return app


def set_fullscreen():
    if app and hasattr(app, 'webview'):
        app.webview.set_fullscreen()


class NativePEWApp(object):
    def __init__(self):
        global app
        app = self

        self.__gtk_application = Gtk.Application.new(
            self.application_id,
            Gio.ApplicationFlags.FLAGS_NONE
        )
        self.__gtk_application.connect('activate', self.__on_activate)

        quit_action = Gio.SimpleAction.new('quit', None)
        quit_action.connect('activate', self.__on_quit_action_activate)
        self.__gtk_application.add_action(quit_action)
        self.__gtk_application.set_accels_for_action('app.quit', ['<Primary>q'])

        self.setUp()

    @property
    def gtk_application(self):
        return self.__gtk_application

    def get_top_window(self):
        return self.__gtk_application.get_active_window()

    def shutdown(self):
        self.__gtk_application.quit()

    def run(self):
        if not self.__gtk_application.register():
            logging.warning("Registration failed")

        if self.__gtk_application.get_is_remote():
            self.__gtk_application.activate()
            return

        if self.view:
            self.__gtk_application.add_window(self.view.window)

        self.__gtk_application.run()

    def __on_activate(self, application):
        active_window = self.__gtk_application.get_active_window()
        if active_window:
            active_window.present()

    def __on_quit_action_activate(self, action, parameter):
        for window in self.windows:
            window.close()

from .menus import *
from .webview import *
