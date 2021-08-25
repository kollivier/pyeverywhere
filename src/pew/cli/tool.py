#!/usr/bin/env python

import argparse
import copy
import glob
import json
import logging
logging.basicConfig()
import os
import shutil
import subprocess
import sys
import tempfile
import webbrowser

import pewtools

from pew.config import load_project_info
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

pew_config = load_pew_config()

android_dir = os.path.join(rootdir, "native", "android")

command_env = os.environ.copy()

verbose = False

templates = [
    "default",
]

def get_default_platform():
    """
    For commands that require a platform to be specified, we default to the platform that the user is currently
    running. This function determines the platform name to use by default.

    :return: String platform name matching a PyEverywhere platform key.
    """
    if sys.platform.startswith('win'):
        return 'win'
    elif sys.platform.startswith('darwin'):
        return 'osx'

    return 'linux'


def run_command(cmd):
    global command_env
    if verbose:
        print("Running command: %r" % cmd)
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
    controller = get_build_controller(args, info_file)
    cmd_args = ["--test"]
    if args.no_functional:
        cmd_args.append("--no-functional")
    sys.exit(run_python_script(controller.get_main_script_path(), cmd_args))


def run(args):
    controller = get_build_controller(args, info_file)
    copy_config_file(args)
    if args.platform == "android":
        apk_file = glob.glob("dist/android/*.apk")[0]
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
        run_python_script(controller.get_main_script_path(), args.args)


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

    controller = get_build_controller(args, info_file)

    requirements = get_value_for_platform("requirements", args.platform, [])

    ignore_paths = []
    if args.config != "":
        ignore_dirs = get_value_for_config("ignore_dirs", args.config)
        print("Ignore dirs specified: %r" % ignore_dirs)
        if ignore_dirs:
            for ignore_dir in ignore_dirs:
                ignore_paths.append(os.path.abspath(ignore_dir))

    data_files = controller.get_app_data_files()

    settings = {
        'requirements': requirements,
        'ignore_paths': ignore_paths,
        'data_files': data_files,
        'extra_build_options': get_value_for_platform("extra_build_options", args.platform, {}),
    }

    return controller.build(settings)


def init(args):
    """
    For now, this is just an alias for update.
    """
    update(args)
    controller = get_build_controller(args, info_file)
    controller.init()


def codesign(args):
    """
    For now, this is just an alias for update.
    """
    controller = get_build_controller(args, info_file)
    controller.codesign()


def notarize(args):
    """
    For now, this is just an alias for update.
    """
    if not sys.platform.startswith('darwin'):
        print("The notarize command must be run on Mac.")
    controller = get_build_controller(args, info_file)
    controller.notarize()


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

    build_opt = commands.add_parser('build', help="Build a native application")
    build_opt.add_argument('platform', choices=platforms, nargs='?', default=get_default_platform(), help='Platform to build project for. Choices are: %r' % (platforms,))
    build_opt.add_argument('--release', action='store_true', help='Build the app in release mode.')
    build_opt.add_argument('--config', default=None, help='Specify a Python config file to use when building the app.')
    build_opt.add_argument('--sign', action='store_true', help='Codesign the build.')
    build_opt.add_argument('extra_args', nargs=argparse.REMAINDER)
    build_opt.set_defaults(func=build)

    build_opt = commands.add_parser('codesign', help="Code sign native application")
    build_opt.add_argument('platform', choices=platforms, nargs='?', default=get_default_platform(), help='Platform to build project for. Choices are: %r' % (platforms,))
    build_opt.add_argument('extra_args', nargs=argparse.REMAINDER)
    build_opt.set_defaults(func=codesign)

    build_opt = commands.add_parser('notarize', help="Notarize native application (Mac only)")
    build_opt.add_argument('platform', choices=platforms, nargs='?', default=get_default_platform(), help='Platform to build project for. Choices are: %r' % (platforms,))
    build_opt.add_argument('--wait', action='store_true', help='Wait until notarization is successful or failed to return.')
    build_opt.add_argument('extra_args', nargs=argparse.REMAINDER)
    build_opt.set_defaults(func=notarize)

    new_opt = commands.add_parser('create', help="Create new PyEverywhere project in the current working directory")
    new_opt.add_argument('name', help='Name of project to create')
    new_opt.add_argument('--template', default='default', help='Specify a project template for the app. Choices are: %r' % (templates,))
    new_opt.add_argument('extra_args', nargs=argparse.REMAINDER)
    new_opt.set_defaults(func=create)

    up_opt = commands.add_parser('init', help="Initialize the PyEverywhere dependencies for the project in the current working directory.")
    up_opt.add_argument('platform', choices=platforms, nargs='?', default=get_default_platform(), help='Platform to run the project on. Choices are: %r' % (platforms,))
    up_opt.add_argument('extra_args', nargs=argparse.REMAINDER)
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

        try:
            global info_json
            info_json = load_project_info()
        except KeyError:
            print("project_info.json references environment variables that are not set.")
            print("Please ensure any environment variables it references are set and try again.")
            sys.exit(1)

        # FIXME: Remove these globals once we better encapsulate the build logic into controllers.
        global command_env
        controller = get_build_controller(args, info_file)
        command_env = controller.get_env()

    sys.exit(args.func(args))

if __name__ == "__main__":
    main()
