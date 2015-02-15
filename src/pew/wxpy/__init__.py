import wx

def run_on_main_thread(func, *args, **kwargs):
    wx.CallAfter(func, *args, **kwargs)

from webview import *