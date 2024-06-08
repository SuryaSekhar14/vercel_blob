# I have no idea how to write pytest modules, please bear with me

import vercel_blob
import dotenv


dotenv.load_dotenv()


def list_all_blobs(cursor=None):
    blob_list = vercel_blob.list({
        'limit': '4',
        'cursor': cursor,
    })

    return blob_list


def upload_a_blob(file_path):
    with open(file_path, 'rb') as f:
        resp = vercel_blob.put('test.txt', f.read(), {
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


if __name__ == '__main__':

    print("Testing all functions")

    print("Testing put()...")
    blob_url = upload_a_blob('requirements.txt').get("url")
    print(blob_url)

    print("Testing list()...")
    print(list_all_blobs())

    print("Testing head()...")
    print(get_blob_metadata(blob_url))

    print("Testing copy()...")
    print(copy_a_blob(blob_url))

    print("Testing delete()...")
    print(delete_a_list_of_blobs(blob_url))

    print("Confirming delete()...")

    try: 
        print(get_blob_metadata(blob_url))
        print("Delete failed")
    except Exception as e:
        print("Delete successful")