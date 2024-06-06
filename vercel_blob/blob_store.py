import requests
import os
import time


_VERCEL_BLOB_API_BASE_URL = 'https://blob.vercel-storage.com'
_API_VERSION = '7'
_PAGINATED_LIST_SIZE = 1000
_DEFAULT_CACHE_AGE = '31536000'
_MAX_RETRY_REQUEST_RETRIES = 3
_DEBUG = os.environ.get('DEBUG', False)


def _get_auth_token_from_env() -> str:
    token = os.environ.get('BLOB_READ_WRITE_TOKEN')

    if not token:
        raise Exception('BLOB_READ_WRITE_TOKEN environment variable not set')

    return token


def _request_factory(url: str, method: str, backoff_factor: int = 0.5, status_forcelist: list = [502, 503, 504], timeout: int = 10, **kwargs) -> requests.Response:
    for attempt in range(1, _MAX_RETRY_REQUEST_RETRIES + 1):
        try:
            response = requests.request(method, url, timeout=timeout, **kwargs)
            if response.status_code not in status_forcelist:
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


def list(opts: dict = {}) -> dict:
    try:
        _tkn = opts['token']
    except KeyError:
        _tkn = _get_auth_token_from_env()

    headers = {
        "authorization": f'Bearer {_tkn}',
    }

    params = {
        "limit": opts.get('limit', str(_PAGINATED_LIST_SIZE)),
    }

    if opts.get('prefix'):
        params['prefix'] = opts['prefix']
    if opts.get('cursor'):
        params['cursor'] = opts['cursor']
    if opts.get('mode'):
        params['mode'] = opts['mode']

    if _DEBUG: print(headers)
    resp = _request_factory(
        f"{_VERCEL_BLOB_API_BASE_URL}",
        'GET',
        params=params,
        headers=headers,
    )

    return _response_handler(resp)


def put(path: str, data: bytes, opts: dict = {}) -> dict:
    try:
        _tkn = opts['token']
    except KeyError:
        _tkn = _get_auth_token_from_env()

    headers = {
        "access": "public",  # Support for private is not yet there, according to Vercel docs at time of writing this code
        "authorization": f'Bearer {_tkn}',
        "x-api-version": _API_VERSION,
        "Content-Type": "application/octet-stream",
        "cacheControlMaxAge": opts.get('cacheControlMaxAge', _DEFAULT_CACHE_AGE),
    }

    if opts.get('addRandomSuffix') == "false":
        headers['x-add-random-suffix'] = "false"

    if _DEBUG: print(headers)
    resp = _request_factory(
        f"{_VERCEL_BLOB_API_BASE_URL}/{path}",
        'PUT',
        headers=headers,
        data=data,
    )

    return _response_handler(resp)


def head(url: str, opts: dict = {}) -> dict:
    try:
        _tkn = opts['token']
    except KeyError:
        _tkn = _get_auth_token_from_env()

    headers = {
        "authorization": f'Bearer {_tkn}',
        "x-api-version": _API_VERSION,
    }

    if _DEBUG: print(headers)
    resp = _request_factory(
        f"{_VERCEL_BLOB_API_BASE_URL}/?url={url}",
        'GET',
        headers=headers,
    )

    return _response_handler(resp)


def delete(url: any, opts: dict = {}) -> dict:
    try:
        _tkn = opts['token']
    except KeyError:
        _tkn = _get_auth_token_from_env()

    headers = {
        "authorization": f'Bearer {_tkn}',
        "x-api-version": _API_VERSION,
    }

    if type(url) == type("") or type(url) == type([]):
        if _DEBUG: print(headers)
        resp = _request_factory(
            f"{_VERCEL_BLOB_API_BASE_URL}/delete",
            'POST',
            headers=headers,
            json={"urls": [url] if isinstance(url, str) else url},
        )
        return _response_handler(resp)
    else:
        raise Exception('url must be a string or a list of strings')

    

