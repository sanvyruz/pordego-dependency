import fnmatch
import glob
import os

from pordego_dependency.snakefood_lib import find_package_names


class DependencyCheckInput(object):

    def __init__(self, input_package, allowed_dependency=None, root=None, source_paths=None,
                 ignores=None):
        """
        :param input_package: package to check
        :param allowed_dependency: Allowed dependency
        """
        self.input_package = input_package
        self._allowed_dependency = allowed_dependency or []
        self.source_paths = source_paths or []
        self.root = root or "."
        self.ignores = ignores or ""
        self._package_path = None

    def __str__(self):
        return "Dependency Check on - {}".format(self.input_package)

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
        return self._filter_ignores(self.package_path)

    @property
    def allowed_dependency(self):
        """
        :return: Package names along with alias as seen by build environment
        """
        return set(self._allowed_dependency)

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

    def _filter_ignores(self, parent_dir):
        return [os.path.join(parent_dir, path) for path in os.listdir(parent_dir)
                if not self._should_remove(path)]

    def _should_remove(self, path):
        if isinstance(self.ignores, basestring):
            ignore_globs = [self.ignores]
        else:
            ignore_globs = self.ignores
        for inore_glob in ignore_globs:
            if fnmatch.fnmatch(path, inore_glob):
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
        self._source_paths = source_paths
        self._all_packages = None
        self._root = root
        self._analysis_packages = analysis_packages or self.all_found_packages
        self._dependency_map = dependency_map or {}
        self._check_cyclic = check_cyclic
        self._check_requirements = check_requirements
        self._ignore = ignore

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
            allowed_dependency = self.dependency_map.get(key) if self.dependency_map else None
            dependency_list.append(DependencyCheckInput(key, allowed_dependency=allowed_dependency,
                                                        root=self.root, source_paths=self.source_paths,
                                                        ignores=self._ignore))
        return dependency_list


def parse_line(line):
    """
    Parse a line from the ignore config

    :param line: line
    :return: None if line is not in a valid ignore format, or a tuple of (file path, block name, rank)
    """
    if not line:
        return None
    return os.path.normpath(line)


