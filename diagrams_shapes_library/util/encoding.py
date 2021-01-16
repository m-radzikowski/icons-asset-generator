import base64
import zlib
from urllib.parse import quote


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


def encode_uri_component(data: str) -> str:
    return quote(data, safe='~()*!.\'')


def text_to_base64(data: str) -> str:
    return base64.standard_b64encode(data.encode('ascii')).decode('ascii')
