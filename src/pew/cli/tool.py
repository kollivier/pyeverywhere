#!/usr/bin/env python

import argparse
import copy
import getpass
import glob
import json
import logging
logging.basicConfig()
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import webbrowser

import pewtools

from pew.constants import platforms as pew_platforms
from pew.controllers import get_build_controller
from pew.controllers.utils import *

# we support starting a local server to run in the browser, but it is not a supported target platform for pew,
# so we add it here.
platforms = copy.copy(pew_platforms) + ['browser']

if 'darwin' in sys.platform:
    import pbxproj

try:
    input = raw_input
except NameError:
    pass

thisdir = os.path.dirname(os.path.abspath(__file__))
rootdir = os.path.abspath(os.path.join(thisdir, "..", "..", ".."))

config_settings = {
    "android.root": "Path to the directory where the Android tools will be stored"
}

pew_config = get_pew_config()

android_dir = os.path.join(rootdir, "native", "android")

command_env = os.environ.copy()

verbose = False

templates = [
    "default",
]

def get_default_platform():
    if sys.platform.startswith('win'):
        return 'win'
    elif sys.platform.startswith('darwin'):
        return 'osx'

    return 'linux'

import struct


def is_png(data):
    return (data[:8] == '\211PNG\r\n\032\n'and (data[12:16] == 'IHDR'))


def get_image_info(filename):
    f = open(filename, 'rb')
    data = f.read(25)
    if is_png(data):
        w, h = struct.unpack('>LL', data[16:24])
        width = int(w)
        height = int(h)
    else:
        raise Exception('not a png image')
    return width, height


def run_command(cmd):
    global command_env
    if verbose:
        print("Running command: %r" % cmd)
        print("Environment: %r" % (command_env,))
    return subprocess.call(cmd, env=command_env)


def run_python_script(script, args):
    py_exe = 'python'

    # On OS X, when running in a virtualenv we need to run scripts from within
    # the framework's Python.app bundle to run GUI apps.
    # Set PYTHONHOME to the virtualenv root to ensure we get virtualenv environment
    if sys.platform.startswith('darwin') and hasattr(sys, 'real_prefix'):
        command_env['PYTHONHOME'] = sys.prefix
        # It appears that framework builds of Python no longer have a python
        # executable in the bin directory, so we add the version to the filename.
        version = sys.version[:3]
        py_exe = '{}/bin/python{}'.format(sys.real_prefix, version)
    result = run_command([py_exe, script, " ".join(args)])
    if sys.platform.startswith('darwin') and hasattr(sys, 'real_prefix'):
        del command_env['PYTHONHOME']
    return result


def codesign_mac(path, identity):
    cmd = ["codesign", "--force", "-vvv", "--verbose=4", "--sign", identity]

    cmd.append(path)
    logging.info("running %s" % " ".join(cmd))

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()
    for line in proc.stdout:
        logging.info(line)
    for line in proc.stderr:
        logging.error(line)

    if proc.returncode != 0:
        logging.error("Code signing failed")
        print("Unable to codesign %s" % path)
        sys.exit(1)
    else:
        logging.info("Code signing succeeded for %s" % path)
        cmd = ['codesign', "--verify", "--deep", "--verbose=4", path]
        logging.info("calling %s" % " ".join(cmd))
        if subprocess.call(cmd) != 0:
            print("Code signed application failed validation.")
            sys.exit(1)


cwd = os.getcwd()

info_json = {}

info_file = os.path.join(cwd, "project_info.json")


def dir_is_pew(check_dir):
    return os.path.exists(os.path.join(cwd, "project_info.json"))


def get(args):
    global config_settings
    if args.name == "all":
        for name in pew_config:
            print("    %s: %s" % (name, pew_config[name]))
    else:
        print("    %s:%s" % (args.name, pew_config[args.name]))


def set(args):
    global pew_config
    name = args.name
    value = args.value
    pew_config[name] = value
    f = open(config_file, "w")
    json.dump(pew_config, f)
    f.close()


def create(args):
    if args.name:
        safe_name = args.name.replace(" ", "")
        dir_name = os.path.join(cwd, safe_name)
        print("Creating project %s in directory %s" % (args.name, dir_name))
        if os.path.exists(dir_name):
            print("Project already exists! Please delete or rename the existing project folder and try again.")
            sys.exit(1)

        shutil.copytree(os.path.join(rootdir, "src", "templates", args.template), dir_name)

        project_json_file = os.path.join(dir_name, "project_info.json")
        project_json = json.load(open(project_json_file))

        project_json["name"] = args.name
        project_json["identifier"] = "com.yourdomain.%s" % safe_name

        json.dump(project_json, open(project_json_file, 'w'))


