from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser
from typing import Dict, Any

from diagrams_shapes_library.arguments import allowed_size_types, default_name_remove


class ProcessorConfig:
    path = None
    output = None
    size = None
    filename_includes = None
    filename_excludes = None
    image_name_remove = None
    library_name_remove = None

    def __init__(self, dictionary):
        for k, v in dictionary.items():
            setattr(self, k, v)


class Processor(metaclass=ABCMeta):
    _conf: ProcessorConfig = None

    def __init__(self, **kwargs):
        self._conf = self._create_config(kwargs)
        self._validate_config()

    @staticmethod
    @abstractmethod
    def add_subcommand(subparsers) -> ArgumentParser:
        pass

    @staticmethod
    def _create_config(config: Dict[str, Any]):
        return ProcessorConfig(config)

    def _validate_config(self):
        if self._conf.size:
            if self._conf.size.find('=') == -1:
                raise InvalidArgument('Size must be in format TYPE=VALUE')

            [size_type, size_value] = self._conf.size.split('=')
            if size_type not in allowed_size_types:
                raise InvalidArgument('Size type must be one of: ' + ', '.join(allowed_size_types))

            try:
                size_value = int(size_value)
            except ValueError:
                raise InvalidArgument('Size value must be an integer value')

            self._conf.size = (size_type, size_value)

        self._conf.image_name_remove = default_name_remove if not self._conf.image_name_remove \
            else self._conf.image_name_remove
        self._conf.library_name_remove = default_name_remove if not self._conf.library_name_remove \
            else self._conf.library_name_remove

    @abstractmethod
    def process(self):
        pass


class InvalidArgument(Exception):
    pass
