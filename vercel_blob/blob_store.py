# pylint: disable=line-too-long, unidiomatic-typecheck

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
import concurrent.futures
from urllib.parse import urlencode
import requests
from tqdm import tqdm

from .progress import _default_colors, ProgressFile
from .errors import BlobConfigError, BlobRequestError, BlobFileError, InvalidColorError
from .utils import debug, validate_pathname, generate_request_id, guess_mime_type

_VERCEL_BLOB_API_BASE_URL = 'https://blob.vercel-storage.com'
_API_VERSION = '10'
_PAGINATED_LIST_SIZE = 1000
_DEFAULT_CACHE_AGE = '31536000'
_MAX_RETRY_REQUEST_RETRIES = 3

_MULTIPART_CHUNK_SIZE = 5 * 1024 * 1024  # 5MB

RED = "\033[1;31m"
NC = "\033[0m"


def _get_auth_token_from_env() -> str:
    token = os.environ.get('BLOB_READ_WRITE_TOKEN')

    if not token:
        raise BlobConfigError('BLOB_READ_WRITE_TOKEN environment variable not set')

    return token


def _get_auth_token(options: dict) -> str:
    try:
        _tkn = options['token']
    except KeyError:
        _tkn = _get_auth_token_from_env()

    return _tkn


def _get_script_path() -> str:
    return os.getcwd() + '/'


def _request_factory(url: str, method: str, backoff_factor: int = 0.5, timeout: int = 10, verbose: bool = False, **kwargs) -> requests.Response:
    """
    Factory function to create and send HTTP requests with retry logic.
    
    Args:
        url (str): The URL to send the request to
        method (str): The HTTP method to use
        backoff_factor (int): Factor to use for exponential backoff
        timeout (int): Timeout in seconds
        verbose (bool): Whether to show progress
        **kwargs: Additional arguments to pass to requests
        
    Returns:
        requests.Response: The response from the request
    """

    for attempt in range(1, _MAX_RETRY_REQUEST_RETRIES + 1):
        try:
            # Create a new session for each attempt
            with requests.Session() as session:
                # Handle upload with progress bar
                if verbose and method in ['PUT', 'POST'] and 'data' in kwargs:
                    data = kwargs['data']
                    total_size = len(data)

                    with tqdm(total=total_size, unit='B', unit_scale=True,
                            desc=f"{_default_colors.desc}Uploading{NC}",
                            bar_format=f"{_default_colors.text}{{l_bar}}{NC}{_default_colors.bar}{{bar:20}}{NC}{_default_colors.text}{{r_bar}}{NC}",
                            ncols=80, ascii=" █") as pbar:
                        progress_file = ProgressFile(data, pbar)

                        # Use the session for the request
                        response = session.request(
                            method,
                            url,
                            data=progress_file,
                            timeout=timeout,
                            **{k:v for k,v in kwargs.items() if k != 'data'}
                        )

                        if response.status_code not in (502, 503, 504):
                            return response

                # Handle download with progress bar
                elif verbose and method == 'GET':
                    response = session.request(method, url, timeout=timeout, stream=True, **kwargs)
                    if response.status_code not in (502, 503, 504):
                        total_size = int(response.headers.get('content-length', 0))
                        with tqdm(total=total_size, unit='B', unit_scale=True,
                                desc=f"{_default_colors.desc}Downloading{NC}",
                                bar_format=f"{_default_colors.text}{{l_bar}}{NC}{_default_colors.bar}{{bar:20}}{NC}{_default_colors.text}{{r_bar}}{NC}",
                                ncols=80, ascii=" █") as pbar:
                            content = b''
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    content += chunk
                                    pbar.update(len(chunk))
                            response._content = content
                            return response

                # Simple request without progress tracking
                else:
                    response = session.request(method, url, timeout=timeout, **kwargs)
                    if response.status_code not in (502, 503, 504):
                        return response

        except requests.exceptions.RequestException as e:
            print(f"Request failed on attempt {attempt} ({e})")
            time.sleep(backoff_factor * attempt)

    return None


def _response_handler(resp: requests.Response | None) -> dict:
    if resp is None:
        raise BlobRequestError("Request failed after retries. Please try again.")
    if resp.status_code != 200:
        raise BlobRequestError(f"An error occoured: {resp.json()}")
    else:
        return resp.json()


