import os

# Files to include

application = "{app_path}"
appname = os.path.basename(application)

files = [ application ]

window_rect = {window_rect}

icon_locations = {
    appname:        {app_icon_pos},
    'Applications': {apps_icon_pos},
}

# Symlinks to create
symlinks = { 'Applications': '/Applications' }

background = "{background}"