def test(args):
    cmd_args = ["--test"]
    if args.no_functional:
        cmd_args.append("--no-functional")
    sys.exit(run_python_script("src/main.py", cmd_args))


def run(args):
    copy_config_file(args)
    if args.platform == "android":
        apk_name = "%s-%s-debug.apk" % (info_json["name"].replace(" ", ""), info_json["version"])
        apk_file = os.path.join(cwd, "dist", "android", apk_name)
        if not os.path.exists(apk_file):
            print("Could not find APK file to run at %s" % apk_file)
            print("Please ensure that you have performed a build and that it succeeded, and try again.")
            sys.exit(1)
        cmd = ["bash", os.path.join(android_dir, "run.sh"), apk_file, info_json["identifier"]]
        sys.exit(run_command(cmd))
    elif args.platform == "ios":
        build(args)  # we can't run the app programmatically, so just use build to load the project.
    elif args.platform == "browser":
        import pew
        ui_root = "src/files/web/index.html"
        if "ui_root" in info_json:
            ui_root = info_json["ui_root"]

        url_args = ''
        if len(args.args) > 0:
            for arg in args.args:
                if len(arg) > 0:
                    if len(url_args) == 0:
                        url_args += '?'
                    else:
                        url_args += '&'

                    if arg.startswith('--'):
                        arg = arg.replace('--', '')

                    url_args += arg

        def open_browser(url):
            print("URL: %s" % url)
            print("If your browser does not open within a few seconds, copy and paste this URL to test.")
            webbrowser.open(url)
        pew.start_local_server(os.path.dirname(ui_root), callback=open_browser)
    else:
        run_python_script('src/main.py', args.args)


def copy_config_file(args):
    src_dir = os.path.join(cwd, "src")
    local_config = os.path.join(src_dir, "local_config.py")
    if os.path.exists(local_config):
        os.remove(local_config)

    if args.config:
        config_path = os.path.abspath(os.path.join("configs", args.config + ".py"))
        if os.path.exists(config_path):
            shutil.copy2(config_path, os.path.join(src_dir, "local_config.py"))
        else:
            print("Specified config file %s not found. Exiting..." % config_path)
            sys.exit(1)


