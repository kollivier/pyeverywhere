import json
import os
import subprocess
import sys

from distutils.core import setup


class BaseBuildController:
    """
    The BaseBuildController is the base class for all platform-specific build controllers. It contains common methods
    and logic needed by most or all of the platform-specific build controllers.
    """

    # default values to be overridden by native subclasses.
    app_ext = ''

    def __init__(self, project_info_file, cmd_args):
        self.project_root = os.path.dirname(project_info_file)
        self.project_info = json.loads(open(project_info_file).read())
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
        if self.args.config:
            platform_dir = os.path.join(platform_dir, self.args.config)

        if not os.path.exists(platform_dir):
            os.makedirs(platform_dir)
        return platform_dir

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

    def build(self):
        """
        Creates a native app for the platform specified to the PyEverywhere command line interface.
        Build outputs will go to the build directory (see get_build_dir()), while any final, packagable outputs
        will go to the distribution directory (see get_dist_dir()).
        """
        pass

    def dist(self):
        """
        Creates a distributable package for your app. This command can only be run after a successful build.
        """
        pass

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
        data_files = [('.', [os.path.join(self.project_root, "project_info.json")])]

        if "packages" in self.project_info:
            packages.extend(self.project_info["packages"])

        if "includes" in self.project_info:
            includes.extend(self.project_info["includes"])

        if "excludes" in self.project_info:
            excludes.extend(self.project_info["excludes"])

        dist_dir = self.get_dist_dir()

        # this is needed on Windows for py2exe to find scripts in the src directory
        sys.path.append(os.path.join(self.project_root, 'src'))

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

        common_options = {
            'packages': packages,
            "excludes": excludes,
            "includes": includes
        }

        return setup(name=name,
              version=self.project_info["version"],
              options=self.get_build_options(common_options),
              app=['src/main.py'],
              windows=['src/main.py'],
              data_files=data_files
        )

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
