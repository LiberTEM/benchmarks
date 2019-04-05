import numpy as np
import dask.array
import dask
import scipy.ndimage

from Benchmark import Benchmark

class DaskBenchmark(Benchmark):
    # 256 MB
    target_chunksize=2**28

    def __init__(self, path, dtype, scan_size, detector_size, warmup_rounds, roi, mask):
        super().__init__(path, dtype, scan_size, detector_size, warmup_rounds, roi, mask)

        # This assumes that scan_size[0] is powers of two
        def calculate_chunking(target, dtype, scan_size, detector_size):
            y = scan_size[0]
            total_size = np.prod(scan_size + detector_size) * dtype.itemsize
            ideal_num = total_size / target
            real_num = 1
            while real_num < ideal_num:
                real_num *= 2

            assert y % real_num == 0

            return (real_num, (y // real_num, scan_size[1]) + detector_size)

        def _mmap_partition(filename, dtype, chunking, chunk_number):
            chunksize = np.prod(chunking)*dtype.itemsize
            offset = chunk_number * chunksize
            return np.memmap(filename, dtype=dtype, mode='r', shape=chunking, offset=offset)

        mmap_partition = dask.delayed(_mmap_partition)

        self.num, self.chunking = calculate_chunking(
            self.target_chunksize, self.dtype, self.scan_size, self.detector_size
        )

        chunks = [dask.array.from_delayed(
            mmap_partition(
                filename=self.path,
                dtype=self.dtype,
                chunking=self.chunking,
                chunk_number=n
            ),
            shape=self.chunking,
            dtype=self.dtype
            ) for n in range(self.num)
        ]
        self.data = dask.array.concatenate(chunks, axis=0)
        self.boolean_mask = self.mask == 1

    def sum_image(self):
        # return self.data[self.roi].sum(axis=0)
        return self.data.sum(axis=0).compute()

    def std_map(self):
        # return self.data[self.roi].std(axis=0)
        return self.data.std(axis=0).compute()

    def masked_sum(self):
        (f, g) = self.detector_size
        flat_data = self.data.reshape((-1, f * g))
        flat_mask = self.mask.reshape(-1)
        return flat_data.dot(flat_mask.T).reshape(self.scan_size).compute()

    def fluctuation_em(self):
        (a, b) = self.scan_size
        (f, g) = self.detector_size
        flat_data = self.data.reshape(a, b, f * g)
        flat_mask = self.boolean_mask.reshape(-1) 
        return flat_data[:, :, flat_mask].std(axis=2).compute()

    def fourier_sum(self):
        (f, g) = self.detector_size
        flat_mask = self.mask.reshape(-1)
        ffts = dask.array.fft.fftshift(dask.array.fft.fft2(self.data))

        return ffts.reshape((-1, f * g)).dot(flat_mask.T).reshape(self.scan_size).compute()

    def center_of_mass(self):
        # TODO find a proper implementation for mapping functions
        (a, b) = self.scan_size
        (h, k, i, j) = self.chunking
        # masked = self.data * self.mask
        def _com(block):
            (a, b, c, d) = block.shape
            res = np.zeros(shape=(a, b, 2))
            for i in range(a):
                for j in range(b):
                    res[i, j] = scipy.ndimage.measurements.center_of_mass(block[i, j])
            return res

        result = dask.array.core.map_blocks(_com, self.data)
        return result.compute()