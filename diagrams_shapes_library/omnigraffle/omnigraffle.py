import json
from argparse import ArgumentParser
from typing import Any, Dict

from diagrams_shapes_library.util.logger import get_logger
from diagrams_shapes_library.processor import Processor

logger = get_logger(__name__)


class OmniGraffle(Processor):

    def add_subcommand(self, subparsers) -> ArgumentParser:
        return subparsers.add_parser('omnigraffle', help='Stencil for OmniGraffle')

    def process(self, args: Dict[str, Any]):
        logger.info('Creating OmniGraffle stencil')
        logger.info(json.dumps(args, indent=4))
