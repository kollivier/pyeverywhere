import os


class BaseBuildController:
    def __init__(self, project_info):
        self.project_info = project_info

    def get_env(self):
        """
        Gets the environment that is passed to build commands.

        :return: An environment based on os.environ with any environment variables required for the platform.
        """
        return os.environ

    def get_python_dist_folder(self):
        """
        Some platforms, particularly mobile platforms, require a cross-compiled version of Python for that platform.
        This method is used to get the path to the root of the cross-compiled Python distro.

        :return: Folder containing Python dist directory, or None if the platform does not create one.
        """
        return None

    def init(self):
        """
        Downloads and initializes any components needed to build for the chosen platform.
        """
        pass