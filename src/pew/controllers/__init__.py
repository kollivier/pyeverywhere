"""
The controllers module contains classes for performing all platform init, build, and management operations.
Right now (11/5/2018) much of the controller logic still lives in the cli/tool.py file, but over time it should
all be migrated here.

This will allow for programmatic control over builds, configuration, etc. as an alternative to using the command line.
"""

from . import android
from . import base


def get_build_controller(platform, project_info):
    """
    Returns a build controller for the targeted platform.

    :param platform: platform being targeted (see pew.platforms for supported values)
    :param project_info: A dictionary containing the project_info.json data.
    :return:
    """
    if platform == 'android':
        return android.AndroidBuildController(project_info)

    return base.BaseBuildController(project_info)
