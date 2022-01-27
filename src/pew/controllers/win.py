import glob
import sys

from .base import BaseBuildController
from .utils import *

this_dir = os.path.abspath(os.path.dirname(__file__))
files_dir = os.path.join(this_dir, 'files')


class WinBuildController(BaseBuildController):
    """
    This class manages OS X builds of PyEverywhere projects.
    """
    app_ext = '.exe'
    cefpython_excludes = []

    def init(self):
        pass

    def get_app_path(self):
        app_path = os.path.join(self.get_dist_dir(), '{}{}'.format('main', self.app_ext))
        if not os.path.exists(app_path):
            name = self.project_info['name']
            app_path =  os.path.join(self.get_dist_dir(), name, '{}{}'.format(name, self.app_ext))

        return app_path

    def get_install_generator_path(self):
        iscc_path = r'C:\Program Files (x86)\Inno Setup 6\iscc.exe'
        if not os.path.exists(iscc_path):
            iscc_path = r'C:\Program Files (x86)\Inno Setup 5\iscc.exe'
        if os.path.exists(iscc_path):
            return iscc_path

        return None

    def get_dll_excludes(self):
        """
        By default, py2exe detects and bundles a lot of system DLLs with the Python app. While this is necessary
        for some DLLs, it can actually cause issues because of conflicts between the version of the bundled DLL
        and the system DLL. This returns a list of system DLLs that we are not to bundle.

        :return: A list of system DLLs not to bundle with the app.
        """

        dll_excludes = [
            'combase.dll', 'credui.dll', 'crypt32.dll', 'cryptui.dll', 'd3d11.dll', 'd3d9.dll', 'dbghelp.dll',
            'dhcpcsvc.dll', 'dwmapi.dll', 'dwrite.dll', 'dxgi.dll', 'dxva2.dll', 'fontsub.dll', 'iertutil.dll',
            'iphlpapi.dll', 'mpr.dll', 'msvcp90.dll', 'ncrypt.dll', 'nsi.dll', 'oleacc.dll', 'oleacc.dll',
            'powrprof.dll', 'psapi.dll', 'psapi.dll', 'secur32.dll', 'setupapi.dll', 'setupapi.dll', 'urlmon.dll',
            'userenv.dll', 'userenv.dll', 'usp10.dll', 'webio.dll', 'winhttp.dll', 'wininet.dll', 'winnsi.dll',
            'wintrust.dll', 'wtsapi.dll', 'wtsapi32.dll'
        ]  # phew...

        return dll_excludes

    def get_build_options(self, common_options):
        py2exe_opts = {
            "dist_dir": self.get_dist_dir(),
            "dll_excludes": self.get_dll_excludes(),
            "packages": common_options['packages'],
            "excludes": common_options['excludes'] + self.cefpython_excludes,
            "includes": common_options['includes']
        }

        return {'py2exe': py2exe_opts}

    def get_platform_data_files(self):
        data_files = []
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
                    self.cefpython_excludes.append(module_name)

        except:  # TODO: Print the error information if verbose is set.
            pass  # if cefpython is not found, we fall back to the stock OS browser
        return data_files

    def build(self, settings):
        builder = get_value_for_platform('build_tool', 'win', 'py2exe')
        if builder == 'pyinstaller':
            return self.pyinstaller_build()
        else:
            self.distutils_build()

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
        if not install_generator or not os.path.exists(install_generator):
            print("Unable to create intallation package as InnoSetup cannot be found.")
            print("Currently, only Inno Setup 5 or above is supported for installer creation.")
            print("Please install Inno Setup if you wish to generate an installer.")
            sys.exit(1)

        return self.run_cmd([install_generator, install_script])

    def _create_innosetup_install_script(self, output_path):
        if not 'id' in self.project_info:
            print("On Windows, projects need a UUID. Please add the following to your project_info.json file:")
            import uuid
            print('"id": "{}"'.format(uuid.uuid4()))
            sys.exit(1)
        values = {
            'id': self.project_info['id'],
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
