import logging

from android.runnable import run_on_ui_thread

from kivy.app import App


@run_on_ui_thread
def run_on_main_thread(func, *args, **kwargs):
    func(*args, **kwargs)

app = None


def get_app():
    return app


class NativePEWApp(App):
    def build(self):
        global app
        app = self
        self.setUp()
        logging.info("starting app...")
        return self.get_main_window().webview

    def shutdown(self):
        pass  # I don't think this is supported natively with Kivy

    def on_pause(self):
        logging.info("on_pause called...")
        # Here you can save data if needed
        return False

    def on_stop(self):
        logging.info("on_stop called...")
        self.shutdown()

    def on_resume(self):
        # Here you can check if any data needs replacing (usually nothing)
        pass


from webview import *
