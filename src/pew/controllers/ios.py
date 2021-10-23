import glob
import subprocess
import sys

# if we're not on Mac, don't rely on this library. This controller doesn't run on other platforms
# so don't raise an error there.
try:
    import pbxproj
except:
    if sys.platform.startswith('darwin'):
        raise
    else:
        pass

import plistlib

import pewtools

from .base import BaseBuildController
from .utils import *

this_dir = os.path.abspath(os.path.dirname(__file__))
files_dir = os.path.join(this_dir, 'files')


class IOSBuildController(BaseBuildController):
    """
    This class manages OS X builds of PyEverywhere projects.
    """
    app_ext = '.app'

    def init(self):
        pass

    def build(self, settings):
        returncode = 0

        build_dir = self.get_build_dir()
        project_dir = os.path.join(self.project_root, "native", "ios", "PythonistaAppTemplate-master")
        if not os.path.exists(project_dir):
            print("iOS support files not downloaded for this project. Run 'pew init ios' first.")
            sys.exit(1)
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)

        src_dir = self.get_source_dir()

        # TODO: Refactor this code into smaller chunks for better readability
        project_build_dir = os.path.join(build_dir, os.path.basename(project_dir))
        shutil.copytree(project_dir, project_build_dir)
        project_xcode_dir = os.path.join(project_build_dir, "PythonistaAppTemplate")
        plist_file = os.path.join(project_xcode_dir, "Info.plist")
        if os.path.exists(plist_file):
            version_short = self.project_info["version"].split(".")
            version_short = ".".join(version_short[:3])
            plist = plistlib.readPlist(plist_file)
            plist['CFBundleIdentifier'] = self.project_info["identifier"]
            plist['CFBundleName'] = plist['CFBundleDisplayName'] = self.project_info["name"]
            plist['CFBundleVersion'] = self.project_info["version"]
            plist['CFBundleIconName'] = 'AppIcon'
            plist['CFBundleShortVersionString'] = version_short
            plist['UIStatusBarHidden'] = get_value_for_platform("hide_status_bar", "ios", True)

            # These are needed because the Python libraries contain references to
            # libs which need permissions.
            plist['NSCalendarsUsageDescription'] = "This app requires access to your calendar information."
            plist['NSPhotoLibraryUsageDescription'] = "This app requires access to your photo library."
            plist['NSBluetoothPeripheralUsageDescription'] = "This app requires access to a bluetooth peripheral."

            icons = get_value_for_platform("icons", "ios", [])
            if len(icons) > 0 and not isinstance(icons, dict):
                appicon_dir = os.path.join(project_xcode_dir, "Assets.xcassets", "AppIcon.appiconset")
                contents_file = os.path.join(appicon_dir, "Contents.json")
                contents = json.loads(open(contents_file).read())

                for icon_data in contents["images"]:
                    scale = 1
                    if "scale" in icon_data:
                        scale = int(icon_data["scale"].replace("x", ""))
                    if "size" in icon_data:
                        width, height = icon_data["size"].split("x")
                        scaled_width = float(width) * scale
                        # FIXME: switch to parsing the png header to get image dimensions
                        # rather than expecting a certain filename convention. See here for info:
                        # https://stackoverflow.com/questions/8032642/how-to-obtain-image-size-using-standard-python-class-without-using-external-lib
                        best_icon = None
                        for icon in icons:
                            basename = os.path.splitext(icon)[0]
                            last_dash = basename.rfind("-")
                            size = basename[last_dash + 1:]
                            try:
                                size = int(size)
                            except:
                                continue
                            if size == scaled_width:
                                best_icon = icon
                                break
                            elif size > scaled_width:
                                if best_icon:
                                    icon_size = os.path.splitext(best_icon)[0].split("-")[1]
                                    if int(icon_size) < size:
                                        continue
                                best_icon = icon

                        if best_icon:
                            full_icon_path = os.path.join(cwd, "icons", "ios", best_icon)
                            filename = None
                            if "filename" in icon_data:
                                dest_icon_path = os.path.join(appicon_dir, icon_data["filename"])
                                shutil.copyfile(full_icon_path, dest_icon_path)
                            else:
                                print("No filename listed for {}".format(scaled_width))
                        else:
                            print("Could not find icon for size {}".format(scaled_width))

            orientation_value = get_value_for_platform("orientation", "ios", "both")
            orientations = [orientation_value]
            if orientation_value == 'all' or orientation_value == 'sensor':
                orientations = ['landscape', 'portrait']
            else:
                plist['UIRequiresFullScreen'] = True

            launch_images = get_value_for_platform("launch_images", "ios", [])
            if len(launch_images) > 0:
                del plist['UILaunchStoryboardName']
                images = []
                for image in launch_images:
                    image_path = os.path.abspath(os.path.join("icons", "ios", image))
                    width, height = get_image_info(image_path)
                    orientation = 'Portrait'

                    size = '{%d, %d}' % (width, height)
                    if width > height:
                        orientation = 'Landscape'
                        # The dimensions for the ImageSize must be specified as if the
                        # image was portrait, even when it's a landscape image.
                        size = '{%d, %d}' % (height, width)
                    filename = os.path.basename(image_path)
                    basename = os.path.splitext(filename)[0]

                    image_keys = {
                        'UILaunchImageMinimumOSVersion': '7.0',
                        'UILaunchImageOrientation': orientation,
                        'UILaunchImageName': basename,
                        'UILaunchImageSize': size
                    }
                    images.append(image_keys)
                plist['UILaunchImages'] = images

            ios_orientations = []
            for orientation in orientations:
                if orientation == 'landscape':
                    ios_orientations.extend(
                        ['UIInterfaceOrientationLandscapeLeft', 'UIInterfaceOrientationLandscapeRight'])
                if orientation == 'portrait':
                    ios_orientations.extend(
                        ['UIInterfaceOrientationPortrait', 'UIInterfaceOrientationPortraitUpsideDown'])

            plist['UISupportedInterfaceOrientations'] = ios_orientations
            plist['UISupportedInterfaceOrientations~ipad'] = ios_orientations

            plistlib.writePlist(plist, plist_file)

        dest_dir = os.path.join(project_build_dir, "Script")
        script_ignore_paths = settings['ignore_paths'] + self.project_info['asset_dirs']
        copy_files(src_dir, dest_dir, script_ignore_paths)
        self.generate_project_info_file()
        copy_pew_module(dest_dir)
        copy_data_files(self.get_app_data_files(), project_build_dir)

        project_file = os.path.join(project_build_dir, "PythonistaAppTemplate.xcodeproj")
        config_file = os.path.join(project_file, "project.pbxproj")
        project = pbxproj.XcodeProject.load(config_file)

        for icon_file in glob.glob(os.path.join("icons", "ios", "*")):
            icon_path = os.path.abspath(icon_file)
            icon_filename = os.path.basename(icon_file)
            dest_path = os.path.join(project_build_dir, icon_filename)
            shutil.copy(icon_path, dest_path)
            project.add_file(icon_filename, force=False)

        if "codesign" in self.project_info and "ios" in self.project_info["codesign"]:
            ios_codesign = self.project_info["codesign"]["ios"]

            # Don't use the pre-defined app icon
            project.remove_flags('PRODUCT_BUNDLE_IDENTIFIER', 'com.omz-software.PythonistaAppTemplate')
            project.remove_flags('ASSETCATALOG_COMPILER_APPICON_NAME', 'AppIcon')

            # TODO: Add support for manual signing
            for target in project.objects.get_targets():
                project_root = project.objects[project.rootObject]
                project_root.set_provisioning_style('Automatic', target)
                project_root.attributes.TargetAttributes[target.get_id()]["DevelopmentTeam"] = ios_codesign[
                    "development_team"]
        project.save()

        # FIXME: This currently only works for pure-Python modules.
        pewtools.copy_deps_to_build(settings['requirements'], build_dir, dest_dir)

        if os.path.exists(config_file):
            f = open(config_file, 'r')
            config = f.read()
            f.close()

            config = config.replace("My App", self.project_info["name"])
            f = open(config_file, 'w')
            f.write(config)
            f.close()
        else:
            print("Unable to update XCode project config file. You may need to manually change some settings.")

        self.run_cmd(["open", project_file.replace(" ", "\\ ")])

        return returncode

    def dist(self):
        return self.build()

    def get_platform_data_files(self):
        return []
