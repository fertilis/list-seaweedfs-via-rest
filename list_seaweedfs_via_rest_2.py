from __future__ import annotations
import collections as col
import urllib.parse
import argparse
import requests
import typing
import os

from dataclasses import dataclass


def list_seaweedfs_objects(url: str, data_dir: str) -> typing.Iterable[FsItem]:
    url2 = urllib.parse.urlparse(url)
    path = url2.path
    tree_store_path = f"{data_dir}/{path.replace('/', '_')}.csv"
    root_fs_item = FsItem(url, 1, 0)
    if os.path.exists(tree_store_path):
        with open(tree_store_path) as f:
            nodes = [Node.from_tsv(line) for line in f.readlines()]
    else:
        nodes = []
    queue = col.deque(nodes)
    with open(tree_store_path, "a") as f:
        while queue:
            node = queue.popleft()
            if node.children:
                queue.extend(node.children)
            else:
                if node.fs_item.is_dir:
                    children: list[FsItem] = list_url(node.fs_item.url)
                    for child in children:
                        f.write(f"{child.to_tsv()}\n")
                    node.children = [Node(node, child) for child in children]
                    queue.extend(node.children)
                else:
                    yield node.fs_item


class FsItem(typing.NamedTuple):
    url: str
    is_dir: int
    file_size: int
    
    def is_child(self, parent: FsItem) -> bool:
        self_slash_count = self.url.count("/")
        parent_slash_count = parent.url.count("/")
        return (
            self.url.startswith(parent.url) 
            and (
                (self_slash_count == parent_slash_count + 1 and self.is_dir and parent.is_dir)
                or (self_slash_count == parent_slash_count and not self.is_dir and parent.is_dir)
            )
        )
    
    def to_tsv(self) -> str:
        return f"{self.url}\t{self.is_dir}\t{self.file_size}"
    
    @classmethod
    def from_tsv(cls, csv: str) -> FsItem:
        url, is_dir, file_size = csv.split("\t")
        return cls(url, int(is_dir), int(file_size))


@dataclass
class Node:
    parent_id: int
    fs_item: FsItem
    children: list[Node] = []
    
    def __init__(self, parent_id: int, fs_item: FsItem):
        self.parent_id = parent_id
        self.fs_item = fs_item
        self.children = []
        
    def to_tsv(self) -> str:
        return f"{self.parent_id}\t{self.fs_item.to_tsv()}"
    
    @classmethod
    def from_tsv(cls, csv: str) -> Node:
        csv = csv.strip()
        parent_id, fs_item = csv.split("\t", 1)
        return cls(int(parent_id), FsItem.from_tsv(fs_item))
        
    
    


class FsItem(typing.NamedTuple):
    url: str
    is_dir: int
    file_size: int
    
    def is_child(self, parent: FsItem) -> bool:
        self_slash_count = self.url.count("/")
        parent_slash_count = parent.url.count("/")
        return (
            self.url.startswith(parent.url) 
            and (
                (self_slash_count == parent_slash_count + 1 and self.is_dir and parent.is_dir)
                or (self_slash_count == parent_slash_count and not self.is_dir and parent.is_dir)
            )
        )
    
    def to_tsv(self) -> str:
        return f"{self.url}\t{self.is_dir}\t{self.file_size}"
    
    @classmethod
    def from_tsv(cls, csv: str) -> FsItem:
        url, is_dir, file_size = csv.split("\t")
        return cls(url, int(is_dir), int(file_size))

    
def list_url(url: str) -> list[FsItem]:
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
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str)
    parser.add_argument("data_dir", type=str)
    args = parser.parse_args()
    for fs_item in list_seaweedfs_objects(args.url, args.data_dir):
        print(fs_item.url)
