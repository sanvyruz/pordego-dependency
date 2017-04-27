"""
Helper file for testing dependencies. Uses snakefood
"""

import os

import snakefood.find as finder
from pordego_dependency.dependency_tools import Dependency, is_builtin_root, UNKNOWN_PACKAGE
from snakefood.fallback.collections import defaultdict
from snakefood.roots import relfile
from snakefood.util import iter_pyfiles, is_python


class DependencyBuilder(object):
    def __init__(self, input_package, files, source_path=None, root_cache=None):
        self.input_package = input_package
        self.files = files
        self.all_errors = []
        self.source_paths = source_path or []
        self.root_cache = root_cache or {}

    def build(self):
        """
        Find all the dependencies
        """
        in_roots = set(self._split_dependency_path(fn)[0] for fn in self.files)
        processed_files = set()
        dependency_details = set()
        for fn in self.files:
            if fn in processed_files or not is_python(fn):
                continue  # Make sure we process each file only once.
            processed_files.add(fn)
            dependency_details |= self._build_dependencies_for_file(fn, in_roots)
        return dependency_details

    def _build_dependencies_for_file(self, file_name, in_roots):
        files, errors = finder.find_dependencies(
            file_name, verbose=False, process_pragmas=True, ignore_unused=False)
        if os.path.basename(file_name) == '__init__.py':
            file_name = os.path.dirname(file_name)
        from_root, from_path = self._split_dependency_path(file_name)
        dependent_files = self._get_dependencies_from_paths(in_roots, files)
        return {Dependency(from_root, from_path, to_root, to_path) for to_root, to_path in dependent_files
                if not is_builtin_root(to_root)}

    def _get_dependencies_from_paths(self, in_roots, files):
        """
        :param in_roots: in list of dir / files in root
        :param files: dependent files
        :return: set of dependency paths
        """
        dependency_paths = set()
        for dfn in set(files):
            xfn = dfn
            if os.path.basename(xfn) == '__init__.py':
                xfn = os.path.dirname(xfn)

            to_ = self._split_dependency_path(xfn)
            into = to_[0] in in_roots
            if into:
                # Skip internal dependency.
                continue
            dependency_paths.add(to_)
        return dependency_paths

    def _split_dependency_path(self, file_name):
        if file_name in self.root_cache:
            root = self.root_cache[file_name]
            dep_path = file_name[len(root)+1:]
        else:
            root, dep_path = relfile(file_name, [])
            self.root_cache[file_name] = root
        return root, dep_path

    def _get_match(self, file_data, check_match_data_list):
        """
        :param file_data: existing dependency
        :param check_match_data_list: dependencies to check for
        :return: None of match found from check_match_data_list
        """
        if not check_match_data_list:
            return None
        file_data_items = file_data.split(os.sep)
        for check_match_data in check_match_data_list:
            for source in self.source_paths:
                if source in file_data_items and check_match_data in file_data_items:
                    return check_match_data
        return None


def find_package_paths(source_roots, ignores=None):
    return {os.path.dirname(path) for path in iter_pyfiles(source_roots, ignores)
            if os.path.basename(path) == "setup.py"}


def find_package_names(source_roots, ignores=None):
    return [os.path.basename(path) for path in find_package_paths(source_roots, ignores=ignores)]


def preload_packages(source_paths, ignores=None):
    all_package_roots = find_package_paths(source_paths, ignores)
    cache = {}
    for package_path in all_package_roots:
        pyfiles = iter_pyfiles([package_path], [], False)
        for fn in pyfiles:
            cache_package(fn, package_path)
            cache[fn] = package_path
    return cache


def cache_package(fn, root):
    names = fn.partition(root)[2].split(os.path.sep)[1:]
    names[-1] = names[-1].rpartition(".")[0]
    if names[-1] == "__init__":
        names = names[:-1]
    modname = ".".join(names)
    finder.module_cache[modname].append(fn)


def find_dotted_module(modname, rname, parentdir, level):
    """
    A version of find_module that supports dotted module names (packages).  This
    function returns the filename of the module if found, otherwise returns
    None.

    If 'rname' is not None, it first attempts to import 'modname.rname', and if it
    fails, it must therefore not be a module, so we look up 'modname' and return
    that instead.

    'parentdir' is the directory of the file that attempts to do the import.  We
    attempt to do a local import there first.

    'level' is the level of a relative import (i.e. the number of leading dots).
    If 0, the import is absolute.
    """
    # Check for builtins.
    if modname in finder.builtin_module_names:
        return os.path.join(finder.libpath, modname), None

    errors = []
    names = modname.split('.')
    for i in range(level - 1):
        parentdir = os.path.dirname(parentdir)
    # Try relative import, then global imports.
    fn = finder.find_dotted(names, parentdir)
    if not fn:
        if modname not in finder.module_cache:
            fn = finder.find_dotted(names)
            if fn:
                finder.module_cache[modname].append(fn)
        file_names = finder.module_cache[modname]
        if not file_names:
            file_names = [os.path.join(UNKNOWN_PACKAGE, modname)]
        fn = file_names[0]
    else:
        file_names = [fn]

    # If this is a from-form, try the target symbol as a module.
    if rname:
        fn2 = None
        for name in file_names:
            fn2 = finder.find_dotted([rname], os.path.dirname(name))
            if fn2:
                break
        if fn2:
            fn = fn2
        else:
            pass
            # Pass-thru and return the filename of the parent, which was found.

    return fn, errors


# monkey patch find so that it works with namespace packages
finder.module_cache = defaultdict(list)
finder.find_dotted_module = find_dotted_module
