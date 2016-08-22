import os
import unittest

import subprocess

from pordego_dependency.dependency_config import DependencyCheckInput
from pordego_dependency.snakefood_lib import find_package_paths, preload_packages, DependencyBuilder
from pordego_dependency.dependency_tools import is_builtin
from snakefood.find import find_dotted_module, module_cache

SOURCE_PATH = "test_source_code"
NS_PKG_1_NAME = "ns_pkg_1"
NS_PKG_2_NAME = "ns_pkg_2"
NAMESPACE_PKG = "namespacepkg"
TP_PKG = "third_party_import_pkg"
OTHER_PKG = "other_package"
LOCAL_PACKAGE = "local_package"


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


class TestThirdPartyDetection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.check_call("pip install {}".format(os.path.join(SOURCE_PATH, LOCAL_PACKAGE)), shell=True)

    @classmethod
    def tearDownClass(cls):
        subprocess.check_call("pip uninstall {} -y".format(LOCAL_PACKAGE), shell=True)

    def test_is_builtin_local_install_subpackage(self):
        """Imports in __init__ files are correctly reported as built in packages"""
        self.assertTrue(is_builtin(os.path.join("local_package", "subpackage")))


class TestDependencyChecker(unittest.TestCase):
    def setUp(self):
        preload_packages([SOURCE_PATH])

    def test_import_installed_package_third_party(self):
        """Third party packages installed in the environment should not be reported as dependencies"""
        self.check_dependencies(TP_PKG, [])

    def test_import_not_installed_third_party(self):
        """Third party packages which are not installed in the local environment should be ignored"""
        self.check_dependencies("third_party_import_external", [])

    def test_import_local_package(self):
        """Packages under the source roots should be included in the dependencies"""
        self.check_dependencies("import_local_deps", [OTHER_PKG])

    def test_import_namespace_package(self):
        """Namespace packages are included in dependency lists"""
        # namespacepkg shows up twice because there are two imports in module_tester to modules
        # in two different packages
        self.check_dependencies(OTHER_PKG, [NAMESPACE_PKG, NAMESPACE_PKG])

    def check_dependencies(self, package_name, expected, ignores=None):
        package = DependencyCheckInput(package_name, source_paths=[SOURCE_PATH])
        self.checker = DependencyBuilder(package_name, package.files, source_path=package.source_paths)
        self.checker.load_dependencies()
        deps = self.checker.get_external_dependencies(ignore_dependencies=ignores)
        dep_package_list = [dep.target_package for dep in deps]
        print "Found deps\n{}\n".format(format_deps(deps))
        self.assertItemsEqual(expected, dep_package_list)


def format_deps(deps):
    return "\n".join([str(d) for d in deps])
