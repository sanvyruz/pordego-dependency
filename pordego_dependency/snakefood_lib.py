"""
Helper file for testing dependencies. Uses snakefood
"""

import os
import re
from importlib import import_module
from os.path import *
from operator import itemgetter

import sys
from snakefood.roots import find_roots, relfile
from snakefood.util import iter_pyfiles, is_python
import snakefood.find as finder
from snakefood.fallback.collections import defaultdict


class DependencyChecker(object):
    """
    Class to check dependency for the files
    """

    def __init__(self, input_package, files, ignore_list=None, source_path=None):
        self.input_package = input_package
        self.files = files
        self.ignores = ignore_list or []
        self.all_files = defaultdict(set)
        self.all_errors = []
        self.processed_files = set()
        self.source_paths = source_path or []

    def load_dependencies(self):
        """
        Find all the dependencies.
        Taken from snakefood/gendeps.py
        """
        fiter = iter_pyfiles(self.files, self.ignores, False)
        in_roots = find_roots(self.files, self.ignores)

        for fn in fiter:
            if fn in self.processed_files:
                continue  # Make sure we process each file only once.
            self.processed_files.add(fn)
            if is_python(fn):
                files, errors = finder.find_dependencies(
                    fn, verbose=False, process_pragmas=True, ignore_unused=True)

                self.all_errors.extend(errors)
            else:
                files = []
            if basename(fn) == '__init__.py':
                fn = dirname(fn)

            self._add_dependencies(fn, in_roots, files)

    def get_external_dependencies(self, ignore_dependencies=None):
        """
        :param ignore_dependencies: Allowed external dependency list
        :return: set of external dependencies
        """
        all_dependency_details = set()
        all_matched_inputs = set()
        for (from_root, from_), targets in sorted(self.all_files.iteritems(), key=itemgetter(0)):
            for to_root, to_ in sorted(targets):
                matched_data = self._get_match(os.path.join(to_root, to_), ignore_dependencies)
                if not matched_data:
                    if is_builtin(to_):
                        continue
                    all_dependency_details.add(DependencyDetail(from_root, from_, to_root, to_, to_))
                else:
                    all_matched_inputs.add(matched_data)
        return all_dependency_details

    def _add_dependencies(self, fn, in_roots, files):
        """
        :param fn: file name
        :param in_roots: in list of dir / files in root
        :param files: depended files
        Modified in this method.
        """
        from_ = relfile(fn, [])
        if from_ is None:
            return None

        # Add the dependencies.
        for dfn in files:
            xfn = dfn
            if basename(xfn) == '__init__.py':
                xfn = dirname(xfn)

            to_ = relfile(xfn, [])
            into = to_[0] in in_roots
            if into:
                # Skip internal dependency.
                continue
            self.all_files[from_].add(to_)

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


def is_builtin(module_path):
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


class DependencyDetail(object):
    """
    Detail of flagging a file as dependent.
    """

    def __init__(self, from_root, from_file, to_root, to_file, matched_dependency):
        self.from_root = from_root
        self.to_root = to_root
        self.from_file = from_file
        self.to_file = to_file
        self.matched_dependency = matched_dependency

    @property
    def source_package(self):
        """Source package name"""
        return os.path.basename(self.from_root)

    @property
    def target_package(self):
        """Target package name"""
        return self.to_file.split(os.path.sep)[0]

    def __str__(self):
        return "{} is dependent on {}. Dependencies from {} to {} ({}) are not allowed".format(self.from_file,
                                                                                               self.to_file,
                                                                                               self.source_package,
                                                                                               self.target_package,
                                                                                               self.to_root)

    def __hash__(self):
        return hash("{},{},{}".format(self.from_root, self.from_file, self.matched_dependency))


def preload_packages(source_paths, ignores=None):
    all_package_roots = find_package_paths(source_paths, ignores)
    for package_path in all_package_roots:
        pyfiles = iter_pyfiles([package_path], [], False)
        for fn in pyfiles:
            cache_package(fn, package_path)


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
        return join(finder.libpath, modname), None

    errors = []
    names = modname.split('.')
    for i in range(level - 1):
        parentdir = dirname(parentdir)
    # Try relative import, then global imports.
    fn = finder.find_dotted(names, parentdir)
    if not fn:
        if modname not in finder.module_cache:
            fn = finder.find_dotted(names)
            if fn:
                finder.module_cache[modname].append(fn)
        file_names = finder.module_cache[modname]
        if not file_names:
            errors.append((finder.ERROR_IMPORT, modname))
            return None, errors
        fn = file_names[0]
    else:
        file_names = [fn]

    # If this is a from-form, try the target symbol as a module.
    if rname:
        fn2 = None
        for name in file_names:
            fn2 = finder.find_dotted([rname], dirname(name))
            if fn2:
                break
        if fn2:
            fn = fn2
        else:
            errors.append((finder.ERROR_SYMBOL, '.'.join((modname, rname))))
            # Pass-thru and return the filename of the parent, which was found.

    return fn, errors


# monkey patch find so that it works with namespace packages
finder.module_cache = defaultdict(list)
finder.find_dotted_module = find_dotted_module