def list(options: dict = None, timeout: int = 10) -> dict:
    """
    Retrieves a list of items from the blob store based on the provided options.

    Args:
        options (dict, optional): A dictionary with the following optional parameters:

            -> `token` (str, optional): A string containing the token to be used for authorization. If not provided, the token will be read from the environment variable.
            -> `limit` (int, optional): The number of items to retrieve. Defaults to 1000.
            -> `prefix` (str, optional): A string used to filter for blob objects contained in a specific folder assuming that the folder name was used in the pathname when the blob object was uploaded
            -> `cursor` (str, optional): A string obtained from a previous response for pagination of retults
            -> `mode` (str, optional): A string specifying the response format. Can either be `expanded` (default) or `folded`. In folded mode all blobs that are located inside a folder will be folded into a single folder string entry
        timeout (int, optional): The timeout for the request. Defaults to 10.
    
    Returns:
        dict: A dictionary containing the response from the blob store.

    Raises:
        AssertionError: If the options parameter is not a dictionary object.

    Example:
        >>> list({"limit": "4", "cursor": "cursor_string_here"})
    """
    if options is None:
        options = {}

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

    debug("Headers: " + str(headers))

    resp = _request_factory(
        f"{_VERCEL_BLOB_API_BASE_URL}",
        'GET',
        params=params,
        headers=headers,
        timeout=timeout,
    )

    return _response_handler(resp)


def _create_multipart_upload(path: str, headers: dict, options: dict) -> dict:
    """
    Initiates a multipart upload session.
    
    Args:
        path (str): The path where the file will be uploaded
        headers (dict): Headers for the request
        options (dict): Additional options
        
    Returns:
        dict: Response containing uploadId and other metadata
    """
    validate_pathname(path)

    mpu_headers = headers.copy()
    mpu_headers['x-mpu-action'] = 'create'

    # Add request ID to headers
    token = _get_auth_token(options)
    request_id = generate_request_id(token)
    mpu_headers['x-api-blob-request-id'] = request_id
    mpu_headers['x-api-blob-request-attempt'] = '0'

    # Create full URL with query parameters
    query_string = urlencode({'pathname': path}, doseq=True)
    url = f"{_VERCEL_BLOB_API_BASE_URL}/mpu?{query_string}"

    # Debug the request
    debug("Creating MPU with:")
    debug(f"URL: {url}")
    debug(f"Headers: {mpu_headers}")
    debug(f"Request ID: {request_id}")

    try:
        resp = _request_factory(
            f"{_VERCEL_BLOB_API_BASE_URL}/mpu?pathname={path}",
            'POST',
            headers=mpu_headers,
            timeout=options.get('timeout', 10),
        )

        debug(f"Response status: {resp.status_code if resp else 'None'}")
        if resp:
            debug(f"Response headers: {resp.headers}")
            try:
                debug(f"Response body: {resp.json()}")
            except Exception as e:
                debug(f"Could not parse response as JSON: {e}")

        return _response_handler(resp)
    except Exception as e:
        debug(f"Error in create_multipart_upload: {str(e)}")
        raise BlobRequestError(f"Error in create_multipart_upload: {str(e)}") from e


