# Listing SeaweedFS objects with REST API

## Motivation

I've encountered a situation when listing by prefix via s3 API is broken.
I tried both boto3 and minio client.

## Implementation

While listing saves file system tree in depth-first order to a file


## Example

```bash
./list.sh https://old-hfs.skns.dev/buckets/algoseek/algoseek/future_spreads/quotes/2023/08/11/ZS/ZSX5/ --data-dir io --verbose
```


## To get a list of objects (url, file size)

```python
from dfs_list import FsItem, load_fs_items

fs_items: list[FsItem] = load_fs_items("https://old-hfs.skns.dev/buckets/algoseek/algoseek/future_spreads/", "io")
```

