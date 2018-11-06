import json
import os


default_key = "default"
info_json = {}
pew_config = {}


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
