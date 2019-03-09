import os

# Files to include

application = "{app_path}"
appname = os.path.basename(application)

files = [ application ]

icon_locations = {
    appname:        (140, 120),
    'Applications': (500, 120)
}

# Symlinks to create
symlinks = { 'Applications': '/Applications' }

background = 'builtin-arrow'
