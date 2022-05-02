import json
import os
# noinspection PyPep8Naming
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from typing import Tuple, List, Dict, Any

from diagrams_shapes_library.common.magnets import create_magnets
from diagrams_shapes_library.common.name import create_name
from diagrams_shapes_library.common.size import get_svg_size, calc_new_size
from diagrams_shapes_library.processor import Processor, ProcessorConfig
from diagrams_shapes_library.util.encoding import text_to_base64, deflate_raw
from diagrams_shapes_library.util.logger import get_logger

logger = get_logger(__name__)

diagrams_net_base_url = 'https://app.diagrams.net/?splash=0&clibs='


class DiagramsNetConfig(ProcessorConfig):
    labels = None
    base_url = None


class DiagramsNet(Processor):
    _conf: DiagramsNetConfig = None

    _library = []

    @staticmethod
    def add_subcommand(subparsers) -> ArgumentParser:
        parser: ArgumentParser = subparsers.add_parser('diagrams.net', help='Shapes library for diagrams.net')

        parser.add_argument('--labels', action='store_true', dest='labels',
                            help='add label with name to images')

        return parser

    @staticmethod
    def _create_config(config: Dict[str, Any]) -> DiagramsNetConfig:
        return DiagramsNetConfig(config)

    def process(self):
        logger.info('Creating Diagrams.net library')

        super().process()

        self._write_library()

    def process_group(self, library_name: str, library_images: List[str]):
        super().process_group(library_name, library_images)

        for image in library_images:
            logger.debug(f'Processing file {image}')

            with open(image) as file:
                svg = file.read()
            title = create_name(os.path.splitext(os.path.basename(image))[0], self._conf.image_name_remove)

            self._library.append(
                self._create_image_params(svg, title)
            )

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

    def _write_library(self):
        library_json = json.dumps(self._library)
        library_xml = self._create_library_xml(library_json)

        library_file = os.path.join(self._conf.output, f'{self._library_name}.xml')
        with open(library_file, 'w') as file:
            file.write(library_xml)
        logger.info(f'Created {library_file}')
