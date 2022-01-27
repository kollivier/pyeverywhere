import glob
import logging
import subprocess
import sys
import tempfile
import time
import zipfile

from .base import BaseBuildController
from .utils import *

this_dir = os.path.abspath(os.path.dirname(__file__))
files_dir = os.path.join(this_dir, 'files')

mac_lib_exts = ['.a', '.dylib', '.plugin', '.so']

def codesign_mac(path, identity, entitlements=None):
    cmd = ["codesign", "--force", "-vvv", "--verbose=4", "--timestamp", "--sign", identity]

    if not entitlements:
        entitlements = os.path.join(files_dir, 'entitlements_default.plist')

    # Use Apple's hardened runtime so that apps can be signed for newer OS versions / certs.
    cmd.extend(["--entitlements", entitlements, "--options", "runtime"])

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


def codesign_zip_files(zip_path, identity):
    zip = zipfile.ZipFile(zip_path, 'r')

    temp_dir = tempfile.mkdtemp()
    cwd = os.getcwd()
    os.chdir(temp_dir)
    # extract the files from the zip first, then sign them and use the zip utility to update them.
    # we do this because zip has a weird feature where you can have two files with the same name
    # in an archive, and Python doesn't provide a method to actually overwrite the file. Thankfully,
    # this is the default behavior of the zip command.
    files_to_update = []
    try:
        for afile in zip.namelist():
            basename, ext = os.path.splitext(afile)
            if ext in mac_lib_exts:
                zip.extract(afile)
                files_to_update.append(afile)

        zip.close()

        for update_file in files_to_update:
            codesign_mac(update_file, identity)
            # it's important that the update file path passed in to the zip command is the same
            # as the relative path in the zip file, so that it overwrites that file instead of adding
            # a new one.
            cmd = ['zip', zip_path, update_file]
            print("Calling {}".format(' '.join(cmd)))
            subprocess.call(cmd)

    finally:
        os.chdir(cwd)
        shutil.rmtree(temp_dir)


def is_executable(filename):
    try:
        output = subprocess.check_output(['file', os.path.abspath(filename)])
        # Executable scripts are reported as 'text executable' so exclude those.
        return b"executable" in output and not b"text" in output
    except:
        raise

    return False


