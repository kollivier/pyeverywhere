import hashlib
import os
import sys
import zipfile

import downloader

__version__ = "0.9.1"

downloads_root_url = "http://files.pyeverywhere.org"

pew_deps = {
    "ios": {
        "XCodeTemplate": {
            "url": "%s/pythonista/1.6beta/PythonistaProjectTemplate.zip" % downloads_root_url,
            "dest_dir": "${PROJECT_DIR}/native/ios",
            "checksum": "c97a709f25bfb2275d911536b498a429"
        }
    },
    "android": {
        "AndroidSDK": {
            "url": "",
            "dest_dir": "${PROJECT_DIR}/native/android",
        }
    }
}


def unzip_file(filename, extract_dir):
    """
    On Unix/Mac, Python's zip file doesn't always correctly handle constructs like symlinks,
    so the easiest approach is to just use the system unzip tool.
    """
    if sys.platform.startswith('win'):
        zip = zipfile.ZipFile(filename, 'r')
        zip.extractall(extract_dir)
        zip.close()
    else:
        result = os.system("unzip -o -d %s %s" % (extract_dir, filename.replace(" ", "\\ ")))
        if result != 0:
            print("Error unzipping files. Aborting update installation.")
            return


def get_checksum_for_file(filename):
    block_size = 8192
    md5 = hashlib.md5()
    with open(filename, "rb") as f:
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()


def get_dependencies_for_platform(platform_name):
    if platform_name in pew_deps:
        platform_deps = pew_deps[platform_name]
        for dep_name in platform_deps:
            dep = platform_deps[dep_name]
            url = dep["url"]
            basename = url[url.rfind("/")+1:]
            output_dir = dep["dest_dir"].replace("${PROJECT_DIR}", os.getcwd())
            output_file = os.path.join(output_dir, basename)
            print("output file = %s" % output_file)
            needs_download = True
            if os.path.exists(output_file):
                checksum = get_checksum_for_file(output_file)
                if checksum == dep["checksum"]:
                    needs_download = False
                else:
                    # make sure we don't keep trying to download with an old, bad file around
                    print("Removing file?")
                    os.remove(output_file)
                    if os.path.exists(output_file):
                        print("Whaaa?")

            if not os.path.exists(output_file) and needs_download:
                downloader.download_file(dep["url"], output_file)
                if os.path.exists(output_file):
                    checksum = get_checksum_for_file(output_file)
                    if checksum != dep["checksum"]:
                        raise Exception("Dependency %s did not download correctly." % output_file)

            if os.path.splitext(output_file)[1] == ".zip":
                unzip_file(output_file, output_dir)

    else:
        print("Could not find any dependencies for %s." % platform_name)