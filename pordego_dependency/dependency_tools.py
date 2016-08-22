import os
import re
import sys
from importlib import import_module


def filter_local_dependencies(dependencies, local_source_paths):
    """
    Return a list of dependencies to packages in the specified source paths

    :type dependencies: list[pordego_dependency.snakefood_lib.Dependency]
    :param local_source_paths: list of paths containing python packages
    """
    return [d for d in dependencies if is_local_package(d.target_path, local_source_paths)]


def is_local_package(file_path, local_source_paths):
    for source in local_source_paths:
        if file_path.startswith(os.path.abspath(source)):
            return True
    return False


def filter_ignored_dependencies(dependencies, ignore_dependency_names):
    return [d for d in dependencies if not is_ignored(d, ignore_dependency_names)]


def is_ignored(dependency, ignore_dependency_names):
    return dependency.target_package in ignore_dependency_names


def filter_builtin_packages(dependencies):
    """Return a list of dependencies with the builtin packages removed"""
    return filter(lambda dep: not dep.is_builtin, dependencies)


def is_builtin(root_path, module_path):
    if "site-packages" in root_path:
        return False
    if root_path.startswith(os.path.dirname(sys.executable)):
        return True
    match_file = re.match(r"(.*)(.py|.pyd|.so|.pyo)$", module_path)
    if match_file:
        module_name = match_file.group(1).replace(os.path.sep, ".")
    else:
        module_name = module_path
    if module_name in sys.builtin_module_names:
        return True
    try:
        import_module(module_name)
    except ImportError:
        return False
    return False


class Dependency(object):
    def __init__(self, from_root, from_file, to_root, to_file):
        self.from_root = from_root
        self.to_root = to_root
        self.from_file = from_file
        self.to_file = to_file

    @property
    def source_package(self):
        """Source package name"""
        return os.path.basename(self.from_root)

    @property
    def target_package(self):
        """Target (dependency) package name"""
        if "site-packages" in self.to_root:
            path_parts = os.path.split(self.to_file)
            package_name = filter(lambda x: x, path_parts)[0]
        else:
            package_name = os.path.basename(self.to_root)
        return package_name

    @property
    def is_builtin(self):
        """Returns true if the dependent package is a built in package"""
        return is_builtin(self.to_root, self.to_file)

    @property
    def target_path(self):
        """Path to the source file"""
        return os.path.join(self.to_root, self.to_file)

    def __str__(self):
        return "{} (from {}) is dependent on {} (to {})".format(
            self.source_package, self.from_file, self.target_package, self.to_file)

    def __hash__(self):
        return (self.source_package, self.target_package).__hash__()

    def __eq__(self, other):
        return (self.source_package, self.target_package) == (other.source_package, other.target_package)
