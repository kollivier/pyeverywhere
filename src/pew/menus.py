

class PEWMenuItemBase:
    def __init__(self, title, handler, shortcut=None):
        self.title = title
        self.shortcut = shortcut
        self.handler = handler
        self.native_object = None


class PEWMenuBase:
    def __init__(self, title):
        self.title = title
        self.items = []
        self.native_object = None

    def add_item(self, menu_item):
        self.items.append(menu_item)


class PEWMenuBarBase:
    def __init__(self):
        self.menus = []
        self.native_object = None

    def add_menu(self, menu):
        self.menus.append(menu)
