# Listing SeaweedFS objects with REST API

## Motivation

I've encountered a situation when listing by prefix via s3 API is broken.
I tried both boto3 and minio client.

## Example

```bash
python3 list_seaweedfs_via_rest.py https://old-hfs.skns.dev/buckets/algoseek/algoseek/future_spreads/ io
```

This will create a file in `io/` directory containing object tree in breadth-first order.

Second run of the script will just build the tree from the file.


```python
from list_seaweedfs_via_rest import list_seaweedfs_objects, FsItem

items = list(list_seaweedfs_objects("https://old-hfs.skns.dev/buckets/algoseek/algoseek/future_spreads/", "io"))
```

Or urls can be just read from file like


```python
from list_seaweedfs_via_rest import read_urls_from_file, FsItem

items = list(read_urls_from_file("https://old-hfs.skns.dev/buckets/algoseek/algoseek/future_spreads/", "io"))
```

