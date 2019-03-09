import os
import pytest
import shutil
import sys
import tempfile
import unittest

import pew.controllers

from pew.constants import platforms

this_dir = os.path.dirname(os.path.abspath(__file__))


class MockArgs:
    def __init__(self, platform=sys.platform):
        self.platform = platform
        self.config = None
        self.release = False


class BuildControllerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean_up_dirs = []
        cls.temp_dir = tempfile.mkdtemp()
        cls.temp_project_dir = os.path.join(cls.temp_dir, 'test_project')
        template_dir = os.path.join(this_dir, 'files', 'test_project')
        shutil.copytree(template_dir, cls.temp_project_dir)
        cls.info_file = os.path.join(cls.temp_project_dir, 'project_info.json')
        cls.clean_up_dirs.append(cls.temp_dir)

    @classmethod
    def tearDownClass(cls):
        for clean_up_dir in cls.clean_up_dirs:
            shutil.rmtree(clean_up_dir)
            assert not os.path.exists(clean_up_dir)

    def run_base_platform_tests(self, platform):
        assert os.path.exists(self.info_file)

        controller = pew.controllers.get_build_controller(MockArgs(platform=platform), self.info_file)
        assert controller

        build_dir = controller.get_build_dir()
        dist_dir = controller.get_dist_dir()

        assert os.path.exists(build_dir) and platform in build_dir
        assert os.path.exists(dist_dir) and platform in dist_dir

        python_dist_dir = controller.get_python_dist_folder()
        if platform != 'android':
            assert python_dist_dir is None

    def test_cross_platform_controller_methods(self):
        for platform in platforms:
            self.run_base_platform_tests(platform)

    def test_osx_dmgbuild_file_created(self):
        controller = pew.controllers.get_build_controller(MockArgs(platform='osx'), self.info_file)
        dmgbuild_settings_file = controller._create_dmgbuild_settings_file()
        assert os.path.exists(dmgbuild_settings_file)

    @pytest.mark.slow
    def test_android_init_creates_dist(self):
        controller = pew.controllers.get_build_controller(MockArgs(platform='android'), self.info_file)

        python_dist_dir = controller.get_python_dist_folder()
        assert python_dist_dir is not None
        assert not os.path.exists(python_dist_dir)
        controller.init()
        assert os.path.exists(python_dist_dir)
        self.clean_up_dirs.append(python_dist_dir)


if __name__ == '__main__':
    unittest.main()