class OSXBuildController(BaseBuildController):
    """
    This class manages OS X builds of PyEverywhere projects.
    """
    app_ext = '.app'

    def init(self):
        pass

    def build(self, settings):
        returncode = self.distutils_build()
        if self.args.sign:
            print("The --sign argument is deprecated and will be removed in version 1.0. Please use pew codesign instead.")
            returncode = self.codesign()

        return returncode

    def codesign(self):
        identity = os.getenv('MAC_CODESIGN_IDENTITY', None)
        if not identity and "codesign" in self.project_info:
            identity = self.project_info['codesign']["osx"]["identity"]
            # TODO: Deprecate in 1.0
            if identity:
                print("Adding identity to project_info.json is deprected and will be removed in v1.0.")
                print("Please set MAC_CODESIGN_IDENTITY in your environment instead.")
        if not identity:
            print("MAC_CODESIGN_IDENTITY must be set for signing to work properly.")
            sys.exit(1)

        base_path = self.get_app_path()
        print("base_path = %r" % base_path)
        sign_paths = []
        zip_paths = []

        for root, dirs, files in os.walk(os.path.join(base_path, "Contents", "Resources")):
            # .framework is a bundle directory that codesign treats like a file to sign.
            for adir in dirs:
                fullpath = os.path.join(root, adir)
                if fullpath.endswith('.framework'):
                    sign_paths.append(fullpath)

            for afile in files:
                fullpath = os.path.join(root, afile)
                basename, ext = os.path.splitext(fullpath)
                # remove the .py files and the .pyo files as we shouldn't use them
                # running a .py file in the bundle can modify it.
                if ext in ['.py', '.pyo']:
                    if os.path.exists(basename + '.pyc'):
                        os.remove(fullpath)
                elif ext in mac_lib_exts:
                    sign_paths.append(fullpath)
                elif ext == '.zip':
                    zip_paths.append(fullpath)
                elif is_executable(fullpath):
                    sign_paths.append(fullpath)

        # we need to update the zip before we start codesigning.
        for path in zip_paths:
            codesign_zip_files(path, identity)

        sign_paths.extend(glob.glob(os.path.join(base_path, "Contents", "Frameworks", "*.framework")))
        sign_paths.extend(glob.glob(os.path.join(base_path, "Contents", "Frameworks", "*.dylib")))
        sign_paths.extend(glob.glob(os.path.join(base_path, "Contents", "MacOS", "*")))
        sign_paths.append(base_path)  # the main app needs to be signed last
        for path in sign_paths:
            codesign_mac(path, identity)

        cmd = ['codesign', "--verify", "--deep", "--verbose=4", base_path]
        logging.info("calling %s" % " ".join(cmd))
        if subprocess.call(cmd) != 0:
            print("Code signed application failed validation.")
            sys.exit(1)

        return 0

    def notarize(self):
        temp_dir = tempfile.mkdtemp()
        try:
            dev_email = os.getenv("MAC_DEV_ID_EMAIL")
            dev_pass = os.getenv("MAC_APP_PASSWORD")
            mac_notarization_provider = os.getenv("MAC_NOTARIZATION_PROVIDER")
            if not dev_email or not dev_pass:
                print("You must specify your Apple developer account information using the MAC_DEV_ID_EMAIL")
                print("and MAC_APP_PASSWORD environment variables in order to codesign the build.")
                sys.exit(1)
            bundle_id = self.project_info['identifier']
            dmg = self.get_dmg_path()

            assert os.path.exists(dmg), "Cannot find disk image to be notarized. Have you run pew package?"

            cmd = [
                "xcrun", "altool", "--notarize-app",
                "--file", dmg,
                "--type", "osx",
                "--username", dev_email,
                "--primary-bundle-id", bundle_id,
                "--output-format", "json",
            ]

            cmd.extend(['--password', dev_pass])
            if mac_notarization_provider:
                cmd.extend(['--asc-provider', mac_notarization_provider])
            print("Uploading app for notarization, this may take a while...")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            notarization_info = {}
            if result.stdout:
                notarization_info = json.loads(result.stdout.decode('utf-8'))

            print("Upload for notarization successful.")
            if result.returncode == 0 and self.args.wait:
                wait_timeout = 600
                wait_time = 0
                print("Waiting on notarization result, this may take some time...")
                notarization_result = None
                status = "Unknown"
                error_retries = 0
                request_uuid = notarization_info['notarization-upload']['RequestUUID']
                while notarization_result is None:
                    if wait_time > wait_timeout:
                        notarization_result = "Timed out"
                        break

                    cmd = ['xcrun', 'altool', '--notarization-info',
                           request_uuid, '-u', dev_email, '-p', dev_pass,
                           '--output-format', 'json']
                    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # This command may sporadically fail, so retry it a couple times before bailing.
                    if result.returncode != 0:
                        if error_retries < 5:
                            print(f"Get info command has failed {error_retries} times. Retrying command in 15 seconds...")
                            time.sleep(15)
                            wait_time += 15
                            error_retries += 1
                            continue
                        else:
                            notarization_result = "Unknown"
                            break

                    if result.stdout:
                        notarization_status = json.loads(result.stdout.decode('utf-8'))

                        status = notarization_status['notarization-info']['Status']
                        print(f"Current notarization status = '{status}'")
                        if status == 'in progress':
                            print("Checking again in 10 seconds...")
                            time.sleep(10)
                            wait_time += 10
                        else:
                            notarization_result = status
                    else:
                        print("No stdout output for notarization status call?")
                        notarization_result = "unknown"

                print(f"Notarization result: {notarization_result}")
                if notarization_result == 'success':
                    print("Stapling notarization to app.")
                    subprocess.call(['xcrun', 'stapler', 'staple', dmg])
                else:
                    print("Notarization failed. Please check your emails for details. Command output:")
                    print(result.stdout)
                    return 1
            elif result.returncode != 0:
                print("Attempt to notarize software failed. The following error was reported")
                if notarization_info and 'product-errors' in notarization_info:
                    for error in notarization_info['product-errors']:
                        print(error['message'])
                else:
                    print(result.stdout)

        finally:
            shutil.rmtree(temp_dir)

        return result.returncode

    def get_dmg_path(self):
        version = self.project_info['version']
        full_app_name = '{}-{}'.format(self.project_info['name'], version)
        path_name = full_app_name.replace(" ", "_").lower()

        if 'disk_image' in self.project_info:
            if 'filename' in self.project_info['disk_image']:
                path_name = self.project_info['disk_image']['filename']

        if 'build_number' in self.project_info:
            path_name += '-build{}'.format(self.project_info['build_number'])

        return os.path.join(self.get_package_dir(), '{}.dmg'.format(path_name))

    def dist(self):
        if not os.path.exists(self.get_app_path()):
            print("Built application does not exist. Please run `pew build` first and then re-run this command.")
            sys.exit(1)
        settings_file = self._create_dmgbuild_settings_file()

        output_path = self.get_dmg_path()

        full_app_name = os.path.splitext(os.path.basename(output_path))[0].replace('_', ' ')

        if 'disk_image' in self.project_info:
            if 'volume_name' in self.project_info['disk_image']:
                full_app_name = self.project_info['disk_image']['volume_name']

        if os.path.exists(output_path):
            os.remove(output_path)
        # dmgbuild is a Python script, so we need to run it using the python executable.
        dmgbuild_cmd = ['dmgbuild', '-s', settings_file, full_app_name, output_path]
        return self.run_cmd(dmgbuild_cmd)

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

        if 'build_number' in self.project_info:
            # Short version string is what the user sees when they check the version
            plist['CFBundleShortVersionString'] = self.project_info['version']
            # Bundle version is more internal, what we would commonly call the build number.
            plist['CFBundleVersion'] = self.project_info['build_number']

        py2app_opts = {
            "dist_dir": self.get_dist_dir(),
            "excludes": common_options["excludes"],
            "includes": common_options["includes"],
            'plist': plist,
            "packages": common_options["packages"],
            "site_packages": False,
            "strip": False
        }

        icons = get_value_for_platform("icons", "osx", None)
        if icons and not isinstance(icons, dict):
            py2app_opts['iconfile'] = icons

        return {'py2app': py2app_opts}

    def _create_dmgbuild_settings_file(self):
        values = {
            'app_path': self.get_app_path(),
            'background': 'builtin-arrow',
            'window_rect': '((20, 100000), (700, 300))',
            'app_icon_pos': '(140, 120)',
            'apps_icon_pos': '(500, 120)',
        }

        di_settings = self.project_info['disk_image'] if 'disk_image' in self.project_info else None
        if di_settings:
            values.update(di_settings)
            # make sure our background path can be found.
            if 'background' in di_settings:
                bgfile = di_settings['background']
                if not os.path.isabs(bgfile):
                    bgfile = os.path.abspath(os.path.join(self.project_root, bgfile))
                values['background'] = bgfile

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
