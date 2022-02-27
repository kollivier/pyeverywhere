Why PyEverywhere?
*****************

PyEverywhere aims to make it easier to create and deploy truly cross-platform desktop
(Win, Linux, and Mac) and mobile (Android and iOS) applications written using Python.

Features
=============

* Provides commands for building, packaging, and deploying Python apps on Win, Linux, Mac, Android and iOS
* Provides a thin UI abstraction layer for building Python applications that use a Web UI (e.g. web apps)

Design Philosophy
==================

* KISS (Keep it Simple, Stupid!). PyEverywhere aims to solve the most common pain points of
  cross-platform app building and packaging. It is not trying to replace Apache Cordova.

* Native-when-needed. Because PyEverywhere is built on top of Pythonista (iOS), Kivy (Android),
  and wxPython (Linux/Mac/Win), you can use their APIs to add platform-specific UI or
  functionality as needed.

* Full HTML5 support. On all platforms, PyEverywhere uses either WebKit or Chromium, leveraging their HTML5 support.

* BYOB (Bring Your Own Backend). Like using wxPython/PyQT for your GUI? Go ahead. Want to package
  up desktop version of a Django web app? No problem.

Basic Workflow
==============

The basic workflow for a PEW application is as follows:

* Create a :class:`pew.ui.PEWApp` subclass and override its :func:`pew.ui.PEWApp.init_ui` method,
* In your :func:`pew.ui.PEWApp.init_ui` method, do the following:
  * Initialize a web server or protocol handler to receive and happen app messages.
  * Construct and show a :class:`pew.ui.WebUIView` and load an HTML page.
* Once the HTML page has been loaded, it will send a :func:`pew.ui.PEWApp.load_complete` message to the delegate.
  Any initialization code that calls JavaScript or requires a fully-loaded UI should be run here.

