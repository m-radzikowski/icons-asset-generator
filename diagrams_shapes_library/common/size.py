from typing import Optional
# noinspection PyPep8Naming
from xml.etree import ElementTree as ET

from diagrams_shapes_library.util.logger import get_logger

logger = get_logger(__name__)


def get_svg_size(svg: str) -> (float, float):
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
