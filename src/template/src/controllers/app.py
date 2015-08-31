import json
import logging
import os
import sys
import urllib

import pew

parentdir = os.path.join(__file__, "..")
thisdir = os.path.dirname(os.path.abspath(parentdir))

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
        self.webview.call_js_function("this_just_in", "No one expects the Spanish Inquisition!")

    def load_complete(self):
        self.webview.call_js_function("app.ui.setView", "home")

        if "--test" in sys.argv or ("PEW_RUN_TESTS" in os.environ and os.environ["PEW_RUN_TESTS"] == "1"):
            self.test_mode = True
            import testrunner

            def testsFinishedCallback(success):
                if success:
                    report_file = testrunner.generate_coverage_report()
                    webbrowser.open("file://" + report_file)

                if not success:
                    logging.error("There were unit test failures, please check the log for details.")
                self.shutdown()

            testrunner.startTestsThread(testsFinishedCallback)

    def search_key_up(self, value):
        pew.ui.show_alert('search_key_up called with value:' + value)
        self.webview.evaluate_javascript("$('#search_bar').val('%s');" % value)
