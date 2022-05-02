import logging

from diagrams_shapes_library.processor import InvalidArgument
from diagrams_shapes_library.arguments import create_arg_parser
from diagrams_shapes_library.diagramsnet.diagramsnet import DiagramsNet
from diagrams_shapes_library.omnigraffle.omnigraffle import OmniGraffle
from diagrams_shapes_library.util.logger import setup_logging, get_logger


def main():
    parser = create_arg_parser([
        DiagramsNet,
        OmniGraffle,
    ])

    args = vars(parser.parse_args())

    verbose = args.get('v')
    setup_logging(level=logging.DEBUG if verbose else logging.INFO)
    logger = get_logger(__name__)

    try:
        processor = args.pop('processor')(**args)
        processor.process()
    except InvalidArgument as e:
        parser.print_usage()
        logger.error(str(e))
        exit(1)


if __name__ == '__main__':
    main()
