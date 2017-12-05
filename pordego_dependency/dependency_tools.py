import os
import re
import sys
from importlib import import_module

UNKNOWN_PACKAGE = "UNKNOWN"


def filter_local_dependencies(dependencies, local_source_paths):
    """
    Return a list of dependencies to packages in the specified source paths

    :type dependencies: list[pordego_dependency.snakefood_lib.Dependency]
    :param local_source_paths: list of paths containing python packages
    """
    return [d for d in dependencies if not d.is_unknown and is_local_package(d.target_path, local_source_paths)]


def is_local_package(file_path, local_source_paths):
    for source in local_source_paths:
        if file_path.startswith(os.path.abspath(source)):
            return True
    return False


def find_redundant_dependency_names(dependencies, allowed_dependency_names):
    return set(allowed_dependency_names) - set([dependency.target_package for dependency in dependencies])


def filter_ignored_dependencies(dependencies, ignore_dependency_names):
    return [d for d in dependencies if not is_ignored(d, ignore_dependency_names)]


def is_ignored(dependency, ignore_dependency_names):
    if ignore_dependency_names is None:
        return False
    return dependency.target_package in ignore_dependency_names


def filter_builtin_packages(dependencies):
    """Return a list of dependencies with the builtin packages removed"""
    return filter(lambda dep: not dep.is_builtin, dependencies)


def is_builtin_root(root_path):
    if os.path.basename(os.path.dirname(sys.executable)) in ["bin", "Scripts"]:
        python_basedir = os.path.split(os.path.dirname(sys.executable))[0]
    else:
        python_basedir = os.path.dirname(sys.executable)
    path_parts = root_path.split(os.path.sep)
    return "usr" in path_parts or ("site-packages" not in root_path and root_path.startswith(python_basedir))


def is_builtin_module(module_path):
    match_file = re.match(r"(.*)(.py|.pyd|.so|.pyo)$", module_path)
    if match_file:
        module_name = match_file.group(1).replace(os.path.sep, ".")
    else:
        module_name = module_path.replace(os.path.sep, ".")
    if module_name in sys.builtin_module_names:
        return True
    try:
        import_module(module_name)
    except ImportError:
        return False
    return True


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
            path_parts = self.to_file.split(os.path.sep)
            package_name = path_parts[0]
        elif self.is_unknown:
            return self.to_file
        else:
            package_name = os.path.basename(self.to_root)
        return package_name

    @property
    def is_builtin(self):
        """Returns true if the dependent package is a built in package"""
        return is_builtin_root(self.to_root)

    @property
    def is_unknown(self):
        """Returns True if the package is unknown such as an uninstalled third party package or bad import"""
        return os.path.basename(self.to_root) == UNKNOWN_PACKAGE

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


