import atexit
import logging
import os
import platform
import sys
import threading

import wx

from cefpython3 import cefpython
WindowUtils = cefpython.WindowUtils()

# Note: this works because we don't import pew UI submodules during initial module load.
# if that changes, we'll need to rework this.
import pew

from ..interfaces import WebViewInterface

MAC = sys.platform.startswith('darwin')

chrome_settings = {
    "debug": True,
    "log_severity": cefpython.LOGSEVERITY_INFO,
    "log_file": os.path.join(pew.get_app_files_dir(), "chromium.log"),
#    "log_severity": cefpython.LOGSEVERITY_INFO,
#    "release_dcheck_enabled": True, # Enable only when debugging.
#    "browser_subprocess_path": "%s/%s" % (
#        cefpython.GetModuleDirectory(), "subprocess")
}
if MAC:
    cefpython_dir = os.path.dirname(os.path.abspath(cefpython.__file__))
    cef_framework_dir = os.path.join(cefpython_dir, 'Chromium Embedded Framework.framework')
    chrome_settings['external_message_pump'] = True
    chrome_settings['framework_dir_path'] = cef_framework_dir
    chrome_settings['resources_dir_path'] = os.path.join(cef_framework_dir, 'Resources')
    chrome_settings["browser_subprocess_path"] = os.path.join(cefpython_dir, 'subprocess')

class ClientHandler:
    # --------------------------------------------------------------------------
    # RequestHandler
    # --------------------------------------------------------------------------
    onload_handled = False
    def OnBeforeBrowse(self, browser, frame, request, user_gesture, is_redirect):
        # - frame.GetUrl() returns current url
        # - request.GetUrl() returns new url
        # - Return true to cancel the navigation or false to allow
        # the navigation to proceed.
        if self.callback is not None:
            return not self.callback(request.GetUrl())
        return False


    def OnKeyEvent(self, browser, event, event_handle):
        """
        The Mac version is supposed to have handling for cut/copy/paste shortcuts, but
        they are not functioning properly, so we add our own implementation here.
        """
        if MAC:
            if event["modifiers"] == 128 and event["type"] != cefpython.KEYEVENT_RAWKEYDOWN:
                if event["native_key_code"] in [7, 8, 9]:
                    return True

            if event["modifiers"] == 128 and event["type"] == cefpython.KEYEVENT_RAWKEYDOWN:
                if event["native_key_code"] == 7:
                    browser.GetFocusedFrame().Cut()
                    return True

                if event["native_key_code"] == 8:
                    browser.GetFocusedFrame().Copy()
                    return True

                elif event["native_key_code"] == 9:
                    browser.GetFocusedFrame().Paste()
                    return True

        return False


@atexit.register
def ShutDown():
    logging.info("Shutting down")
    cefpython.Shutdown()

logging.info("Initializing WebView?")

PEWThread = threading.Thread


class NativeWebView(WebViewInterface):
    def __init__(self, name="WebView", size=(1024, 768)):
        self.webview = None
        cefpython.Initialize(chrome_settings)

        self.view = wx.Frame(None, -1, name, size=size)

        self.browser_panel = wx.Panel(self.view, style=wx.WANTS_CHARS)
        self.browser_panel.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.browser_panel.Bind(wx.EVT_SIZE, self.OnSize)

        # self.browser_panel = wx.Panel(self.view, style=wx.WANTS_CHARS)
        self.browser_panel.Bind(wx.EVT_SIZE, self.OnSize)
        self.browser_panel.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)

        if MAC:
            try:
                # noinspection PyUnresolvedReferences
                from AppKit import NSApp
                # Make the content view for the window have a layer.
                # This will make all sub-views have layers. This is
                # necessary to ensure correct layer ordering of all
                # child views and their layers. This fixes Window
                # glitchiness during initial loading on Mac (Issue #371).
                NSApp.windows()[0].contentView().setWantsLayer_(True)
            except ImportError:
                logging.error("PyObjC needs to be installed to use Chromium on Mac.")

        window_info = cefpython.WindowInfo()
        settings = {
            'dom_paste_disabled': False
        }
        (width, height) = self.browser_panel.GetClientSize().Get()
        window_info.SetAsChild(self.browser_panel.GetHandle(),
                               [0, 0, width, height])
        self.webview = cefpython.CreateBrowserSync(window_info, settings=settings,
                                             url="about:blank")

        client = ClientHandler()
        self.webview.SetClientHandler(client)
        client.callback = self.HandleURL

        self.timer = None
        self.create_timer()

        self.view.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnSize(self, event):
        logging.info("OnSize called...")
        if not self.webview:
            return
        if platform.system() == "Windows":
            WindowUtils.OnSize(self.browser_panel.GetHandle(),
                               0, 0, 0)
        elif platform.system() == "Linux":
            (x, y) = (0, 0)
            (width, height) = self.browser_panel.GetSize().Get()
            self.webview.SetBounds(x, y, width, height)
        self.webview.NotifyMoveOrResizeStarted()

    def OnSetFocus(self, _):
        if not self.webview:
            return
        if platform.system() == "Windows":
            WindowUtils.OnSetFocus(self.browser_panel.GetHandle(),
                                   0, 0, 0)
        self.webview.SetFocus(True)

    def create_timer(self):
        # See also "Making a render loop":
        # http://wiki.wxwidgets.org/Making_a_render_loop
        # Another way would be to use EVT_IDLE in MainFrame.
        self.timer = wx.Timer(self.view, -1)
        self.view.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(10)  # 10ms timer

    def on_timer(self, event):
        cefpython.MessageLoopWork()

    def show(self):
        self.view.Show()

    def set_fullscreen(self, enable=True):
        self.view.ShowFullScreen(enable)

    def set_window_title(self, title):
        self.view.SetTitle(title)

    def load_url(self, url):
        self.webview.LoadUrl(url)

    def get_user_agent(self):
        return ""

    def set_user_agent(self, user_agent):
        pass

    def set_menubar(self, menubar):
        self.view.SetMenuBar(menubar.native_object)

    def reload(self):
        self.webview.Reload()

    def go_back(self):
        self.webview.GoBack()

    def go_forward(self):
        self.webview.GoForward()

    def clear_history(self):
        pass

    def get_url(self):
        return self.webview.GetUrl()

    def evaluate_javascript(self, js):
        self.webview.GetMainFrame().ExecuteJavascript(js)

    def OnClose(self, event):
        logging.info("OnClose called...")
        if self.timer:
            self.timer.Stop()
        if self.webview:
            self.webview.ParentWindowWillClose()
            self.webview = None

        event.Skip()

    def HandleURL(self, url):
        #self.evaluate_javascript("$('#search_bar').val('%s');" % url)
        return self.webview_should_start_load(self, url, None)

    def OnLoadComplete(self, event):
        return self.webview_did_finish_load(self)

    def OnLoadStateChanged(self, event):
        if event.GetState() == wx.webkit.WEBKIT_STATE_STOP:
            return self.OnLoadComplete(event)
