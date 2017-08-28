#!/usr/bin/env python

import argparse
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

from distutils.core import setup

import pewtools

if 'darwin' in sys.platform:
    import pbxproj

try:
    input = raw_input
except NameError:
    pass

thisdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
srcdir = os.path.join(thisdir, 'src')

config_dir = os.path.expanduser(os.path.join("~", ".pyeverywhere"))
if not os.path.exists(config_dir):
    os.makedirs(config_dir)

config_settings = {
    "android.root": "Path to the directory where the Android tools will be stored"
}

config_file = os.path.join(config_dir, "config.json")
pew_config = {}
if os.path.exists(config_file):
    pew_config = json.load(open(config_file))

android_dir = os.path.join(thisdir, "native", "android")

command_env = os.environ.copy()

default_android_root = os.path.abspath(os.path.join(os.path.expanduser("~"), ".pyeverywhere", "native", "android"))
android_root = default_android_root
if "android.root" in pew_config:
    android_root = pew_config['android.root']

if not os.path.exists(android_root):
    try:
        os.makedirs(android_root)
    except:
        print("Unable to create android root, trying default...")
        android_root = default_android_root
        if not os.path.exists(android_root):
            os.makedirs(android_root)

command_env['ANDROID_ROOT'] = android_root

verbose = False


platforms = [
    "android",
    "browser",
    "ios",
    "linux",
    "mac",
    "win"
]

templates = [
    "default",
]


from StringIO import StringIO
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


default_key = "default"
cwd = os.getcwd()

info_json = {}

info_file = os.path.join(cwd, "project_info.json")


def copy_files(src_dir, build_dir, ignore_paths):
    def _logpath(path, names):
        for ignore_dir in ignore_paths:
            if ignore_dir in path:
                print("Ignoring %s" % path)
                return names
        print("Copying %s" % path)
        return []
    ignore = _logpath

    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)

    print("Copying source files to build tree, please wait...")
    shutil.copytree(src_dir, build_dir, ignore=ignore)

    shutil.copy2(os.path.join(cwd, "project_info.json"), build_dir)


def copy_pew_module(build_dir):
    pew_src_dir = os.path.join(thisdir, "src", "pew")
    pew_dest_dir = os.path.join(build_dir, "pew")
    # For now, we want to allow developers to use their own customized pew module
    # until we offer more advanced configuration options. If they don't though,
    # just copy ours over.
    if not os.path.exists(pew_dest_dir):
        shutil.copytree(pew_src_dir, pew_dest_dir)


def get_value_for_config(key, config_name, default_return=None):
    if key in info_json:
        if "configs" in info_json[key] and config_name in info_json[key]["configs"]:
            return info_json[key]["configs"][config_name]
        elif default_key in info_json[key]:
            return info_json[key][default_key]

    return default_return


def get_value_for_platform(key, platform_name, default_return=None):
    if key in info_json:
        if platform_name in info_json[key]:
            return info_json[key][platform_name]
        elif default_key in info_json[key]:
            return info_json[key][default_key]

    return default_return


def create_android_setup_sh(info_json):
    global cwd
    android_sdk = "19"
    android_build_tools = "23.0.3"

    if "sdks" in info_json and "android" in info_json["sdks"]:
        android_sdk_info = info_json["sdks"]["android"]
        if "target_sdk" in android_sdk_info:
            android_sdk = str(android_sdk_info["target_sdk"])
        if "build_tools" in android_sdk_info:
            android_build_tools = android_sdk_info["build_tools"]

    android_native_dir = os.path.join(cwd, "native", "android")
    if not os.path.exists(android_native_dir):
        os.makedirs(android_native_dir)

    android_setup_file = os.path.join(android_native_dir, "setup.sh")
    f = open(android_setup_file, "w")
    f.write("""
export ANDROIDAPI={}
export ANDROIDBUILDTOOLSVER={}
""".format(android_sdk, android_build_tools))
    f.close()


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

        shutil.copytree(os.path.join(thisdir, "src", "templates", args.template), dir_name)

        project_json_file = os.path.join(dir_name, "project_info.json")
        project_json = json.load(open(project_json_file))

        project_json["name"] = args.name
        project_json["identifier"] = "com.yourdomain.%s" % safe_name

        json.dump(project_json, open(project_json_file, 'w'))


