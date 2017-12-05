import os
import unittest

from pordego_dependency.dependency_analysis import DependencyAnalyzer
from pordego_dependency.dependency_config import DependencyConfig
from pordego_dependency.entry_point import build_package_dependencies
from pordego_dependency.snakefood_lib import preload_packages
from tests.test_source_code_names import SOURCE_PATH, IMPORT_LOCAL_DEPS_PKG, SOURCE_FOLDER_PACKAGE_NAME1, \
    SOURCE_FOLDER_PACKAGE_NAME2


class DependencyAnalysisTest(unittest.TestCase):
    cur_dir = None

    @classmethod
    def setUpClass(cls):
        cls.cur_dir = os.path.abspath(".")
        os.chdir(os.path.dirname(__file__))

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.cur_dir)

    def test_analysis_on_well_defined_dependency_map(self):
        config = DependencyConfig(
            source_paths=[SOURCE_PATH],
            analysis_packages=[IMPORT_LOCAL_DEPS_PKG],
            dependency_map={IMPORT_LOCAL_DEPS_PKG: ["other_package"]}
        )
        root_cache = preload_packages(config.source_paths)
        package_dependency_map = build_package_dependencies(config, root_cache)

        analyzer = DependencyAnalyzer(config)
        self.assertFalse(analyzer.analyze(package_dependency_map).has_error)

    def test_analysis_when_dependency_list_of_package_is_empty(self):
        config = DependencyConfig(
            source_paths=[SOURCE_PATH],
            analysis_packages=[IMPORT_LOCAL_DEPS_PKG],
            dependency_map={IMPORT_LOCAL_DEPS_PKG: []}
        )
        root_cache = preload_packages(config.source_paths)
        package_dependency_map = build_package_dependencies(config, root_cache)

        analyzer = DependencyAnalyzer(config)

        # since IMPORT_LOCAL_DEPS_PKG depends on OTHER_PACKAGE
        self.assertTrue(analyzer.analyze(package_dependency_map).has_error)

    def test_analysis_when_analysis_package_not_in_dependency_map(self):
        """If a package in the analysis packages does not have an entry in the dependency map, do not allow any dependencies"""
        config = DependencyConfig(
            source_paths=[SOURCE_PATH],
            analysis_packages=[IMPORT_LOCAL_DEPS_PKG],
            dependency_map={}
        )
        root_cache = preload_packages(config.source_paths)
        package_dependency_map = build_package_dependencies(config, root_cache)

        analyzer = DependencyAnalyzer(config)

        # since IMPORT_LOCAL_DEPS_PKG depends on OTHER_PACKAGE
        self.assertTrue(analyzer.analyze(package_dependency_map).has_error)

    def test_analysis_with_redundancy_in_dependency_map(self):
        config = DependencyConfig(
            source_paths=[SOURCE_PATH],
            analysis_packages=[IMPORT_LOCAL_DEPS_PKG],
            dependency_map={IMPORT_LOCAL_DEPS_PKG: ["other_package", "some-legacy-dependency"]}
        )
        root_cache = preload_packages(config.source_paths)
        package_dependency_map = build_package_dependencies(config, root_cache)

        analyzer = DependencyAnalyzer(config)
        self.assertTrue(analyzer.analyze(package_dependency_map).has_error)

    def test_analysis_with_source_paths_allowed(self):
        config = DependencyConfig(
            source_paths=[SOURCE_PATH],
            analysis_packages=[SOURCE_FOLDER_PACKAGE_NAME1],
            dependency_map={SOURCE_FOLDER_PACKAGE_NAME1: [SOURCE_FOLDER_PACKAGE_NAME2]}
        )
        root_cache = preload_packages(config.source_paths)
        package_dependency_map = build_package_dependencies(config, root_cache)

        analyzer = DependencyAnalyzer(config)
        # deps allowed from folder 1 to folder 2
        self.assertFalse(analyzer.analyze(package_dependency_map).has_error)

    def test_analysis_with_source_paths_not_allowed(self):
        config = DependencyConfig(
            source_paths=[SOURCE_PATH],
            analysis_packages=[SOURCE_FOLDER_PACKAGE_NAME2],
            dependency_map={SOURCE_FOLDER_PACKAGE_NAME1: [SOURCE_FOLDER_PACKAGE_NAME2]}
        )
        root_cache = preload_packages(config.source_paths)
        package_dependency_map = build_package_dependencies(config, root_cache)

        analyzer = DependencyAnalyzer(config)
        # deps not allowed from folder 2 to folder 1
        self.assertTrue(analyzer.analyze(package_dependency_map).has_error)