def _upload_part(path: str, upload_id: str, key: str, part_number: int, data: bytes, headers: dict, options: dict, verbose: bool = False) -> dict:
    """
    Uploads a single part of a multipart upload.

    Args:
        path (str): The path where the file will be uploaded
        upload_id (str): The upload ID from create_multipart_upload
        key (str): The key from create_multipart_upload
        part_number (int): The part number (1-based)
        data (bytes): The data to upload
        headers (dict): Headers for the request
        options (dict): Additional options
        verbose (bool): Whether to show progress
        
    Returns:
        dict: Response containing part information
    """
    # Validate pathname first
    validate_pathname(path)

    part_headers = headers.copy()
    part_headers['x-mpu-action'] = 'upload'
    part_headers['x-mpu-upload-id'] = upload_id
    part_headers['x-mpu-key'] = requests.utils.quote(key)
    part_headers['x-mpu-part-number'] = str(part_number)
    part_headers['Content-Type'] = 'application/octet-stream'

    token = _get_auth_token(options)
    request_id = generate_request_id(token)
    part_headers['x-api-blob-request-id'] = request_id
    part_headers['x-api-blob-request-attempt'] = '0'

    url = f"{_VERCEL_BLOB_API_BASE_URL}/mpu?pathname={path}"

    debug(f"Uploading part {part_number}:")
    debug(f"URL: {url}")
    debug(f"Data length: {len(data)} bytes")
    debug(f"Upload ID: {upload_id}")

    resp = _request_factory(
        url,
        'POST',
        headers=part_headers,
        data=data,
        timeout=options.get('timeout', 30),
        verbose=verbose,
    )

    response_data = _response_handler(resp)

    debug(f"Part {part_number} upload response: {response_data}")

    # We need to extract the ETag from the response
    # In the current implementation, we're getting a full file response
    # Let's extract the etag from headers first
    etag = None

    # Try to get etag from response headers if available in resp
    if hasattr(resp, 'headers') and resp.headers.get('etag'):
        etag = resp.headers.get('etag')
    elif isinstance(response_data, dict):
        # Try to find etag in the response data
        if 'etag' in response_data:
            etag = response_data['etag']
        elif 'ETag' in response_data:
            etag = response_data['ETag']

    # If we still don't have an etag, generate one based on part number
    if not etag:
        # This is a fallback - the server should provide an etag
        etag = f"\"part-{part_number}-{int(time.time())}\""
        debug(f"Warning: Using fallback etag {etag} for part {part_number}")

    return {"partNumber": part_number, "etag": etag}


def _complete_multipart_upload(path: str, upload_id: str, key: str, parts: list, headers: dict, options: dict) -> dict:
    """
    Completes a multipart upload.
    
    Args:
        path (str): The path where the file was uploaded
        upload_id (str): The upload ID from create_multipart_upload
        key (str): The key from create_multipart_upload
        parts (list): List of uploaded parts
        headers (dict): Headers for the request
        options (dict): Additional options
        
    Returns:
        dict: Final response containing the uploaded file information
    """
    # Validate pathname first
    validate_pathname(path)

    complete_headers = headers.copy()
    complete_headers['x-mpu-action'] = 'complete'
    complete_headers['x-mpu-upload-id'] = upload_id
    complete_headers['x-mpu-key'] = requests.utils.quote(key)  # URL encode the key
    complete_headers['content-type'] = 'application/json'

    # Add request ID to headers
    token = _get_auth_token(options)
    request_id = generate_request_id(token)
    complete_headers['x-api-blob-request-id'] = request_id
    complete_headers['x-api-blob-request-attempt'] = '0'

    # Create URL for completion
    url = f"{_VERCEL_BLOB_API_BASE_URL}/mpu?pathname={path}"

    debug("Completing multipart upload:")
    debug(f"Parts: {parts}")

    # Format the parts array - make sure structure matches what's expected
    formatted_parts = []
    for part in parts:
        if isinstance(part, dict) and 'partNumber' in part and 'etag' in part:
            formatted_parts.append({
                'partNumber': part['partNumber'],
                'etag': part['etag']
            })

    resp = _request_factory(
        url,
        'POST',
        headers=complete_headers,
        json=formatted_parts,
        timeout=options.get('timeout', 10),
    )
    return _response_handler(resp)


