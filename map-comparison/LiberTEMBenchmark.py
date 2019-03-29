import functools

import numpy as np

import libertem.api as lt
from libertem import udf
from libertem.common.buffers import BufferWrapper

from Benchmark import Benchmark

class LiberTEMBenchmark(Benchmark):
    def __init__(self, path, dtype, scan_size, detector_size, warmup_rounds, roi, mask):
        super().__init__(path, dtype, scan_size, detector_size, warmup_rounds, roi, mask)
        self.ctx = lt.Context()
        self.ds = self.ctx.load(
            'raw', 
            path=path,
            dtype=dtype,
            scan_size=scan_size,
            detector_size_raw=detector_size,
            crop_detector_to=detector_size,
        )
        self.boolean_mask = self.mask == 1

    def sum_image(self):
        sum_analysis = self.ctx.create_sum_analysis(dataset=self.ds)
        # return self.data[self.roi].sum(axis=0)
        return self.ctx.run(sum_analysis)

    def std_map(self):
        def make_result_buffers():
            return  {
                'x2': BufferWrapper(
                    kind="sig", dtype="float64"
                ),
                'x': BufferWrapper(
                    kind="sig", dtype="float64"
                ),
            }
        
        def std_merge(dest, src):
            for key in ('x2', 'x'):
                dest[key][:] += src[key]
            
        def make_std(frame, x2, x):
            x2[:] += frame**2
            x[:] += frame

        res = self.ctx.run_udf(
            dataset=self.ds,
            fn=make_std,
            make_buffers=make_result_buffers,
            merge=std_merge
        )

        x = res['x'].data
        x2 = res['x2'].data

        # return self.data[self.roi].std(axis=0)
        return np.sqrt(np.abs(x/self.ds.shape.sig.size - x2/self.ds.shape.sig.size**2))

    def masked_sum(self):
        mask = self.mask
        
        def mask_factory():
            return mask

        mask_analysis = self.ctx.create_mask_analysis(dataset=self.ds, factories=[mask_factory])
        return self.ctx.run(mask_analysis)

    def fluctuation_em(self):

        def make_result_buffers():
            return {
                'std': BufferWrapper(
                    kind="nav", dtype="float32"
                )
            }

        def init_std(partition, boolean_mask):
            return {
                'boolean_mask': boolean_mask
            }

        def make_std(frame, std, boolean_mask):
            std[:] = frame[boolean_mask].std()

        res = self.ctx.run_udf(
            dataset=self.ds,
            fn=make_std,
            make_buffers=make_result_buffers,
            init=functools.partial(init_std, boolean_mask=self.boolean_mask)
        )
        return res

    def fourier_sum(self):
        def make_result_buffers():
            return {
                'fou': BufferWrapper(
                    kind="nav", dtype="complex64"
                )
            }

        def init_fou(partition, boolean_mask):
            return {
                'boolean_mask': boolean_mask
            }

        def make_fou(frame, fou, boolean_mask):
            fou[:] = np.fft.fftshift(np.fft.fft2(frame))[boolean_mask].sum()

        res = self.ctx.run_udf(
            dataset=self.ds,
            fn=make_fou,
            make_buffers=make_result_buffers,
            init=functools.partial(init_fou, boolean_mask=self.boolean_mask)
        )
        return res


    def center_of_mass(self):
        com_analysis = self.ctx.create_com_analysis(dataset=self.ds)
        return self.ctx.run(com_analysis)