"""
The PEW test module contains utilities for running unit tests on a PEW application.
"""

import logging
import os
import re
import tempfile
import threading
import unittest

import pew

has_figleaf = False
try:
    import figleaf
    import figleaf.annotate_html as html_report
    has_figleaf = True
except Exception, e:
    import traceback
    logging.warning(traceback.format_exc(e))


class PEWTestCase(unittest.TestCase):
    """
    PEWTestCase is a subclass of a unittest.TestCase with additional functionality
    for simulating web UI input and waiting for asynchonous changes to take effect.
    """
    def setUp(self):
        self.app = pew.get_app()
        self.webview = self.app.get_main_window()

    def waitForResponse(self, timeout=10):
        """
        Waits until the UI sends a message back to the app. Used to enable verification
        that JS bridge event messages are sent and with the proper response data.
        
        Params:
            :param timeout: time in seconds to wait for the event
        """
        time_waited = 0
        sleep_time = 0.05
        while time_waited < timeout:
            time_waited += sleep_time
            time.sleep(sleep_time)
            if self.webview.message_received:
                break

    def simulatePress(self, selector):
        """
        Simulates a click or touch event on a UI element.
        
        Params:
            :param selector: jQuery selector of element(s) to press
        """
        self.webview.clear_message_received_flag()
        self.webview.evaluate_javascript("$(\"%s\").simulate('click')" % selector)

    def simulateTextInput(self, selector, text):
        """
        Simulates text input in a UI text field.
        
        Params:
            :param selector: jQuery selector of element(s) to receive text input
        """
        self.webview.clear_message_received_flag()
        self.webview.evaluate_javascript("$(\"%s\").val('%s')" % (id, text))


class PEWTestRunner:
    """
    Class for running both functional and unit tests on a PEWApp.
    """
    def start_coverage_tests(self):
        """
        Starts code coverage monitoring during the tests.
        """
        if has_figleaf:
            figleaf.start(ignore_python_lib=True)
    
    
    def generate_coverage_report(self):
        """
        Generates a coverage report in HTML format.
        
        Returns the absolute path to the report file. Note that it is generated
        in a temp directory, so be sure to either move or delete the report.
        """
        if not has_figleaf:
            return 
    
        figleaf.stop()
        tempdir = tempfile.mkdtemp()
        coverage_file = os.path.join(tempdir, "coverage.txt")
        logging.info("Writing coverage to %s" % coverage_file)
        logging.info("coverage info = %r" % figleaf.get_data())
        figleaf.write_coverage(coverage_file)
    
        coverage = {}
        d = figleaf.read_coverage(coverage_file)
        coverage_data = figleaf.combine_coverage(coverage, d)
    
        logging.info("Preparing to write report...")
    
        report_dir = os.path.join(tempdir, "figleaf-html-report")
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        html_report.report_as_html(coverage_data, report_dir, [re.compile(".*testrunner.py"), re.compile(".*site-packages.*"), re.compile(".*pubsub.*")], {})
    
        logging.info("Writing report to %s" % report_dir)
        return os.path.join(report_dir, "index.html")
    
    
    def runTests(self, allTests=True, callback=None):
        """
        Runs all tests defined in your project's tests/unit directory, along with
        tests/functional if you have set allTests to True.
        
        Params:
            :param allTests: True to run all tests including GUI and functional, False to just run the unit tests (e.g. headless testing)
            :param callback: function to call upon test completion. It returns a boolean indicating whether or not the tests passed
        """
        # use the basic test runner that outputs to sys.stderr
        temp_dir = tempfile.mkdtemp()
        test_runner = unittest.TextTestRunner(stream=open(os.path.join(temp_dir, "test_output.txt"), 'w'))
        # automatically discover all tests in the current dir of the form test*.py
        # NOTE: only works for python 2.7 and later
        test_dirs = ['tests/unit']
        if allTests:
            test_dirs.append('tests/functional')
    
        for test_dir in test_dirs:
            print("Running tests in %s, cwd = %s" % (test_dir, os.getcwd()))
            test_loader = unittest.defaultTestLoader
            test_suite = test_loader.discover(test_dir, top_level_dir=os.getcwd())
            # run the test suite
            result = test_runner.run(test_suite)
    
            for failure in result.failures:
                logging.error("%s" % failure[1])
    
            for error in result.errors:
                logging.error("%s" % error[1])
    
            if not result.wasSuccessful():
                break
    
        if callback is not None:
            callback(result.wasSuccessful())
    
    
    def startTestsThread(self, callback):
        """
        The only way to run the tests on the main thread and wait until certain asynchronous messages are received
        is to spin the main GUI event loop while we wait for messages, but not all platforms expose this functionality.
    
        So as an alternative, we run the tests on a thread so that we can simply sleep until the messages arrive.
        """
        thread = threading.Thread(target=runTests, args=(True,callback))
        thread.start()

if __name__ == "__main__":
    test_runner = PEWTestRunner()
    test_runner.start_coverage_tests()
    test_runner.runTests(allTests=False)
