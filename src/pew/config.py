import json
import logging
import os

from collections import Mapping, UserDict

cwd = os.getcwd()
project_config_file = os.path.join(cwd, 'project_info.json')

info_json = {}


def load_project_info(info_file=project_config_file):
    # TODO: Consider if we should be doing the env variable substitution at access time.
    # This has the benefit of allowing unused variables on a particular platform from
    # needing env vars set. The downsides are that it complicates implementation, and
    # means that the script could get quite far along before erroring out.
    data = os.path.expandvars(open(info_file, "r").read())
    if '$' in data:
        # print(data)
        # print(dict(os.environ))
        raise ValueError("Unresolved environment variables in project_info.json file.")
    global info_json
    info_json = json.loads(data)
    return info_json


def get_project_info():
    assert len(info_json) > 0, "Attempt to access project properties before load_project_info was called."
    return info_json
