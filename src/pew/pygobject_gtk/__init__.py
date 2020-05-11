import logging
import marshal
import os
import sys

import gi
gi.require_version('Gio', '2.0')
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import GLib, Gio, Gtk, WebKit2


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
        top_window = app.gtk_get_top_window()
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
        top_window = app.gtk_get_top_window()
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

        application_flags = Gio.ApplicationFlags.HANDLES_COMMAND_LINE
        if self.handles_open_file_uris:
            application_flags |= Gio.ApplicationFlags.HANDLES_OPEN

        self.__gtk_application = Gtk.Application.new(
            self.application_id,
            application_flags
        )
        self.__gtk_application.connect('startup', self.__on_startup)
        self.__gtk_application.connect('activate', self.__on_activate)
        self.__gtk_application.connect('command-line', self.__on_command_line)
        self.__gtk_application.connect('open', self.__on_open)
        self.__gtk_application.connect('shutdown', self.__on_shutdown)

        quit_action = Gio.SimpleAction.new('quit', None)
        quit_action.connect('activate', self.__on_quit_action_activate)
        self.__gtk_application.add_action(quit_action)
        self.__gtk_application.set_accels_for_action('app.quit', ['<Primary>q'])

        self.__webkit_web_context = None

    def run(self):
        self.__gtk_application.run(sys.argv)

    def shutdown(self):
        # No-op. GTK main loop will shut itself down and call this function.
        # This can be overrided to add additional cleanups.
        pass

    @property
    def user_data_directory(self):
        base_dir = GLib.get_user_data_dir()
        application_id = getattr(self, 'application_id')
        if application_id:
            return os.path.join(base_dir, application_id)
        else:
            return None

    @property
    def gtk_application(self):
        return self.__gtk_application

    @property
    def webkit_web_context(self):
        if self.__webkit_web_context:
            return self.__webkit_web_context

        if self.user_data_directory:
            website_data_manager = WebKit2.WebsiteDataManager(base_data_directory=self.user_data_directory)
        else:
            website_data_manager = None

        webkit_web_context = WebKit2.WebContext(website_data_manager=website_data_manager)

        if self.user_data_directory:
            cookies_filename = os.path.join(self.user_data_directory, 'cookies.sqlite')
            cookie_manager = webkit_web_context.get_cookie_manager()
            cookie_manager.set_accept_policy(WebKit2.CookieAcceptPolicy.NO_THIRD_PARTY)
            cookie_manager.set_persistent_storage(cookies_filename, WebKit2.CookiePersistentStorage.SQLITE)

        self.__webkit_web_context = webkit_web_context

        return webkit_web_context

    def gtk_get_top_window(self):
        return self.__gtk_application.get_active_window()

    def __gtk_present_top_window(self):
        active_window = self.gtk_get_top_window()
        if active_window:
            active_window.present()

    def __on_startup(self, application):
        pass

    def __on_activate(self, application):
        self.init_ui()
        self.__gtk_present_top_window()

    def __on_command_line(self, application, command_line):
        # Run self.init_ui after processing local command line. This allows
        # applications to exit cleanly (before init_ui has been run) in
        # response to command line arguments.

        try:
            argv = command_line.get_arguments()[1:]
            self.handle_command_line(argv)
        except SystemExit as exit:
            return exit.code
        except Exception as error:
            logging.warning("Error handling command line", error)
            return 1

        application.activate()

        return 0

    def __on_open(self, application, files, n_files, hint):
        file_uris = [f.get_uri() for f in files]
        self.handle_open_file_uris(file_uris)

    def __on_shutdown(self, application):
        self.shutdown()

    def __on_quit_action_activate(self, action, parameter):
        for window in self.__gtk_application.get_windows():
            window.close()

from .menus import *
from .webview import *
