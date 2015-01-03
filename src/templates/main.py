from kivy.app import App

import AppMain

class ServiceApp(App):                                                                          
    def build(self):
        a = AppMain.Application()
		a.run()

		return a.get_main_window()                                                                           

if __name__ == '__main__':                                                                      
    ServiceApp().run()