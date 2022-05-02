import json
import os
# noinspection PyPep8Naming
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from typing import Tuple, List, Dict, Any
from urllib.parse import urljoin, quote

from diagrams_shapes_library.common.images_finder import get_image_groups
from diagrams_shapes_library.common.magnets import create_magnets
from diagrams_shapes_library.common.name import create_name
from diagrams_shapes_library.common.size import get_svg_size, calc_new_size
from diagrams_shapes_library.processor import Processor, ProcessorConfig
from diagrams_shapes_library.util.encoding import text_to_base64, deflate_raw
from diagrams_shapes_library.util.io import create_output_dir
from diagrams_shapes_library.util.logger import get_logger

logger = get_logger(__name__)

diagrams_net_base_url = 'https://app.diagrams.net/?splash=0&clibs='


class DiagramsNetConfig(ProcessorConfig):
    single_library: bool = None
    vertex_magnets = None
    side_magnets = None
    labels = None
    base_url = None


class DiagramsNet(Processor):
    _conf: DiagramsNetConfig = None

    @staticmethod
    def add_subcommand(subparsers) -> ArgumentParser:
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

    @staticmethod
    def _create_config(config: Dict[str, Any]) -> DiagramsNetConfig:
        return DiagramsNetConfig(config)

    def process(self):
        logger.info('Creating Diagrams.net library')

        create_output_dir(self._conf.output)

        libraries = get_image_groups(self._conf.path, self._conf.filename_includes, self._conf.filename_excludes,
                                     self._conf.single_library, self._conf.library_name_remove)

        total_images_count = sum(len(images) for images in libraries.values())

        for library_name, library_images in libraries.items():
            self._process_group(library_name, library_images)

        if self._conf.base_url:
            self._generate_links(libraries)

        logger.info(f'Created {len(libraries)} library files with {total_images_count} elements')

    def _process_group(self, library_name: str, library_images: List[str]):
        logger.info(f'Processing {len(library_images)} images from group "{library_name}"')

        library = []
        for image in library_images:
            logger.debug(f'Processing file {image}')

            with open(image) as file:
                svg = file.read()
            title = create_name(os.path.splitext(os.path.basename(image))[0], self._conf.image_name_remove)

            library.append(
                self._create_image_params(svg, title)
            )

        library_json = json.dumps(library)
        library_xml = self._create_library_xml(library_json)

        library_file = os.path.join(self._conf.output, library_name + '.xml')
        with open(library_file, 'w') as file:
            file.write(library_xml)

    def _create_image_params(self, svg: str, title: str) -> dict:
        points = create_magnets(self._conf.vertex_magnets, self._conf.side_magnets)
        label = title if self._conf.labels else None
        size = get_svg_size(svg)

        if self._conf.size:
            size = calc_new_size(size, self._conf.size)

        svg_base64 = text_to_base64(svg)
        xml = self._create_model_xml(svg_base64, size, points, label)
        deflated_xml = deflate_raw(xml)

        return {
            'xml': deflated_xml,
            'w': size[0],
            'h': size[1],
            'title': title,
            'aspect': 'fixed',
        }

    def _create_model_xml(self, svg: str, size: Tuple[float, float], points: List[Tuple[float, float]],
                          label: str) -> str:
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
            'style': self._styles_to_str(image_styles)
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
                'style': self._styles_to_str(label_styles),
                'value': label,
            })
            ET.SubElement(label_cell, "mxGeometry",
                          {'width': str(size), 'height': str(20), 'y': str(size), 'as': 'geometry'})

        return ET.tostring(model, encoding='unicode', method='xml')

    @staticmethod
    def _styles_to_str(styles: Dict[str, str]) -> str:
        params = []
        for k, v in styles.items():
            params.append(f'{k}={v}' if v is not None else k)
        return ';'.join(params)

    @staticmethod
    def _create_library_xml(data: str) -> str:
        library = ET.Element("mxlibrary")
        library.text = data
        return ET.tostring(library, encoding='unicode', method='xml')

    def _generate_links(self, libraries):
        data = ''
        library_names = list(libraries.keys())
        library_names.sort()
        library_urls = ['U' + urljoin(self._conf.base_url, quote(lib + '.xml')) for lib in library_names]

        if len(library_urls) > 1:
            all_url = diagrams_net_base_url + ';'.join(library_urls)
            data += f'All:\n{all_url}\n\n'

        for i in range(len(library_names)):
            data += library_names[i] + ':\n'
            data += diagrams_net_base_url + library_urls[i] + '\n\n'

        with open(os.path.join(self._conf.output, 'links.txt'), 'w') as file:
            file.write(data)
