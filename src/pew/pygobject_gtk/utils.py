import string

import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk


def _gdk_key_names():
    for ascii_char in string.printable:
        gdk_keyval = Gdk.unicode_to_keyval(ord(ascii_char))
        gdk_key_name = Gdk.keyval_name(gdk_keyval)
        yield ascii_char, gdk_key_name


GDK_KEY_NAMES = dict(_gdk_key_names())


def normalize_gdk_key_name(key_name):
    if key_name in GDK_KEY_NAMES:
        return GDK_KEY_NAMES[key_name]

    gdk_keyval = Gdk.keyval_from_name(key_name)

    if gdk_keyval == Gdk.KEY_VoidSymbol:
        return None

    return Gdk.keyval_name(gdk_keyval)
