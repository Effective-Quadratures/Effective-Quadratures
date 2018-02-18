#!/usr/bin/env python
from unittest import TestCase
import unittest
from equadratures import *
import numpy as np

class TestPolyint(TestCase):

    def test_polynomial_and_derivative_constructions(self):
        s = Parameter(lower=-1, upper=1, param_type='Uniform', points=2, derivative_flag=1)
        uq_parameters = [s,s]
        uq = Polyint(uq_parameters)
        num_elements = 2
        pts, x1, x2 = meshgrid(-1.0, 1.0, num_elements,num_elements)

        P , Q = uq.getMultivariatePolynomial(pts)

        s = Parameter(lower=-1, upper=2, param_type='Uniform', points=4, derivative_flag=0)
        T = IndexSet('Tensor grid', [5])
        uq = Polyint([s])
        pts = np.linspace(-1, 1, 20)
        P , D = uq.getMultivariatePolynomial(pts)

    def test_pseudospectral_coefficient_routines(self):
        def expfun(x):
            return np.exp(x[0] +  x[1])

        s = Parameter(lower=-1, upper=1, points=5)
        T = IndexSet('Sparse grid', level=3, growth_rule='linear', dimension=2)
        uq = Polyint([s,s], T)
        coefficients, index_set, evaled_pts = uq.getPolynomialCoefficients(expfun)

    def test_pseudospectral_approximation_tensor(self):

        def expfun(x):
            return np.exp(x[0] + x[1] ) + 0.5*np.cos(x[0]*2*np.pi)

        # Compare actual function with polynomial approximation
        s = Parameter(lower=-1, upper=1, points=6)
        T = IndexSet('Tensor grid', [5,5])
        uq = Polyint([s,s], T)
        num_elements = 10
        coefficients, index_set, evaled_pts = uq.getPolynomialCoefficients(expfun)
        pts, x1, x2 = meshgrid(-1.0, 1.0, num_elements,num_elements)
        Approx = uq.getPolynomialApproximation(expfun, pts, coefficients)
        A = np.reshape(Approx, (num_elements,num_elements))
        fun = evalfunction(pts, expfun)

    def test_pseudospectral_approximation_spam(self):

        def expfun(x):
            return np.exp(x[0] + x[1] ) + 0.5*np.cos(x[0]*2*np.pi)

        # Compare actual function with polynomial approximation
        s = Parameter(lower=-1, upper=1, points=6)
        T = IndexSet('Sparse grid', level=3, growth_rule='linear', dimension=2)
        uq = Polyint([s,s], T)
        num_elements = 10
        coefficients, index_set, evaled_pts = uq.getPolynomialCoefficients(expfun)
        pts, x1, x2 = meshgrid(-1.0, 1.0, num_elements,num_elements)
        Approx = uq.getPolynomialApproximation(expfun, pts)
        
if __name__ == '__main__':
    unittest.main()
