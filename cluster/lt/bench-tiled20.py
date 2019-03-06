import os
import time

import click

for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[k] = '1'

from libertem.api import Context
from libertem.executor.inline import InlineJobExecutor
from libertem.executor.dask import DaskJobExecutor
from libertem.io.dataset.raw_direct import DirectRawFileDataSet
from libertem.io.dataset.raw import RawFileDataSet
import numpy as np
import psutil
import json


class BenchmarkDaskExecutor(DaskJobExecutor):
    def __init__(self, node_limit=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._node_limit = node_limit

    def get_available_workers(self):
        """
        returns list of dict with keys 'name' and 'host'
        """
        workers = super().get_available_workers()
        if self._node_limit is None:
            return workers
        hosts = list(sorted(set([w['host'] for w in workers])))
        hosts_to_use = {*hosts[:self._node_limit]}

        return [
            w
            for w in workers
            if w['host'] in hosts_to_use
        ]


def _preload():
    import libertem.preload  # NOQA


@click.command()
@click.option('--path', default="/data/tiled20.raw")
@click.option('--scheduler-uri', default=None)
@click.option('--stackheight', default=32)
@click.option('--scan-size', default="10240,768")
@click.option('--method', type=click.Choice(['direct', 'mmap', 'read']), required=True)
@click.option('--num-masks', default=1)
@click.option('--num-workers', default=psutil.cpu_count(logical=False))
@click.option('--num-nodes', default=None, type=int)
def main(path, scheduler_uri, stackheight, scan_size, method, num_masks, num_workers, num_nodes):
    scan_size = tuple(int(x) for x in scan_size.split(","))
    if num_nodes is not None and scheduler_uri is None:
        raise Exception("num_nodes limit only works for non-local cluster")
    if scheduler_uri is None:
        dask_executor = BenchmarkDaskExecutor.make_local(cluster_kwargs={
            'threads_per_worker': 1,
            'n_workers': num_workers,
        })
    else:
        dask_executor = BenchmarkDaskExecutor.connect(scheduler_uri, node_limit=num_nodes)
    ctx = Context(executor=dask_executor)

    workers = ctx.executor.get_available_workers()
    for worker in workers:
        ctx.executor.client.run(_preload, workers=[worker['name']])

    def _load():
        if method == "direct":
            ds = DirectRawFileDataSet(
                path=path,
                dtype="float32",
                scan_size=scan_size,
                detector_size=(128, 128),
                stackheight=stackheight,
            )
        elif method == "read":
            ds = DirectRawFileDataSet(
                path=path,
                dtype="float32",
                scan_size=scan_size,
                detector_size=(128, 128),
                stackheight=stackheight,
                enable_direct=False,
            )
        elif method == "mmap":
            ds = RawFileDataSet(
                path=path,
                dtype="float32",
                scan_size=scan_size,
                detector_size_raw=(128, 128),
                crop_detector_to=(128, 128),
            )
        ds = ds.initialize()
        return ds

    def _getsize():
        return os.stat(path).st_size

    ds = dask_executor.run_function(_load)
    dask_executor.run_function(ds.check_valid)

    total_size = dask_executor.run_function(_getsize)
    assert total_size == np.dtype(ds.dtype).itemsize * ds.shape.size

    def _make_random_mask():
        return np.random.randn(128, 128).astype("float32")

    apply_mask = ctx.create_mask_analysis(
        dataset=ds,
        factories=num_masks * [_make_random_mask]
    )

    # dry-run:
    ctx.run(apply_mask)

    # timed run:
    t0 = time.time()
    ctx.run(apply_mask)
    t1 = time.time()
    delta = t1 - t0

    tilesize_bytes = stackheight * 128 * 128 * 4

    results = {
        "path": path,
        "num_masks": num_masks,
        "bytes": total_size,
        "time": delta,
        "throughput_mib": total_size / delta / 1024 / 1024,
        "tilesize_bytes": tilesize_bytes,
        "method": method,
        "num_nodes": num_nodes,
        "workers": workers,
    }
    print(json.dumps(results, indent=4))


if __name__ == "__main__":
    main()
