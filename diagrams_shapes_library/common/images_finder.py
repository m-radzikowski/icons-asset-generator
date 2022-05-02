import glob
import os
from collections import defaultdict
from itertools import filterfalse
from typing import List, Dict

from diagrams_shapes_library.common.name import create_name
from diagrams_shapes_library.util.logger import get_logger

logger = get_logger(__name__)


def get_image_groups(path: str, filename_includes: List[str], filename_excludes: List[str],
                     group_name_remove: List[str],
                     image_extension='svg') -> Dict[str, List[str]]:
    images = _list_images(path, image_extension, filename_includes, filename_excludes)

    if not images:
        raise Exception('No images found')

    return group_images(path, images, group_name_remove)


def _list_images(dir_path: str, ext: str, name_includes: List[str], name_excludes: List[str]) -> List[str]:
    files = [f for f in glob.glob(os.path.join(dir_path, '**/*.' + ext), recursive=True)]

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


def group_images(base_path: str, images: List[str], group_name_remove: List[str]) -> Dict[str, List[str]]:
    groups = defaultdict(list)

    for image in images:
        group_name = get_group_name(base_path, image, group_name_remove)
        groups[group_name].append(image)

    return groups


def get_group_name(base_path: str, file_name: str, group_name_remove: List[str]) -> str:
    abs_base_path = os.path.abspath(base_path)
    abs_file_path = os.path.abspath(file_name)
    rel_file_path = abs_file_path[len(abs_base_path) + 1:]

    if rel_file_path.find('/') == -1:  # file in root-level images dir
        group_name = abs_base_path.split('/')[-1]
    else:
        group_name = rel_file_path.split('/')[0]

    name = create_name(group_name, group_name_remove)

    return name
