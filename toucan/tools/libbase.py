import abc

class ToolBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def run(self):
        """Main method"""
        pass