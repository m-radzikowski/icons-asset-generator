import json
import os
# noinspection PyPep8Naming
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from typing import Optional, Tuple, List, Dict
from urllib.parse import urljoin, quote

from diagrams_shapes_library.common.images_finder import get_image_groups
from diagrams_shapes_library.common.magnets import create_magnets
from diagrams_shapes_library.common.name import create_name
from diagrams_shapes_library.util.encoding import text_to_base64, deflate_raw
from diagrams_shapes_library.processor import Processor
from diagrams_shapes_library.util.io import create_output_dir
from diagrams_shapes_library.util.logger import get_logger

logger = get_logger(__name__)

diagrams_net_base_url = 'https://app.diagrams.net/?splash=0&clibs='


class DiagramsNet(Processor):

    def add_subcommand(self, subparsers) -> ArgumentParser:
        parser: ArgumentParser = subparsers.add_parser('diagrams.net', help='Shapes library for diagrams.net')

        parser.add_argument('--single-library', action='store_true', dest='single_library',
                            help='create single output library')
        parser.add_argument('--no-vertex-magnets', action='store_false', dest='vertex_magnets',
                            help='don\'t create connection points on vertices (corners)')
        parser.add_argument('--side-magnets', metavar='COUNT', default=5, type=int,
                            help='number of connection points for each side (default: 5)')
        parser.add_argument('--labels', action='store_true', dest='labels',
                            help='add label with name to images')
        parser.add_argument('--base-url', metavar='URL',
                            help='base URL to generate link(s) to open libraries in diagrams.net')

        return parser

    def process(self, **kwargs):
        logger.info('Creating Diagrams.net library')

        create_output_dir(kwargs['output'])

        libraries = get_image_groups(kwargs['path'], kwargs['filename_includes'], kwargs['filename_excludes'],
                                     kwargs['single_library'], kwargs['library_name_remove'])

        total_images_count = 0

        for library_name, library_images in libraries.items():
            logger.info(f'Processing {len(library_images)} images from group "{library_name}"')
            total_images_count += len(library_images)

            library = []
            for image in library_images:
                with open(image) as file:
                    svg = file.read()
                title = create_name(os.path.splitext(os.path.basename(image))[0], kwargs['image_name_remove'])
                library.append(
                    create_image_params(svg, title, kwargs['vertex_magnets'], kwargs['side_magnets'], kwargs['labels'],
                                        kwargs['size'])
                )

            library_json = json.dumps(library)
            library_xml = create_library_xml(library_json)

            library_file = os.path.join(kwargs['output'], library_name + '.xml')
            with open(library_file, 'w') as file:
                file.write(library_xml)

        if kwargs['base_url']:
            data = ''
            library_names = list(libraries.keys())
            library_names.sort()
            library_urls = ['U' + urljoin(kwargs['base_url'], quote(lib + '.xml')) for lib in library_names]

            if len(library_urls) > 1:
                all_url = diagrams_net_base_url + ';'.join(library_urls)
                data += f'All:\n{all_url}\n\n'

            for i in range(len(library_names)):
                data += library_names[i] + ':\n'
                data += diagrams_net_base_url + library_urls[i] + '\n\n'

            with open(os.path.join(kwargs['output'], 'links.txt'), 'w') as file:
                file.write(data)

        logger.info(f'Created {len(libraries)} library files with {total_images_count} elements')


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
