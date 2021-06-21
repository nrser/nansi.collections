#!/usr/bin/env python

from pathlib import Path
from subprocess import run
import sys
import shutil

REPO_ROOT = Path(
    run(
        ["git", "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        encoding="utf-8",
    ).stdout.strip()
)

GALAXY_YAML_PATH = REPO_ROOT / "galaxy.yml"
LICENSE_PATH = REPO_ROOT / "LICENSE"
META_PATH = REPO_ROOT / "meta"

GALAXY_YAML = GALAXY_YAML_PATH.read_text(encoding="utf-8")

def iter_collections():
    for file_path in REPO_ROOT.iterdir():
        if (
            file_path != (REPO_ROOT / "dev") and (
                (file_path / "roles").exists() or
                (file_path / "plugins").exists()
            )
        ):
            yield file_path

def write_galaxy_yml(collection_path: Path):
    contents = GALAXY_YAML.replace(
        "namespace: nrser",
        "namespace: nansi",
    ).replace(
        "name: nansi",
        f"name: {collection_path.name}",
    )
    (collection_path / "galaxy.yml").write_text(
        contents,
        encoding="utf-8",
    )

def copy(collection_path: Path, file_name: str):
    src = REPO_ROOT / file_name
    dest = collection_path / file_name
    if src.is_dir():
        shutil.copytree(
            src,
            dest,
            dirs_exist_ok=True,
        )
    else:
        shutil.copy(src, dest)

def main(args):
    for collection_path in iter_collections():
        write_galaxy_yml(collection_path)
        copy(collection_path, "LICENSE")
        copy(collection_path, "meta")

if __name__ == '__main__':
    main(sys.argv[1:])
