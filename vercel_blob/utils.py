"""
Utility functions for the Vercel Blob Storage API.
"""

import os
import time
import random
import math
from mimetypes import guess_type
from .errors import BlobRequestError

_DISALLOWED_PATHNAME_CHARACTERS = ["//"]
_MAXIMUM_PATHNAME_LENGTH = 950

_DEBUG = os.environ.get('VERCEL_BLOB_DEBUG', False)


def guess_mime_type(url) -> str:
    """
    Guess the MIME type of a file based on its URL.
    
    Args:
        url: The URL or path to the file
        
    Returns:
        str: The MIME type of the file, or "application/octet-stream" if it can't be determined
    """
    mime_type, _ = guess_type(url, strict=False)

    if mime_type:
        return mime_type
    else:
        return "application/octet-stream"


def validate_pathname(pathname: str) -> None:
    """
    Validates the pathname according to Vercel Blob specifications.

    Args:
        pathname (str): The pathname to validate

    Raises:
        BlobRequestError: If the pathname is invalid
    """
    if not pathname:
        raise BlobRequestError("pathname is required")

    if len(pathname) > _MAXIMUM_PATHNAME_LENGTH:
        raise BlobRequestError(f"pathname is too long, maximum length is {_MAXIMUM_PATHNAME_LENGTH}")

    for invalid_character in _DISALLOWED_PATHNAME_CHARACTERS:
        if invalid_character in pathname:
            raise BlobRequestError(f'pathname cannot contain "{invalid_character}", please encode it if needed')


def generate_request_id(token):
    """
    Generate a request ID similar to the Vercel Blob JavaScript SDK.

    Args:
        token (str): The authentication token

    Returns:
        str: A unique request ID
    """
    token_parts = token.split('_')
    store_id = token_parts[3] if len(token_parts) > 3 else ""

    timestamp = int(time.time() * 1000)

    random_hex = hex(math.floor(random.random() * 0xffffffff))[2:]

    return f"{store_id}:{timestamp}:{random_hex}"


def debug(message: str) -> None:
    """
    Prints debug message if the VERCEL_BLOB_DEBUG environment variable is set.
    
    Args:
        message (str): The debug message to print
    """
    if _DEBUG:
        print(message)


__all__ = ["guess_mime_type", "validate_pathname", "generate_request_id", "debug"]
