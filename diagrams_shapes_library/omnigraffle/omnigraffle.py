import json
from argparse import ArgumentParser

from diagrams_shapes_library.processor import Processor
from diagrams_shapes_library.util.logger import get_logger

logger = get_logger(__name__)


class OmniGraffle(Processor):

    @staticmethod
    def add_subcommand(subparsers) -> ArgumentParser:
        return subparsers.add_parser('omnigraffle', help='Stencil for OmniGraffle')

    def process(self):
        logger.info('Creating OmniGraffle stencil')
        logger.info(json.dumps(self._conf, indent=4))

        raise NotImplementedError()
