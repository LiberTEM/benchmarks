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


def _preload():
    import libertem.preload  # NOQA


@click.command()
@click.option('--path', default="/data/tiled20.raw")
@click.option('--scheduler-uri')
@click.option('--stackheight', default=32)
@click.option('--direct/--no-direct', default=True)
def main(path, scheduler_uri, stackheight, direct):
    dask_executor = DaskJobExecutor.connect(scheduler_uri)
    ctx = Context(executor=dask_executor)

    workers = ctx.executor.get_available_workers()
    for worker in workers:
        ctx.executor.client.run(_preload, workers=[worker['name']])

    def _load():
        if direct:
            ds = DirectRawFileDataSet(
                path=path,
                dtype="float32",
                scan_size=(20 * 512, 768),
                detector_size=(128, 128),
                stackheight=stackheight,
            )
        else:
            ds = RawFileDataSet(
                path=path,
                dtype="float32",
                scan_size=(20 * 512, 768),
                detector_size_raw=(128, 128),
                crop_detector_to=(128, 128),
            )
        ds = ds.initialize()
        return ds

    def _getsize():
        return os.stat(path).st_size

    total_size = dask_executor.run_function(_getsize)
    ds = dask_executor.run_function(_load)
    dask_executor.run_function(ds.check_valid)

    apply_ring = ctx.create_ring_analysis(dataset=ds)

    # dry-run:
    ctx.run(apply_ring)

    # timed run:
    t0 = time.time()
    ctx.run(apply_ring)
    t1 = time.time()
    delta = t1 - t0

    print("{} bytes in {}s = {}MiB/s".format(total_size, delta, total_size / delta / 1024 / 1024))
    print("tilesize_bytes = {}KiB".format(stackheight * 128 * 128 * 4 / 1024))


if __name__ == "__main__":
    main()
