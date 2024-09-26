# pylint: disable=line-too-long, unidiomatic-typecheck, dangerous-default-value


'''
This library provides a Python interface for interacting with the Vercel Blob Storage API. 

The package provides functions for uploading, downloading, listing, copying, and deleting blob objects in the Vercel Blob Store.

>>> import vercel_blob
>>> put(path = file_path, data = data).get("url")
'https://blobstore.public.blob.vercel-storage.com/file.txt-1673995438295-0'

The source code for this package can be found on GitHub at: https://github.com/SuryaSekhar14/vercel_blob
'''


import os
import time
from mimetypes import guess_type
import requests


_VERCEL_BLOB_API_BASE_URL = 'https://blob.vercel-storage.com'
_API_VERSION = '7'
_PAGINATED_LIST_SIZE = 1000
_DEFAULT_CACHE_AGE = '31536000'
_MAX_RETRY_REQUEST_RETRIES = 3
_DEBUG = os.environ.get('VERCEL_BLOB_DEBUG', False)


def _get_auth_token_from_env() -> str:
    token = os.environ.get('BLOB_READ_WRITE_TOKEN')

    if not token:
        raise Exception('BLOB_READ_WRITE_TOKEN environment variable not set')

    return token


def _get_auth_token(options: dict) -> str:
    try:
        _tkn = options['token']
    except KeyError:
        _tkn = _get_auth_token_from_env()

    return _tkn


def _guess_mime_type(url) -> str:
    mime_type, _ = guess_type(url, strict=False)

    if mime_type:
        return mime_type
    else:
        return "application/octet-stream"


def _get_script_path() -> str:
    return os.getcwd() + '/'


def _request_factory(url: str, method: str, backoff_factor: int = 0.5, timeout: int = 10, **kwargs) -> requests.Response:
    for attempt in range(1, _MAX_RETRY_REQUEST_RETRIES + 1):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            if response.status_code not in (502, 503, 504):
                return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed on attempt {attempt} ({e})")
            time.sleep(backoff_factor * attempt)
    return None


def _response_handler(resp: requests.Response) -> dict:
    if resp is None:
        raise Exception("Request failed after retries. Please try again.")
    elif resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(f"An error occoured: {resp.json()}")


def list(options: dict = {}) -> dict:
    """
    Retrieves a list of items from the blob store based on the provided options.

    Args:
        options (dict, optional): A dictionary with the following optional parameters:

            -> `token` (str, optional): A string containing the token to be used for authorization. If not provided, the token will be read from the environment variable.
            -> `limit` (int, optional): The number of items to retrieve. Defaults to 1000.
            -> `prefix` (str, optional): A string used to filter for blob objects contained in a specific folder assuming that the folder name was used in the pathname when the blob object was uploaded
            -> `cursor` (str, optional): A string obtained from a previous response for pagination of retults
            -> `mode` (str, optional): A string specifying the response format. Can either be `expanded` (default) or `folded`. In folded mode all blobs that are located inside a folder will be folded into a single folder string entry
    
    Returns:
        dict: A dictionary containing the response from the blob store.

    Raises:
        AssertionError: If the options parameter is not a dictionary object.

    Example:
        >>> list({"limit": "4", "cursor": "cursor_string_here"})
    """

    assert type(options) == type({}), "Options passed must be a Dictionary Object"

    headers = {
        "authorization": f'Bearer {_get_auth_token(options)}',
    }

    params = {
        "limit": options.get('limit', str(_PAGINATED_LIST_SIZE)),
    }

    if options.get('prefix'):
        params['prefix'] = options['prefix']
    if options.get('cursor'):
        params['cursor'] = options['cursor']
    if options.get('mode'):
        params['mode'] = options['mode']

    if _DEBUG:
        print("Headers: " + str(headers))

    resp = _request_factory(
        f"{_VERCEL_BLOB_API_BASE_URL}",
        'GET',
        params=params,
        headers=headers,
    )

    return _response_handler(resp)