def put(path: str, data: bytes, options: dict = None, timeout: int = 10, verbose: bool = False, multipart: bool = False) -> dict:
    """
    Uploads the given data to the specified path in the Vercel Blob Store.
    For files larger than 25MB, uses multipart upload.

    Args:
        path (str): The path inside the blob store, where the data will be uploaded.
        data (bytes): The data to be uploaded.
        options (dict, optional): A dictionary with the following optional parameters:

            -> `token` (str, optional): A string containing the token to be used for authorization. If not provided, the token will be read from the environment variable.
            -> `addRandomSuffix` (str, optional): A boolean value to specify if a random suffix should be added to the path. Defaults to "true".
            -> `cacheControlMaxAge` (str, optional): A string containing the cache control max age value. Defaults to "31536000".
            -> `allowOverwrite` (str, optional): A boolean value to specify if an existing file should be overwritten. Defaults to "false".
            -> `maxConcurrentUploads` (int, optional): Maximum number of concurrent part uploads. Defaults to 5.
        timeout (int, optional): The timeout for the request. Defaults to 10.
        verbose (bool, optional): Whether to show detailed information during upload. Defaults to False.
            
    Returns:
        dict: The response from the Vercel Blob Store API.

    Raises:
        AssertionError: If the type of `path` is not a string object.
        AssertionError: If the type of `data` is not a bytes object.
        AssertionError: If the type of `options` is not a dictionary object.

    Example:
        >>> with open('test.txt', 'rb') as f:
        >>>     put("test.txt", f.read(), {"addRandomSuffix": "true"}, verbose=True)
    """
    if options is None:
        options = {}

    assert type(path) == type(""), "path must be a string object"
    assert type(data) == type(b""), "data must be a bytes object"
    assert type(options) == type({}), "Options passed must be a Dictionary Object"

    # Get max concurrent uploads (default to 5)
    max_concurrent_uploads = options.get('maxConcurrentUploads', 5)
    if not isinstance(max_concurrent_uploads, int) or max_concurrent_uploads < 1:
        max_concurrent_uploads = 5

    headers = {
        "access": "public",  # Support for private is not yet there, according to Vercel docs at time of writing this code
        "authorization": f'Bearer {_get_auth_token(options)}',
        "x-api-version": _API_VERSION,
        "x-content-type": guess_mime_type(path),
        "x-cache-control-max-age": options.get('cacheControlMaxAge', _DEFAULT_CACHE_AGE),
    }

    if options.get('addRandomSuffix') in ("false", False, "0"):
        headers['x-add-random-suffix'] = "0"

    if options.get('allowOverwrite') in ("true", True, "1"):
        headers['x-allow-overwrite'] = "1"

    debug("Headers: " + str(headers))

    # Use multipart upload for large files
    if multipart:
        if verbose:
            debug("multipart is set to true, using multipart upload")
            debug(f"Using {max_concurrent_uploads} concurrent uploads")

        # Create multipart upload
        upload_info = _create_multipart_upload(path, headers, options)
        debug(f"Create multipart upload response: {upload_info}")

        if 'uploadId' not in upload_info or 'key' not in upload_info:
            raise BlobRequestError(f"Invalid response from create multipart upload: {upload_info}")

        upload_id = upload_info['uploadId']
        key = upload_info['key']

        # Split data into chunks and upload parts
        total_parts = (len(data) + _MULTIPART_CHUNK_SIZE - 1) // _MULTIPART_CHUNK_SIZE

        if verbose:
            debug(f"Uploading {total_parts} parts with {max_concurrent_uploads} concurrent uploads...")
            pbar = tqdm(total=len(data), unit='B', unit_scale=True,
                       desc=f"{_default_colors.desc}Uploading parts{NC}",
                       bar_format=f"{_default_colors.text}{{l_bar}}{NC}{_default_colors.bar}{{bar:20}}{NC}{_default_colors.text}{{r_bar}}{NC}",
                       ncols=80, ascii=" █")

        # Prepare chunks
        chunks = []
        for i in range(total_parts):
            start = i * _MULTIPART_CHUNK_SIZE
            end = min(start + _MULTIPART_CHUNK_SIZE, len(data))
            chunks.append((i + 1, data[start:end]))

        # Upload parts in parallel using ThreadPoolExecutor
        parts = [None] * total_parts  # Pre-allocate the parts list

        # Function to upload a part and update progress
        def upload_part_with_progress(args):
            part_number, chunk = args
            part_info = _upload_part(path, upload_id, key, part_number, chunk, headers, options, verbose=False)
            if verbose:
                pbar.update(len(chunk))
            return part_number - 1, part_info  # Return index and part info

        # Use ThreadPoolExecutor for parallel uploads
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent_uploads) as executor:
            # Submit all upload tasks
            future_to_part = {executor.submit(upload_part_with_progress, chunk_info): chunk_info[0] for chunk_info in chunks}

            # Process completed uploads as they finish
            for future in concurrent.futures.as_completed(future_to_part):
                try:
                    index, part_info = future.result()
                    parts[index] = part_info
                    debug(f"Part {index + 1} completed: {part_info}")
                except Exception as exc:
                    part_num = future_to_part[future]
                    print(f"Error uploading part {part_num}: {exc}")
                    raise

        if verbose:
            pbar.close()
            debug("All parts uploaded. Completing multipart upload...")

        # Complete multipart upload
        return _complete_multipart_upload(path, upload_id, key, parts, headers, options)

    # Regular upload for small files
    resp = _request_factory(
        f"{_VERCEL_BLOB_API_BASE_URL}/?pathname={path}",
        'PUT',
        headers=headers,
        data=data,
        timeout=timeout,
        verbose=verbose,
    )

    return _response_handler(resp)


