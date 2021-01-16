import os
import re
from typing import List


def create_name(file_path: str, name_remove: List[str]) -> str:
    name = os.path.splitext(os.path.basename(file_path))[0]

    name = re.sub(r'|'.join(map(re.escape, name_remove)), ' ', name)
    name = re.sub(' +', ' ', name)

    name = name.strip()

    return name
