import glob
import hashlib
import logging
import os
import shutil
import subprocess
import sys
import zipfile

from . import downloader
from virtualenvapi.manage import VirtualEnvironment

__version__ = "0.9.1"

downloads_root_url = "http://files.pyeverywhere.org"

thisdir = os.path.dirname(os.path.abspath(__file__))
rootdir = os.path.abspath(os.path.join(thisdir, "..", ".."))

dir_macros = {
    "PROJECT_DIR": os.getcwd(),
    "PEW_DIR": rootdir,
}

pew_deps = {
    "ios": {
        "XCodeTemplate": {
            "url": "https://github.com/kollivier/PythonistaAppTemplate/archive/master.zip",
            "dest_dir": "${PROJECT_DIR}/native/ios",
            "checksum": "5854ef7719b4c7bfab0b08052025e3ff"
        }
    }
}

pew_cmds = {
    "android": [
        ["/bin/bash", "${PEW_DIR}/native/android/init.sh"],
        # ["/bin/bash", "${PEW_DIR}/native/android/build_p4a.sh"]
    ]
}


def resolve_macros(path):
    output = path
    for macro_name in dir_macros:
        output = output.replace("${%s}" % macro_name, dir_macros[macro_name])

    return output

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
        result = os.system("unzip -o %s -d %s" % (filename.replace(" ", "\\ "), extract_dir.replace(" ", "\\ ")))
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
            output_dir = resolve_macros(dep["dest_dir"])
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            output_file = os.path.join(output_dir, basename)
            print("output file = %s" % output_file)
            needs_download = True
            if os.path.exists(output_file) and "checksum" in dep:
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


def initialize_platform(platform_name, command_env, verbose=False):
    if platform_name in pew_cmds:
        for cmd in pew_cmds[platform_name]:
            final_cmd = []
            for arg in cmd:
                final_cmd.append(resolve_macros(arg))

            if verbose:
                print("Running command %r" % final_cmd)
            subprocess.check_call(final_cmd, env=command_env)


def copy_deps_to_build(deps, build_dir, dest_dir, python=None):
    venv_dir = os.path.join(build_dir, 'venv')
    env = VirtualEnvironment(venv_dir, python=python)
    env.open_or_create()

    venv_site_packages = glob.glob(os.path.join(venv_dir, 'lib', 'python*', 'site-packages'))[0]

    ignore_paths = []
    for path in os.listdir(venv_site_packages):
        ignore_paths.append(path)

    print("venv ignore paths = %r" % ignore_paths)

    for dep in deps:
        env.install(dep)

    for path in os.listdir(venv_site_packages):
        if not path in ignore_paths:
            fullpath = os.path.join(venv_site_packages, path)
            outpath = os.path.join(dest_dir, path)
            logging.info("Copying dependency: %s" % path)
            if os.path.isfile(fullpath):
                shutil.copy2(fullpath, outpath)
            else:
                shutil.copytree(fullpath, outpath)
        else:
            logging.info("Ignoring %s" % path)
