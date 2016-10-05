from abc import ABCMeta, abstractproperty
from operator import itemgetter


class AnalysisResult(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def has_error(self):
        """The analysis found an error"""

    @abstractproperty
    def error_messages(self):
        """
        List of error messages to show to the user

        :rtype: list[basestring]
        """



class DependencyAnalysisResult(object):
    def __init__(self):
        self.missing_requirements = []
        self.extra_requirements = []
        self.invalid_dependencies = set()

    def update_requirements_results(self, package_path, missing_requirements, extra_requirements):
        if missing_requirements:
            self.missing_requirements.append((package_path, missing_requirements))
        if extra_requirements:
            self.extra_requirements.append((package_path, extra_requirements))

    def update_invalid_dependencies(self, invalid_deps):
        self.invalid_dependencies |= set(invalid_deps)

    @property
    def has_error(self):
        return any([self.missing_requirements, self.extra_requirements, self.invalid_dependencies])

    @property
    def error_message(self):
        errors = []
        if self.invalid_dependencies:
            errors.append("Found {} dependency violations:\n{}".format(len(self.invalid_dependencies),
                                                                       "\n".join([str(i) for i in
                                                                                  self.invalid_dependencies])))
        if self.missing_requirements:
            errors.append(self._format_reqs(self.missing_requirements, "must contain", "missing"))
        if self.extra_requirements:
            errors.append(self._format_reqs(self.extra_requirements, "should not contain", "extra"))

        return "\n\n".join(errors)

    @classmethod
    def _format_reqs(cls, req_set, message, name):
        req_count = len(req_set)
        req_list = "\n".join(filter(None, [cls._format_req(req, message) for req in sorted(req_set,
                                                                                           key=itemgetter(0))]))
        return "Found {} {} requirements:\n{}".format(req_count, name, req_list)

    @classmethod
    def _format_req(cls, req, message):
        if not req[1]:
            return None
        return "{source_package} requirements {message} {req_package}".format(source_package=req[0],
                                                                              message=message,
                                                                              req_package=", ".join(sorted(req[1])))