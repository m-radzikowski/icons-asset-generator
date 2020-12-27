import base64
import glob
import gzip
import json
import os
import re
import shutil
import sys
import zlib
from itertools import filterfalse, groupby
from typing import List, Dict

import xml.etree.cElementTree as ET
from urllib.parse import quote


def main():
    path = './AWS-Architecture-Assets-For-Light-and-Dark-BG_20200911/AWS-Architecture-Service-Icons_20200911'
    filename_includes = ['_48']
    filename_excludes = []
    image_name_remove = ['.', '_', '-', 'Arch', '48']
    library_name_remove = ['.', '_', '-', 'Arch']
    size = 50
    output_dir = 'library'

    create_output_dir(output_dir)

    images = list_images(path, filename_includes, filename_excludes)

    if not images:
        print('No SVG images found', file=sys.stderr)
        exit(1)

    grouped_images = group_images_by_dir(path, images)
    total_count = 0

    for group_name, group_images in grouped_images.items():
        print(f'Processing {len(group_images)} images from group "{group_name}"')
        total_count += len(group_images)

        library = []
        for image in group_images:
            with open(image) as file:
                svg = file.read()
            svg_base64 = base64.standard_b64encode(svg.encode('ascii')).decode('ascii')
            xml = create_model_xml(svg_base64, size)
            deflated = deflate_raw(xml)
            library.append({
                'xml': deflated,
                'w': size,
                'h': size,
                'title': create_name(os.path.splitext(os.path.basename(image))[0], image_name_remove),
                'aspect': 'fixed',
            })

        library_json = json.dumps(library)
        library_xml = create_library_xml(library_json)

        with open(os.path.join(output_dir, create_name(group_name, library_name_remove) + '.xml'), 'w') as file:
            file.write(library_xml)

    print(f'Created {len(grouped_images)} library files with {total_count} elements')


def create_name(name: str, name_remove: List[str]) -> str:
    name = os.path.splitext(os.path.basename(name))[0]

    name = re.sub(r'|'.join(map(re.escape, name_remove)), ' ', name)
    name = re.sub(' +', ' ', name)

    name = name.strip()

    return name


def deflate_raw(data: str):
    """
    Deflates data with zlib, but without wrapper (header and CRC).
    See https://stackoverflow.com/a/59051367
    :return: Base64 encoded compressed data
    """
    compress = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15, memLevel=8,
                                strategy=zlib.Z_DEFAULT_STRATEGY)
    encoded_data = encode_uri_component(data).encode('ascii')
    compressed_data = compress.compress(encoded_data)
    compressed_data += compress.flush()
    return base64.b64encode(compressed_data).decode('ascii')


def encode_uri_component(data):
    return quote(data, safe='~()*!.\'')


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


if __name__ == '__main__':
    main()
