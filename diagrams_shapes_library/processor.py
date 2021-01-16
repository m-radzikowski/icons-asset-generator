from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser
from typing import Dict, Any


class Processor(metaclass=ABCMeta):

    @abstractmethod
    def add_subcommand(self, subparsers) -> ArgumentParser:
        pass

    @abstractmethod
    def process(self, args: Dict[str, Any]):
        pass
