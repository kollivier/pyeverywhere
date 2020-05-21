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

* KISS (Keep it Simple, Smarty!). Our priority is on easy to understand and easy to maintain code.
  For you, that means less potential for bugs and more leveraging of existing tools that are battle-tested
* Because PyEverywhere is built on top of Pythonista (iOS), Kivy (Android), and wxPython (Linux/Mac/Win),
  you can use their APIs to add platform-specific UI or functionality.
* Full HTML5 support. On all platforms, PyEverywhere uses either WebKit or Chromium, leveraging their HTML5 support.
* BYOWF (Bring Your Own Web Framework). You are free to use whatever JS frameworks, libraries, or templating tools you wish
  to run your app. Django? Flask? Your own custom layer? No problem.
* Test your UI in the browser directly to leverage teh native debugging tools.
* Unit and functional test support. Using :class:`pew.PEWTestCase`, you can automate UI interaction and
  test that the application performs as expected. The project template includes a working example of this
* Support for third-party Python modules. You can add pure Python third-party modules to your app, along with
  some C++ library Python wrappers. More will continue to be added!

Basic Workflow
==============

The basic workflow for a PEW application is as follows:

* Create a :class:`pew.ui.PEWApp` subclass and override its :func:`pew.ui.PEWApp.init_ui` method,
* In your :func:`pew.ui.PEWApp.init_ui` method, do the following:
  * Initialize a web server or protocol handler to receive and happen app messages.
  * Construct and show a :class:`pew.ui.WebUIView` and load an HTML page.
* Once the HTML page has been loaded, it will send a :func:`pew.ui.PEWApp.load_complete` message to the delegate.
  Any initialization code that calls JavaScript or requires a fully-loaded UI should be run here.

