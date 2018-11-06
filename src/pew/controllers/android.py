import os
import subprocess
import sys

from .base import BaseBuildController
from .utils import *


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


class AndroidBuildController(BaseBuildController):
    """
    This class manages Android builds of PyEverywhere projects.
    """

    default_android_sdk = "19"
    default_android_build_tools = "23.0.3"
    default_requirements = ["openssl","python2","pyjnius","genericndkbuild"]
    android_ndk_version = 'r10e'
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
            android_env['ANDROIDNDK'],
            '~/.local/bin',
            '{}/platform-tools'.format(android_env['ANDROIDSDK']),
            '{}/tools'.format(android_env['ANDROIDSDK']),
            '{}/bin'.format(android_env['ANT_HOME']),
            android_env['PATH']
        ]
        android_env['PATH'] = ':'.join(paths)
        print("PATH = {}".format(android_env['PATH']))

        return android_env

    def init(self):
        self.create_distribution()

    def create_distribution(self):
        """
        Creates an Android python distribution that meets the project specifications. Throws an error upon
        failure.
        """
        cmd = [
            'p4a',
            'create',
            '--dist_name', "{}_dist".format(self.project_info["name"].replace(" ", "")),
            '--bootstrap', self.bootstrap,

        ]
        reqs = get_value_for_platform("requirements", self.platform, self.default_requirements)
        if len(reqs) > 0:
            cmd.extend(['--requirements', ','.join(reqs)])

        subprocess.call(cmd, env=self.get_env())

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
