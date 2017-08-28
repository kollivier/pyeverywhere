import unittest

import models.mpquotes as mp

class QuoteTests(unittest.TestCase):
    def testQuote(self):
        last_quote = None
        quotes = mp.get_all_quotes()
        
        for i in range(5):
            quote = mp.get_random_quote()
            self.assertIn(quote, quotes)
            if last_quote is not None:
                self.assertNotEqual(quote, last_quote)
                
            last_quote = quote
