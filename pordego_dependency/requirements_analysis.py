from logging import getLogger
from operator import itemgetter

import pkg_resources
from pordego_dependency.analysis_result import AnalysisResult
from pordego_dependency.requirement_resolver import RequirementResolver, get_top_level_packages, get_distribution, \
    CachedDistribution

logger = getLogger(__name__)


class RequirementsAnalyzer(object):
    def __init__(self, analysis_config):
        """
        :type analysis_config: pordego_dependency.dependency_config.DependencyConfig
        """
        self.analysis_config = analysis_config

    def analyze(self, package_dependency_map):
        result = RequirementsAnalysisResult()
        local_package_names = set(self.analysis_config.all_found_packages)
        local_source_package_map = {}
        package_path_dist_map = {}
        for package_path in package_dependency_map:
            if package_path in package_path_dist_map:
                dist, top_level_packages = package_path_dist_map[package_path]
            else:
                dist = get_distribution(package_path)
                top_level_packages = get_top_level_packages(package_path)
            cached_dist = CachedDistribution(dist, top_level_packages)
            local_source_package_map[dist.key] = cached_dist
            package_path_dist_map[package_path] = cached_dist
        req_resolver = RequirementResolver(local_source_package_map,
                                           self.analysis_config.package_server_url,
                                           self.analysis_config.pip_options,
                                           local_package_names=local_package_names,
                                           ignore_third_party=self.analysis_config.ignore_third_party)
        for package_path, package_dependencies in package_dependency_map.iteritems():
            distribution = package_path_dist_map[package_path].distribution
            result.update(package_path, *self.analyze_package(distribution, package_dependencies,
                                                              req_resolver))
        return result

    def analyze_package(self, distribution, package_dependencies, requirement_resolver):
        missing_reqs = set()
        extra_reqs = set()
        if self.analysis_config.check_requirements:
            listed_requirements = set(get_listed_requirements(distribution))
            dependency_names = {dep.target_package for dep in package_dependencies}
            missing_reqs = dependency_names - listed_requirements
            extra_reqs = listed_requirements - dependency_names
            if extra_reqs:
                missing_reqs, extra_reqs = self.filter_resolved_requirements(requirement_resolver, missing_reqs,
                                                                             extra_reqs)
        return missing_reqs, extra_reqs

    @staticmethod
    def filter_resolved_requirements(requirement_resolver, missing_reqs, extra_reqs):
        for dist_key, cached_dist in requirement_resolver.resolve_requirements(extra_reqs).iteritems():
            for pack in cached_dist.top_level_packages:
                if pack in missing_reqs:
                    missing_reqs.remove(pack)
                    for extra_req in extra_reqs:
                        if cached_dist.distribution in pkg_resources.Requirement.parse(extra_req):
                            extra_reqs.remove(extra_req)
                            break
                    break
        return missing_reqs, extra_reqs


class RequirementsAnalysisResult(AnalysisResult):
    def __init__(self):
        self.missing_requirements = []
        self.extra_requirements = []

    def update(self, package_path, missing_requirements, extra_requirements):
        if missing_requirements:
            self.missing_requirements.append((package_path, missing_requirements))
        if extra_requirements:
            self.extra_requirements.append((package_path, extra_requirements))

    @property
    def has_error(self):
        return any([self.missing_requirements, self.extra_requirements])

    @property
    def error_messages(self):
        errors = []
        if self.missing_requirements:
            errors.append(self._format_reqs(self.missing_requirements,
                                            "must contain projects that export these packages:", "missing"))
        if self.extra_requirements:
            errors.append(self._format_reqs(self.extra_requirements, "should not contain", "extra"))
        return errors

    @classmethod
    def _format_reqs(cls, req_list, message, name):
        req_count = len(req_list)
        req_list = "\n".join(filter(None, [cls._format_req(req, message) for req in sorted(req_list,
                                                                                           key=itemgetter(0))]))
        return "Found {} packages with {} requirements:\n{}".format(req_count, name, req_list)

    @classmethod
    def _format_req(cls, req, message):
        if not req[1]:
            return None
        return "{source_package} requirements {message} {req_package}".format(source_package=req[0],
                                                                              message=message,
                                                                              req_package=", ".join(sorted(req[1])))


def get_listed_requirements(distribution):
    return [req.name for req in distribution.requires()]


