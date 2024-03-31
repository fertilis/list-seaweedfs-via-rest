from __future__ import annotations
import urllib.parse
import requests
import typing


class FsItem(typing.NamedTuple):
    url: str
    is_dir: int
    file_size: int

    def is_child(self, parent: FsItem) -> bool:
        self_slash_count = self.url.count("/")
        parent_slash_count = parent.url.count("/")
        return self.url.startswith(parent.url) and (
            (
                self_slash_count == parent_slash_count + 1
                and self.is_dir
                and parent.is_dir
            )
            or (
                self_slash_count == parent_slash_count
                and not self.is_dir
                and parent.is_dir
            )
        )


def list_url(url: str) -> list[FsItem]:
    if not url.endswith("/"):
        return []
    url2 = urllib.parse.urlparse(url)
    url_prefix = f"{url2.scheme}://{url2.netloc}"
    response = requests.get(url, headers={"Accept": "application/json"})
    if response.status_code == 200:
        data = response.json()
        items = []
        for raw_item in data["Entries"]:
            item_url = f"{url_prefix}{raw_item['FullPath']}"
            is_dir = int("chunks" not in raw_item)
            if is_dir and not item_url.endswith("/"):
                item_url += "/"
                size = 0
            else:
                size = sum(chunk["size"] for chunk in raw_item["chunks"])
            item = FsItem(item_url, is_dir, size)
            items.append(item)
        return items
    else:
        raise Exception(f"Failed to list {url}: {response.status_code}")
