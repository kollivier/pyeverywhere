import os
import shutil
import sys
import unittest


import pew.controllers


class BuildControllerTestCase(unittest.TestCase):
    def setUp(self):
        self.info = {
            'name': 'Test App'
        }

    @classmethod
    def setUpClass(cls):
        cls.clean_up_dirs = []

    @classmethod
    def tearDownClass(cls):
        for clean_dir in cls.clean_up_dirs:
            shutil.rmtree(clean_dir)

    def test_init_native(self):
        controller = pew.controllers.get_build_controller(sys.platform, self.info)
        assert controller

        controller.init()

        assert not controller.get_python_dist_folder()

    def test_init_android(self):
        controller = pew.controllers.get_build_controller('android', self.info)
        assert controller

        python_dist_dir = controller.get_python_dist_folder()
        # assert not os.path.exists(python_dist_dir)

        controller.init()
        assert os.path.exists(python_dist_dir)
        self.clean_up_dirs.append(python_dist_dir)


if __name__ == '__main__':
    unittest.main()