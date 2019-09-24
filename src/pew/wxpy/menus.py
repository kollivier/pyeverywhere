import wx

from ..menus import PEWMenuBase
from ..menus import PEWMenuBarBase
from ..menus import PEWMenuItemBase


class PEWMenuItem(PEWMenuItemBase):
    def __init__(self, title, handler, shortcut=None):
        super(PEWMenuItem, self).__init__(title, handler, shortcut)
        text = self.title
        if self.shortcut is not None:
            text += "\t{}".format(self.shortcut)
        self.native_title = text

    def bind(self):
        self.native_object.GetMenu().Bind(wx.EVT_MENU, self.call_handler, self.native_object)

    def call_handler(self, event):
        self.handler()


class PEWMenu(PEWMenuBase):
    def __init__(self, title):
        super(PEWMenu, self).__init__(title)
        # we add the title in PEWMenuBar.add_item
        self.native_object = wx.Menu()

    def add_item(self, item):
        super(PEWMenu, self).add_item(item)
        print("item = {}".format(item.native_object))
        item.native_object = self.native_object.Append(wx.NewId(), item.native_title)
        item.bind()


class PEWMenuBar(PEWMenuBarBase):
    def __init__(self):
        super(PEWMenuBar, self).__init__()
        self.native_object = wx.MenuBar()

    def add_menu(self, menu):
        super(PEWMenuBar, self).add_menu(menu)
        self.native_object.Append(menu.native_object, menu.title)
