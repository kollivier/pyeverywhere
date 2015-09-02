import logging
logging.basicConfig(level=logging.DEBUG)
import os
import sys

thisdir = os.path.dirname(os.path.abspath(__file__))

import pew


def start_app():
    import controllers.app

    app = controllers.app.Application()
    app.run()


if "--test" in sys.argv or ("PEW_RUN_TESTS" in os.environ and os.environ["PEW_RUN_TESTS"] == "1"):
    olddir = os.getcwd()
    os.chdir(thisdir)

    failures = False
    # if we are running functional tests, we should spin up the UI, but
    # if we're just running unit tests we should just run them and quit.
    if "--no-functional" in sys.argv:
        import pew.test
        print("only running unit tests?")
        test_runner = pew.test.PEWTestRunner()
        test_runner.start_coverage_tests()
        def finished_callback(success):
            if success:
                report = test_runner.generate_coverage_report()
                print("Coverage report available at:")
                print(report)
            else:
                failures = True

        test_runner.runTests(allTests=False, callback=finished_callback)
    else:
        start_app()

    os.chdir(olddir)
    if failures:
        sys.exit(1)
    else:
        sys.exit(0)

start_app()
