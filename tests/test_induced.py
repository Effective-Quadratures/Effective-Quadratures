from unittest import TestCase
import unittest
from equadratures.poly import Poly
from equadratures.sampling_methods.induced import Induced
from equadratures.parameter import Parameter
from equadratures.basis import Basis

import numpy as np
# import time


class TestSamplingGeneration(TestCase):

    def test_sampling(self):
        d = 3
        order = 3
        param = Parameter(distribution='uniform', order=order, lower=-1.0, upper=1.0)
        myparameters = [param for _ in range(d)]
        # mybasis = Basis('total-order')
        # mypoly1 = Poly(myparameters, mybasis, method='least-squares', sampling_args={'mesh':'monte-carlo', 'subsampling-algorithm':'qr', 'sampling-ratio':1.0} )
        # assert mypoly1._quadrature_points.shape == (order+1, d)
        mybasis2 = Basis('total-order')
        mypoly2 = Poly(myparameters, mybasis2, method='least-squares', sampling_args={'mesh':'induced', 'subsampling-algorithm':'qr', 'sampling-ratio':1.0})
        # print(mypoly2._quadrature_points.shape)
        assert mypoly2._quadrature_points.shape == (mypoly2.basis.cardinality, d)

    def test_induced_jacobi_evaluation(self):

        dimension = 3
        parameters = [Parameter(1, "Uniform", upper=1, lower=-1)]*dimension
        basis = Basis("total-order")

        # initialise_time = time.time()
        induced_sampling = Induced(parameters, basis)
        # print(f"time taken to initialise class: {time.time()-initialise_time}")

        parameter = parameters[0]
        parameter.order = 3
        cdf_value = induced_sampling.induced_jacobi_evaluation(0, 0, 0, parameter)
        np.testing.assert_allclose(cdf_value, 0.5, atol=0.00001)
        cdf_value = induced_sampling.induced_jacobi_evaluation(0, 0, 1, parameter)
        assert cdf_value == 1
        cdf_value = induced_sampling.induced_jacobi_evaluation(0, 0, -1, parameter)
        assert cdf_value == 0
        cdf_value = induced_sampling.induced_jacobi_evaluation(0, 0, 0.6, parameter)
        np.testing.assert_allclose(cdf_value, 0.7462, atol=0.00005)
        cdf_value = induced_sampling.induced_jacobi_evaluation(0, 0, 0.999, parameter)
        np.testing.assert_allclose(cdf_value, 0.99652, atol=0.000005)

    # def test_induced_sampling(self):
    #     """
    #     An integration test for the whole routine
    #     """
    #     dimension = 3
    #     parameters = [Parameter(3, "Uniform", upper=1, lower=-1)]*dimension
    #     basis = Basis("total-order", [3]*dimension)

    #     induced_sampling = Induced(parameters, basis)

    #     quadrature_points = induced_sampling.get_points()
    #     assert quadrature_points.shape == (63, 3)


if __name__ == '__main__':
    unittest.main()