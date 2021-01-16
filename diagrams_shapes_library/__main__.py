from argparse import ArgumentParser
from typing import Dict, Any, List

from diagrams_shapes_library.diagramsnet.diagramsnet import DiagramsNet
from diagrams_shapes_library.omnigraffle.omnigraffle import OmniGraffle
from diagrams_shapes_library.processor import Processor
from diagrams_shapes_library.util.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def main():
    args = parse_arguments([
        DiagramsNet(),
        OmniGraffle(),
    ])

    func = args.pop('func')
    func(**args)


def parse_arguments(processors: List[Processor]) -> Dict[str, Any]:
    default_name_remove = ['.', '-', '_']
    default_name_remove_help = ' '.join(default_name_remove)
    allowed_size_types = ['width', 'height', 'longest']

    parser = ArgumentParser(description='Convert images into application libraries.')
    parser.add_argument('--path', metavar='PATH', help='input files directory path', required=True)
    parser.add_argument('--output', metavar='PATH', default='./library',
                        help='output directory path (default: ./library)')
    parser.add_argument('--size', metavar='TYPE=VALUE', type=str,
                        help='resize images to target size; allowed TYPE values: ' + ', '.join(allowed_size_types))
    parser.add_argument('--filename-includes', metavar='VALUE', default=[], action='extend', nargs='+',
                        help='strings to filter image file name by, taking only those which contains them all')
    parser.add_argument('--filename-excludes', metavar='VALUE', default=[], action='extend', nargs='+',
                        help='strings to filter image file name by, taking only those which do not contain any of them')
    parser.add_argument('--image-name-remove', metavar='VALUE', default=[], action='extend', nargs='+',
                        help='strings to be removed from image file name ' +
                             f'(default: {default_name_remove_help})')
    parser.add_argument('--library-name-remove', metavar='VALUE', default=[], action='extend', nargs='+',
                        help='strings to be removed from library file name ' +
                             f'(default: {default_name_remove_help})')

    subparsers = parser.add_subparsers(title='target format', metavar='TARGET', required=True)

    for processor in processors:
        subparser = processor.add_subcommand(subparsers)
        subparser.set_defaults(func=processor.process)

    args = vars(parser.parse_args())

    if args['size']:
        if args['size'].find('=') == -1:
            parser.print_usage()
            logger.error('Size must be in format TYPE=VALUE')
            exit(1)

        [size_type, size_value] = args['size'].split('=')
        if size_type not in allowed_size_types:
            parser.print_usage()
            logger.error('Size type must be one of: ' + ', '.join(allowed_size_types))
            exit(1)

        try:
            size_value = int(size_value)
        except ValueError:
            parser.print_usage()
            logger.error('Size value must be an integer value')
            exit(1)

        args['size'] = (size_type, size_value)

    args['image_name_remove'] = default_name_remove if not args['image_name_remove'] else args['image_name_remove']
    args['library_name_remove'] = default_name_remove if not args['library_name_remove'] \
        else args['library_name_remove']

    return args


if __name__ == '__main__':
    main()
