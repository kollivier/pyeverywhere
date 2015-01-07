from kivy.app import App

import logging

import AppMain

class ServiceApp(App):                                                                          
    def build(self):
        a = AppMain.Application()
        a.run()
        logging.info("starting app...")
        return a.get_main_window().webview                                                                          

if __name__ == '__main__':                                                                      
    ServiceApp().run()