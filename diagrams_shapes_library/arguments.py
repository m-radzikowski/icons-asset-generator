from argparse import ArgumentParser, ONE_OR_MORE
from typing import List

default_name_remove = ['.', '-', '_']


def create_arg_parser(processors: List) -> ArgumentParser:
    default_name_remove_help = ' '.join(default_name_remove)

    parser = ArgumentParser(description='Convert images into application libraries.')
    parser.add_argument('--path', metavar='PATH', help='input files directory path', required=True)
    parser.add_argument('--output', metavar='PATH', default='./library',
                        help='output directory path (default: ./library)')
    parser.add_argument('--filename-includes', metavar='VALUE', default=[], action='extend', nargs=ONE_OR_MORE,
                        help='strings to filter image file name by, taking only those which contains them all')
    parser.add_argument('--filename-excludes', metavar='VALUE', default=[], action='extend', nargs=ONE_OR_MORE,
                        help='strings to filter image file name by, taking only those which do not contain any of them')
    parser.add_argument('--image-name-remove', metavar='VALUE', default=[], action='extend', nargs=ONE_OR_MORE,
                        help='strings to be removed from image file name ' +
                             f'(default: {default_name_remove_help})')
    parser.add_argument('--library-name-remove', metavar='VALUE', default=[], action='extend', nargs=ONE_OR_MORE,
                        help='strings to be removed from library file name ' +
                             f'(default: {default_name_remove_help})')
    parser.add_argument('--no-vertex-magnets', action='store_false', dest='vertex_magnets',
                        help='don\'t create connection points on vertices (corners)')
    parser.add_argument('--side-magnets', metavar='COUNT', default=5, type=int,
                        help='number of connection points for each side (default: 5)')
    parser.add_argument('-v', action='store_true', help='enable verbose logs')

    subparsers = parser.add_subparsers(title='target format', metavar='TARGET', required=True)

    for processor in processors:
        subparser = processor.add_subcommand(subparsers)
        subparser.set_defaults(processor=processor)

    return parser