def test(args):
    cmd = "python src/main.py --test"
    if args.no_functional:
        cmd += " --no-functional"
    sys.exit(run_command(cmd))


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
        ui_root = "src/files/www/index.html"
        if "ui_root" in info_json:
            ui_root = info_json["ui_root"]

        def open_browser(url):
            webbrowser.open(url)
        pew.start_local_server(os.path.dirname(ui_root), callback=open_browser)
    else:
        run_command(["python", "src/main.py", " ".join(args.args)])


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

    if args.platform == "android":
        filename = info_json["name"].replace(" ", "")
        if args.config and args.config.strip() != "":
            build_dir = os.path.join(build_dir, args.config)

        icon_dir = os.path.join(cwd, "icons", "android")
        icon = os.path.join(icon_dir, get_value_for_platform("icons", "android", "fakefile"))
        print("Icon is %s" % icon)
        whitelist = os.path.abspath(get_value_for_platform("whitelist_file", "android", "fakefile"))
        launch = os.path.abspath(get_value_for_platform("launch_images", "android", "fakefile"))
        orientation = get_value_for_platform("orientation", "android", "sensor")
        intent_filters = os.path.abspath(get_value_for_platform("intent_filters", "android", "fakefile"))

        keystore = ""
        keyalias = ""
        keypasswd = ""

        build_type = ""
        if args.release:
            build_type = "release"
            signing = get_value_for_platform("codesign", "android", "")
            keystore = os.path.abspath(signing['keystore'])
            keyalias = signing['alias']
            print("signing = %r" % (signing,))
            print("keystore = %r, alias = %r" % (keystore, keyalias))
            if 'passwd' in signing:
                keypasswd = signing['passwd']
            else:
                keypasswd = getpass.getpass()

        if len(requirements) > 0:
            requirements = ",".join(requirements)
        else:
            requirements = ""

        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)

        parent_dir = os.path.dirname(build_dir)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        copy_files(src_dir, build_dir, ignore_paths)
        venv_dir = os.path.join(build_dir, "venv")
        if not os.path.exists(venv_dir):
            os.makedirs(venv_dir)
        pewtools.copy_deps_to_build(info_json["packages"], venv_dir, build_dir)
        copy_pew_module(build_dir)

        shutil.rmtree(venv_dir)

        cmd = ["bash", os.path.join(android_dir, "build.sh"), info_json["identifier"], filename, info_json["version"], build_dir, icon, launch, whitelist, orientation, requirements, build_type, intent_filters, keystore, keyalias, keypasswd]
        returncode = run_command(cmd)
    if args.platform == "ios":
        project_dir = os.path.join(cwd, "native", "ios", "PythonistaAppTemplate-master")
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        project_build_dir = os.path.join(build_dir, os.path.basename(project_dir))
        shutil.copytree(project_dir, project_build_dir)
        plist_file = os.path.join(project_build_dir, "PythonistaAppTemplate", "Info.plist")
        if os.path.exists(plist_file):
            version_short = info_json["version"].split(".")
            version_short = ".".join(version_short[:3])
            plist = plistlib.readPlist(plist_file)
            plist['CFBundleIdentifier'] = info_json["identifier"]
            plist['CFBundleName'] = plist['CFBundleDisplayName'] = info_json["name"]
            plist['CFBundleVersion'] = info_json["version"]
            plist['CFBundleShortVersionString'] = version_short
            plist['UIStatusBarHidden'] = get_value_for_platform("hide_status_bar", "ios", True)
            
            # These are needed because the Python libraries contain references to
            # libs which need permissions. 
            plist['NSCalendarsUsageDescription'] = "This app requires access to your calendar information."
            plist['NSPhotoLibraryUsageDescription'] = "This app requires access to your photo library."
            plist['NSBluetoothPeripheralUsageDescription'] = "This app requires access to a bluetooth peripheral."

            icons = get_value_for_platform("icons", "ios", [])
            if len(icons) > 0:
                plist['CFBundleIconFiles'] = icons

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
        files_src_dir = os.path.join(src_dir, "files")
        script_ignore_paths = ignore_paths + [files_src_dir]
        copy_files(src_dir, dest_dir, script_ignore_paths)
        copy_pew_module(dest_dir)
        files_dest_dir = os.path.join(project_build_dir, "files")
        copy_files(files_src_dir, files_dest_dir, ignore_paths)

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
            f = open(config_file, 'rb')
            config = f.read()
            f.close()

            config = config.replace("My App", info_json["name"])
            f = open(config_file, 'wb')
            f.write(config)
            f.close()
        else:
            print("Unable to update XCode project config file. You may need to manually change some settings.")

        run_command(["open", project_file.replace(" ", "\\ ")])

    elif args.platform in ["mac", "win"]:
        if args.platform == 'mac':
            import py2app

            sys.argv = [sys.argv[0], "py2app"]
        else:
            import py2exe
            sys.argv = [sys.argv[0], "py2exe"]

        excludes = []
        packages = []
        plist = {
            'CFBundleIdentifier': info_json["identifier"],
        }

        if "packages" in info_json:
            packages.extend(info_json["packages"])

        dist_dir = "dist/%s" % args.platform
        if not os.path.exists(dist_dir):
            os.makedirs(dist_dir)

        dll_excludes = ["combase.dll", "credui.dll", "crypt32.dll", "dhcpcsvc.dll", "msvcp90.dll", "mpr.dll", "oleacc.dll", "powrprof.dll", "psapi.dll", "setupapi.dll", "userenv.dll",  "usp10.dll", "wtsapi32.dll"]
        dll_excludes.extend(["iertutil.dll", "iphlpapi.dll", "nsi.dll", "psapi.dll", "oleacc.dll", "urlmon.dll", "Secur32.dll", "setupapi.dll", "userenv.dll", "webio.dll","wininet.dll", "winhttp.dll", "winnsi.dll", "wtsapi.dll"])

        dll_excludes.extend(["cryptui.dll", "d3d9.dll", "d3d11.dll", "dbghelp.dll", "dwmapi.dll", "dwrite.dll", "dxgi.dll", "dxva2.dll", "fontsub.dll", "ncrypt.dll", "wintrust.dll"])

        # this is needed on Windows for py2exe to find scripts in the src directory
        sys.path.append(src_dir)

        data_files = [('.', [os.path.join(cwd, "project_info.json")])]
        for root, dirs, files in os.walk("src/files"):
            files_in_dir = []
            for afile in files:
                if not afile.startswith("."):
                    files_in_dir.append(os.path.join(root, afile))
            if len(files_in_dir) > 0:
                data_files.append((root.replace("src/", ""), files_in_dir))

        try:
            import cefpython3
            cefp = os.path.dirname(cefpython3.__file__)
            cef_files = ['%s/icudtl.dat' % cefp]
            cef_files.extend(glob.glob('%s/*.exe' % cefp))
            cef_files.extend(glob.glob('%s/*.dll' % cefp))
            cef_files.extend(glob.glob('%s/*.pak' % cefp))
            cef_files.extend(glob.glob('%s/*.bin' % cefp))
            data_files.extend([('', cef_files),
                ('locales', ['%s/locales/en-US.pak' % cefp]),
                ]
            )
            for cef_pyd in glob.glob(os.path.join(cefp, 'cefpython_py*.pyd')):
                version_str = "{}{}.pyd".format(sys.version_info[0], sys.version_info[1])
                if not cef_pyd.endswith(version_str):
                    module_name = 'cefpython3.' + os.path.basename(cef_pyd).replace('.pyd', '')

                    print("Excluding pyd: {}".format(module_name))
                    excludes.append(module_name)

        except:  # TODO: Print the error information if verbose is set.
            pass  # if cefpython is not found, we fall back to the stock OS browser

        print("data_files = %r" % data_files)
        name = info_json["name"]
        # workaround a bug in py2exe where it expects strings instead of Unicode
        if args.platform == 'win':
            name = name.encode('utf-8')
        py2exe_opts = {
            "dll_excludes": dll_excludes,
            "packages": packages,
            "excludes": excludes,
        }
        py2app_opts = {
            "dist_dir": dist_dir, 
            'plist': plist,
            "packages": packages,
            "site_packages": True,
        }

        setup(name=name,
              version=info_json["version"],
              options={
                  'py2app': py2app_opts,
                  'py2exe': py2exe_opts
              },
              app=['src/main.py'],
              windows=['src/main.py'],
              data_files=data_files
        )

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", dest="verbose", action="store_true", help="Enable verbose output")
    # parser.add_argument("command", description="", help="Command to run. Acceptable commands are: %r" % commands)
    commands = parser.add_subparsers(title='commands', help='Commands to operate on PyEverywhere projects')

    build_opt = commands.add_parser('build', help="Build PyEverywhere binary")
    build_opt.add_argument('platform', choices=platforms, help='Platform to build project for. Choices are: %r' % (platforms,))
    build_opt.add_argument('--release', action='store_true', help='Build the app in release mode.')
    build_opt.add_argument('--config', default=None, help='Specify a Python config file to use when building the app.')
    build_opt.set_defaults(func=build)

    new_opt = commands.add_parser('create', help="Create new PyEverywhere project in the current working directory")
    new_opt.add_argument('name', help='Name of project to create')
    new_opt.add_argument('--template', default='default', help='Specify a project template for the app. Choices are: %r' % (templates,))

    new_opt.set_defaults(func=create)

    up_opt = commands.add_parser('init', help="Initialize the PyEverywhere dependencies for the project in the current working directory.")
    up_opt.add_argument('platform', choices=platforms, help='Platform to run the project on. Choices are: %r' % (platforms,))
    up_opt.set_defaults(func=init)

    run_opt = commands.add_parser('run', help="Run PyEverywhere project")
    run_opt.add_argument('platform', choices=platforms, help='Platform to run the project on. Choices are: %r' % (platforms,))
    run_opt.add_argument('--config', default=None, help='Specify a Python config file to use when running the app. For iOS and Android, this must be specified in the build step.')
    run_opt.add_argument('args', nargs=argparse.REMAINDER)
    run_opt.set_defaults(func=run)

    test_opt = commands.add_parser('test', help="Run PyEverywhere project")
    test_opt.add_argument('platform', choices=platforms, help='Platform to run the project on. Choices are: %r' % (platforms,))
    test_opt.add_argument('--no-functional', action='store_true', help='Only run unit tests, do not start the GUI and run functional tests.')
    test_opt.set_defaults(func=test)

    up_opt = commands.add_parser('update', help="Update the PyEverywhere dependencies for the project in the current working directory.")
    up_opt.add_argument('platform', choices=platforms, help='Platform to run the project on. Choices are: %r' % (platforms,))
    up_opt.set_defaults(func=update)

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

        global info_json
        info_json = json.loads(open(info_file, "rb").read())
        create_android_setup_sh(info_json)
    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
