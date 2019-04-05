import os
import json
import psutil

import click

from benchs import benchs

def _preload():
    import libertem.preload  # NOQA

@click.command()
@click.option('--path', 
    default=r'testfile.raw')
@click.option('--scheduler-uri', default=None)
@click.option('--stackheight', default=32)
@click.option('--scan-size', default="64,64")
@click.option('--detector-size', default="128,128")
@click.option('--dtype', default="float32")
@click.option('--bench', type=click.Choice(['dask', 'dask.distributed', 'numpy', 'libertem']), required=True)
@click.option('--which', type=click.Choice(benchs), multiple=True)
@click.option('--skip', type=click.Choice(benchs), multiple=True)
@click.option('--num-workers', default=psutil.cpu_count(logical=False))
@click.option('--num-nodes', default=None, type=int)
@click.option('--warmup-rounds', default=1)
def main(path, scheduler_uri, stackheight, dtype, scan_size, detector_size, bench, which, skip, num_workers, num_nodes,
         warmup_rounds):
    scan_size = tuple(int(x) for x in scan_size.split(","))
    detector_size = tuple(int(x) for x in detector_size.split(","))
    (a, b) = scan_size
    (f, g) = detector_size

    # We have to make sure that this happens before numpy is loaded.
    if bench == 'libertem':
        for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
            os.environ[k] = '1'

    import numpy as np

    roi = np.zeros(shape=scan_size, dtype=np.bool)
    roi[(a * 5) // 10:(a * 6) // 10, (b * 2) // 10:(b * 3) // 10] = True
    
    mask = np.zeros(shape=detector_size, dtype=np.float32)
    mask[(f * 5) // 10:(f * 6) // 10, (g * 2) // 10:(g * 3) // 10] = 1

    if bench == 'libertem':
        from LiberTEMBenchmark import LiberTEMBenchmark as Bm
    elif bench == 'numpy':
        from NumpyBenchmark import NumpyBenchmark as Bm
    elif bench == 'dask.distributed':
        import dask.distributed as dd
        dd.Client(address=scheduler_uri)
        from DaskBenchmark import DaskBenchmark as Bm
    elif bench == 'dask':
        from DaskBenchmark import DaskBenchmark as Bm

    b = Bm(path, dtype, scan_size, detector_size, warmup_rounds, roi, mask)
    print(json.dumps(b.bench_all(which, skip)))

if __name__ == "__main__":
    main()
