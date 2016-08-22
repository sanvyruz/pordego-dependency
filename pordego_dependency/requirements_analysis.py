import glob
import os
from contextlib import contextmanager

import sys

from subprocess import check_output

import pkg_resources
import shutil


def analyze_requirements(package_path, dependencies):
    listed_requirements = set(get_listed_requirements(package_path))
    dependency_names = {dep.target_package for dep in dependencies}
    missing_reqs = dependency_names - listed_requirements
    extra_reqs = listed_requirements - dependency_names
    return missing_reqs, extra_reqs


def get_listed_requirements(package_path):
    with change_dir(package_path):
        check_output([sys.executable, "setup.py", "egg_info"])
        try:
            dist = pkg_resources.find_distributions(package_path).next()
            return [req.name for req in dist.requires()]
        finally:
            for egg_path in glob.glob("*.egg-info"):
                try:
                    shutil.rmtree(egg_path)
                except Exception:
                    pass


@contextmanager
def change_dir(new_path):
    orig_path = os.path.abspath(os.curdir)
    os.chdir(new_path)
    try:
        yield
    finally:
        os.chdir(orig_path)
