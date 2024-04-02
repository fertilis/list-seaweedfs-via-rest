from __future__ import annotations
import urllib.parse
import argparse
import requests
import typing
import os


class Node:
    __slots__ = ["id", "parent_id", "visited", "offset", "payload"]

    def __init__(
        self, id: int, parent_id: int, visited: int, offset: int, payload: FsItem
    ):
        self.id = id
        self.parent_id = parent_id
        self.visited = visited
        self.offset = offset
        self.payload = payload

    @classmethod
    def from_tsv(cls, text: str) -> Node:
        id, parent_id, visited, offset, url, is_dir, file_size = text.strip().split(
            "\t"
        )
        id = int(id)
        parent_id = int(parent_id)
        visited = int(visited)
        offset = int(offset)
        payload = FsItem(url, int(is_dir), int(file_size))
        return cls(id, parent_id, visited, offset, payload)

    def to_tsv(self) -> str:
        return (
            f"{self.id}\t{self.parent_id}\t{self.visited}\t{self.offset}\t{self.payload.url}"
            f"\t{self.payload.is_dir}\t{self.payload.file_size}"
        )

    def __repr__(self) -> str:
        return self.to_tsv()


def dfs_list(url: str, data_dir: str = "io", verbose: bool = False) -> list[Node]:
    """
    1. Go to last node
    2. If visited, go to sibling (node to the left) or parent if no sibling
    3. If not visited:
        3.1 list url
        3.2 create children
        3.3 write children to the end of file
        3.4 append children to the list
        3.5. update visited status of the node in the file
    4. Repeat 1-3 until attempting to go to root's parent
    """
    store_path = f"{data_dir}/{urllib.parse.urlparse(url).path.replace('/', '_')}.csv"
    if os.path.exists(store_path):
        with open(store_path) as f:
            text = f.read()
        nodes = [Node.from_tsv(line) for line in text.splitlines()]
    else:
        nodes = []
        os.makedirs(data_dir, exist_ok=True)

    if not nodes:
        with open(store_path, "w") as f:
            pass

    with open(store_path, "r+") as f:
        if not nodes:
            root = Node(
                id=0,
                parent_id=-1,
                visited=0,
                offset=f.tell(),
                payload=FsItem(url, 1, 0),
            )
            nodes = [root]
            line = root.to_tsv()
            f.write(f"{line}\n")
            if verbose:
                print(root.to_tsv())
        i = len(nodes) - 1
        # fmt: off
#        import pdb; pdb.set_trace()
        while i >= 0:
            node = nodes[i]
            if node.visited:
                if verbose:
                    print(node.to_tsv())
                i -= 1
                nonvisited_sibling_found = False
                while i > 0 and nodes[i].parent_id == node.parent_id:
                    sibling = nodes[i]
                    if sibling.visited:
                        i -= 1
                        if verbose:
                            print(sibling.to_tsv())
                    else:
                        nonvisited_sibling_found = True
                        break
                if not nonvisited_sibling_found:
                    i = node.parent_id
            else:
                f.seek(0, os.SEEK_END)
                for j, fs_item in enumerate(list_url(node.payload.url)):
                    child = Node(id=len(nodes) + j, parent_id=i, visited=0, offset=f.tell(), payload=fs_item)
                    f.write(f"{child.to_tsv()}\n")
                    nodes.append(child)
                    if verbose:
                        print(child.to_tsv())
                node.visited = 1
                f.seek(node.offset)
                f.write(f"{node.to_tsv()}\n")
                i = len(nodes) - 1


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
        if data["Entries"] is None:
            return []
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


def load_fs_items(url: str, data_dir: str = "io") -> list[FsItem]:
    store_path = f"{data_dir}/{urllib.parse.urlparse(url).path.replace('/', '_')}.csv"
    if not os.path.exists(store_path):
        return []
    with open(store_path) as f:
        text = f.read()
    return [Node.from_tsv(line).fs_item for line in text.splitlines()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str)
    parser.add_argument("--data-dir", type=str, default="io")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    dfs_list(args.url, args.data_dir, args.verbose)
