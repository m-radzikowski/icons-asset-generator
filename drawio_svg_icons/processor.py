import glob
import json
import os
import re
import shutil
import sys
import xml.etree.cElementTree as ET
from argparse import Namespace, ArgumentParser
from itertools import filterfalse, groupby
from typing import List, Dict

from drawio_svg_icons.encoding import deflate_raw, text_to_base64


def main():
    args = parse_arguments()

    size = 50

    create_output_dir(args.output_dir)

    images = list_images(args.svg_dir, args.filename_includes, args.filename_excludes)

    if not images:
        print('No SVG images found', file=sys.stderr)
        exit(1)

    if args.single_library:
        grouped_images = {
            args.svg_dir.split('/')[-1]: images
        }
    else:
        grouped_images = group_images_by_dir(args.svg_dir, images)

    total_count = 0

    for group_name, group_images in grouped_images.items():
        print(f'Processing {len(group_images)} images from group "{group_name}"')
        total_count += len(group_images)

        library = []
        for image in group_images:
            with open(image) as file:
                svg = file.read()
            svg_base64 = text_to_base64(svg)
            xml = create_model_xml(svg_base64, size)
            deflated = deflate_raw(xml)
            library.append({
                'xml': deflated,
                'w': size,
                'h': size,
                'title': create_name(os.path.splitext(os.path.basename(image))[0], args.image_name_remove),
                'aspect': 'fixed',
            })

        library_json = json.dumps(library)
        library_xml = create_library_xml(library_json)

        library_file = os.path.join(args.output_dir, create_name(group_name, args.library_name_remove) + '.xml')
        with open(library_file, 'w') as file:
            file.write(library_xml)

    print(f'Created {len(grouped_images)} library files with {total_count} elements')


def parse_arguments() -> Namespace:
    parser = ArgumentParser(description='Convert SVG files into diagrams.net library')
    parser.add_argument('--svg-dir', default='./svg', help='svg files directory path (default: ./svg)')
    parser.add_argument('--output-dir', default='./library',
                        help='path to the output directory (default: ./library)')
    parser.add_argument('--filename-includes', default=[], action='extend', nargs='*',
                        help='strings to filter image file name by, taking only those which contains them all')
    parser.add_argument('--filename-excludes', default=[], action='extend', nargs='*',
                        help='strings to filter image file name by, taking only those which do not contain any of them')
    parser.add_argument('--image-name-remove', default=['.', '-', '_'], action='extend', nargs='*',
                        help='strings to be removed and replaced by spaces from image file name (default: . - _)')
    parser.add_argument('--library-name-remove', default=['.', '-', '_'], action='extend', nargs='*',
                        help='strings to be removed and replaced by spaces from library file name (default: . - _)')
    parser.add_argument('--single-library', action='store_true', dest='single_library',
                        help='create single output library')

    return parser.parse_args()


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
    return file_name[len(path):].split('/')[1]


def create_model_xml(svg: str, size: int) -> str:
    model = ET.Element("mxGraphModel")
    root = ET.SubElement(model, "root")

    ET.SubElement(root, "mxCell", {'id': '0'})
    ET.SubElement(root, "mxCell", {'id': '1', 'parent': '0'})

    styles = {
        'shape': 'image',
        'verticalLabelPosition': 'bottom',
        'verticalAlign': 'top',
        'imageAspect': '0',
        'aspect': 'fixed',
        'image': 'data:image/svg+xml,' + svg,
    }
    style = ';'.join([f'{k}={v}' for k, v in styles.items()])

    cell = ET.SubElement(root, "mxCell", {'id': '2', 'parent': '1', 'vertex': '1', 'style': style})
    ET.SubElement(cell, "mxGeometry", {'width': str(size), 'height': str(size), 'as': 'geometry'})

    return ET.tostring(model, encoding='unicode', method='xml')


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
