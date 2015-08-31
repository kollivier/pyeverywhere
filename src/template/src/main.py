import logging
logging.basicConfig(level=logging.DEBUG)
import os
import sys

thisdir = os.path.dirname(os.path.abspath(__file__))


def start_app():
    import controllers.app

    app = controllers.app.Application()
    app.run()


if "--test" in sys.argv or ("PEW_RUN_TESTS" in os.environ and os.environ["PEW_RUN_TESTS"] == "1"):
    import testrunner
    testrunner.start_coverage_tests()

    olddir = os.getcwd()
    os.chdir(thisdir)

    failures = False
    if "--no-functional" in sys.argv:
        print("only running unit tests?")

        def finished_callback(success):
            if success:
                report = testrunner.generate_coverage_report()
                print("Coverage report available at:")
                print(report)
            else:
                failures = True

        testrunner.runTests(allTests=False, callback=finished_callback)
    else:
        start_app()

    os.chdir(olddir)
    if failures:
        sys.exit(1)
    else:
        sys.exit(0)

start_app()