def put(path: str, data: bytes, options: dict = {}) -> dict:
    """
    Uploads the given data to the specified path in the Vercel Blob Store.

    Args:
        path (str): The path inside the blob store, where the data will be uploaded.
        data (bytes): The data to be uploaded.
        options (dict, optional): A dictionary with the following optional parameters:

            -> `token` (str, optional): A string containing the token to be used for authorization. If not provided, the token will be read from the environment variable.
            -> `addRandomSuffix` (str, optional): A boolean value to specify if a random suffix should be added to the path. Defaults to "true".
            -> `cacheControlMaxAge` (str, optional): A string containing the cache control max age value. Defaults to "31536000".
            
    Returns:
        dict: The response from the Vercel Blob Store API.

    Raises:
        AssertionError: If the type of `path` is not a string object.
        AssertionError: If the type of `data` is not a bytes object.
        AssertionError: If the type of `options` is not a dictionary object.

    Example:
        >>> with open('test.txt', 'rb') as f:
        >>>     put("test.txt", f.read(), {"addRandomSuffix": "true"})
    """

    assert type(path) == type(""), "path must be a string object"
    assert type(data) == type(b""), "data must be a bytes object"
    assert type(options) == type({}), "Options passed must be a Dictionary Object"

    headers = {
        "access": "public",  # Support for private is not yet there, according to Vercel docs at time of writing this code
        "authorization": f'Bearer {_get_auth_token(options)}',
        "x-api-version": _API_VERSION,
        "x-content-type": _guess_mime_type(path),
        "x-cache-control-max-age": options.get('cacheControlMaxAge', _DEFAULT_CACHE_AGE),
    }

    if options.get('addRandomSuffix') in ("false", False, "0"):
        headers['x-add-random-suffix'] = "0"

    if _DEBUG:
        print("Headers: " + str(headers))

    resp = _request_factory(
        f"{_VERCEL_BLOB_API_BASE_URL}/{path}",
        'PUT',
        headers=headers,
        data=data,
    )

    return _response_handler(resp)


def head(url: str, options: dict = {}) -> dict:
    """
    Gets the metadata of the blob object at the specified URL.

    Args:
        url (str): The URL to send the HEAD request to.
        options (dict, optional): Additional options for the request. Defaults to {}.

            -> `token` (str, optional): A string containing the token to be used for authorization. If not provided, the token will be read from the environment variable.

    Returns:
        dict: The response from the HEAD request.

    Raises:
        AssertionError: If the `url` argument is not a string object.
        AssertionError: If the `options` argument is not a dictionary object.

    Example:
        >>> head("https://blobstore.public.blob.vercel-storage.com/test-folder/test.txt")
    """

    assert type(url) == type(""), "url must be a string object"
    assert type(options) == type({}), "Options passed must be a Dictionary Object"

    headers = {
        "authorization": f'Bearer {_get_auth_token(options)}',
        "x-api-version": _API_VERSION,
    }

    if _DEBUG:
        print("Headers: " + str(headers))

    resp = _request_factory(
        f"{_VERCEL_BLOB_API_BASE_URL}/?url={url}",
        'GET',
        headers=headers,
    )

    return _response_handler(resp)


def delete(url: any, options: dict = {}) -> dict:
    """
    Deletes the specified URL(s) from the Vercel Blob Store.

    Args:
        url (str or list): The URL(s) to be deleted. It can be a string or a list of strings.
        options (dict, optional): Additional options for the delete operation. Defaults to {}.

            -> `token` (str, optional): A string containing the token to be used for authorization. If not provided, the token will be read from the environment variable.

    Returns:
        dict: The response from the delete operation.

    Raises:
        Exception: If the url parameter is not a string or a list of strings.

    Example:
        >>> delete("https://blobstore.public.blob.vercel-storage.com/test-folder/test.txt")
    """

    assert type(options) == type({}), "Options passed must be a Dictionary Object"

    headers = {
        "authorization": f'Bearer {_get_auth_token(options)}',
        "x-api-version": _API_VERSION,
    }

    if type(url) == type("") or (type(url) == type([]) and all(isinstance(u, str) for u in url)):
        if _DEBUG:
            print("Headers: " + str(headers))

        resp = _request_factory(
            f"{_VERCEL_BLOB_API_BASE_URL}/delete",
            'POST',
            headers=headers,
            json={"urls": [url] if isinstance(url, str) else url},
        )
        return _response_handler(resp)
    else:
        raise Exception('url must be a string or a list of strings')


