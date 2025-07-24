#!/usr/bin/env python

import pathlib
import logging
import subprocess

import click

logger = logging.getLogger(__name__)


def index_for_all(dest_path: pathlib.Path):
    links = []
    for index_path in dest_path.glob("*/*/index.html"):
        human_name = "/".join(index_path.parent.parts[-2:])
        links.append(f"<li><a href='{index_path.relative_to(dest_path).as_posix()}'>{human_name}</a></li>")
    links = "\n".join(links)

    doc = f"""<!doctype html><html><head><title>Benchmark index</title></head>
    <body><ul>{links}</ul></body></html>"""

    with open(dest_path / "index.html", "w") as f:
        f.write(doc)


def index_for_repo(
    dest_path: pathlib.Path,
    indices: list[pathlib.Path],
):
    links = []

    for index_path in indices:
        human_name = "/".join(index_path.parent.parts[-3:])
        links.append(f"<li><a href='{index_path.relative_to(dest_path).as_posix()}'>{human_name}</a></li>")

    links = "\n".join(links)

    doc = f"""<!doctype html><html><head><title>Benchmark index</title></head>
    <body><ul>{links}</ul></body></html>"""

    with open(dest_path / "index.html", "w") as f:
        f.write(doc)


def make_html(folder: pathlib.Path, repo: str, benchmark_name: str):
    svgs = list(sorted(folder.glob("*.svg")))
    imgs = "\n".join(
        f"<p>Benchmark: {img.name}<br/><img src='{img.name}'/></p>"
        for img in svgs
    )

    doc = f"""<!doctype html><html><head><title>{repo}: {benchmark_name}</title></head>
    <body>{imgs}</body></html>"""

    dest_path = folder / "index.html"
    with open(dest_path, "w") as f:
        f.write(doc)
    return dest_path


@click.command()
@click.option("--src-folder", type=pathlib.Path, required=True)
@click.option("--dest-folder", type=pathlib.Path, required=True)
@click.option("--repo", type=str, required=True)
def main(
    src_folder: pathlib.Path,
    dest_folder: pathlib.Path,
    repo: str,
):
    """
    Render all benchmark results from one repo.

    src_folder should point to the top level of directories that contain the
    json benchmark results for one repository, for example
    ./collected/LiberTEM/cb-testing/, there should be a sub directory for every
    named "benchmark group" (i.e. juwels_cpu, juwels_gpu, ...)
    """
    logging.basicConfig(level=logging.INFO)
    indices = []
    for bench_path in (src_folder / repo).glob("*"):
        if not bench_path.is_dir():
            logging.warning(f"spurious file {bench_path}, ignoring")
            continue

        svgs_folder = dest_folder / repo / bench_path.name

        args = [
            "pytest-benchmark",
            "compare",
        ]
        args += [p.as_posix() for p in bench_path.glob("*.json")]
        args += [
            f"--histogram={svgs_folder.as_posix()}/{bench_path.name}",
            "--group-by=fullname",
            "--sort=name",
        ]
        logger.info(f"running {' '.join(args)}")
        subprocess.run(args, check=True)
        indices.append(make_html(svgs_folder, benchmark_name=bench_path.name, repo=repo))

    index_for_repo(dest_path=dest_folder / repo, indices=indices)
    index_for_all(dest_path=dest_folder)


if __name__ == "__main__":
    main()