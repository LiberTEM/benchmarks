#!/usr/bin/env python

import re
import os
import zipfile
import pathlib
import logging

import click

logger = logging.getLogger(__name__)


def _make_new_path(
    repo_name: str,
    benchmark_name: str,
    base_folder: pathlib.Path,
) -> pathlib.Path:
    """
    Make a filename for saving 
    The file/directory structure should be as follows:

    <base_folder>/<repo_name>/<benchmark_name>/<NNNNN>.json

    where N is a digit.
    """
    dest_folder = base_folder / repo_name / benchmark_name
    existing_files = dest_folder.glob("*.json")
    pattern = re.compile(r"^(?P<index>[0-9]+)\.json$")
    indices = []
    for path in existing_files:
        m = pattern.match(os.path.basename(path))
        if m is None:
            logger.warning(f"file {path} doesn't match the expected pattern")
            continue
        index = int(m.groupdict()['index'])
        indices.append(index)
    if len(indices) == 0:
        new_index = 1
    else:
        new_index = max(indices) + 1
    new_path = dest_folder / f'{new_index:05d}.json'
    return new_path


@click.command()
@click.argument("zip_paths", nargs=-1, type=pathlib.Path)
@click.option("--inner-filename", default="bench-results.json", type=str)
@click.option("--repo-name", type=str)
@click.option("--dest-folder", type=pathlib.Path)
def main(
    zip_paths: list[pathlib.Path],
    inner_filename: str,
    repo_name: str,
    dest_folder: pathlib.Path,
):
    logging.basicConfig(level=logging.INFO)
    for zip_path in zip_paths:
        benchmark_name = os.path.splitext(zip_path.name)[0]
        with zipfile.ZipFile(zip_path) as zf:
            bench_bytes = zf.read(inner_filename)
            new_path = _make_new_path(repo_name, benchmark_name, dest_folder)
            new_path.parent.mkdir(exist_ok=True, parents=True)
            logging.info(f"collecting {zip_path} into {new_path}")
            with open(new_path, "wb") as f:
                f.write(bench_bytes)


if __name__ == "__main__":
    main()