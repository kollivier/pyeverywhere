import glob
import logging
import subprocess
import sys

from .base import BaseBuildController
from .utils import *

this_dir = os.path.abspath(os.path.dirname(__file__))
files_dir = os.path.join(this_dir, 'files')


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


class OSXBuildController(BaseBuildController):
    """
    This class manages OS X builds of PyEverywhere projects.
    """
    app_ext = '.app'

    def init(self):
        pass

    def build(self, settings):
        returncode = self.distutils_build()
        if "codesign" in self.project_info:
            base_path = self.get_app_path()
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
                codesign_mac(path, self.project_info["codesign"]["osx"]["identity"])

        return returncode

    def dist(self):
        if not os.path.exists(self.get_app_path()):
            print("Built application does not exist. Please run `pew build` first and then re-run this command.")
            sys.exit(1)
        settings_file = self._create_dmgbuild_settings_file()

        full_app_name = '{}-{}'.format(self.project_info['name'], self.project_info['version'])
        path_name = full_app_name.replace(" ", "_").lower()
        output_path = os.path.join(self.get_package_dir(), '{}.dmg'.format(path_name))
        if os.path.exists(output_path):
            os.remove(output_path)
        # dmgbuild is a Python script, so we need to run it using the python executable.
        dmgbuild_cmd = ['dmgbuild', '-s', settings_file, full_app_name, output_path]
        self.run_cmd(dmgbuild_cmd)

    def get_platform_data_files(self):
        return []

    def get_build_options(self, common_options):
        plist = {
            'CFBundleIdentifier': self.project_info["identifier"],
            # Make sure the browser will load localhost URLs
            'NSAppTransportSecurity': {
                'NSAllowsArbitraryLoads': True,
                'NSExceptionDomains': {
                    'localhost': {
                        'NSExceptionAllowsInsecureHTTPLoads': True
                    }
                }
            }
        }

        py2app_opts = {
            "dist_dir": self.get_dist_dir(),
            "excludes": common_options["excludes"],
            "includes": common_options["includes"],
            'plist': plist,
            "packages": common_options["packages"],
            "site_packages": True,
            "strip": False
        }

        return {'py2app': py2app_opts}

    def _create_dmgbuild_settings_file(self):
        values = {
            'app_path': self.get_app_path()
        }
        settings = open(os.path.join(files_dir, 'dmgbuild_settings_template.py')).read()
        # since this is a Python file, it is cleaner to just replace specific keys than to escape the special characters
        # in a Python that would trip up format or other string replacement approaches.
        for key in values:
            settings = settings.replace("{" + key + "}", values[key])

        output_filename = os.path.join(self.get_build_dir(), 'dmgbuild_settings.py')
        f = open(output_filename, 'w')
        f.write(settings)
        f.close()

        return output_filename