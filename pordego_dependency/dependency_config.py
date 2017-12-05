import fnmatch
import glob
import os
from snakefood.util import iter_pyfiles

from pordego_dependency.snakefood_lib import find_package_names


class DependencyCheckInput(object):

    def __init__(self, input_package, allowed_dependency=None, root=None, source_paths=None,
                 ignores=None, ignore_redundant=False):
        """
        :param input_package: package to check
        :param allowed_dependency: Allowed dependency
        """
        self.input_package = input_package
        self._allowed_dependency = allowed_dependency or []  # default to not allowing any dependencies
        self.source_paths = source_paths or []
        self.root = root or "."
        self.ignores = ignores or ""
        self._package_path = None
        self._ignore_redundant = ignore_redundant

    def __str__(self):
        return "Dependency Check on - {}".format(self.input_package)

    @property
    def ignore_redundant(self):
        return self._ignore_redundant

    @property
    def package_path(self):
        if not self._package_path:
            self._package_path = self._find_package_path()
        return self._package_path

    @property
    def files(self):
        """
        :return: files under input package
        """
        return [found_file for found_file in iter_pyfiles([self.package_path], None, abspaths=False)
                if not self._is_ignored(found_file)]

    @property
    def allowed_dependency(self):
        """
        :return: Package names along with alias as seen by build environment
        """
        return self._allowed_dependency

    def _find_package_path(self):
        for source_path in self.source_paths:
            if self.root:
                path = os.path.join(os.path.abspath(self.root), source_path, self.input_package)
            else:
                path = os.path.join(source_path, self.input_package)
            parents_list = glob.glob(path)
            if parents_list:
                return parents_list[0]
        raise Exception("Could not find package {} in paths {}".format(self.input_package, self.source_paths))

    def _is_ignored(self, path):
        if isinstance(self.ignores, basestring):
            ignore_globs = [self.ignores]
        else:
            ignore_globs = self.ignores
        for ignore_glob in ignore_globs:
            if fnmatch.fnmatch(path, ignore_glob):
                return True
        return False


class DependencyConfig(object):
    def __init__(self, source_paths, analysis_packages=None, dependency_map=None, root=None, check_cyclic=None,
                 check_requirements=False, ignore=None, **kw):
        """
        :param source_paths: List of source paths to analyze
        :param analysis_packages: List of packages to run checks on (default all)
        :param dependency_map: Map of paths or packages to paths or packages of allowed dependencies
        """
        self._source_paths = source_paths or []
        self._all_packages = None
        self._root = root
        self._analysis_packages = analysis_packages or self.all_found_packages
        self._dependency_map = dependency_map or {}
        self._check_cyclic = check_cyclic
        self._check_requirements = check_requirements
        self._ignore = ignore
        self.ignore_third_party = kw.get("ignore_third_party")
        self.package_server_url = kw.get("package_server_url")
        self.pip_options = kw.get("pip_options")

    @property
    def root(self):
        """
        :return: reference to root from current path. Like "../..", from which source/input_packages can be detected.
        """
        return self._root

    @property
    def all_found_packages(self):
        """List of all packages found in the source_dirs"""
        if self._all_packages is None:
            self._all_packages = find_package_names(self.source_paths)
        return self._all_packages

    @property
    def check_cyclic(self):
        """
        Raise exception when there is a cyclic dependency
        """
        return self._check_cyclic

    @property
    def check_requirements(self):
        """Analysis should check if the install_requires contains all the dependencies"""
        return self._check_requirements

    @property
    def source_paths(self):
        """Paths to source directories"""
        return filter(None, self._source_paths)

    @property
    def analysis_packages(self):
        """List of packages to analyze. If None, all packages found in the source paths are analyzed"""
        return self._analysis_packages

    @property
    def dependency_map(self):
        """Dict of format package_to_check: allowed_dependencies """
        return self._dependency_map

    @property
    def dependency_inputs(self):
        """
        :return: List of DependencyCheckInput instances that hold dependency_map
        """
        dependency_list = []
        for key in self.analysis_packages:
            if key.endswith('/'):
                source_paths = [os.path.join(base_path, key[:-1]) for base_path in self.source_paths]
                analysis_packages = find_package_names(source_paths)
            else:
                analysis_packages = [key]
                source_paths = self.source_paths
            allowed_dependency = self.dependency_map.get(key, []) if self.dependency_map else []
            # if any deps are specified as folders, have to ignore redundant since we are adding all packages under
            # the folder
            ignore_redundant = any((dep.endswith('/') for dep in allowed_dependency))
            for package_name in analysis_packages:
                dependency_list.append(DependencyCheckInput(package_name,
                                                            allowed_dependency=self.expand_allowed_dependencies(allowed_dependency),
                                                            root=self.root,
                                                            source_paths=source_paths,
                                                            ignores=self._ignore,
                                                            ignore_redundant=ignore_redundant))
        return dependency_list

    def expand_allowed_dependencies(self, allowed_dependency_list):
        expanded_allowed_dependencies = []
        for dep in allowed_dependency_list:
            if dep.endswith("/"):
                expanded_allowed_dependencies.extend(
                    find_package_names([os.path.join(base_path, dep[:-1]) for base_path in self.source_paths]))
            else:
                expanded_allowed_dependencies.append(dep)
        return expanded_allowed_dependencies


def parse_line(line):
    """
    Parse a line from the ignore config

    :param line: line
    :return: None if line is not in a valid ignore format, or a tuple of (file path, block name, rank)
    """
    if not line:
        return None
    return os.path.normpath(line)


