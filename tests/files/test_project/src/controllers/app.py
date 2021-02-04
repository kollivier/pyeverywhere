import json
import logging
import os
import sys

import pew


# Replace this with your app's root URL
APP_ROOT_URL = "https://google.com/"

# get the root src directory
thisdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pew.platform in ["mac", "win"] and hasattr(sys, "frozen"):
    thisdir = os.path.dirname(os.path.abspath(sys.argv[0]))

# in source builds, project_info.json is a directory above the sources, but
# in frozen apps it's in the same directory as all other resources.
json_dir = thisdir
if json_dir.endswith("src"):
    json_dir = os.path.dirname(json_dir)

info_json = json.loads(open(os.path.join(json_dir, "project_info.json"), "rb").read())


class Application(pew.PEWApp):
    def setUp(self):
        """
        Start your UI and app run loop here.
        """
        sys.excepthook = self.unhandled_exception

        self.webview = pew.WebUIView(info_json["name"], APP_ROOT_URL, "myapp", self)
        # make sure we show the UI before run completes, as otherwise
        # it is possible the run can complete before the UI is shown,
        # causing the app to shut down early
        self.webview.show()
        return 0

    def unhandled_exception(self, exc_type, value, trace):
        import traceback
        logging.error("Exception occurred?")
        error_text = '\n'.join(traceback.format_exception(type, value, trace))
        logging.error(error_text)
        # handle exception here, including showing UI dialogs if desired

    def get_main_window(self):
        return self.webview

    def load_complete(self):
        """
        Called when the UI is fully loaded and ready to accept JavaScript commands.
        """
        pass
