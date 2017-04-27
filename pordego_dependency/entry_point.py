import time

from pordego_dependency.dependency_analysis import DependencyAnalyzer, logger
from pordego_dependency.dependency_config import DependencyConfig
from pordego_dependency.requirements_analysis import RequirementsAnalyzer
from pordego_dependency.snakefood_lib import preload_packages, DependencyBuilder


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
    analyse_cyclic_dependency(config)
    root_cache = preload_packages(config.source_paths)

    package_dependency_map = build_package_dependencies(config, root_cache)
    analyze_results([analyzer.analyze(package_dependency_map) for analyzer in build_analyzers(config)])


def build_analyzers(config):
    analyses = [DependencyAnalyzer(config)]
    if config.check_requirements:
        analyses.append(RequirementsAnalyzer(config))
    return analyses


def analyze_results(results):
    """
    Check the results of the dependency analyses and report errors

    :type results: list[pordego_dependency.analysis_result.AnalysisResult]
    :raise: AssertionError
    """
    errors = []
    for result in results:
        if result.has_error:
            errors.extend(result.error_messages)
    if errors:
        raise AssertionError("\n\n".join(errors))


def log_time(f):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            return f(*args, **kwargs)
        finally:
            logger.info("Completed in %s s", time.time() - start_time)
    return wrapper


@log_time
def build_package_dependencies(config, root_cache):
    package_dependency_map = {}
    logger.info("Building package dependency map for %s packages...", len(config.dependency_inputs))
    for dependency_check_input in sorted(config.dependency_inputs, key=lambda dep: dep.input_package):
        dependency_builder = DependencyBuilder(dependency_check_input.input_package,
                                               dependency_check_input.files,
                                               source_path=config.source_paths,
                                               root_cache=root_cache)
        package_dependency_map[dependency_check_input.package_path] = dependency_builder.build()
    return package_dependency_map


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
