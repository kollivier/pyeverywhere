Overview
********

PyEverywhere lets you generate Python applications for deployment on major
desktop and mobile platforms. To speed cross-platform development, it uses
HTML for the UI with a bridge layer for passing messages back and forth
between the UI and the app.

Consider the HTML UI the view layer of your application, while Python provides
the controller and model sections. 

Features
========

* KISS (Keep it Simple, Stupid!). Our priority is on easy to understand and easy to maintain code.
  For you, that means less potential for bugs and more leveraging of existing tools that are battle-tested
* Because PyEverywhere is built on top of Pythonista (iOS), Kivy (Android), and wxPython (Mac/Win), 
  you can use their APIs for platform-specific UI or functionality.
* Full HTML5 support. Anything the native browsers support, you can support in your app
* BYOF (Bring Your Own Framework). The only requirements are jQuery and nativebridge.js.
  Otherwise, you are free to use whatever JS frameworks, libraries, or templating tools you wish
* Mock UI creation support. The native bridge supports the use of an optional JS controller. When
  a protocol is not specified, it will fall back to sending the messages to the JS controller instead.
  This makes it possible to completely test the UI from a browser, which helps to catch UI bugs and JS errors
* Unit and functional test support. Using :class:`pew.PEWTestCase`, you can automate UI interaction and
  test that the application performs as expected
* Support for third-party Python modules. You can add pure Python third-party modules to your app, along with
  some C++ library Python wrappers. More will continue to be added!

Basic Workflow
==============

The basic workflow for a PEW application is as follows:

* Create a :class:`pew.PEWApp` subclass and override it's setUp method
* In your setUp method, construct and show a :class:`pew.WebUIView` and load an HTML page. You will 
  need to specify a delegate to receive messages from the UI, and a protocol used to send those messages
* Once the HTML page has been loaded, it will send a load_complete message to the delegate
* In the load_complete handle, using the :func:`pew.WebUIView.call_js_function`, marshall UI data to JSON format
  and send it to a JavaScript function used to load the UI data
* As the user interacts with the UI, send event messages back to Python
  using the bridge.sendMessage method, found in nativebridge.js. Use call_js_function to update the UI when needed
