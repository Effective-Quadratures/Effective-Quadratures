"""The Weibull distribution."""
import numpy as np
from distribution import Distribution
from recurrence_utils import custom_recurrence_coefficients
from scipy.special import erf, erfinv, gamma, beta, betainc, gammainc

class Weibull(Distribution):
    """
    The class defines a Weibull object. It is the child of Distribution.

    :param double shape:
		Lower bound of the support of the Weibull distribution.
    :param double scale:
		Upper bound of the support of the Weibull distribution.
    """
    def __init__(self, shape=None, scale=None):
        self.shape = shape
        self.scale = scale
        if ( self.shape < 0.0 ) or (self.scale < 0.0):
            raise(ValueError, 'For a Weibull distribution, the shape and scale parameters must be greater than or equal to 0.')
        self.mean = self.scale * gamma(1.0 + 1.0/self.shape)
        self.variance = self.scale**2 * ( gamma(1.0 + 2.0/self.shape) - (gamma(1.0 + 1.0/self.shape))**2  )
        self.skewness = (gamma(1.0 + 3.0/self.shape) * self.scale**3 - 3 * self.mean * self.variance - self.mean**3  )/( np.sqrt(self.variance)**3 )
        self.bounds = np.array([0, np.inf])

    def getDescription(self):
        """
        A description of the Weibull distribution.

        :param Weibull self:
            An instance of the Weibull class.
        :return:
            A string describing the Weibull distribution.
        """
        text = "A Weibull distribution with a shape parameter of "+str(self.shape)+" and a scale parameter of "+str(self.scale)
        return text

    def getPDF(self, N):
        """
        A Weibull probability density function.

        :param Weibull self:
            An instance of the Weibull class.
        :param integer N:
            Number of points for defining the probability density function.
        """
        x = np.linspace(0.0000001, 15.0/self.shape, N)
        w = self.shape/self.scale * (x/self.scale)**(self.shape-1.0) * np.exp(-1.0 * (x/self.scale)**self.shape )
        return x, w

    def getiCDF(self, xx):
        """
        An inverse Weibull cumulative density function.

        :param Weibull self:
            An instance of the Weibull class.
        :param array xx:
            A numpy array of uniformly distributed samples between [0,1].
        :return:
            Inverse CDF samples associated with the Weibull distribution.
        """
        return self.scale * (-np.log(1.0 - xx))**(1.0/self.shape)

    def getCDF(self, N):
        """
        A Weibull cumulative density function.

        :param Weibull self:
            An instance of the Weibull class.
        :param integer N:
            Number of points for defining the cumulative density function.
        :return:
            An array of N equidistant values over the support of the distribution.
        :return:
            Cumulative density values along the support of the Weibull distribution.
        """
        x = np.linspace(0, 15.0/self.shape, N)
        w = 1 - np.exp(-1.0 * ( (x) / (self.scale * 1.0)  )**self.shape)
        return x, w
