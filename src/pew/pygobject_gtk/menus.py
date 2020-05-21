import logging
import string
import sys
from itertools import chain

from ..menus import PEWMenuBase
from ..menus import PEWMenuBarBase
from ..menus import PEWMenuItemBase
from ..menus import PEWShortcut

from .utils import normalize_gdk_key_name

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio


def get_logger():
    return logging.getLogger("pew[gtk]")


class PEWMenuItem(PEWMenuItemBase):
    def __init__(self, title, handler=None, command=None, shortcut=None):
        super(PEWMenuItem, self).__init__(title, handler, command, shortcut)

        self.__gio_action = Gio.SimpleAction(name=self.gio_action_name)

        if handler:
            self.__gio_action.connect('activate', self.__on_menu_item_activate)
            self.__gio_action.set_enabled(True)
        else:
            self.__gio_action.set_enabled(False)

        self.__gtk_accels = self.__get_gtk_accels()

        self.__gio_menu_item = Gio.MenuItem()
        self.__gio_menu_item.set_label(title)
        self.__gio_menu_item.set_detailed_action(self.gio_window_action_name)

    @property
    def gio_action_name(self):
        return 'pew-action-{}'.format(id(self))

    @property
    def gio_window_action_name(self):
        return 'win.'+self.gio_action_name

    @property
    def gio_action(self):
        return self.__gio_action

    @property
    def gio_menu_item(self):
        return self.__gio_menu_item

    @property
    def native_object(self):
        return self.__gio_menu_item

    @property
    def gtk_accels(self):
        return self.__gtk_accels

    @native_object.setter
    def native_object(self, value):
        self.__gio_menu_item = value

    def __on_menu_item_activate(self, action, parameter):
        self.handler()

    def __get_gtk_accels(self):
        if not self.shortcut:
            return []
        elif not isinstance(self.shortcut, PEWShortcut):
            log = get_logger()
            log.warning("Keyboard shortcut {} is not using PEWShortcut.".format(self.shortcut))
            log.warning("Text shortcuts are deprecated. Please use PEWShortcut to create keyboard shortcuts.")
            log.warning("Support for text shortcuts will be removed in v1.0")
            return []
        else:
            gdk_key_name = normalize_gdk_key_name(self.shortcut.key)
            gdk_modifiers = ''.join(
                map(lambda modifier: "<{}>".format(modifier), self.shortcut.modifiers)
            )

            if gdk_key_name is None:
                log = get_logger()
                log.warning("Keyboard shortcut {} contains an unknown key name".format(self.shortcut))
                return []

            return ["{}{}".format(gdk_modifiers, gdk_key_name)]



class PEWMenu(PEWMenuBase):
    def __init__(self, title):
        super(PEWMenu, self).__init__(title)
        self.__gio_menu = Gio.Menu()

    @property
    def gio_menu(self):
        return self.__gio_menu

    @property
    def native_object(self):
        return self.__gio_menu

    @native_object.setter
    def native_object(self, value):
        self.__gio_menu = value

    def add(self, title, handler=None, command=None, shortcut=None):
        new_item = PEWMenuItem(title, handler, command, shortcut)
        self.add_item(new_item)

    def add_item(self, item):
        super(PEWMenu, self).add_item(item)
        self.__gio_menu.append_item(item.gio_menu_item)

    def add_separator(self):
        pass


class PEWMenuBar(PEWMenuBarBase):
    def __init__(self):
        super(PEWMenuBar, self).__init__()
        self.__gio_menu = Gio.Menu()

    @property
    def gio_menu(self):
        return self.__gio_menu

    @property
    def native_object(self):
        return self.__gio_menu

    @native_object.setter
    def native_object(self, value):
        self.__gio_menu = value

    def add_menu(self, menu):
        super(PEWMenuBar, self).add_menu(menu)

        if self.__gio_menu.get_n_items() == 0:
            # The first submenu is special and doesn't have a heading
            section_label = None
        else:
            section_label = menu.title

        self.__gio_menu.append_section(
            section_label,
            menu.gio_menu
        )

    def gtk_connect_actions(self, gtk_application, gtk_window):
        for menu_item in self.__iter_menu_items():
            gtk_window.add_action(menu_item.gio_action)
            gtk_application.set_accels_for_action(
                menu_item.gio_window_action_name,
                menu_item.gtk_accels
            )

    def __iter_menu_items(self):
        return chain.from_iterable(menu.items for menu in self.menus)

