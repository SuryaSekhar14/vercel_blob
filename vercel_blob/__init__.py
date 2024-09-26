# pylint: disable=line-too-long


'''
This library provides a Python interface for interacting with the Vercel Blob Storage API. 

The package provides functions for uploading, downloading, listing, copying, and deleting blob objects in the Vercel Blob Store.

>>> import vercel_blob
>>> put(path = file_path, data = data).get("url")
'https://blobstore.public.blob.vercel-storage.com/file.txt-1673995438295-0'

The source code for this package can be found on GitHub at: https://github.com/SuryaSekhar14/vercel_blob
'''


from .blob_store import *


__author__ = 'Surya Sekhar Datta <hello@surya.dev>'
__version__ = '0.3.0'