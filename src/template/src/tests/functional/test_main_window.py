import pew


class SampleProjectFunctionalTests(pew.test.PEWTestCase):
    def testLoaded(self):
        # make sure the app and webview references are active
        self.assertIsNotNone(self.app)
        self.assertIsNotNone(self.webview)
        
    def testQuoteButton(self):
        initial_text = "Welcome to Hello World the App! Click the button to see some Python magic!"
        spam_text = self.webview.get_js_value('$("#spam").text()')
        self.assertEqual(spam_text, initial_text)
        
        self.simulatePress("#quote_button")
        
        # wait until we've received the event in Python land before continuing the tests.
        self.waitForResponse()
        spam_text = self.webview.get_js_value('$("#spam").text()')
        self.assertNotEqual(spam_text, initial_text)
