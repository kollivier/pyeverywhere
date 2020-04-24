import getpass
import glob
import logging
import os
import shutil
import subprocess
import sys

from .base import BaseBuildController
from .utils import *

import pewtools


cwd = os.getcwd()
default_android_root = os.path.abspath(os.path.join(os.path.expanduser("~"), ".pyeverywhere", "native", "android"))
android_root = default_android_root

this_dir = os.path.dirname(os.path.abspath(__file__))
files_dir = os.path.join(this_dir, 'files', 'android')

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


class AndroidBuildController(BaseBuildController):
    """
    This class manages Android builds of PyEverywhere projects.
    """

    default_android_sdk = "29"
    default_android_build_tools = "29.0.2"
    default_arch = 'armeabi-v7a'
    default_requirements = ["openssl","python3","pyjnius","genericndkbuild"]
    android_ndk_version = 'r21'
    ant_version = '1.9.9'

    platform = 'android'
    bootstrap = 'webview'

    def get_sdk_platform(self):
        if sys.platform == 'darwin':
            return 'macosx'

        # TODO: Support Windows?
        return 'linux'

    def get_env(self):
        """
        Clones os.environ and adds Android and PyEverywhere specific environment variables. The resulting
        environment can be passed into any system or subprocess calls.
        :return: A customized Android environment
        """
        android_sdk, android_build_tools = self.get_android_sdk_info()
        android_env = os.environ.copy()
        android_env['ANDROIDAPI'] = android_sdk
        android_env['ANDROIDBUILDTOOLSVER'] = android_build_tools
        android_env['ANDROID_ROOT'] = android_root
        android_env['ANDROIDSDK'] = "{}/android-sdk-{}".format(android_root, self.get_sdk_platform())
        android_env['ANDROIDNDKVER'] = self.android_ndk_version
        android_env['ANDROIDNDK'] = "{}/android-ndk-{}".format(android_root, self.android_ndk_version)
        android_env['ANT_VERSION'] = self.ant_version
        android_env['ANT_HOME'] = "{}/apache-ant-{}".format(android_root, self.ant_version)
        paths = [
            android_env['PATH'],
            android_env['ANDROIDNDK'],
            '~/.local/bin',
            '{}/platform-tools'.format(android_env['ANDROIDSDK']),
            '{}/tools'.format(android_env['ANDROIDSDK']),
            '{}/bin'.format(android_env['ANT_HOME']),
        ]
        android_env['PATH'] = ':'.join(paths)
        print("PATH = {}".format(android_env['PATH']))

        return android_env

    def init(self):
        self.create_distribution()

    def build(self, settings):
        src_dir = self.get_source_dir()
        filename = self.project_info["name"].replace(" ", "")
        build_dir = self.get_build_dir()
        if self.args.config and self.args.config.strip() != "":
            build_dir = os.path.join(self.get_build_dir(), self.args.config)

        ignore_paths = settings['ignore_paths']
        data_files = settings['data_files']
        requirements = settings['requirements']
        extra_build_options = settings.get('extra_build_options', {})
        services = extra_build_options.get('services', [])
        permissions = set(extra_build_options.get('extra_permissions', []) + ['WRITE_EXTERNAL_STORAGE', 'ACCESS_NETWORK_STATE'])
        minsdk = str(extra_build_options.get("minsdk", ""))
        fileprovider_paths_filename = extra_build_options.get('fileprovider_paths_filename')
        sdk = str(extra_build_options.get("sdk", ""))

        cmd = ['p4a', 'apk',
                '--window',
                '--bootstrap', self.bootstrap,
                '--package', self.project_info['identifier'],
                '--name', filename,
                '--dist_name', self.get_dist_name(),
                '--version', self.project_info["version"],
                '--private', build_dir,
                '--arch', self.get_arch(),
                '--add-source', os.path.join(files_dir, 'org', 'kosoftworks', 'pyeverywhere'),
        ]

        if minsdk:
            cmd.extend(['--minsdk', minsdk])
            cmd.extend(['--ndk-api', minsdk])

        if sdk:
            cmd.extend(['--android-api', sdk])

        for service in services:
            cmd.extend(['--service', service])

        if fileprovider_paths_filename:
            cmd.extend(['--fileprovider-paths', os.path.join(src_dir, fileprovider_paths_filename)])

        for permission in permissions:
            cmd.extend(['--permission', permission])

        if len(requirements) > 0:
            requirements = ",".join(requirements)
        else:
            requirements = ",".join(self.default_requirements)
        cmd.extend(['--requirements', requirements])

        has_build_version_num = False
        if 'build_number' in self.project_info:
            try:
                int(self.project_info['build_number'])
                has_build_version_num = True
            except:
                pass

        if not has_build_version_num:
            print("Android builds require the build_number to be set to an integer in addition to the version field.")
            sys.exit(1)

        cmd.extend(['--numeric-version', self.project_info['build_number']])

        icon_file = get_value_for_platform("icons", "android")
        if icon_file:
            icon = os.path.abspath(icon_file)
            if not os.path.exists(icon):
                icon_dir = os.path.join(cwd, "icons", "android")
                icon = os.path.join(icon_dir, icon_file)
                logging.warning("Please specify a path to your icon that's relative to your project_info.json file")
                logging.warning("Specifying android icons by filename only is deprecated and will be removed")

            if not os.path.exists(icon):
                print("Could not find specified icon file: %s" % icon_file)
                sys.exit(1)

            cmd.extend(['--icon', icon])

        whitelist = get_value_for_platform("whitelist_file", "android")
        if whitelist and os.path.exists(whitelist):
            whitelist = os.path.abspath(whitelist)
            cmd.extend(['--whitelist', whitelist])
        launch = get_value_for_platform("launch_images", "android")
        if launch and os.path.exists(launch):
            launch = os.path.abspath(launch)
            cmd.extend(['--presplash', launch])
        orientation = get_value_for_platform("orientation", "android", "sensor")
        if orientation:
            cmd.extend(['--orientation', orientation])
        intent_filters = get_value_for_platform("intent_filters", "android")
        if intent_filters and os.path.exists(intent_filters):
            intent_filters = os.path.abspath(intent_filters)
            cmd.extend(['--intent-filters', intent_filters])

        keystore = ""
        keyalias = ""
        keypasswd = ""

        build_type = ""
        if self.args.release:
            build_type = "release"
            signing = get_value_for_platform("codesign", "android")
            if signing:
                keystore = os.path.abspath(signing['keystore'])
                keyalias = signing['alias']
                if 'passwd' in signing:
                    keypasswd = signing['passwd']
                else:
                    keypasswd = getpass.getpass()

                cmd.extend(['--keystore', keystore, '--signkey', keyalias, '--keystorepw', keypasswd])

        if build_type == "release":
            cmd.append('--release')

        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)

        parent_dir = os.path.dirname(build_dir)
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        copy_files(src_dir, build_dir, ignore_paths)
        copy_data_files(data_files, build_dir)

        venv_dir = os.path.join(build_dir, "venv")
        if not os.path.exists(venv_dir):
            os.makedirs(venv_dir)
        if "packages" in self.project_info:
            python = "python2.7"
            pewtools.copy_deps_to_build(self.project_info["packages"], venv_dir, build_dir, python)
        copy_pew_module(build_dir)

        shutil.rmtree(venv_dir)

        result = self.run_cmd(cmd)

        apks = glob.glob(os.path.join(cwd, '*.apk'))
        for apk in apks:
            dest_path = os.path.join(self.get_dist_dir(), os.path.basename(apk))
            os.rename(apk, dest_path)

        return result

    def get_arch(self):
        arch = self.default_arch
        if '64bit' in self.args.extra_args:
            arch = 'arm64-v8a'
        return arch

    def get_dist_name(self):
        return "{}_dist".format(self.project_info["name"].replace(" ", ""))

    def get_python_dist_folder(self):
        return os.path.expanduser('~/.python-for-android/dists/{}'.format(self.get_dist_name()))

    def create_distribution(self):
        """
        Creates an Android python distribution that meets the project specifications. Throws an error upon
        failure.
        """
        cmd = [
            'p4a',
            'create',
            '--arch', self.get_arch(),
            '--dist_name', self.get_dist_name(),
            '--bootstrap', self.bootstrap,

        ]
        reqs = get_value_for_platform("requirements", self.platform, self.default_requirements)
        if len(reqs) > 0:
            cmd.extend(['--requirements', ','.join(reqs)])

        return self.run_cmd(cmd)

    def get_android_sdk_info(self):
        """
        Retrieves Android SDK and platform tools version info. If not set by the project, default values are used.
        :return: A tuple of (android_sdk_version, android_build_tools_version)
        """
        android_sdk = self.default_android_sdk
        android_build_tools = self.default_android_build_tools
        if "sdks" in self.project_info and "android" in self.project_info["sdks"]:
            android_sdk_info = self.project_info["sdks"]["android"]
            if "target_sdk" in android_sdk_info:
                android_sdk = str(android_sdk_info["target_sdk"])
            if "build_tools" in android_sdk_info:
                android_build_tools = android_sdk_info["build_tools"]

        return android_sdk, android_build_tools
