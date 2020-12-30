import glob
import json
import os
import re
import shutil
# noinspection PyPep8Naming
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from itertools import filterfalse, groupby
from typing import List, Dict, Tuple, Optional, Any
from urllib.parse import urljoin, quote

from drawio_svg_icons.encoding import deflate_raw, text_to_base64
from drawio_svg_icons.logger import get_logger
from drawio_svg_icons.magnets import create_magnets

logger = get_logger(__name__)

diagrams_net_base_url = 'https://app.diagrams.net/?splash=0&clibs='


def main():
    args = parse_arguments()

    create_output_dir(args['output_dir'])

    images = list_images(args['svg_dir'], args['filename_includes'], args['filename_excludes'])

    if not images:
        logger.error('No SVG images found')
        exit(1)

    if args['single_library']:
        grouped_images = {
            args['svg_dir'].split('/')[-1]: images
        }
    else:
        grouped_images = group_images_by_dir(args['svg_dir'], images)

    libraries = []
    total_images_count = 0

    for group_name, group_images in grouped_images.items():
        logger.info(f'Processing {len(group_images)} images from group "{group_name}"')
        total_images_count += len(group_images)

        library = []
        for image in group_images:
            with open(image) as file:
                svg = file.read()
            title = create_name(os.path.splitext(os.path.basename(image))[0], args['image_name_remove'])
            library.append(
                create_image_params(svg, title, args['vertex_magnets'], args['side_magnets'], args['labels'],
                                    args['size'])
            )

        library_json = json.dumps(library)
        library_xml = create_library_xml(library_json)

        library_file_name = create_name(group_name, args['library_name_remove']) + '.xml'
        library_file = os.path.join(args['output_dir'], library_file_name)
        with open(library_file, 'w') as file:
            file.write(library_xml)
        libraries.append(library_file_name)

    if args['base_url']:
        data = ''
        library_urls = ['U' + urljoin(args['base_url'], quote(lib)) for lib in libraries]

        if len(library_urls) > 1:
            all_url = diagrams_net_base_url + ';'.join(library_urls)
            data += f'All:\n{all_url}\n\n'

        for i in range(len(libraries)):
            data += os.path.basename(libraries[i]) + ':\n'
            data += diagrams_net_base_url + library_urls[i] + '\n\n'

        with open(os.path.join(args['output_dir'], 'links.txt'), 'w') as file:
            file.write(data)

    logger.info(f'Created {len(grouped_images)} library files with {total_images_count} elements')


def parse_arguments() -> Dict[str, Any]:
    default_name_remove = ['.', '-', '_']
    default_name_remove_help = ' '.join(default_name_remove)
    allowed_size_types = ['width', 'height', 'longest']

    parser = ArgumentParser(description='Convert SVG files into diagrams.net library')
    parser.add_argument('--svg-dir', metavar='PATH', default='./svg', help='svg files directory path (default: ./svg)')
    parser.add_argument('--output-dir', metavar='PATH', default='./library',
                        help='path to the output directory (default: ./library)')
    parser.add_argument('--size', metavar='TYPE=VALUE', type=str,
                        help='resize images to target size; allowed TYPE values: ' + ', '.join(allowed_size_types))
    parser.add_argument('--filename-includes', metavar='VALUE', default=[], action='extend', nargs='+',
                        help='strings to filter image file name by, taking only those which contains them all')
    parser.add_argument('--filename-excludes', metavar='VALUE', default=[], action='extend', nargs='+',
                        help='strings to filter image file name by, taking only those which do not contain any of them')
    parser.add_argument('--image-name-remove', metavar='VALUE', default=[], action='extend', nargs='+',
                        help='strings to be removed and replaced by spaces from image file name ' +
                             f'(default: {default_name_remove_help})')
    parser.add_argument('--library-name-remove', metavar='VALUE', default=[], action='extend', nargs='+',
                        help='strings to be removed and replaced by spaces from library file name ' +
                             f'(default: {default_name_remove_help})')
    parser.add_argument('--single-library', action='store_true', dest='single_library',
                        help='create single output library')
    parser.add_argument('--no-vertex-magnets', action='store_false', dest='vertex_magnets',
                        help='don\'t create magnets on vertices (corners)')
    parser.add_argument('--side-magnets', metavar='COUNT', default=5, type=int,
                        help='number of magnets for each side (default: 5)')
    parser.add_argument('--labels', action='store_true', dest='labels',
                        help='add label with name to images')
    parser.add_argument('--base-url', metavar='URL',
                        help='base URL to generate link(s) to open libraries in diagrams.net')

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


def create_output_dir(dir_name) -> None:
    shutil.rmtree(dir_name, ignore_errors=True)
    os.mkdir(dir_name)


def list_images(dir_path: str, name_includes: List[str], name_excludes: List[str]) -> List[str]:
    files = [f for f in glob.glob(os.path.join(dir_path, '**/*.svg'), recursive=True)]

    files = filter_file_name_include(files, name_includes)
    files = filter_file_name_exclude(files, name_excludes)

    files.sort()

    return files


