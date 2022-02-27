Python App Distribution on macOS
*********************************

For various reasons, the Python situation on macOS has gotten somewhat...
complicated. This `XKCD <https://xkcd.com>`_ comic sums it up pretty nicely:

.. image:: https://imgs.xkcd.com/comics/python_environment_2x.png
   :target: https://xkcd.com/1987/
   :height: 500px
   :align: center

When you're attempting macOS python app packaging and distribution,
there are some things that are important to know:

1. On Mac, GUI apps must be an app bundle. Unlike on Linux and Windows,
   cli tools cannot run GUIs. Python has a special build that handles
   this called a "framework build", but this is not the default build
   config. (If you're curious, it does this by redirecting to a python
   in an .app bundle binary)

2. Some Python builds are compiled specifically for the OS version they
   are running on. That is, they are not backwards-compatible and not
   intended for redistribution. As a result, they may rely on libraries
   not available on other systems. They may also not support all architectures
   your users may have. (e.g. x86_64 and Apple silicon)

3. Python itself now has Apple Silicon builds, called "Universal" builds.
   As of now (Jan 2022), I would recommend against using these builds for
   building apps, as a number of Python extensions do not have releases
   with support for Apple Silicon yet. This situation will probably improve
   significantly over the coming year, now that Python has made universal
   builds the only option for 3.10.

The upshot of all this, in short, is that if you use the wrong Python build when
building and packaging a GUI application using PyEverywhere, then it's likely
to either fail to build, or worse, it will build but will not run on another
user's machine.

When this happens, you will likely see cryptic errors about loading dylibs
or so modules. This is because python itself, or some extension, depends on a
library version that's available on your machine but not on theirs, or the
version found is not of the correct architecture for the user's machine.
To make things extra-confusing, these libaries may even have the same name as
system libraries, so the libraries may seem to exist on the user's machine, but
not be the version of the library the app is looking for.

For example, you may get an error that the app failed to load `libz.dylib`,
even though it clearly exists on the system. What it doesn't tell you is that
it was looking for the version installed by homebrew when you were installing
python using it, NOT the system version of the library provided by macOS
(which it found and determined was not the correct version).

The python builds from python.org solves these problems. Their builds maximize
backwards compatibility and are built for multiple architectures, so that the
builds will run on pretty much any macOS system. You can build on a M1 Mac with
the latest macOS and it will run on older versions and Intel Macs. These builds
also pass those flags to setup.py scripts, so any extensions built using them will
also be backwards-compatible in the same way. (pypi extensions are often built
using these flags.)

TL;DR: Use Python.org builds whenever creating and packaging GUI apps. If you have
other Pythons, make sure you setup your PyEverywhere app's environment with a venv
that uses the Python.org python.
