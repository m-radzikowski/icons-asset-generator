import os
import plistlib
from argparse import ArgumentParser
from typing import List, Dict, Any, Tuple

import cairosvg
from PyPDF2 import PdfFileReader

from diagrams_shapes_library.common.name import create_name
from diagrams_shapes_library.processor import Processor, ProcessorConfig
from diagrams_shapes_library.util.logger import get_logger

logger = get_logger(__name__)

templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
data_template_file = os.path.join(templates_dir, 'data.plist')
sheet_template_file = os.path.join(templates_dir, 'sheet.plist')
image_template_file = os.path.join(templates_dir, 'image.plist')

stencil_file_name = 'output.gstencil'


class OmniGraffleConfig(ProcessorConfig):
    text_output: bool = None


class OmniGraffle(Processor):
    _conf: OmniGraffleConfig = None

    _data_pl = None
    _image_pl_tpl = None
    _stencil_path = None
    _image_idx = 0

    @staticmethod
    def add_subcommand(subparsers) -> ArgumentParser:
        parser: ArgumentParser = subparsers.add_parser('omnigraffle', help='Stencil for OmniGraffle')

        parser.add_argument('--text-output', action='store_true',
                            help='write OmniGraffle data file as text instead of binary')

        return parser

    def process(self):
        logger.info('Creating OmniGraffle stencil')

        self._data_pl = self._create_data_plist()
        self._image_pl_tpl = self._load_image_plist_template()

        self._stencil_path = os.path.join(self._conf.output, stencil_file_name)

        super().process()

        self._save_data_plist(self._stencil_path, self._data_pl, self._conf.text_output)

    def _create_dirs(self):
        super()._create_dirs()
        os.mkdir(self._stencil_path)

    def process_group(self, library_name: str, library_images: List[str]):
        super().process_group(library_name, library_images)

        sheet_pl = self._create_sheet_plist(library_name)
        sheet_image_bounds = []

        for image in library_images:
            logger.debug(f'Processing file {image}')

            self._image_idx += 1
            pdf_image_path = self._save_image_as_pdf(image, self._stencil_path, self._image_idx)
            stencil_name = create_name(image, self._conf.image_name_remove)
            sheet_image_bounds.append(self._calc_next_image_bounds(pdf_image_path, sheet_image_bounds))
            image_pl = self._create_image_plist(self._image_pl_tpl, self._image_idx, stencil_name, sheet_image_bounds[-1],
                                                self._conf.vertex_magnets, self._conf.side_magnets)
            self._add_image_to_sheet(sheet_pl, image_pl)

        self._add_sheet_to_data(self._data_pl, sheet_pl)

    @staticmethod
    def _add_image_to_sheet(sheet_pl: Dict[str, Any], image_pl: Dict[str, Any]) -> None:
        sheet_pl['GraphicsList'].append(image_pl)

    @staticmethod
    def _save_image_as_pdf(source: str, dir_path: str, idx: int) -> str:
        pdf_path = os.path.join(dir_path, f'image{idx}.pdf')
        cairosvg.svg2pdf(url=source, write_to=pdf_path, dpi=72)
        return pdf_path

    @staticmethod
    def _calc_next_image_bounds(pdf_image_path: str, sheet_image_bounds: List[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
        with open(pdf_image_path, 'rb') as fp:
            input1 = PdfFileReader(fp)
            media_box = input1.getPage(0).mediaBox

        _, _, width, height = media_box
        space_between = 50

        if len(sheet_image_bounds) == 0:
            x = 0
            y = 0
        elif len(sheet_image_bounds) > 1 and (len(sheet_image_bounds)) % 5 == 0:
            last_line_bounds = sheet_image_bounds[-5:]
            _, prev_y, _, _ = last_line_bounds[0]

            max_last_line_height = max(bounds[3] for bounds in last_line_bounds)

            x = 0
            y = prev_y + max_last_line_height + space_between
        else:
            prev_x, prev_y, prev_width, prev_height = sheet_image_bounds[-1]
            x = prev_x + prev_width + space_between
            y = prev_y

        return x, y, width, height

    def _create_image_plist(self, plist_template: Dict[str, Any], idx: int, stencil_name: str, bounds: Tuple[int, int, int, int],
                            vertex_magnets: bool, side_magnets: int) -> Dict[str, Any]:
        image_pl = plist_template.copy()
        image_pl['Bounds'] = '{{' + str(bounds[0]) + ', ' + str(bounds[1]) + '},' + \
                             '{' + str(bounds[2]) + ', ' + str(bounds[3]) + '}}'
        image_pl['ID'] = idx
        image_pl['ImageID'] = idx
        image_pl['Name'] = stencil_name

        magnet_positions = []
        if vertex_magnets:
            magnet_positions.extend(self._create_vertex_magnets())
        magnet_positions.extend(self._create_side_magnets(side_magnets))

        magnets = ['{' + str(pos[0]) + ', ' + str(pos[1]) + '}' for pos in magnet_positions]
        image_pl['Magnets'] = magnets

        return image_pl

    @staticmethod
    def _create_vertex_magnets() -> List[Tuple[float, float]]:
        return [
            (-1, -1),
            (1, -1),
            (1, 1),
            (-1, 1),
        ]

    @staticmethod
    def _create_side_magnets(count: int) -> List[Tuple[float, float]]:
        factor = 2 / (count + 1)

        magnets = []
        for i in range(1, count + 1):
            value = -1 + factor * i
            magnets.extend([
                (-1, value),
                (value, -1),
                (1, value),
                (value, 1),
            ])

        return magnets

    def _load_image_plist_template(self) -> Dict[str, Any]:
        return self._load_plist(image_template_file)

    def _create_data_plist(self) -> Dict[str, Any]:
        return self._load_plist(data_template_file)

    def _create_sheet_plist(self, sheet_title: str) -> Dict[str, Any]:
        sheet_pl = self._load_plist(sheet_template_file)
        sheet_pl['SheetTitle'] = sheet_title
        return sheet_pl

    @staticmethod
    def _add_sheet_to_data(data_pl: Dict[str, Any], sheet_pl: Dict[str, Any]) -> None:
        images_count = len(sheet_pl['GraphicsList'])

        data_pl['Sheets'].append(sheet_pl)

        data_pl['ImageCounter'] += images_count
        data_pl['ImageList'].extend([f'image{image["ID"]}.pdf' for image in sheet_pl['GraphicsList']])

    @staticmethod
    def _load_plist(file_path: str) -> Dict[str, Any]:
        with open(file_path, 'rb') as fp:
            return plistlib.load(fp)

    @staticmethod
    def _save_data_plist(path: str, data_pl: Dict[str, Any], text_output: bool) -> None:
        data_file = os.path.join(path, 'data.plist')
        with open(data_file, 'wb') as fp:
            fmt = plistlib.FMT_XML if text_output else plistlib.FMT_BINARY
            # noinspection PyTypeChecker
            plistlib.dump(data_pl, fp, fmt=fmt)
