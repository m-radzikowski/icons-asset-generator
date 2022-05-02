import logging


def setup_logging(level):
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
