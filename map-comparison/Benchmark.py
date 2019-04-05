import time

import numpy as np

class Benchmark:
    def __init__(self, path, dtype, scan_size, detector_size, warmup_rounds, roi, mask):
        self.path = path
        self.dtype = np.dtype(dtype)
        self.scan_size = scan_size
        self.detector_size = detector_size
        self.warmup_rounds = warmup_rounds
        self.roi = roi
        self.mask = mask

    def bench_all(self):
        funcs = ['sum_image', 'std_map', 'masked_sum', 'fluctuation_em', 'fourier_sum', 'center_of_mass']
        result = {}
        for f in funcs:
            func = self.__getattribute__(f)
            print('%s: Warming up test %s' % (self.__class__.__name__, f))
            for _ in range(self.warmup_rounds):
                func()
            print('%s: Starting test %s...' % (self.__class__.__name__, f))
            t0 = time.time()
            func()
            t1 = time.time()
            delta = t1 - t0
            print('%s: Finished test %s in %f s.' % (self.__class__.__name__, f, delta))
            result[f] = delta
        return result

    def sum_image(self):
        raise NotImplementedError

    def std_map(self):
        raise NotImplementedError

    def masked_sum(self):
        raise NotImplementedError

    def fluctuation_em(self):
        raise NotImplementedError

    def fourier_sum(self):
        raise NotImplementedError

    def center_of_mass(self):
        raise NotImplementedError