def head(url: str, options: dict = None, timeout: int = 10) -> dict:
    """
    Gets the metadata of the blob object at the specified URL.

    Args:
        url (str): The URL to send the HEAD request to.
        options (dict, optional): Additional options for the request. Defaults to {}.

            -> `token` (str, optional): A string containing the token to be used for authorization. If not provided, the token will be read from the environment variable.
        timeout (int, optional): The timeout for the request. Defaults to 10.

    Returns:
        dict: The response from the HEAD request.

    Raises:
        AssertionError: If the `url` argument is not a string object.
        AssertionError: If the `options` argument is not a dictionary object.

    Example:
        >>> head("https://blobstore.public.blob.vercel-storage.com/test-folder/test.txt")
    """
    if options is None:
        options = {}

    assert type(url) == type(""), "url must be a string object"
    assert type(options) == type({}), "Options passed must be a Dictionary Object"

    headers = {
        "authorization": f'Bearer {_get_auth_token(options)}',
        "x-api-version": _API_VERSION,
    }

    debug("Headers: " + str(headers))

    resp = _request_factory(
        f"{_VERCEL_BLOB_API_BASE_URL}/?url={url}",
        'GET',
        headers=headers,
        timeout=timeout,
    )

    return _response_handler(resp)


def delete(url: any, options: dict = None, timeout: int = 10) -> dict:
    """
    Deletes the specified URL(s) from the Vercel Blob Store.

    Args:
        url (str or list): The URL(s) to be deleted. It can be a string or a list of strings.
        options (dict, optional): Additional options for the delete operation. Defaults to {}.

            -> `token` (str, optional): A string containing the token to be used for authorization. If not provided, the token will be read from the environment variable.
        timeout (int, optional): The timeout for the request. Defaults to 10.

    Returns:
        dict: The response from the delete operation.

    Raises:
        Exception: If the url parameter is not a string or a list of strings.

    Example:
        >>> delete("https://blobstore.public.blob.vercel-storage.com/test-folder/test.txt")
    """
    if options is None:
        options = {}

    assert type(options) == type({}), "Options passed must be a Dictionary Object"

    headers = {
        "authorization": f'Bearer {_get_auth_token(options)}',
        "x-api-version": _API_VERSION,
    }

    if type(url) == type("") or (type(url) == type([]) and all(isinstance(u, str) for u in url)):
        debug("Headers: " + str(headers))

        resp = _request_factory(
            f"{_VERCEL_BLOB_API_BASE_URL}/delete",
            'POST',
            headers=headers,
            json={"urls": [url] if isinstance(url, str) else url},
            timeout=timeout,
        )
        return _response_handler(resp)
    else:
        raise BlobConfigError('url must be a string or a list of strings')


