#!/usr/bin/env python3
import os
import re
from pathlib import Path
import typing as T
import sys


def get_files(path: Path, ext: str, recurse: bool = False) -> T.Iterable[Path]:
    """
    yield files in path with suffix ext. Optionally, recurse directories.
    """

    path = Path(path).expanduser().resolve()

    if path.is_dir():
        for p in path.iterdir():
            if p.is_file() and p.suffix == ext:
                yield p
            elif p.is_dir():
                if recurse:
                    yield from get_files(p, ext, recurse)
    elif path.is_file():
        yield path
    else:
        raise FileNotFoundError(path)


def process_internal_link_match(mobj):
    old_url = mobj.group(1)
    new_url = old_url
    old_link = mobj.group(0)
    sub = False

    if old_link == "#":
        return old_link

    # Convert to Wiki.js internal link syntax.
    # [link](/Folder/File.md)

    if not old_url.startswith('/'):
        sub = True
        new_url = '/' + new_url

    if old_url.endswith('.md'):
        sub = True
        new_url = new_url[:-3]

    if sub:
        new_link = re.sub(re.escape(old_url), new_url, old_link)
        return new_link
    return old_link

def remove_block_ref_hashes(fp: str):
    regex = r"(.+)( \^[=a-zA-Z0-9]+)"
    path = Path(fp).resolve().expanduser()
    files = get_files(path, ".md", True)

    def remove_block_ref(mobj):
        return mobj.group(1)

    for fn in files:
        text = fn.read_text(errors="ignore")
        new_text = re.sub(regex, remove_block_ref, text)
        fn.write_text(new_text)

def get_blockref_text(fp: str, ref_hash: str) -> str:
    with open(fp) as fobj:
        text = fobj.read()
        # Finds the block with the specified hash
        return re.search(r"(.+)( \^" + ref_hash + ")", text).group(1).rstrip()

def process_blockref_match(mobj, vault_root):
    file = mobj.group(1)
    ref_hash = mobj.group(2)
    new_text = get_blockref_text(os.path.join(vault_root, file), ref_hash)
    return new_text

def update_local_links(fp: str, ext: str):
    regex = r"\]\(([=a-zA-Z0-9\_\/\?\&\%\+\#\.\-]+)\)"
    path = Path(fp).resolve().expanduser()

    files = get_files(path, ext, True)

    for fn in files:
        text = fn.read_text(errors="ignore")
        new_text = re.sub(regex, process_internal_link_match, text)
        fn.write_text(new_text)

def update_block_refs(fp: str, ext: str):
    regex = r"\!\[.+\]\(([=a-zA-Z0-9\_\/\?\&\%\+\#\.\-]+)\#\^([=a-zA-Z0-9]+)\)"
    path = Path(fp).resolve().expanduser()

    files = get_files(path, ext, True)
    for fn in files:
        text = fn.read_text(errors="ignore")
        new_text = re.sub(regex, lambda mobj: process_blockref_match(mobj, fp), text)
        fn.write_text(new_text)


if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        print(args[0] + " requires the obsidian vault root dir as an argument.")
        sys.exit(1)

    directory = args[1]
    if not os.path.isdir(directory):
        print(args[1] + " is either not a directory or does not exist.")
        sys.exit(1)

    print("Recursively editing markdown files in directory " + directory)
    update_local_links(directory, ".md")
    update_block_refs(directory, ".md")
    remove_block_ref_hashes(directory)
