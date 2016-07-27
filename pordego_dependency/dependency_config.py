import glob
import os


class DependencyCheckInput(object):

    def __init__(self, input_package, allowed_dependency=None, root=None, source_paths=None):
        """
        :param input_package: package to check
        :param allowed_dependency: Allowed dependency
        """
        self.input_package = input_package
        self._allowed_dependency = allowed_dependency or []
        self.source_paths = source_paths or []
        self.root = root or "."

    def __str__(self):
        return "Dependency Check on - {}".format(self.input_package)

    @property
    def files(self):
        """
        :return: files under input package
        """
        parents_list = []
        fails = []
        for source_path in self.source_paths:
            if self.root:
                path = os.path.join(os.path.abspath(self.root), source_path, self.input_package)
            else:
                path = os.path.join(source_path, self.input_package)
            parents_list = glob.glob(path)
            if parents_list:
                break
            fails.append(path)
        if not parents_list:
            raise ValueError("Wrong input package name - {}. Parent - {}".format(self.input_package, fails))
        new_parent = parents_list[0]
        ignore_names = ["setup.py", "requirements.txt", "test"]
        valid_dirs = filter(None, [in_dir if in_dir not in ignore_names else None
                                   for in_dir in os.listdir(new_parent)])
        return [os.path.join(new_parent, valid_dir) for valid_dir in valid_dirs]

    @property
    def allowed_dependency(self):
        """
        :return: Package names along with alias as seen by build environment
        """
        return set(self._allowed_dependency)


class DependencyConfig(object):
    def __init__(self, source_paths, analysis_packages=None, dependency_map=None, root=None, check_cyclic=None, **kw):
        """
        :param source_paths: List of source paths to analyze
        :param analysis_packages: Path patterns to ignore (such as *tests*)
        :param dependency_map: Maximum allowed complexity. Defaults to "B"
        """
        self._source_paths = source_paths
        self._root = root
        self._analysis_packages = analysis_packages or []
        self._dependency_map = dependency_map or {}
        self._check_cyclic = check_cyclic

    @property
    def root(self):
        """
        :return: reference to root from current path. Like "../..", from which source/input_packages can be detected.
        """
        return self._root

    @property
    def check_cyclic(self):
        """
        Raise exception when there is a cyclic dependency
        """
        return self._check_cyclic

    @property
    def source_paths(self):
        """Paths to source directories"""
        return filter(None, self._source_paths)

    @property
    def analysis_packages(self):
        """List of paths to ignore (can include glob patterns like "*tests*" """
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
            allowed_dependency = self.dependency_map.get(key)
            dependency_list.append(DependencyCheckInput(key, allowed_dependency=allowed_dependency,
                                                        root=self.root, source_paths=self.source_paths))
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


