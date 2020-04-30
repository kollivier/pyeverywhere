import logging
import threading

from enum import Enum

from ..interfaces import WebViewInterface

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gdk, Gtk, WebKit2


PEWThread = threading.Thread


class NativeWebView(WebViewInterface):
    ZOOM_INCREMENTS = {
        0: 0.5,
        1: 0.75,
        2: 1.0,
        3: 1.25,
        4: 1.5
    }

    def __init__(self, name="WebView", size=(1024, 768)):
        self.default_zoom_increment = self.current_zoom_increment = 2
        self.__name = name
        self.__size_width, self.__size_height = size

        self.__gtk_window = None
        self.__gtk_header_bar = Gtk.HeaderBar(
            spacing=6,
            title=name,
            show_close_button=True
        )

        self.__gtk_menu_button = Gtk.MenuButton(
            direction=Gtk.ArrowType.NONE
        )
        self.__gtk_header_bar.pack_end(self.__gtk_menu_button)
        
        self.__gtk_webview = WebKit2.WebView()
        self.__gtk_webview.connect(
            'decide-policy',
            self.__gtk_webview_on_decide_policy
        )
        self.__gtk_webview.connect(
            'load-changed',
            self.__gtk_webview_on_load_changed
        )
        self.__gtk_webview.connect(
            'notify::title',
            self.__gtk_webview_on_notify_title
        )

    @property
    def window(self):
        return self.gtk_window

    @property
    def default_zoom(self):
        return self.default_zoom_increment

    @property
    def gtk_application(self):
        return self.delegate.gtk_application

    @property
    def gtk_window(self):
        # Defer creating gtk_window since we need self.delegate to be set

        if self.__gtk_window:
            return self.__gtk_window

        gtk_window = Gtk.ApplicationWindow(application=self.gtk_application)
        gtk_window.connect('destroy', self.__gtk_window_on_destroy)
        gtk_window.set_titlebar(self.__gtk_header_bar)
        gtk_window.set_default_size(self.__size_width, self.__size_height)
        gtk_window.add(self.__gtk_webview)
        self.__gtk_window = gtk_window

        return gtk_window

    def show(self):
        self.gtk_window.show_all()

    def close(self):
        self.gtk_window.close()

    def reload(self):
        self.__gtk_webview.reload()

    def set_fullscreen(self, enable=True):
        if enable:
            self.gtk_window.fullscreen()
        else:
            self.gtk_window.unfullscreen()

    def set_menubar(self, menubar):
        application = self.gtk_window.get_application()

        self.menu_popover = Gtk.Popover.new_from_model(
            self.__gtk_menu_button,
            menubar.gio_menu
        )
        menubar.gtk_connect_actions(application, self.gtk_window)

        self.__gtk_menu_button.set_popover(self.menu_popover)

    def load_url(self, url):
        self.__gtk_webview.load_uri(url)

    def present_window(self):
        if self.__gtk_window and self.__gtk_window.get_realized():
            self.__gtk_window.present_with_time(Gdk.CURRENT_TIME)

    def get_zoom_level(self):
        # Public interface actually speaks in zoom increments, not webkit's
        # fractional zoom levels.
        return self.current_zoom_increment

    def set_zoom_level(self, zoom_increment):
        # Translate integer zoom increment to a fractional zoom level used
        # internally for webkit.
        zoom_level = self.ZOOM_INCREMENTS.get(zoom_increment, None)
        if zoom_level:
            self.current_zoom_increment = zoom_increment
            self.__gtk_webview.set_zoom_level(zoom_level)

    def get_user_agent(self):
        settings = self.__gtk_webview.get_settings()
        return settings.get_user_agent()

    def set_user_agent(self, user_agent):
        settings = self.__gtk_webview.get_settings()
        settings.set_user_agent(user_agent)

    def get_url(self):
        return self.__gtk_webview.get_uri()

    def clear_history(self):
        # This is unsupported in the current version of WebKitGTK
        pass

    def go_back(self):
        self.__gtk_webview.go_back()

    def go_forward(self):
        self.__gtk_webview.go_forward()

    def evaluate_javascript(self, js):
        self.__gtk_webview.run_javascript(js)

    def __gtk_window_on_destroy(self, window):
        self.shutdown()

    def __gtk_webview_on_decide_policy(self, webview, decision, decision_type):
        if decision_type == WebKit2.PolicyDecisionType.NAVIGATION_ACTION:
            target_uri = decision.get_request().get_uri()
            if not self.webview_should_start_load(self, target_uri, None):
                decision.ignore()
                return True

        return False

    def __gtk_webview_on_load_changed(self, webview, load_event):
        if load_event == WebKit2.LoadEvent.FINISHED:
            if not self.current_zoom_increment == self.default_zoom_increment:
                self.set_zoom_level(self.current_zoom_increment)
            self.webview_did_finish_load(self)

    def __gtk_webview_on_notify_title(self, webview, param):
        pass

