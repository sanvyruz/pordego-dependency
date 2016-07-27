import os
import unittest

from pordego_dependency.snakefood_lib import find_package_paths, preload_packages
from snakefood.find import find_dotted_module, module_cache

SOURCE_PATH = "test_source_code"
NS_PKG_1_NAME = "ns_pkg_1"
NS_PKG_2_NAME = "ns_pkg_2"
NAMESPACE_PKG = "namespacepkg"

class TestSnakefoodLib(unittest.TestCase):

    def tearDown(self):
        module_cache.clear()

    def test_find_package_paths(self):
        """Return a list of packages under a list of source directories"""
        packages = find_package_paths([SOURCE_PATH])
        expected = {os.path.abspath(os.path.join(SOURCE_PATH, path)) for path in os.listdir(SOURCE_PATH)}
        self.assertEqual(expected, packages)

    def test_preload_packages(self):
        """Load packages into the snakefood cache, including namespace packages"""
        preload_packages([SOURCE_PATH])
        module_1_expected_path = os.path.abspath(os.path.join(SOURCE_PATH, NS_PKG_1_NAME, NAMESPACE_PKG, "module_1.py"))
        module_2_expected_path = os.path.abspath(os.path.join(SOURCE_PATH, NS_PKG_2_NAME, NAMESPACE_PKG, "module_2.py"))

        self.assertEqual(module_1_expected_path, find_dotted_module("namespacepkg.module_1", "test_method_1", None, 0)[0])
        self.assertEqual(module_1_expected_path, find_dotted_module(NAMESPACE_PKG, "module_1", None, 0)[0])
        self.assertEqual(module_2_expected_path, find_dotted_module("namespacepkg.module_2", "test_method_2", None, 0)[0])
        self.assertEqual(module_2_expected_path, find_dotted_module(NAMESPACE_PKG, "module_2", None, 0)[0])
