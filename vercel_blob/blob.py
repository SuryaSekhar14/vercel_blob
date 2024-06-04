import requests
import os

_VERCEL_BLOB_API_BASE_URL = 'https://blob.vercel-storage.com'
_API_VERSION = '7'
_PAGINATED_LIST_SIZE = 1000
_DEFAULT_CACHE_AGE = '31536000'
_DEBUG = os.environ.get('DEBUG', False)



def _get_auth_token_from_env():
    token = os.environ.get('BLOB_READ_WRITE_TOKEN')

    if not token:
        raise Exception('BLOB_READ_WRITE_TOKEN environment variable not set')
    
    return token

def _response_handler(resp: requests.Response) -> dict:
    if resp.status_code == 200:
        return resp.json()
    else:
        raise Exception(f"An error occoured: {resp.json()}")


def list(opts: dict = {}) -> dict:
    headers = {
        "authorization": f'Bearer {opts.get("token", _get_auth_token_from_env())}',
        "limit": opts.get('limit', str(_PAGINATED_LIST_SIZE)),
    }

    if opts.get('prefix'):
        headers['prefix'] = opts['prefix']
    if opts.get('cursor'):
        headers['cursor'] = opts['cursor']
    if opts.get('mode'):
        headers['mode'] = opts['mode']

    if _DEBUG == True: print(headers)
    resp = requests.get(
        f"{_VERCEL_BLOB_API_BASE_URL}",
        headers=headers,
    )

    return _response_handler(resp)


def put(path: str, data: bytes, opts: dict = {}) -> dict:
    headers = {
        "access": "public",  # Support for private is not yet there, according to Vercel docs at time of writing this code
        "authorization": f'Bearer {opts.get("token", _get_auth_token_from_env())}',
        "x-api-version": _API_VERSION,
        "Content-Type": "application/octet-stream",
        "cacheControlMaxAge": opts.get('cacheControlMaxAge', _DEFAULT_CACHE_AGE),
    }

    if opts.get('addRandomSuffix') == "false":
        headers['x-add-random-suffix'] = "false"

    if _DEBUG == True: print(headers)
    resp = requests.put(
        f"{_VERCEL_BLOB_API_BASE_URL}/{path}",
        data=data,
        headers=headers,
    )

    return _response_handler(resp)


def head(url: str, opts: dict = {}) -> dict:
    headers = {
        "authorization": f'Bearer {opts.get("token", _get_auth_token_from_env())}',
        "x-api-version": _API_VERSION,
    }

    if _DEBUG == True: print(headers)
    resp = requests.get(
        f"{_VERCEL_BLOB_API_BASE_URL}/?url={url}",
        headers=headers,
    )

    return _response_handler(resp)


def delete(url: any, opts: dict = {}) -> dict:
    headers = {
        "authorization": f'Bearer {opts.get("token", _get_auth_token_from_env())}',
        "x-api-version": _API_VERSION,
    }

    if type(url) == type("") or type(url) == type([]):
        if _DEBUG == True: print(headers)
        resp = requests.post(
            f"{_VERCEL_BLOB_API_BASE_URL}/delete",
            json={"urls": [url] if isinstance(url, str) else url},
            headers=headers,
        )
        return _response_handler(resp)
    else:
        raise Exception('url must be a string or a list of strings')

    

