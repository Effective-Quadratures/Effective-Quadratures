#!/usr/bin/env python
from effective_quadratures.polynomial import Polynomial
import numpy as np

def main():
    
    # Parameter test 1: getPDFs()
    var1 = Parameter(points=12, shape_parameter_A=2, shape_parameter_B=3, param_type='TruncatedGaussian', lower=3, upper=10)
    x, y = var1.getPDF(50)
    print x, y
    print '\n'

    # Parameter test 2: getRecurrenceCoefficients()
    var2 = Parameter(points=15, param_type='Uniform', lower=-1, upper=1)
    ab = var2.getRecurrenceCoefficients()
    print ab
    print '\n'

    # Parameter test 3: getJacobiMatrix()
    var3 = Parameter(points=5, param_type='Beta', lower=0, upper=1, shape_parameter_A=2, shape_parameter_B=3)
    J = var3.getJacobiMatrix()
    print J
    print '\n'

    # Parameter test 4: getJacobiEigenvectors()
    var4 = Parameter(points=5, param_type='Gaussian', shape_parameter_A=0, shape_parameter_B=2)
    V = var4.getJacobiEigenvectors()
    print V
    print '\n'

    # Parameter test 5: computeMean()
    var5 = Parameter(points=10, param_type='Weibull', shape_parameter_A=1, shape_parameter_B=5)
    mu = var5.computeMean()
    print mu
    print '\n'

    # Parameter test 6: getOrthoPoly(points):
    x = np.linspace(-1,1,15)
    var6 = Parameter(points=10, param_type='Uniform', lower=-1, upper=1)
    poly = var6.getOrthoPoly(x)
    print poly
    print '\n'

    # Parameter test 7: Now with derivatives
    var7 = Parameter(points=7, param_type='Uniform', lower=-1, upper=1, derivative_flag=1)
    poly, derivatives = var7.getOrthoPoly(x)
    print poly, derivatives
    print '\n'

    # Parameter test 8: getLocalQuadrature():
    var8 = Parameter(points=5, shape_parameter_A=0.8, param_type='Exponential')
    p, w = var8.getLocalQuadrature()
    print p, w
    print '\n'
    return 0

main()