def build(args):
    returncode = 0
    copy_config_file(args)

    src_dir = os.path.join(cwd, "src")
    build_dir = os.path.join(cwd, "build", args.platform)
    requirements = get_value_for_platform("requirements", args.platform, [])
    requirements = requirements + get_value_for_platform("requirements", "common", [])

    ignore_paths = []
    if args.config != "":
        ignore_dirs = get_value_for_config("ignore_dirs", args.config)
        print("Ignore dirs specified: %r" % ignore_dirs)
        if ignore_dirs:
            for ignore_dir in ignore_dirs:
                ignore_paths.append(os.path.abspath(ignore_dir))

    data_files = [('.', [os.path.join(cwd, "project_info.json")])]
    asset_dirs = []
    if "asset_dirs" in info_json:
        asset_dirs = info_json["asset_dirs"]
    else:
        message = "WARNING: Specifying asset_dirs with a list of directories for your app's static files is now required. Please add \"asset_dirs\": ['src/files'] to your project_info.json file."
        print(message)
        asset_dirs = ['src/files']

    for asset_dir in asset_dirs:
        for root, dirs, files in os.walk(asset_dir):
            files_in_dir = []
            for afile in files:
                if not afile.startswith("."):
                    files_in_dir.append(os.path.join(root, afile))
            if len(files_in_dir) > 0:
                data_files.append((root.replace("src/", ""), files_in_dir))

    settings = {
        'requirements': requirements,
        'ignore_paths': ignore_paths,
        'data_files': data_files
    }

    if args.platform == "android":
        controller = get_build_controller(args, info_file)
        returncode = controller.build(args, settings)
    if args.platform == "ios":
        project_dir = os.path.join(cwd, "native", "ios", "PythonistaAppTemplate-master")
        if not os.path.exists(project_dir):
            print("iOS support files not downloaded for this project. Run 'pew init ios' first.")
            sys.exit(1)
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        project_build_dir = os.path.join(build_dir, os.path.basename(project_dir))
        shutil.copytree(project_dir, project_build_dir)
        project_xcode_dir = os.path.join(project_build_dir, "PythonistaAppTemplate")
        plist_file = os.path.join(project_xcode_dir, "Info.plist")
        if os.path.exists(plist_file):
            version_short = info_json["version"].split(".")
            version_short = ".".join(version_short[:3])
            plist = plistlib.readPlist(plist_file)
            plist['CFBundleIdentifier'] = info_json["identifier"]
            plist['CFBundleName'] = plist['CFBundleDisplayName'] = info_json["name"]
            plist['CFBundleVersion'] = info_json["version"]
            plist['CFBundleIconName'] = 'AppIcon'
            plist['CFBundleShortVersionString'] = version_short
            plist['UIStatusBarHidden'] = get_value_for_platform("hide_status_bar", "ios", True)
            
            # These are needed because the Python libraries contain references to
            # libs which need permissions. 
            plist['NSCalendarsUsageDescription'] = "This app requires access to your calendar information."
            plist['NSPhotoLibraryUsageDescription'] = "This app requires access to your photo library."
            plist['NSBluetoothPeripheralUsageDescription'] = "This app requires access to a bluetooth peripheral."

            icons = get_value_for_platform("icons", "ios", [])
            if len(icons) > 0:
                appicon_dir = os.path.join(project_xcode_dir, "Assets.xcassets", "AppIcon.appiconset")
                contents_file = os.path.join(appicon_dir, "Contents.json")
                contents = json.loads(open(contents_file).read())

                for icon_data in contents["images"]:
                    scale = 1
                    if "scale" in icon_data:
                        scale = int(icon_data["scale"].replace("x", ""))
                    if "size" in icon_data:
                        width, height = icon_data["size"].split("x")
                        scaled_width = float(width) * scale
                        # FIXME: switch to parsing the png header to get image dimensions
                        # rather than expecting a certain filename convention. See here for info:
                        # https://stackoverflow.com/questions/8032642/how-to-obtain-image-size-using-standard-python-class-without-using-external-lib
                        best_icon = None
                        for icon in icons:
                            basename = os.path.splitext(icon)[0]
                            last_dash = basename.rfind("-")
                            size = basename[last_dash+1:]
                            try:
                                size = int(size)
                            except:
                                continue
                            if size == scaled_width:
                                best_icon = icon
                                break
                            elif size > scaled_width:
                                if best_icon:
                                    icon_size = os.path.splitext(best_icon)[0].split("-")[1]
                                    if int(icon_size) < size:
                                        continue
                                best_icon = icon

                        if best_icon:
                            full_icon_path = os.path.join(cwd, "icons", "ios", best_icon)
                            filename = None
                            if "filename" in icon_data:
                                dest_icon_path = os.path.join(appicon_dir, icon_data["filename"])
                                shutil.copyfile(full_icon_path, dest_icon_path)
                            else:
                                print("No filename listed for {}".format(scaled_width))
                        else:
                            print("Could not find icon for size {}".format(scaled_width))

            orientation_value = get_value_for_platform("orientation", "ios", "both")
            orientations = [orientation_value]
            if orientation_value == 'all' or orientation_value == 'sensor':
                orientations = ['landscape', 'portrait']
            else:
                plist['UIRequiresFullScreen'] = True

            launch_images = get_value_for_platform("launch_images", "ios", [])
            if len(launch_images) > 0:
                del plist['UILaunchStoryboardName']
                images = []
                for image in launch_images:
                    image_path = os.path.abspath(os.path.join("icons", "ios", image))
                    width, height = get_image_info(image_path)
                    orientation = 'Portrait'

                    size = '{%d, %d}' % (width, height)
                    if width > height:
                        orientation = 'Landscape'
                        # The dimensions for the ImageSize must be specified as if the
                        # image was portrait, even when it's a landscape image.
                        size = '{%d, %d}' % (height, width)
                    filename = os.path.basename(image_path)
                    basename = os.path.splitext(filename)[0]

                    image_keys = {
                        'UILaunchImageMinimumOSVersion': '7.0',
                        'UILaunchImageOrientation': orientation,
                        'UILaunchImageName': basename,
                        'UILaunchImageSize': size
                    }
                    images.append(image_keys)
                plist['UILaunchImages'] = images

            ios_orientations = []
            for orientation in orientations:
                if orientation == 'landscape':
                    ios_orientations.extend(['UIInterfaceOrientationLandscapeLeft', 'UIInterfaceOrientationLandscapeRight'])
                if orientation == 'portrait':
                    ios_orientations.extend(['UIInterfaceOrientationPortrait', 'UIInterfaceOrientationPortraitUpsideDown'])

            plist['UISupportedInterfaceOrientations'] = ios_orientations
            plist['UISupportedInterfaceOrientations~ipad'] = ios_orientations

            plistlib.writePlist(plist, plist_file)

        dest_dir = os.path.join(project_build_dir, "Script")
        script_ignore_paths = ignore_paths + asset_dirs
        copy_files(src_dir, dest_dir, script_ignore_paths)
        copy_pew_module(dest_dir)
        copy_data_files(data_files, project_build_dir)

        project_file = os.path.join(project_build_dir, "PythonistaAppTemplate.xcodeproj")
        config_file = os.path.join(project_file, "project.pbxproj")
        project = pbxproj.XcodeProject.load(config_file)

        for icon_file in glob.glob(os.path.join("icons", "ios", "*")):
            icon_path = os.path.abspath(icon_file)
            icon_filename = os.path.basename(icon_file)
            dest_path = os.path.join(project_build_dir, icon_filename)
            shutil.copy(icon_path, dest_path)
            project.add_file(icon_filename, force=False)

        if "codesign" in info_json and "ios" in info_json["codesign"]:
            ios_codesign = info_json["codesign"]["ios"]

            # Don't use the pre-defined app icon
            project.remove_flags('PRODUCT_BUNDLE_IDENTIFIER', 'com.omz-software.PythonistaAppTemplate')
            project.remove_flags('ASSETCATALOG_COMPILER_APPICON_NAME', 'AppIcon')

            # TODO: Add support for manual signing
            for target in project.objects.get_targets():
                project_root = project.objects[project.rootObject]
                project_root.set_provisioning_style('Automatic', target)
                project_root.attributes.TargetAttributes[target.get_id()]["DevelopmentTeam"] = ios_codesign["development_team"]
        project.save()

        # FIXME: This currently only works for pure-Python modules.
        pewtools.copy_deps_to_build(requirements, build_dir, dest_dir)

        if os.path.exists(config_file):
            f = open(config_file, 'r')
            config = f.read()
            f.close()

            config = config.replace("My App", info_json["name"])
            f = open(config_file, 'w')
            f.write(config)
            f.close()
        else:
            print("Unable to update XCode project config file. You may need to manually change some settings.")

        run_command(["open", project_file.replace(" ", "\\ ")])

    elif args.platform in ["osx", "win"]:
        controller = get_build_controller(args, info_file)
        controller.build(settings)

        if sys.platform.startswith("darwin") and "codesign" in info_json:
            base_path = os.path.join(dist_dir, "%s.app" % info_json["name"])
            print("base_path = %r" % base_path)
            # remove the .py files and the .pyo files as we shouldn't use them
            # running a .py file in the bundle can modify it.
            for root, dirs, files in os.walk(os.path.join(base_path, "Contents", "Resources", "lib", "python2.7")):
                for afile in files:
                    fullpath = os.path.join(root, afile)
                    ext = os.path.splitext(fullpath)[1]
                    if ext in ['.py', '.pyo']:
                        os.remove(fullpath)

            sign_paths = []
            sign_paths.extend(glob.glob(os.path.join(base_path, "Contents", "Frameworks", "*.framework")))
            sign_paths.extend(glob.glob(os.path.join(base_path, "Contents", "Frameworks", "*.dylib")))
            exes = ["Python"]
            for exe in exes:
                sign_paths.append(os.path.join(base_path, 'Contents', 'MacOS', exe))
            sign_paths.append(base_path)  # the main app needs to be signed last
            for path in sign_paths:
                codesign_mac(path, info_json["codesign"]["osx"]["identity"])

    return returncode


