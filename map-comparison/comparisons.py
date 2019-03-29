import os
import json
import psutil

import click

for k in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS']:
    os.environ[k] = '1'

import numpy as np
# import dask.distributed as dd

from NumpyBenchmark import NumpyBenchmark
from LiberTEMBenchmark import LiberTEMBenchmark
from DaskBenchmark import DaskBenchmark

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
@click.option('--method', type=click.Choice(['direct', 'mmap', 'read']), required=True)
@click.option('--num-workers', default=psutil.cpu_count(logical=False))
@click.option('--num-nodes', default=None, type=int)
@click.option('--warmup-rounds', default=1)
def main(path, scheduler_uri, stackheight, dtype, scan_size, detector_size, method, num_workers, num_nodes,
         warmup_rounds):
    scan_size = tuple(int(x) for x in scan_size.split(","))
    detector_size = tuple(int(x) for x in detector_size.split(","))
    (a, b) = scan_size
    (f, g) = detector_size
    
    roi = np.zeros(shape=scan_size, dtype=np.bool)
    roi[(a * 5) // 10:(a * 6) // 10, (b * 2) // 10:(b * 3) // 10] = True
    
    mask = np.zeros(shape=detector_size, dtype=np.float32)
    mask[(f * 5) // 10:(f * 6) // 10, (g * 2) // 10:(g * 3) // 10] = 1

    numpy_bench = NumpyBenchmark(path, dtype, scan_size, detector_size, warmup_rounds, roi, mask)  
    print(json.dumps(numpy_bench.bench_all()))

    libertem_bench = LiberTEMBenchmark(path, dtype, scan_size, detector_size, warmup_rounds, roi, mask)
    print(json.dumps(libertem_bench.bench_all()))
    
    dask_bench = DaskBenchmark(path, dtype, scan_size, detector_size, warmup_rounds, roi, mask)
    print(json.dumps(dask_bench.bench_all()))

    print("Starting distributed client...")
 #   client = dd.Client(address=scheduler_uri)
    dask_bench = DaskBenchmark(path, dtype, scan_size, detector_size, warmup_rounds, roi, mask)   
    print(json.dumps(dask_bench.bench_all()))

if __name__ == "__main__":
    main()
