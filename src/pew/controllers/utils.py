import json
import os
import shutil
import subprocess

default_key = "default"
info_json = {}
pew_config = {}

cwd = os.getcwd()
thisdir = os.path.dirname(os.path.abspath(__file__))
rootdir = os.path.abspath(os.path.join(thisdir, "..", "..", ".."))


def get_pew_config():
    global pew_config

    config_dir = os.path.expanduser(os.path.join("~", ".pyeverywhere"))
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    config_file = os.path.join(config_dir, "config.json")

    if os.path.exists(config_file):
        pew_config = json.load(open(config_file))


def set_project_info(info):
    global info_json
    info_json = info


def get_value_for_platform(key, platform_name, default_return=None):
    global info_json
    if key in info_json:
        if platform_name in info_json[key]:
            return info_json[key][platform_name]
        elif default_key in info_json[key]:
            return info_json[key][default_key]

    return default_return


def get_value_for_config(key, config_name, default_return=None):
    if key in info_json:
        if "configs" in info_json[key] and config_name in info_json[key]["configs"]:
            return info_json[key]["configs"][config_name]
        elif default_key in info_json[key]:
            return info_json[key][default_key]

    return default_return


def copy_files(src_dir, build_dir, ignore_paths):
    def _logpath(path, names):
        for ignore_dir in ignore_paths:
            if ignore_dir in path:
                print("Ignoring %s" % path)
                return names
        print("Copying %s" % path)
        return []
    ignore = _logpath

    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)

    print("Copying source files to build tree, please wait...")
    shutil.copytree(src_dir, build_dir, ignore=ignore)

    shutil.copy2(os.path.join(cwd, "project_info.json"), build_dir)

def copy_data_files(data_files, build_dir):
    for out_dir, files in data_files:
        out_dir = os.path.join(build_dir, out_dir)
        for filename in files:
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            shutil.copy(filename, out_dir)


def copy_pew_module(build_dir):
    pew_src_dir = os.path.join(rootdir, "src", "pew")
    pew_dest_dir = os.path.join(build_dir, "pew")
    # For now, we want to allow developers to use their own customized pew module
    # until we offer more advanced configuration options. If they don't though,
    # just copy ours over.
    if not os.path.exists(pew_dest_dir):
        shutil.copytree(pew_src_dir, pew_dest_dir)