def init(args):
    """
    For now, this is just an alias for update.
    """
    update(args)
    controller = get_build_controller(args, info_file)
    controller.init()


def update(args):
    print("Copying latest dependencies into project...")

    tempdir = tempfile.mkdtemp()

    pewtools.get_dependencies_for_platform(args.platform)
    global command_env, verbose
    pewtools.initialize_platform(args.platform, command_env, verbose=verbose)

    if os.path.exists(tempdir):
        try:
            shutil.rmtree(tempdir)
        except Exception as e:
            import traceback
            logging.error(traceback.format_exc(e))


def dist(args):
    """
    For now, this is just an alias for update.
    """
    controller = get_build_controller(args, info_file)
    controller.dist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-q", dest="verbose", action="store_false", help="Disable verbose output")
    # parser.add_argument("command", description="", help="Command to run. Acceptable commands are: %r" % commands)
    commands = parser.add_subparsers(title='commands', help='Commands to operate on PyEverywhere projects')

    build_opt = commands.add_parser('build', help="Build PyEverywhere binary")
    build_opt.add_argument('platform', choices=platforms, nargs='?', default=get_default_platform(), help='Platform to build project for. Choices are: %r' % (platforms,))
    build_opt.add_argument('--release', action='store_true', help='Build the app in release mode.')
    build_opt.add_argument('--config', default=None, help='Specify a Python config file to use when building the app.')
    build_opt.set_defaults(func=build)

    new_opt = commands.add_parser('create', help="Create new PyEverywhere project in the current working directory")
    new_opt.add_argument('name', help='Name of project to create')
    new_opt.add_argument('--template', default='default', help='Specify a project template for the app. Choices are: %r' % (templates,))

    new_opt.set_defaults(func=create)

    up_opt = commands.add_parser('init', help="Initialize the PyEverywhere dependencies for the project in the current working directory.")
    up_opt.add_argument('platform', choices=platforms, nargs='?', default=get_default_platform(), help='Platform to run the project on. Choices are: %r' % (platforms,))
    up_opt.set_defaults(func=init)

    run_opt = commands.add_parser('run', help="Run PyEverywhere project")
    run_opt.add_argument('platform', choices=platforms, nargs='?', default=get_default_platform(), help='Platform to run the project on. Choices are: %r' % (platforms,))
    run_opt.add_argument('--config', default=None, help='Specify a Python config file to use when running the app. For iOS and Android, this must be specified in the build step.')
    run_opt.add_argument('args', nargs=argparse.REMAINDER)
    run_opt.set_defaults(func=run)

    test_opt = commands.add_parser('test', help="Run PyEverywhere project tests")
    test_opt.add_argument('platform', choices=platforms, nargs='?', default=get_default_platform(), help='Platform to run the project tests on. Choices are: %r' % (platforms,))
    test_opt.add_argument('--no-functional', action='store_true', help='Only run unit tests, do not start the GUI and run functional tests.')
    test_opt.set_defaults(func=test)

    up_opt = commands.add_parser('update', help="Update the PyEverywhere dependencies for the project in the current working directory.")
    up_opt.add_argument('platform', choices=platforms, nargs='?', default=get_default_platform(), help='Platform to run the project on. Choices are: %r' % (platforms,))
    up_opt.set_defaults(func=update)

    dist_opt = commands.add_parser('package', help="Create a distributable package for the PyEverywhere project.")
    dist_opt.add_argument('platform', choices=platforms, nargs='?', default=get_default_platform(), help='Platform to distribute the project for. Choices are: %r' % (platforms,))
    dist_opt.add_argument('--config', default=None, help='Specify a Python config file to use when running the app. For iOS and Android, this must be specified in the build step.')
    dist_opt.set_defaults(func=dist)

    config_text = ""
    for name in config_settings:
        config_text += "    %s: %s" % (name, config_settings[name])
    config_opt = commands.add_parser('set', help="Configure PyEverywhere settings.")
    config_opt.add_argument('name', help='Setting to configure.')
    config_opt.add_argument('value', help='Value for the configuration setting.')
    config_opt.set_defaults(func=set)

    get_opt = commands.add_parser('get', help="View PyEverywhere settings.")
    get_opt.add_argument('name', help='Setting to view. Specify "all" to view all settings.')
    get_opt.set_defaults(func=get)

    args = parser.parse_args()

    if args.verbose:
        global verbose
        verbose = True
        print("Verbose output set.")

    if not args.func in [create, get, set]:
        if not os.path.exists(info_file):
            print("Unable to find project info file at %s. pew cannot continue." % info_file)
            sys.exit(1)

        # FIXME: Remove these globals once we better encapsulate the build logic into controllers.
        global command_env
        global info_json
        info_json = json.loads(open(info_file, "r").read())
        set_project_info(info_json)

        controller = get_build_controller(args, info_file)
        command_env = controller.get_env()

    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
