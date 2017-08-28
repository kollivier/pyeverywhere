import json
import logging
import os
import random
import sys
import urllib
import webbrowser

import pew

import models.mpquotes

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

        index = os.path.abspath(os.path.join(thisdir, "files", "web", "index.html"))
        try:
            url = "file://%s" % urllib.parse.quote(index)
        except ImportError:
            url = "file://%s" % urllib.quote(index)
        logging.debug("url: %r" % url)
        if not os.path.exists(index):
            raise Exception("Unable to load UI file")
        self.webview = pew.WebUIView(info_json["name"], url, "myapp", self)
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

    def make_it_so(self):
        self.webview.call_js_function("this_just_in", models.mpquotes.get_random_quote())

    def load_complete(self):
        """
        Called when the UI is fully loaded and ready to accept JavaScript commands.
        """
        self.webview.call_js_function("app.ui.setView", "home")

        if "--test" in sys.argv or ("PEW_RUN_TESTS" in os.environ and os.environ["PEW_RUN_TESTS"] == "1"):
            self.test_mode = True
            import pew.test
            
            test_runner = pew.test.PEWTestRunner()

            def testsFinishedCallback(success):
                """
                Do any cleanup and reporting here.
                """
                if success:
                    report_file = test_runner.generate_coverage_report()
                    webbrowser.open("file://" + report_file)

                if not success:
                    logging.error("There were unit test failures, please check the log for details.")
                self.shutdown()

            test_runner.startTestsThread(testsFinishedCallback)
