import glob
import os
import shutil
import sys
import tarfile
import zipfile
from collections import namedtuple
from contextlib import contextmanager, closing
from logging import getLogger
from subprocess import check_call, CalledProcessError, check_output, STDOUT
from tempfile import NamedTemporaryFile, mkdtemp

import pkg_resources
import requests
from requests import ConnectionError
from requests.exceptions import ReadTimeout

logger = getLogger(__name__)


CachedDistribution = namedtuple("CachedDistribution", ["distribution", "top_level_packages"])


class RequirementResolver(object):
    def __init__(self, local_source_package_map=None, package_server_url=None, pip_options=None,
                 local_package_names=None, ignore_third_party=True):
        self.package_server_url = package_server_url or "https://pypi.python.org/pypi"
        self.pip_options = pip_options or {}
        self.local_package_names = local_package_names or set()
        self.package_server_not_responding = False
        self.cached_dists = {}
        self.cached_dists.update(local_source_package_map or {})
        self.ignore_third_party = ignore_third_party
        self.session = requests.session()

    def filter_existing_requirements(self, requirements):
        exist_requires = []
        for req in requirements:
            try:
                url = self.package_server_url+"/{}".format(req)
                r = self.session.head(url, headers={"Accept": "application/json"})
            except (ConnectionError, ReadTimeout):
                self.package_server_not_responding = True
                break
            else:
                if r.status_code == requests.codes.ok:
                    exist_requires.append(req)
        return exist_requires

    def filter_local_packages(self, requirements):
        return [req for req in requirements if req not in self.local_package_names]

    def resolve_requirements(self, requirements):
        tlp_map = {}
        not_found_reqs = []
        for req in requirements:
            dist = get_dist_from_package(req, self.cached_dists)
            if dist:
                tlp_map[dist.key] = self.cached_dists[dist.key]
            else:
                not_found_reqs.append(req)
        if not_found_reqs and not self.ignore_third_party:
            not_found_reqs = self.filter_existing_requirements(self.filter_local_packages(not_found_reqs))
            found_pkg_map = self.resolve_packages_from_pypi(not_found_reqs)
            self.cached_dists.update(found_pkg_map)
            tlp_map.update(found_pkg_map)
        return tlp_map

    def resolve_installed_packages(self, requirements):
        dist = pkg_resources

    def resolve_packages_from_pypi(self, requirements):
        if self.package_server_not_responding:
            logger.warning("Skipping requirements resolution because package server is not responding")
            return {}
        if not requirements:
            return {}
        logger.info("Resolving requirements %s from pypi", requirements)
        with write_temp_req_file(requirements) as req_file_path:
            with temp_dir() as temp_path:
                self.run_pip_resolve_command(temp_path, req_file_path)
                return get_top_level_package_map(temp_path)

    def build_pip_resolve_command(self, install_path, req_file_path):
        command = ["pip", "download", "--no-deps", "--disable-pip-version-check", "--dest", install_path,
                   "--retries", "0", "--index-url", self.package_server_url]

        for opt_value in self.filter_pip_options(self.pip_options, command).iteritems():
            command.extend(opt_value)
        command.extend(["-r", req_file_path])
        return command

    def run_pip_resolve_command(self, temp_path, req_file_path):
        with open(os.devnull, "w") as f:
            try:
                check_call(self.build_pip_resolve_command(temp_path, req_file_path), stderr=STDOUT)
            except CalledProcessError:
                logger.warning("Failed to resolve packages")

    @staticmethod
    def filter_pip_options(pip_options, pip_command):
        pip_options = dict(pip_options)
        for reserved_option in filter(lambda arg: arg.startswith("--"), pip_command):
            pip_options.pop(reserved_option, None)
        return pip_options


def get_top_level_package_map(base_path):
    top_level_package_map = {}
    for path in extract_packages(base_path):
        dist = get_distribution(path)
        top_level_package_map[dist.key] = CachedDistribution(dist, get_top_level_packages(path))
    return top_level_package_map


def get_top_level_packages(package_path):
    return [name.partition(".py")[0] for name in os.listdir(package_path)
            if os.path.exists(os.path.join(package_path, name, "__init__.py"))
            or name.endswith(".py") and name != "setup.py"]


def extract_packages(path):
    extracted_paths = []
    for file_name in os.listdir(path):
        full_path = os.path.join(path, file_name)
        dest_path = os.path.join(path, os.path.splitext(file_name)[0])
        if tarfile.is_tarfile(full_path):
            extracter = tarfile.open
        elif zipfile.is_zipfile(full_path):
            extracter = zipfile.ZipFile
        else:
            raise Exception("Unknown file format for file {}".format(file_name))
        with extracter(full_path) as f:
            f.extractall(dest_path)
            subdirs = list(os.listdir(dest_path))
            if len(subdirs) == 1:
                dest_path = os.path.join(dest_path, subdirs[0])
        extracted_paths.append(dest_path)
    return extracted_paths


def get_distribution(package_path):
    dist = try_find_dist(package_path)
    if not dist:
        dist = get_dist_from_egg_info(package_path)
    if not dist:
        dist = create_distribution(package_path)
    return dist


def try_find_dist(package_path):
    try:
        return pkg_resources.find_distributions(package_path).next()
    except Exception:
        return None


def create_distribution(package_path):
    return pkg_resources.Distribution.from_filename(os.path.basename(package_path)+".egg")


def get_dist_from_egg_info(package_path):
    with change_dir(package_path):
        logger.info("Building egg info for package at %s", package_path)
        build_egg_info()
        try:
            dist = pkg_resources.find_distributions(package_path).next()
            dist.requires()
            return dist
        except StopIteration:
            logger.warning("Unable to get distribution information from package at %s."
                           "Requirements analysis might find false positives", package_path)
            return None
        finally:
            for egg_path in glob.glob("*.egg-info"):
                try:
                    shutil.rmtree(egg_path)
                except Exception:
                    pass


def build_egg_info():
    code = "import setuptools;import sys;sys.argv[0]='setup.py';__file__={0!r};execfile(__file__)".format(
        os.path.join(os.path.abspath("."), 'setup.py')
    )
    call_args = [sys.executable, '-c', code, "egg_info"]
    try:
        check_output(call_args, stderr=STDOUT)
    except CalledProcessError as e:
        logger.warning("Unable to build egg-info for package at %s. "
                       "Probably the setup file imports some package that is not installed or something like that. "
                       "Here is the output: %s",
                       os.path.abspath("."), e.output)


def get_dist_from_package(package_name, dist_package_map):
    for cached_dist in dist_package_map.itervalues():
        if package_name in cached_dist.top_level_packages:
            return cached_dist.distribution
    return None


@contextmanager
def write_temp_req_file(requirement_names):
    # On windows, temp files can't be opened by another process while already open
    #  so we can't use the default delete=True
    with closing(NamedTemporaryFile(suffix=".txt", delete=False)) as f:
        f.write("\n".join(requirement_names))
        file_path = f.name
    try:
        yield file_path
    finally:
        os.remove(file_path)


@contextmanager
def temp_dir():
    temp_path = mkdtemp()
    try:
        yield temp_path
    finally:
        shutil.rmtree(temp_path)


@contextmanager
def change_dir(new_path):
    orig_path = os.path.abspath(os.curdir)
    os.chdir(new_path)
    try:
        yield
    finally:
        os.chdir(orig_path)
