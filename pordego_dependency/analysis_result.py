from abc import ABCMeta, abstractproperty


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
