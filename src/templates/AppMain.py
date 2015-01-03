import mobilepy

class Application(object):

    def run():
        """
        Start your UI and app run loop here.
        """
        
        view = mobilepy.ui.create_main_webview_ui("http://www.kosoftworks.com", self)
        return 0

    def webview_should_start_load(self, webview, url, nav_type):
        return True
    def webview_did_start_load(self, webview):
        pass
    def webview_did_finish_load(self, webview):
        pass
    def webview_did_fail_load(self, webview, error_code, error_msg):
        pass