def filter_file_name_include(files: List[str], keywords: List[str]) -> List[str]:
    if not keywords:
        return files

    return list(
        filter(lambda file: all(keyword in os.path.basename(file) for keyword in keywords), files)
    )


def filter_file_name_exclude(files: List[str], keywords: List[str]) -> List[str]:
    if not keywords:
        return files

    return list(
        filterfalse(lambda file: any(keyword in os.path.basename(file) for keyword in keywords), files)
    )


def group_images_by_dir(path: str, images: List[str]) -> Dict[str, List[str]]:
    return {key: list(items) for key, items in groupby(images, lambda file_name: get_group_dir(path, file_name))}


def get_group_dir(path: str, file_name: str):
    abs_dir_path = os.path.abspath(path)
    abs_file_path = os.path.abspath(file_name)
    return abs_file_path[len(abs_dir_path):].split('/')[1]


def create_image_params(svg: str, title: str, vertex_magnets: bool, side_magnets: int, labels: bool,
                        resize: (str, int)) -> dict:
    points = create_magnets(vertex_magnets, side_magnets)
    label = title if labels else None
    size = get_size(svg)

    if resize:
        size = calc_new_size(size, resize)

    svg_base64 = text_to_base64(svg)
    xml = create_model_xml(svg_base64, size, points, label)
    deflated_xml = deflate_raw(xml)

    return {
        'xml': deflated_xml,
        'w': size[0],
        'h': size[1],
        'title': title,
        'aspect': 'fixed',
    }


def get_size(svg: str) -> (float, float):
    def parse_units(val: str) -> Optional[float]:
        if val is None:
            return None

        if val and val.endswith('px'):
            val = val[:-2]

        try:
            return float(val)
        except ValueError:
            logger.warning(f'Not supported size unit in value: {val}')
            return None

    root = ET.fromstring(svg)

    width = parse_units(root.get('width'))
    height = parse_units(root.get('height'))

    if not width or not height:
        viewbox = root.get('viewBox')
        if not viewbox:
            raise Exception('No width and height or viewBox defined in SVG')
        (box_x, box_y, box_width, box_height) = viewbox.split(' ')
        width = float(box_width) - float(box_x)
        height = float(box_height) - float(box_y)

    return width, height


def calc_new_size(size: (float, float), resize: (str, int)) -> (float, float):
    (width, height) = size
    (resize_type, resize_value) = resize

    if resize_type == 'longest':
        resize_type = 'width' if width > height else 'height'

    aspect_ratio = width / height

    if resize_type == 'width':
        new_width = resize_value
        new_height = new_width / aspect_ratio
    else:
        new_height = resize_value
        new_width = new_height * aspect_ratio

    return new_width, new_height


def create_model_xml(svg: str, size: Tuple[float, float], points: List[Tuple[float, float]], label: str) -> str:
    model = ET.Element("mxGraphModel")
    root = ET.SubElement(model, "root")

    ET.SubElement(root, "mxCell", {'id': '0'})
    ET.SubElement(root, "mxCell", {'id': '1', 'parent': '0'})

    image_styles = {
        'shape': 'image',
        'verticalLabelPosition': 'bottom',
        'verticalAlign': 'top',
        'imageAspect': '0',
        'aspect': 'fixed',
        'image': 'data:image/svg+xml,' + svg,
        'points': '[' + ','.join([f'[{p[0]},{p[1]}]' for p in points]) + ']',
    }
    image_cell = ET.SubElement(root, "mxCell", {
        'id': '2',
        'parent': '1',
        'vertex': '1',
        'style': styles_to_str(image_styles)
    })
    ET.SubElement(image_cell, "mxGeometry", {'width': str(size[0]), 'height': str(size[1]), 'as': 'geometry'})

    if label:
        label_styles = {
            'text': None,
            'html': '1',
            'align': 'center',
            'verticalAlign': 'middle',
            'resizable': '0',
            'points': '[]',
            'autosize': '1',
        }
        label_cell = ET.SubElement(root, "mxCell", {
            'id': '3',
            'parent': '1',
            'vertex': '1',
            'style': styles_to_str(label_styles),
            'value': label,
        })
        ET.SubElement(label_cell, "mxGeometry",
                      {'width': str(size), 'height': str(20), 'y': str(size), 'as': 'geometry'})

    return ET.tostring(model, encoding='unicode', method='xml')


def styles_to_str(styles: Dict[str, str]) -> str:
    params = []
    for k, v in styles.items():
        params.append(f'{k}={v}' if v is not None else k)
    return ';'.join(params)


def create_library_xml(data: str) -> str:
    library = ET.Element("mxlibrary")
    library.text = data
    return ET.tostring(library, encoding='unicode', method='xml')


def create_name(name: str, name_remove: List[str]) -> str:
    name = os.path.splitext(os.path.basename(name))[0]

    name = re.sub(r'|'.join(map(re.escape, name_remove)), ' ', name)
    name = re.sub(' +', ' ', name)

    name = name.strip()

    return name
