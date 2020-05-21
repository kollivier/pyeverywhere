import logging

from .constants import KEY_MODIFIERS


class PEWMenuItemBase:
    def __init__(self, title, handler=None, command=None, shortcut=None):
        self.command = command
        self.title = title
        self.shortcut = shortcut
        self.handler = handler
        self.native_object = None


class PEWMenuBase:
    def __init__(self, title):
        self.title = title
        self.items = []
        self.native_object = None

    def add(self, title, handler=None, command=None, shortcut=None):
        new_item = PEWMenuItemBase(title, handler, command, shortcut)
        self.add_item(new_item)

    def add_item(self, menu_item):
        self.items.append(menu_item)

    def add_separator(self):
        pass


class PEWMenuBarBase:
    def __init__(self):
        self.menus = []
        self.native_object = None

    def add_menu(self, menu):
        self.menus.append(menu)


class PEWShortcut:
    def __init__(self, key, modifiers=tuple()):
        self.key = key

        if all(modifier in KEY_MODIFIERS for modifier in modifiers):
            self.modifiers = modifiers
        else:
            logging.warning("Unsupported modifier in list:", modifiers)
            self.modifiers = tuple()

    def __str__(self):
        if self.modifiers:
            return '{}-{}'.format('+'.join(self.modifiers), self.key)
        else:
            return self.key
