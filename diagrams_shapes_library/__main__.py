from diagrams_shapes_library.processor import InvalidArgument
from diagrams_shapes_library.arguments import create_arg_parser
from diagrams_shapes_library.diagramsnet.diagramsnet import DiagramsNet
from diagrams_shapes_library.omnigraffle.omnigraffle import OmniGraffle
from diagrams_shapes_library.util.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    parser = create_arg_parser([
        DiagramsNet,
        OmniGraffle,
    ])

    args = vars(parser.parse_args())

    try:
        processor = args.pop('processor')(**args)
        processor.process()
    except InvalidArgument as e:
        parser.print_usage()
        logger.error(str(e))
        exit(1)


if __name__ == '__main__':
    main()
