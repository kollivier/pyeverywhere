import os
import sys


def start_app():
    import controllers.app

    app = controllers.app.Application()
    app.run()

start_app()
