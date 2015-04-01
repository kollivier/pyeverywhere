from android.runnable import run_on_ui_thread

from kivy.app import App

@run_on_ui_thread
def run_on_main_thread(func, *args, **kwargs):
    func(*args, **kwargs)

app = None
def get_app():
    return app

class PEWApp(App):                                                                          
    def build(self):
        global app
        app = self
        self.setUp()
        logging.info("starting app...")
        return self.get_main_window().webview

    def on_pause(self):
        # Here you can save data if needed
        return True                                                                        

    def on_resume(self):
        # Here you can check if any data needs replacing (usually nothing)
        pass


from webview import *