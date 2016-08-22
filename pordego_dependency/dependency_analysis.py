import os
from logging import getLogger
from operator import itemgetter

from pordego_dependency.dependency_config import DependencyConfig
from pordego_dependency.dependency_tools import filter_local_dependencies, filter_ignored_dependencies, \
    filter_builtin_packages
from pordego_dependency.requirements_analysis import analyze_requirements
from pordego_dependency.snakefood_lib import DependencyBuilder, preload_packages

logger = getLogger(__name__)


def build_config(config_dict):
    if config_dict is None:
        raise Exception("No config specified")
    return DependencyConfig(**config_dict)


def analyze_dependency(config_dict):
    """
    Analyzes Dependency

    :param config_dict: dictionary parsed from config file
    :return:
    """
    config = build_config(config_dict)
    dependency_result = DependencyResult()
    analyse_cyclic_dependency(config)
    root_cache = preload_packages(config.source_paths)

    for dependency_check_input in sorted(config.dependency_inputs, key=lambda dep: dep.input_package):
        analyze_package_dependencies(dependency_check_input, config, dependency_result, root_cache)

    if dependency_result.has_error:
        raise AssertionError(dependency_result.error_message)


def analyze_package_dependencies(dependency_check_input, config, dependency_result, root_cache):
    dependency_builder = DependencyBuilder(dependency_check_input.input_package,
                                           dependency_check_input.files,
                                           source_path=config.source_paths,
                                           root_cache=root_cache)
    all_dependencies = dependency_builder.load_dependencies()
    if config.check_requirements:
        dependency_result.update_requirements_results(dependency_check_input.package_path,
                                                      *analyze_requirements(dependency_check_input.package_path,
                                                                            filter_builtin_packages(all_dependencies)))
    if dependency_check_input.allowed_dependency:
        non_ignored_depends = filter_ignored_dependencies(filter_local_dependencies(all_dependencies,
                                                                                    config.source_paths),
                                                          dependency_check_input.allowed_dependency)
        dependency_result.update_invalid_dependencies(non_ignored_depends)


def analyse_cyclic_dependency(config):
    """
    Raise exception when there is dependency cycle and check is true in config
    """
    validator = DependencyInputValidator(config.dependency_inputs)
    if validator.is_cyclic():
        msg = ("Found cyclic dependency in {}".format(validator.dependency_inputs))
        if config.check_cyclic:
            raise AssertionError(msg)


class DependencyResult(object):
    def __init__(self):
        self.missing_requirements = []
        self.extra_requirements = []
        self.invalid_dependencies = set()

    def update_requirements_results(self, package_path, missing_requirements, extra_requirements):
        self.missing_requirements.append((package_path, missing_requirements))
        self.extra_requirements.append((package_path, extra_requirements))

    def update_invalid_dependencies(self, invalid_deps):
        self.invalid_dependencies |= set(invalid_deps)

    @property
    def has_error(self):
        return any([self.missing_requirements, self.extra_requirements, self.invalid_dependencies])

    @property
    def error_message(self):
        errors = []
        if self.invalid_dependencies:
            errors.append("Found {} dependency violations:\n{}".format(len(self.invalid_dependencies),
                                                                       "\n".join([str(i) for i in
                                                                                  self.invalid_dependencies])))
        errors.append(self._format_reqs(self.missing_requirements, "must contain", "missing"))
        errors.append(self._format_reqs(self.extra_requirements, "should not contain", "extra"))

        return "\n\n".join(errors)

    @classmethod
    def _format_reqs(cls, req_set, message, name):
        req_count = len(req_set)
        req_list = "\n".join(filter(None, [cls._format_req(req, message) for req in sorted(req_set,
                                                                                           key=itemgetter(1))]))
        return "Found {} {} requirements:\n{}".format(req_count, name, req_list)

    @classmethod
    def _format_req(cls, req, message):
        if not req[1]:
            return None
        source_req_file = os.path.join(req[0], "requirements.txt")
        return "{source_package} {message} {req_package}".format(source_package=source_req_file,
                                                                 message=message,
                                                                 req_package=", ".join(sorted(req[1])))


class DependencyInputValidator(object):
    """
    Class to validate dependency input
    """

    def __init__(self, dependency_inputs):
        """

        :param dependency_inputs: List of DependencyCheckInput objects
        """
        self.dependency_inputs = {
            dc.input_package: dc.allowed_dependency for dc in dependency_inputs
            }

    def is_cyclic(self):
        """
        Determines if there is a cycle in dependency input by trying to do a topological sort
        :return: bool
        """
        while self.dependency_inputs:
            depended_packages = set()
            for package in self.dependency_inputs.keys():
                for dependencies in self.dependency_inputs.itervalues():
                    if dependencies and package in dependencies:
                        depended_packages.add(package)
                        break
            non_depended_packages = set(self.dependency_inputs.keys()).difference(depended_packages)
            for package in non_depended_packages:
                self.dependency_inputs.pop(package)

            if not non_depended_packages and self.dependency_inputs:
                return True
        return False
