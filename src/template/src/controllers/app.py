import json
import logging
import os
import random
import sys
import urllib

import pew

thisdir = pew.get_app_dir()

# in source builds, project_info.json is a directory above the sources, but
# in frozen apps they're all in the same directory.
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
        phrases = [
            "No one expects the Spanish Inquisition!",
            "And now for something completely different.",
            "No one expects the spammish repitition!",
            "Our experts describe you as an appallingly dull fellow, unimaginative, timid, lacking in initiative, spineless, easily dominated, no sense of humour, tedious company and irrepressibly drab and awful. And whereas in most professions these would be considerable drawbacks, in chartered accountancy they are a positive boon.",
            "It's not pining. It's passed on. This parrot is no more. It has ceased to be. It's expired and gone to meet its maker. This is a late parrot. It's a stiff. Bereft of life, it rests in peace. If you hadn't nailed it to the perch, it would be pushing up the daisies. It's rung down the curtain and joined the choir invisible. THIS IS AN EX-PARROT.",
            "It's just a flesh wound.",
            "I'm sorry to have kept you waiting, but I'm afraid my walk has become rather sillier recently."
            "Well you can't expect to wield supreme executive power just because some watery tart threw a sword at you.",
            "All right... all right... but apart from better sanitation, the medicine, education, wine, public order, irrigation, roads, a fresh water system, and public health ... what have the Romans ever done for us?",
            "Nudge, nudge, wink, wink. Know what I mean?",
            "Oh! Come and see the violence inherent in the system! Help, help! I'm being repressed!",
            "-She turned me into a newt! -A newt? -I got better..."
        ]
        
        self.webview.call_js_function("this_just_in", random.choice(phrases))

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