def copy(blob_url: str, to_path: str, options: dict = {}) -> dict:
    """
    Copy a blob from a source URL to a destination path inside the blob store.

    Args:
        blob_url (str): The URL of the source blob.
        to_path (str): The destination path where the blob will be copied to.
        options (dict, optional): Additional options for the copy operation. Defaults to {}.

            -> `token` (str, optional): A string containing the token to be used for authorization. If not provided, the token will be read from the environment variable.
            -> `cacheControlMaxAge` (str, optional): A string containing the cache control max age value. Defaults to "31536000".
            -> `addRandomSuffix` (str, optional): A boolean value to specify if a random suffix should be added to the path. Defaults to "false" for copy operation.

    Returns:
        dict: The response from the copy operation.

    Raises:
        AssertionError: If the blob_url parameter is not a string object.
        AssertionError: If the to_path parameter is not a string object.
        AssertionError: If the options parameter is not a dictionary object.

    Example:
        >>> copy("https://blobstore.public.blob.vercel-storage.com/test-folder/test.txt", "copy-test/test.txt", {"addRandomSuffix": "false"})
    """

    assert type(blob_url) == type(""), "blob_url must be a string object"
    assert type(to_path) == type(""), "to_path must be a string object"
    assert type(options) == type({}), "Options passed must be a Dictionary Object"

    headers = {
        "access": "public",
        "authorization": f'Bearer {_get_auth_token(options)}',
        "x-api-version": _API_VERSION,
        "x-content-type": _guess_mime_type(blob_url),
        "x-cache-control-max-age": options.get('cacheControlMaxAge', _DEFAULT_CACHE_AGE),
    }

    if options.get('addRandomSuffix') != None:
        headers['x-add-random-suffix'] = "1"

    if _DEBUG:
        print("Headers: " + str(headers))

    to_path_encoded = requests.utils.quote(to_path)
    resp = _request_factory(
        f"{_VERCEL_BLOB_API_BASE_URL}/{to_path_encoded}",
        'PUT',
        headers=headers,
        params={"fromUrl": blob_url},
    )

    return _response_handler(resp)


def download_file(url: str, path: str = '', options: dict = {}):
    """
    Downloads the blob object at the specified URL, and saves it to the specified path.

    Args:
        url (str): The URL of the blob object to download.
        path (str, optional): The path where the downloaded file will be saved. If not provided, the file will be saved in the current working directory.
        options (dict, optional): Additional options for the download operation. Defaults to {}.

            -> `token` (str, optional): A string containing the token to be used for authorization. If not provided, the token will be read from the environment variable.

    Returns:
        bytes: The data of the blob object.

    Raises:
        AssertionError: If the url parameter is not a string object.
        Exception: If an error occurs during the download process.

    Example:
        >>> download_file("https://blobstore.public.blob.vercel-storage.com/test-folder/test.txt", "path/to/save/", options={"token": "my_token"})
    """

    assert type(url) == type(""), "url must be a string object"
    assert type(path) == type(""), "path must be a string object"
    assert type(options) == type({}), "Options passed must be a Dictionary Object"

    script_path = _get_script_path()
    sanitized_path = path.lstrip('/')
    path_to_save = script_path + sanitized_path
    if path_to_save != script_path:
        assert path.endswith('/'), "path must be a valid directory path, ending with '/'"
        assert os.path.exists(path_to_save), "path must be a valid directory path"

    if _DEBUG:
        print(f"Downloading file from {url} to {path_to_save}")

    try:
        resp = _request_factory(
            f"{url}?download=1",
            'GET'
        ).content
        try:
            with open(f"{path_to_save}{url.split('/')[-1]}", 'wb') as f:
                f.write(resp)
        except FileNotFoundError as e:
            if _DEBUG:
                print(f"An error occurred. Please try again. Error: {e}")
            raise Exception("The directory must exist before downloading the file. Please create the directory and try again.")
    except Exception as e:
        if _DEBUG:
            print(f"An error occurred. Please try again. Error: {e}")
        raise Exception("An error occurred. Please try again.")
