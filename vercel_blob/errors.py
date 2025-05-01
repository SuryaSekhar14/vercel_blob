# pylint: disable=unnecessary-pass

"""
Custom exceptions for the Vercel Blob Store API.
"""

class BlobConfigError(Exception):
    """Exception raised for configuration errors in the Vercel Blob Store."""
    pass

class BlobRequestError(Exception):
    """Exception raised for errors during API requests to the Vercel Blob Store."""
    pass

class BlobFileError(Exception):
    """Exception raised for file-related errors when working with the Vercel Blob Store."""
    pass

class InvalidColorError(ValueError):
    """Raised when an invalid color code is provided."""
    pass

__all__ = ["BlobConfigError", "BlobRequestError", "BlobFileError", "InvalidColorError"]
