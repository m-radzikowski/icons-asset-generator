import logging


def setup_logging():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
