import logging
import sys
import wx

from ..menus import PEWMenuBase
from ..menus import PEWMenuBarBase
from ..menus import PEWMenuItemBase
from ..menus import PEWShortcut


def get_logger():
    return logging.getLogger("pew[wx]")


command_id_mapping = {
    'copy': wx.ID_COPY,
    'cut': wx.ID_CUT,
    'paste': wx.ID_PASTE,
    'redo': wx.ID_REDO,
    'select-all': wx.ID_SELECTALL,
    'undo': wx.ID_UNDO
}

class PEWMenuItem(PEWMenuItemBase):
    def __init__(self, title, handler=None, command=None, shortcut=None):
        super(PEWMenuItem, self).__init__(title, handler, command, shortcut)
        text = self.title
        if self.shortcut is not None:
            shortcut = self.shortcut
            if isinstance(shortcut, PEWShortcut):
                native_shortcut = shortcut.key
                if len(shortcut.modifiers) > 0:
                    native_shortcut = "{}-{}".format('+'.join(shortcut.modifiers), shortcut.key)
                shortcut = native_shortcut
            else:
                log = get_logger()
                log.warning("Keyboard shortcut {} is not using PEWShortcut.".format(shortcut))
                log.warning("Text shortcuts are deprecated. Please use PEWShortcut to create keyboard shortcuts.")
                log.warning("Support for text shortcuts will be removed in v1.0")
            text += "\t{}".format(shortcut)
        self.native_title = text

    def bind(self):
        if self.handler:
            self.native_object.GetMenu().Bind(wx.EVT_MENU, self.call_handler, self.native_object)

    def call_handler(self, event):
        self.handler()


class PEWMenu(PEWMenuBase):
    def __init__(self, title):
        super(PEWMenu, self).__init__(title)
        # we add the title in PEWMenuBar.add_item
        self.native_object = wx.Menu()

    def add(self, title, handler=None, command=None, shortcut=None):
        new_item = PEWMenuItem(title, handler, command, shortcut)
        self.add_item(new_item)

    def add_item(self, item):
        super(PEWMenu, self).add_item(item)
        item_id = wx.NewId()
        if item.command and item.command in command_id_mapping:
            item_id = command_id_mapping[item.command]
        item.native_object = self.native_object.Append(item_id, item.native_title)
        item.bind()

    def add_separator(self):
        self.native_object.AppendSeparator()


class PEWMenuBar(PEWMenuBarBase):
    def __init__(self):
        super(PEWMenuBar, self).__init__()
        self.native_object = wx.MenuBar()

    def add_menu(self, menu):
        super(PEWMenuBar, self).add_menu(menu)
        self.native_object.Append(menu.native_object, menu.title)
