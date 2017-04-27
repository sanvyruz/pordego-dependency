from logging import getLogger

from pordego_dependency.analysis_result import AnalysisResult
from pordego_dependency.analyzer import Analyzer
from pordego_dependency.dependency_tools import filter_local_dependencies, filter_ignored_dependencies

logger = getLogger(__name__)


class DependencyAnalyzer(Analyzer):
    def __init__(self, config):
        self._config = config

    def analyze(self, package_dependency_map):
        result = DependencyAnalysisResult()
        for dependency_input in self._config.dependency_inputs:
            dependencies = package_dependency_map[dependency_input.package_path]
            local_depends = filter_local_dependencies(dependencies, self._config.source_paths)
            if dependency_input.allowed_dependency:
                non_ignored_depends = filter_ignored_dependencies(local_depends,
                                                                  dependency_input.allowed_dependency)
                result.update_invalid_dependencies(non_ignored_depends)
        return result


class DependencyAnalysisResult(AnalysisResult):
    def __init__(self):
        self.invalid_dependencies = set()

    def update_invalid_dependencies(self, invalid_deps):
        self.invalid_dependencies |= set(invalid_deps)

    @property
    def has_error(self):
        return any([self.invalid_dependencies])

    @property
    def error_messages(self):
        errors = []
        if self.invalid_dependencies:
            errors.append("Found {} dependency violations:\n{}".format(len(self.invalid_dependencies),
                                                                       "\n".join([str(i) for i in
                                                                                  self.invalid_dependencies])))
        return errors
