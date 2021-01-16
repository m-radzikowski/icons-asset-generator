import os
import shutil


def create_output_dir(dir_name) -> None:
    shutil.rmtree(dir_name, ignore_errors=True)
    os.mkdir(dir_name)
