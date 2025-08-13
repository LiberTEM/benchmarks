#!/usr/bin/env python
"""
Subsample raw data points of all benchmarks; limit to a given number of points

Why: pytest-benchmark can't be controlled in a way that limits the number of
rounds to run, but we do need the raw time data to compare runs.

Instead of keeping 100k's of points, maybe a few thousand are enough?
"""

import io
import sys
import json

import click
import numpy as np


def update_single_bench(bench_data, num_max_points):
    if len(bench_data["stats"]["data"]) <= num_max_points:
        return bench_data
    rng = np.random.default_rng()

    bench_data["stats"]["data"] = bench_data["stats"]["data"][-num_max_points:]


def update_benches(bench_data, num_max_points):
    for bench in bench_data["benchmarks"]:
        update_single_bench(bench, num_max_points)


@click.command
@click.argument("num_max_points", type=int)
def main(num_max_points):
    """
    Reduce number of points in a benchmark result by selecting the last NUM_MAX_POINTS.
    Reads json from stdin, writes json to stdout.
    """
    input_data = sys.stdin.read()
    bench_dict = json.loads(input_data)
    update_benches(bench_dict, num_max_points=num_max_points)
    print(json.dumps(bench_dict, indent=2))


if __name__ == "__main__":
    main()
