from logging import getLogger

from pordego_dependency.dependency_config import DependencyConfig
from pordego_dependency.snakefood_lib import DependencyChecker, preload_packages

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
    all_dependencies = set()
    analyse_cyclic_dependency(config)
    preload_packages(config.source_paths)
    for dependency_check_input in config.dependency_inputs:
        dependency_checker = DependencyChecker(dependency_check_input.input_package,
                                               dependency_check_input.files,
                                               source_path=config.source_paths,
                                               )
        dependency_checker.load_dependencies()
        all_dependency_details = dependency_checker.get_external_dependencies(
            ignore_dependencies=dependency_check_input.allowed_dependency
        )
        if all_dependency_details:
            all_dependencies.update(all_dependency_details)

    if all_dependencies:
        msg = "Found {} dependency violations:\n{}".format(len(all_dependencies),
                                                           "\n".join([str(i) for i in all_dependencies]))
        raise AssertionError(msg)


def analyse_cyclic_dependency(config):
    """
    Raise exception when there is dependency cycle and check is true in config
    """
    validator = DependencyInputValidator(config.dependency_inputs)
    if validator.is_cyclic():
        msg = ("Found cyclic dependency in {}".format(validator.dependency_inputs))
        if config.check_cyclic:
            raise AssertionError(msg)


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
