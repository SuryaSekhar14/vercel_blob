# I have no idea how to write pytest modules, please bear with me

import dotenv
import vercel_blob

dotenv.load_dotenv()


def list_all_blobs(cursor=None):
    blob_list = vercel_blob.list({
        'limit': '4',
        'cursor': cursor,
    })

    return blob_list


def upload_a_blob(file_path):
    with open(file_path, 'rb') as f:
        resp = vercel_blob.put('test-custom-testing-script.txt', f.read(), {
                "addRandomSuffix": "false",
            })
        return resp


def get_blob_metadata(url):
    resp = vercel_blob.head(url)
    return resp


def delete_a_list_of_blobs(url):
    resp = vercel_blob.delete([
            url
        ])
    return resp


def copy_a_blob(url):
    resp = vercel_blob.copy(url, "copy-test/test.txt", {
        "addRandomSuffix": "true"
    })
    return resp


def download_a_blob(url):
    resp = vercel_blob.download_file(url)
    return resp


if __name__ == '__main__':

    print("Testing all functions")

    print("\nTesting put()...")
    blob_url = upload_a_blob('requirements.txt').get("url")
    print(blob_url)

    print("\nTesting list()...")
    print(list_all_blobs())

    print("\nTesting head()...")
    print(get_blob_metadata(blob_url))

    print("\nTesting copy()...")
    print(copy_a_blob(blob_url))

    print("\nTesting download()...")
    print(download_a_blob(blob_url))

    print("\nDeleting downloaded file from local filesystem...")
    import os
    os.remove('test-custom-testing-script.txt')

    print("\nTesting delete()...")
    print(delete_a_list_of_blobs(blob_url))

    print("Confirming delete()...")

    try: 
        print(get_blob_metadata(blob_url))
        print("Delete failed")
    except Exception as e:
        print("Delete successful")