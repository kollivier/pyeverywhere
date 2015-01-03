import os

import ui

def button_tapped(sender):
    sender.title = 'Hello'

def create_main_webview_ui(url, app_controller):
    view = ui.View()                                      # [1]
    view.name = 'WebView'                                    # [2]
    view.background_color = 'white'                       # [3]
    webview = ui.WebView()
    webview.delegate = app_controller
    webview.flex = 'WH'
    webview.load_url(url)               # [4]
    view.add_subview(webview)                              # [8]
    view.present('fullscreen', hide_title_bar=True)                                 # [9]

    return view
