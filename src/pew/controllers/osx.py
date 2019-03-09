import os
import subprocess
import sys
import tempfile

from .base import BaseBuildController
from .utils import *

this_dir = os.path.abspath(os.path.dirname(__file__))
files_dir = os.path.join(this_dir, 'files')


class OSXBuildController(BaseBuildController):
    """
    This class manages OS X builds of PyEverywhere projects.
    """
    app_ext = '.app'

    def init(self):
        self.create_distribution()

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