Project Info File Format Reference
***********************************

In the root directory of your PyEverywhere project, you will find a file named
project_info.json. This JSON file is where you specify project information, and it will
be used to update the native projects accordingly.

Sample File With Comments
=========================

.. code-block:: javascript

    {
        "name": "My Project",
        "version": "0.9.5.6",
        "identifier": "org.pyeverywhere.MyProject",
        "packages": ["pubsub"], # list of Python packages to include
        "icons": { # list of icons, by platform
            "ios": [
                "Icon-60.png",
                "Icon-72.png",
                "Icon-72@2x.png",
                "Icon-Small-50.png",
                "Icon-Small-50@2x.png",
                "Icon.png",
                "Icon@2x.png"
            ]
        },
        "codesign":
        {
            "osx": # code-signing identity to use when code-signing app
            {
                "identity": "Developer ID Application: My Name"
            }
        }
    }