def copy(blob_url: str, to_path: str, options: dict = None, timeout: int = 10, verbose: bool = False) -> dict:
    """
    Copy a blob from a source URL to a destination path inside the blob store.

    Args:
        blob_url (str): The URL of the source blob.
        to_path (str): The destination path where the blob will be copied to.
        options (dict, optional): Additional options for the copy operation. Defaults to {}.

            -> `token` (str, optional): A string containing the token to be used for authorization. If not provided, the token will be read from the environment variable.
            -> `cacheControlMaxAge` (str, optional): A string containing the cache control max age value. Defaults to "31536000".
            -> `addRandomSuffix` (str, optional): A boolean value to specify if a random suffix should be added to the path. Defaults to "false" for copy operation.
        timeout (int, optional): The timeout for the request. Defaults to 10.
        verbose (bool, optional): Whether to show detailed information during copy operation. Defaults to False.

    Returns:
        dict: The response from the copy operation.

    Raises:
        AssertionError: If the blob_url parameter is not a string object.
        AssertionError: If the to_path parameter is not a string object.
        AssertionError: If the options parameter is not a dictionary object.

    Example:
        >>> copy("https://blobstore.public.blob.vercel-storage.com/test-folder/test.txt", "copy-test/test.txt", {"addRandomSuffix": "false"}, verbose=True)
    """
    if options is None:
        options = {}

    assert type(blob_url) == type(""), "blob_url must be a string object"
    assert type(to_path) == type(""), "to_path must be a string object"
    assert type(options) == type({}), "Options passed must be a Dictionary Object"

    headers = {
        "access": "public",
        "authorization": f'Bearer {_get_auth_token(options)}',
        "x-api-version": _API_VERSION,
        "x-content-type": guess_mime_type(blob_url),
        "x-cache-control-max-age": options.get('cacheControlMaxAge', _DEFAULT_CACHE_AGE),
    }

    if options.get('addRandomSuffix') != None:
        headers['x-add-random-suffix'] = "1"

    debug("Headers: " + str(headers))

    to_path_encoded = requests.utils.quote(to_path)
    resp = _request_factory(
        f"{_VERCEL_BLOB_API_BASE_URL}/?pathname={to_path_encoded}",
        'PUT',
        headers=headers,
        params={"fromUrl": blob_url},
        timeout=timeout,
        verbose=verbose,
    )

    return _response_handler(resp)


def download_file(url: str, path: str = '', options: dict = None, timeout: int = 10, verbose: bool = False):
    """
    Downloads the blob object at the specified URL, and saves it to the specified path.

    Args:
        url (str): The URL of the blob object to download.
        path (str, optional): The path where the downloaded file will be saved. If not provided, the file will be saved in the current working directory.
        options (dict, optional): Additional options for the download operation. Defaults to {}.

            -> `token` (str, optional): A string containing the token to be used for authorization. If not provided, the token will be read from the environment variable.
        timeout (int, optional): The timeout for the request. Defaults to 10.
        verbose (bool, optional): Whether to show detailed information during download. Defaults to False.

    Returns:
        bytes: The data of the blob object.

    Raises:
        AssertionError: If the url parameter is not a string object.
        Exception: If an error occurs during the download process.

    Example:
        >>> download_file("https://blobstore.public.blob.vercel-storage.com/test-folder/test.txt", "path/to/save/", options={"token": "my_token"}, verbose=True)
    """
    if options is None:
        options = {}

    assert type(url) == type(""), "url must be a string object"
    assert type(path) == type(""), "path must be a string object"
    assert type(options) == type({}), "Options passed must be a Dictionary Object"

    script_path = _get_script_path()
    sanitized_path = path.lstrip('/')
    path_to_save = script_path + sanitized_path
    if path_to_save != script_path:
        assert path.endswith('/'), "path must be a valid directory path, ending with '/'"
        assert os.path.exists(path_to_save), "path must be a valid directory path"

    debug(f"Downloading file from {url} to {path_to_save}")

    try:
        resp = _request_factory(
            f"{url}?download=1",
            'GET',
            timeout=timeout,
            verbose=verbose,
        ).content
        try:
            with open(f"{path_to_save}{url.split('/')[-1]}", 'wb') as f:
                f.write(resp)
        except FileNotFoundError as e:
            debug(f"An error occurred. Please try again. Error: {e}")
            raise BlobFileError("The directory must exist before downloading the file. Please create the directory and try again.") from e
    except Exception as e:
        debug(f"An error occurred. Please try again. Error: {e}")
        raise BlobRequestError("An error occurred. Please try again.") from e


def set_progress_bar_colours(desc=None, bar=None, text=None):
    """
    Set the colors for all progress bars.
    
    Args:
        desc (str, optional): Color code for description (hex or ANSI)
        bar (str, optional): Color code for progress bar (hex or ANSI)
        text (str, optional): Color code for progress text (hex or ANSI)
    """
    try:
        _default_colors.set_colors(desc, bar, text)
    except InvalidColorError as e:
        print(f"{RED}Warning: Invalid color configuration: {e}{NC}")
        print(f"{RED}Using default colors instead{NC}")
