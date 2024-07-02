from . import blob_store

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
        
    return blob_store.list(options)


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

    return blob_store.put(path, data, options)


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
    
    return blob_store.head(url, options)


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

    return blob_store.delete(url, options)


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

    return blob_store.copy(blob_url, to_path, options)


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

    return blob_store.download_file(url, path, options)














