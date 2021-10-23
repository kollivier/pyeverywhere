import json
import logging
import os
import shutil
import subprocess
import sys

from distutils.core import setup

from .utils import get_value_for_platform
from ..config import load_project_info


class BaseBuildController:
    """
    The BaseBuildController is the base class for all platform-specific build controllers. It contains common methods
    and logic needed by most or all of the platform-specific build controllers.
    """

    # default values to be overridden by native subclasses.
    app_ext = ''

    def __init__(self, project_info_file, cmd_args):
        self.project_root = os.path.dirname(project_info_file)
        self.project_info = load_project_info(project_info_file)
        self.args = cmd_args
        self.platform = self.args.platform

    def get_app_path(self):
        """
        Returns the path to the application. This code does not assume nor expect the app to have been created,
        so calling code should check for existance before using this file or directory.

        This also may not be a fully self-contained file or folder. You may need to package other files in the
        same directory, in subdirectories, or even package app dependencies to get a fully working app.

        :return: A string with the built application file.
        """

        return os.path.join(self.get_dist_dir(), '{}{}'.format(self.project_info['name'], self.app_ext))

    def get_env(self):
        """
        Gets the environment that is passed to build commands.

        :return: An environment based on os.environ with any environment variables required for the platform.
        """
        return os.environ

    def get_source_dir_relative(self):
        """
        Returns the directory relative to the project root where source files live.
        Defaults to "src".
        :return: A string to an existing directory where source files live.
        """
        source_dir = 'src'
        if 'source_dir' in self.project_info:
            source_dir = self.project_info['source_dir']
        return source_dir

    def get_source_dir(self):
        """
        Returns the root directory where the application's source code lives. Defaults to <project_root>/src.

        :return: A string to an existing directory that contain's the application's source code.
        """
        return os.path.join(self.project_root, self.get_source_dir_relative())

    def get_main_script_path(self):
        """
        Returns the relative path to the main Python script for running the application.
        :return: A string to a main.py Python script.
        """
        return os.path.join(self.get_source_dir_relative(), 'main.py')

    def get_import_hooks_script_path(self):
        """
        Returns the relative path to a Python script with extra import hooks, if needed.
        :return: A string to a main.py Python script, or None if not specified.
        """

        if 'import_hooks_file' in self.project_info:
            return os.path.join(self.get_source_dir_relative(), self.project_info['import_hooks_file'])

        return None

    def get_dist_dir(self):
        """
        Returns the directory relative to the project build root where build outputs to be packaged are stored.
        Defaults to the 'dist/<platform>' directory of the project root.

        If the directory does not exist, it will be created.

        :return: A string path to an existing directory.
        """
        return self._get_platform_dir('dist')

    def get_build_dir(self):
        """
        Returns the directory relative to the project root where all build outputs will be stored.
        Defaults to the 'build/<platform>' directory of the project root.

        If the directory does not exist, it will be created.

        :return: A string path to an existing directory.
        """
        return self._get_platform_dir('build')

    def get_package_dir(self):
        """
        Returns the directory where packaging outputs, e.g. installers, package manager packages, etc. will be stored.
        Defaults to the 'package/<platform>' directory of the project root.

        If the directory does not exist, it will be created.

        :return: A string path to an existing directory.
        """
        return self._get_platform_dir('package')

    def _get_platform_dir(self, dir_name):
        """
        Internal method for retrieving platform-specific directories, such as the build and dist sub-directories.

        :param dir_name: Name of the sub-directory for which to retrieve the platform-specific path.

        :return: A string path to an existing directory.
        """
        platform_dir = os.path.join(self.project_root, dir_name, self.platform)
        if hasattr(self.args, 'config') and self.args.config:
            platform_dir = os.path.join(platform_dir, self.args.config)

        if not os.path.exists(platform_dir):
            os.makedirs(platform_dir)
        return platform_dir

    def get_app_data_files(self):
        asset_dirs = []
        data_files = []
        source_dir_name = self.get_source_dir_relative()
        if "asset_dirs" in self.project_info:
            asset_dirs = self.project_info["asset_dirs"]
        else:
            message = "WARNING: Specifying asset_dirs with a list of directories for your app's static files is now required. Please add \"asset_dirs\": ['{}/files'] to your project_info.json file.".format(source_dir_name)
            print(message)
            asset_dirs = [os.path.join(source_dir_name, 'files')]

        for asset_dir in asset_dirs:
            for root, dirs, files in os.walk(asset_dir):
                files_in_dir = []
                for afile in files:
                    if not afile.startswith("."):
                        files_in_dir.append(os.path.join(root, afile))
                if len(files_in_dir) > 0:
                    data_files.append((root.replace("{}/".format(source_dir_name), ""), files_in_dir))

        return data_files

    def get_python_dist_folder(self):
        """
        Some platforms, particularly mobile platforms, require a cross-compiled version of Python for that platform.
        This method is used to get the path to the root of the cross-compiled Python distro.

        :return: Folder containing Python dist directory, or None if the platform does not create one.
        """
        return None

    def get_build_options(self):
        """
        Returns a platform-specific dictionary of build options, ready to pass to setup's options argument.

        :return: A dictionary of build options.
        """

    def get_platform_data_files(self):
        """
        This function returns a list of any platform or dependency-specific files that need bundled with the app
        that are not automatically bundled by the platform app build tools.

        :return: A list of (subdir, [files...]) tuples in the format expected by setup's data_files argument.
        """

    def init(self):
        """
        Downloads and initializes any components needed to build for the chosen platform.
        """
        pass

    def build(self, settings):
        """
        Creates a native app for the platform specified to the PyEverywhere command line interface.
        Build outputs will go to the build directory (see get_build_dir()), while any final, packagable outputs
        will go to the distribution directory (see get_dist_dir()).
        """
        raise NotImplementedError("Build support has not been implemented for this platform.")

    def codesign(self):
        """
        Code signs a native application. Each platform must specify environment variables containing
        the secrets for code signing.

        On Mac:
        - MAC_CODESIGN_IDENTITY: This is the name of your signing cert.
        For notarization:
        - MAC_DEV_ID_EMAIL: The email address of the developer account signing the build.
        - MAC_APP_PASSWORD: Application-specific password, see Apple's notarization instructions for more.
        - MAC_NOTARIZATION_PROVIDER: If the account belongs to multiple teams, use this to specify which should notarize.
        """
        raise NotImplementedError("Code signing support has not been implemented for this platform.")

    def notarize(self):
        raise NotImplementedError("Notarization is currently a Mac-specific action.")

    def dist(self):
        """
        Creates a distributable package for your app. This command can only be run after a successful build.
        """
        pass

    def generate_project_info_file(self):
        # The project config source file may have unresolved values in the form of environment
        # variables. Instead of copying the source file, we export the loaded data to a file
        # (with all values resolved) and bundle that file instead.
        built_project_info = os.path.join(self.get_build_dir(), "project_info.json")
        with open(built_project_info, 'w', encoding='utf-8') as output:
            output.write(json.dumps(self.project_info, indent=4, ensure_ascii=False))
        return built_project_info

    def get_data_files(self):
        data_files = [('.', [self.generate_project_info_file()])]

        data_files.extend(self.get_app_data_files())

        return data_files

    def distutils_build(self):
        if self.platform == 'osx':
            import py2app

            sys.argv = [sys.argv[0], "py2app"]
        else:
            import py2exe
            sys.argv = [sys.argv[0], "py2exe"]

        includes = []
        excludes = []
        packages = []
        data_files = [('.', [self.generate_project_info_file()])]

        if "packages" in self.project_info:
            packages.extend(get_value_for_platform("packages", self.platform, []))

        if "includes" in self.project_info:
            includes.extend(get_value_for_platform("includes", self.platform, []))

        if "excludes" in self.project_info:
            excludes.extend(get_value_for_platform("excludes", self.platform, []))

        dist_dir = self.get_dist_dir()

        # this is needed on Windows for py2exe to find scripts in the src directory
        sys.path.append(self.get_source_dir())

        data_files.extend(self.get_app_data_files())
        data_files.extend(self.get_platform_data_files())

        print("data_files = %r" % data_files)
        name = self.project_info["name"]
        # workaround a bug in py2exe where it expects strings instead of Unicode
        if self.platform == 'win':
            name = name.encode('utf-8')

        # Make sure py2exe bundles the modules that six references
        # the Py3 version of py2exe natively supports this so this is a 2.x only fix
        if sys.version_info[0] == 2:
            includes.extend(["urllib", "SimpleHTTPServer"])
        else:
            # The Py3 version, however, gets into infinite recursion while importing parse.
            # see https://stackoverflow.com/questions/29649440/py2exe-runtimeerror-with-tweepy
            excludes.append("six.moves.urllib.parse")

        excludes.append('tkinter')

        common_options = {
            'packages': packages,
            "excludes": excludes,
            "includes": includes
        }

        setup(name=name,
              version=self.project_info["version"],
              options=self.get_build_options(common_options),
              app=[self.get_main_script_path()],
              windows=[self.get_main_script_path()],
              data_files=data_files
        )

        return 0

    def pyinstaller_build(self):
        import PyInstaller.__main__

        # if we don't do this, PyInstaller will ask to confirm overwrite.
        if os.path.exists(self.get_dist_dir()):
            shutil.rmtree(self.get_dist_dir(), ignore_errors=True)

        cmd = ['-D', '-n', self.project_info['name'], '--distpath', self.get_dist_dir(), '--noconsole']

        icon = get_value_for_platform('icons', self.platform)
        if icon and not isinstance(icon, dict):
            cmd.append('--icon={}'.format(os.path.abspath(icon)))

        if 'packages' in self.project_info:
            for pkg in self.project_info['packages']:
                cmd.append('--hidden-import={}'.format(pkg))

        if 'includes' in self.project_info:
            for include in self.project_info['includes']:
                cmd.append('--hidden-import={}'.format(include))

        if 'excludes' in self.project_info:
            for exclude in self.project_info['excludes']:
                cmd.append('--exclude-module={}'.format(exclude))

        try:
            # cefpython has a hook file to help PyInstaller package it, so we add it here.
            import cefpython3
            this_dir = os.path.dirname(os.path.abspath(__file__))
            src_dir = os.path.join(os.getcwd())
            this_dir_rel = os.path.relpath(this_dir, src_dir)
            # PyInstaller expects hook dirs to be relative to the CWD, not absolute paths.
            cmd.append('--additional-hooks-dir={}'.format(os.path.join(this_dir_rel, 'files', 'hooks')))
        except:
            logging.info("Could not find CEFPython, so not installing hook.")
            pass

        data_files = self.get_data_files()
        for data in data_files:
            dest = data[0]
            files = data[1]
            for afile in files:
                data_str = '{}{}{}'.format(afile.replace('/', os.sep), os.pathsep, dest)
                cmd.append('--add-data={}'.format(data_str))

        cmd.append(self.get_main_script_path())
        import_hooks_file = self.get_import_hooks_script_path()
        if import_hooks_file:
            if os.path.exists(import_hooks_file):
                cmd.append(self.get_import_hooks_script_path())
            else:
                print("Cannot find {}".format(import_hooks_file))
                print("Make sure the file exists and the path is relative to your project's source directory.")

        # run directly via Python as we can hit command line max length limits
        PyInstaller.__main__.run(cmd)

    def run_cmd(self, cmd):
        """
        Runs a program on the computer with any environment settings needed to perform builds on the given platform.

        :param cmd: A list with the command to run and arguments. The first argument should be the command executable.

        :return: The return code of the program, typically 0 is used to indicate success.
        """
        stdout = None
        if self.args.verbose:
            print("Running command: {}".format(' '.join(cmd)))
            # stdout = subprocess.PIPE
        return subprocess.call(cmd, env=self.get_env(), stdout=stdout, stderr=stdout)
