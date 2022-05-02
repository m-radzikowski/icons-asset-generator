from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser
from typing import Dict, Any, List

from icons_asset_generator.arguments import default_name_remove
from icons_asset_generator.common.images_finder import get_image_groups
from icons_asset_generator.common.name import create_name
from icons_asset_generator.util.io import create_output_dir
from icons_asset_generator.util.logger import get_logger

logger = get_logger(__name__)


class ProcessorConfig:
    path = None
    output = None
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

        self._library_name = create_name(self._conf.path.rstrip('/').split('/')[-1], self._conf.library_name_remove)

    @staticmethod
    @abstractmethod
    def add_subcommand(subparsers) -> ArgumentParser:
        pass

    @staticmethod
    def _create_config(config: Dict[str, Any]):
        return ProcessorConfig(config)

    def _validate_config(self):
        self._conf.image_name_remove = default_name_remove if not self._conf.image_name_remove \
            else self._conf.image_name_remove
        self._conf.library_name_remove = default_name_remove if not self._conf.library_name_remove \
            else self._conf.library_name_remove

    def process(self):
        self._create_dirs()

        self._libraries = get_image_groups(self._conf.path, self._conf.filename_includes, self._conf.filename_excludes, self._conf.library_name_remove)

        for library_name, library_images in self._libraries.items():
            self.process_group(library_name, library_images)

    def _create_dirs(self):
        create_output_dir(self._conf.output)

    @abstractmethod
    def process_group(self, library_name: str, library_images: List[str]):
        logger.info(f'Processing {len(library_images)} images from group "{library_name}"')
