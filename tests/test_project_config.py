import os
import unittest

import pytest

from pew.config import load_project_info

this_dir = os.path.dirname(os.path.abspath(__file__))


class ProjectConfigTest(unittest.TestCase):
    def test_basic_project_info_load(self):
        info_file = os.path.join(this_dir, 'files', 'test_project', 'project_info.json')
        project_info = load_project_info(info_file)
        self.assertEqual(project_info['name'], "Sample Project")
        self.assertEqual(project_info['version'], "0.0.1")
        self.assertEqual(project_info['identifier'], "org.pyeverywhere.SampleProject")

    def test_envvar_project_info_load(self):
        info_file = os.path.join(this_dir, 'files', 'test_project', 'project_info_env_vars.json')
        with self.assertRaises(ValueError):
            load_project_info(info_file)
        # assign one var but not the other
        os.environ['APP_NAME'] = "Sample Project"
        with self.assertRaises(ValueError):
            load_project_info(info_file)

        os.environ['APP_VERSION'] = "1.2.3"
        project_info = load_project_info(info_file)

        self.assertEqual(project_info['name'], "Sample Project")
        self.assertEqual(project_info['version'], "1.2.3")
        self.assertEqual(project_info['identifier'], "org.pyeverywhere.SampleProject")
