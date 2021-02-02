from ..menus import PEWMenuBase
from ..menus import PEWMenuBarBase
from ..menus import PEWMenuItemBase
from ..menus import PEWShortcut


# iOS apps don't have menus, so use these stub classes for cross-platform code
PEWMenu = PEWMenuBase
PEWMenuBar = PEWMenuBarBase
PEWMenuBarItem = PEWMenuItemBase
