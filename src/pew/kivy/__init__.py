from android.runnable import run_on_ui_thread

@run_on_ui_thread
def run_on_main_thread(func, *args, **kwargs):
    func(*args, **kwargs)

from webview import *