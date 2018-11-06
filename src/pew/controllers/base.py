import os


class BaseBuildController:
    def __init__(self, project_info):
        self.project_info = project_info

    def get_env(self):
        return os.environ

    def init(self):
        pass