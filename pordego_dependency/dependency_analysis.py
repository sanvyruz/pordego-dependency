from logging import getLogger

from collections import defaultdict

from pordego_dependency.analysis_result import AnalysisResult
from pordego_dependency.analyzer import Analyzer
from pordego_dependency.dependency_tools import filter_local_dependencies, filter_ignored_dependencies, \
    find_redundant_dependency_names

logger = getLogger(__name__)


class DependencyAnalyzer(Analyzer):
    def __init__(self, config):
        self._config = config

    def analyze(self, package_dependency_map):
        result = DependencyAnalysisResult()
        for dependency_input in self._config.dependency_inputs:
            dependencies = package_dependency_map[dependency_input.package_path]
            local_depends = filter_local_dependencies(dependencies, self._config.source_paths)
            allowed_dependency_names = dependency_input.allowed_dependency
            if allowed_dependency_names is not None:
                non_ignored_depends = filter_ignored_dependencies(local_depends, allowed_dependency_names)
                result.update_invalid_dependencies(non_ignored_depends)

                redundant_dependency_names = find_redundant_dependency_names(local_depends, allowed_dependency_names)
                if redundant_dependency_names and not dependency_input.ignore_redundant:
                    result.update_redundant_dependency_names(dependency_input.input_package, redundant_dependency_names)
        return result


class DependencyAnalysisResult(AnalysisResult):
    def __init__(self):
        self.invalid_dependencies = set()
        self.redundant_dependencies = defaultdict(set)

    def update_invalid_dependencies(self, invalid_deps):
        self.invalid_dependencies |= set(invalid_deps)

    @property
    def has_error(self):
        return any([self.invalid_dependencies]) or any(self.redundant_dependencies)

    @property
    def error_messages(self):
        errors = []
        if self.invalid_dependencies:
            errors.append("Found {} dependency violations:\n{}".format(len(self.invalid_dependencies),
                                                                       "\n".join([str(i) for i in
                                                                                  self._sorted_deps()])))
        if self.redundant_dependencies:
            for package, dependencies in self.redundant_dependencies.iteritems():
                errors.append("Following dependencies of {} are redundant: {}".format(package, ", ".join(dependencies)))
        return errors

    def update_redundant_dependency_names(self, input_package, redundant_dependency_names):
        self.redundant_dependencies[input_package] |= redundant_dependency_names

    def _sorted_deps(self):
        return sorted(self.invalid_dependencies, key=lambda dep: dep.source_package)
