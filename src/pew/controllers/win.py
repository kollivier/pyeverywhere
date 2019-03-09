import os
import subprocess
import sys
import tempfile

from .base import BaseBuildController
from .utils import *

this_dir = os.path.abspath(os.path.dirname(__file__))
files_dir = os.path.join(this_dir, 'files')


class WinBuildController(BaseBuildController):
    """
    This class manages OS X builds of PyEverywhere projects.
    """
    app_ext = '.exe'

    def init(self):
        pass

    def get_app_path(self):
        return os.path.join(self.get_dist_dir(), '{}{}'.format('main', self.app_ext))

    def get_install_generator_path(self):
        return r'C:\Program Files (x86)\Inno Setup 5\iscc.exe'

    def dist(self):
        if not os.path.exists(self.get_app_path()):
            print("Path = {}".format(self.get_app_path()))
            print("Built application does not exist. Please run `pew build` first and then re-run this command.")
            sys.exit(1)

        full_app_name = '{}-{}'.format(self.project_info['name'], self.project_info['version'])
        path_name = full_app_name.replace(" ", "_").lower()
        output_path = os.path.join(self.get_package_dir(), '{}.exe'.format(path_name))

        install_script = self._create_innosetup_install_script(output_path)
        install_generator = self.get_install_generator_path()
        if not os.path.exists(install_generator):
            print("Unable to create intallation package as the installer generator cannot be found at: ")
            print(install_generator)
            print("Currently, only Inno Setup 5 is supported for installer creation.")
            print("Please install Inno Setup 5 if you wish to generate an installer.")
            sys.exit(1)

        self.run_cmd([install_generator, install_script])

    def _create_innosetup_install_script(self, output_path):
        values = {
            'app_path': os.path.dirname(self.get_app_path()),
            'app_name': self.project_info['name'],
            'app_version': self.project_info['version'],
            'exe_name': os.path.basename(self.get_app_path()),
            'output_dir': os.path.dirname(output_path),
            'output_filename': os.path.splitext(os.path.basename(output_path))[0]
        }
        iss_install_script = open(os.path.join(files_dir, 'win_innosetup_template.iss')).read()
        iss_install_script = iss_install_script % values

        output_filename = os.path.join(self.get_build_dir(), 'innosetup_install_script.iss')
        f = open(output_filename, 'w')
        f.write(iss_install_script)
        f.close()

        return output_filename