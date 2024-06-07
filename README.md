# vercel_blob

A Python wrapper for the Vercel Blob Storage API

## Installation


```bash
pip3 install vercel_blob
```

## Getting Started

### Python Version

This package (vercel_blob) was written using Python 3 in mind, and Python 2 will not work properly.

### Set Environment Variable for Authorization

```bash
export BLOB_READ_WRITE_TOKEN="superssecretkey"
```

### Add vercel_blob to your code

```python
import vercel_blob
#or
import vercel_blob.blob_store
# or if you want to use an alias
import vercel_blob.blob_store as vb_store
```

## Using vercel_blob

Currently only supports the basic list, put, delete and head(get file metadata) operations. Here's a quick overview:

### List all files in the Blob Storage
The list method will return a list of all files in the blob storage. You can pass 'limit' to limit the returned number of blobs.
```python
def list_all_blobs():
    blobs = vercel_blob.blob_store.list({
        'limit': '5',
    })
```

list() returns a JSON object in the following format:

```javascript
blobs: {
  size: `number`;
  uploadedAt: `Date`;
  pathname: `string`;
  url: `string`;
  downloadUrl: `string`
}[]
cursor?: `string`;
hasMore: `boolean`;
folders?: `string[]`
```

For a long list of blob objects (the default list limit is 1000), you can use the cursor and hasMore parameters to paginate through the results as shown in the example below:

```python
blobs = vercel_blob.blob_store.list({
        'limit': '4',
        'cursor': cursor,
    })
```

### Upload File / Blob to the Storage

```

```

### Delete a blob or a list of blobs from the Blob Storage
```

```

### Get blob metadata
```

```