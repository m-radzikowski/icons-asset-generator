from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser
from typing import Dict, Any, List

from diagrams_shapes_library.arguments import allowed_size_types, default_name_remove
from diagrams_shapes_library.common.images_finder import get_image_groups
from diagrams_shapes_library.util.io import create_output_dir
from diagrams_shapes_library.util.logger import get_logger

logger = get_logger(__name__)


class ProcessorConfig:
    path = None
    output = None
    size = None
    filename_includes = None
    filename_excludes = None
    image_name_remove = None
    library_name_remove = None
    vertex_magnets = None
    side_magnets = None

    def __init__(self, dictionary):
        for k, v in dictionary.items():
            setattr(self, k, v)


class Processor(metaclass=ABCMeta):
    _conf: ProcessorConfig = None

    _libraries: Dict[str, List[str]] = {}

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

    def process(self):
        self._create_dirs()

        self._libraries = get_image_groups(self._conf.path, self._conf.filename_includes, self._conf.filename_excludes,
                                           False, self._conf.library_name_remove)

        total_images_count = sum(len(images) for images in self._libraries.values())

        for library_name, library_images in self._libraries.items():
            self.process_group(library_name, library_images)

        logger.info(f'Created {len(self._libraries)} library files with {total_images_count} elements')

    def _create_dirs(self):
        create_output_dir(self._conf.output)

    @abstractmethod
    def process_group(self, library_name: str, library_images: List[str]):
        logger.info(f'Processing {len(library_images)} images from group "{library_name}"')


class InvalidArgument(Exception):
    pass
