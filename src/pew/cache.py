import logging
import os
import pickle
import sys


cache_filename = "app_data"

if "--test" in sys.argv or ("PEW_RUN_TESTS" in os.environ and os.environ["PEW_RUN_TESTS"] == "1"):
    cache_filename += "_test"

def set_cache_dir(cache_dir):
    global cache_filename
    cache_filename = os.path.join(cache_dir, os.path.basename(cache_filename))

cache = None
def get_cache():
    global cache
    if cache is None:
        if os.path.exists(cache_filename):
            cache = pickle.load(open(cache_filename, "rb"))
        if cache is None:
            cache = {}

        # create any keys we're looking for with defaults so we don't have to constantly test if keys exist 
        if not "characters" in cache:
            cache["characters"] = {}
    return cache

def save_cache():
    global cache
    logging.info("Saving cache to %r" % cache_filename)
    pickle.dump(cache, open(cache_filename, "wb"))