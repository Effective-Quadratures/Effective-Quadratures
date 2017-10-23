from unittest import TestCase
import unittest
from equadratures import *
import numpy as np
from scipy import stats as s

class TestStats(TestCase):
    
    def setUp(self):
        self.degree = 5
        points_used = self.degree + 1
        self.x1 = Parameter(param_type="Uniform", lower=0.0, upper=1.0, points=points_used)
        self.x2 = Parameter(param_type="Uniform", lower=0.0, upper=1.0, points=points_used)
        self.x3 = Parameter(param_type="Uniform", lower=-1, upper=1, points=points_used)
        
    def test_1(self):
        def fun1(x):
            return x[0]        
        x1 = self.x1
        degree = self.degree
        parameters = [x1]
        basis = IndexSet('Tensor grid',[degree])
        uqProblem = Polyint(parameters,basis)
        coefficients, indices, pts = uqProblem.getPolynomialCoefficients(fun1)
        stats = Statistics(coefficients, basis, parameters)
        
        epsilon = 1e-5
        assert(abs((stats.mean - 0.5)/(0.5 + epsilon)) < 0.1)
        assert(abs((stats.variance - 1/12.0)/(1/12.0+ epsilon)) < 0.1)
        assert(abs((stats.skewness - 0)/(0+ epsilon)) < 0.1)
        assert(abs((stats.kurtosis - 1.8)/(1.8+ epsilon)) < 0.1)


    def test_2(self):
        def fun2(x):
            return x[0]+x[1]+x[2]        
        x1 = self.x1
        x2 = self.x2
        x3 = self.x3
        degree = self.degree
        parameters = [x1,x2,x3]
        basis = IndexSet('Tensor grid',[degree,degree,degree])
        uqProblem = Polyint(parameters,basis)
        coefficients, indices, pts = uqProblem.getPolynomialCoefficients(fun2)
        stats = Statistics(coefficients, basis, parameters)
        fosi = stats.getSobol(1)
        x1_samples = x1.getSamples(1000000)
        x2_samples = x2.getSamples(1000000)
        x3_samples = x3.getSamples(1000000)
        f = np.zeros((1000000,1))
        
        for i in range(1000000):
            f[i,0] = fun2([x1_samples[i,0], x2_samples[i,0], x3_samples[i,0]])
        
        MC_mean = np.mean(f)
        MC_var = np.var(f)
        MC_skew = s.skew(f)
        MC_kurt = s.kurtosis(f, fisher = False)
        epsilon = 1e-5
        assert(abs((stats.mean - 1.0)/(MC_mean + epsilon)) < 0.1)
        assert(abs((stats.variance - MC_var)/(MC_var+ epsilon)) < 0.1)
        assert(abs((stats.skewness - 0)/(0+ epsilon)) < 0.1)
        assert(abs((stats.kurtosis - MC_kurt)/(MC_kurt+ epsilon)) < 0.1)

    def test_3(self):
        def fun3(x):
            return np.exp(x[0]+x[1])
        x1 = self.x1
        x2 = self.x2
        degree = self.degree
        parameters = [x1,x2]
        basis = IndexSet('Tensor grid',[degree,degree])
        uqProblem = Polyint(parameters,basis)
        coefficients, indices, pts = uqProblem.getPolynomialCoefficients(fun3)
        stats = Statistics(coefficients, basis, parameters)
        fosi = stats.getSobol(1)
        
        x1_samples = x1.getSamples(1000000)
        x2_samples = x2.getSamples(1000000)
        f = np.zeros((1000000,1))
        
        for i in range(1000000):
            f[i,0] = fun3([x1_samples[i,0], x2_samples[i,0]])
        
        MC_mean = np.mean(f)
        MC_var = np.var(f)
        MC_skew = s.skew(f)
        MC_kurt = s.kurtosis(f, fisher = False)
        epsilon = 1e-5
        assert(abs((stats.mean - MC_mean)/(MC_mean + epsilon)) < 0.1)
        assert(abs((stats.variance - MC_var)/(MC_var+ epsilon)) < 0.1)
        assert(abs((stats.skewness - MC_skew)/(MC_skew+ epsilon)) < 0.1)
        assert(abs((stats.kurtosis - MC_kurt)/(MC_kurt+ epsilon)) < 0.1)

if __name__ == '__main__':
    unittest.main()
