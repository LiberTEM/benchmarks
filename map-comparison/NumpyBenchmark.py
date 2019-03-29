import numpy as np
import scipy.ndimage

from Benchmark import Benchmark

class NumpyBenchmark(Benchmark):
    def __init__(self, path, dtype, scan_size, detector_size, warmup_rounds, roi, mask):
        super().__init__(path, dtype, scan_size, detector_size, warmup_rounds, roi, mask)
        self.data = np.memmap(
            self.path, 
            dtype=self.dtype, 
            mode='r', 
            shape=self.scan_size + self.detector_size
        )
        self.boolean_mask = self.mask == 1

    def sum_image(self):
        # return self.data[self.roi].sum(axis=0)
        return self.data.sum(axis=0)

    def std_map(self):
        # return self.data[self.roi].std(axis=0)
        return self.data.std(axis=0)

    def masked_sum(self):
        (f, g) = self.detector_size
        flat_data = self.data.reshape((-1, f * g))
        flat_mask = self.mask.reshape(-1)
        return np.dot(flat_data, flat_mask.T).reshape(self.scan_size)

    def fluctuation_em(self):
        return self.data[:, :, self.boolean_mask].std(axis=2)

    def fourier_sum(self):
        (f, g) = self.detector_size
        flat_mask = self.mask.reshape(-1)
        return np.dot(
            np.fft.fftshift(np.fft.fft2(self.data)).reshape((-1, f * g)), 
            flat_mask.T    
        ).reshape(self.scan_size)

    def center_of_mass(self):
        (a, b) = self.scan_size
        # masked = self.data * self.mask
        result = np.zeros(shape=(a, b, 2))
        for i in range (a):
            for j in range(b):
                # result[i, j] = scipy.ndimage.measurements.center_of_mass(masked[i, j])
                result[i, j] = scipy.ndimage.measurements.center_of_mass(self.data[i, j])
        return result