"""
The controllers module contains classes for performing all platform init, build, and management operations.
Right now (11/5/2018) much of the controller logic still lives in the cli/tool.py file, but over time it should
all be migrated here.

This will allow for programmatic control over builds, configuration, etc. as an alternative to using the command line.
"""

from . import android, base, osx


def get_build_controller(args, project_info_file):
    """
    Returns a build controller for the targeted platform.

    :param platform: platform being targeted (see pew.platforms for supported values)
    :param project_info: A dictionary containing the project_info.json data.
    :return:
    """
    impl = base.BaseBuildController
    if args.platform == 'android':
        impl = android.AndroidBuildController
    if args.platform == 'osx':
        impl = osx.OSXBuildController

    return impl(project_info_file, args)
