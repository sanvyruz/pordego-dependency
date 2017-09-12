import unittest

from pordego_dependency.dependency_analysis import DependencyAnalyzer
from pordego_dependency.dependency_config import DependencyConfig
from pordego_dependency.entry_point import build_package_dependencies
from pordego_dependency.snakefood_lib import preload_packages
from tests.test_source_code_names import SOURCE_PATH, IMPORT_LOCAL_DEPS_PKG


class DependencyAnalysisTest(unittest.TestCase):
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
