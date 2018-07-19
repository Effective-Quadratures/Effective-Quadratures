"""The Chi-squared distribution."""
import numpy as np
from distribution import Distribution
from scipy.special import erf, erfinv, gamma, gammainc

class Chisquared(Distribution):
    """
    The class defines a Chi-squared object. It is the child of Distribution.
    
    :param int dofs:
		Degrees of freedom for the chi-squared distribution.
    """
    def __init__(self, dofs):
        self.dofs = dofs
        if self.dofs == 1:
            self.bounds = np.array([1e-15, np.inf])
        else:
            self.bounds = np.array([0.0, np.inf])
        self.mean = float(self.dofs)
        self.variance = 2 * self.mean
        self.skewness = np.sqrt(8.0 / self.mean)
        self.kurtosis = 12.0/self.mean + 3.0 
    
    def getDescription(self):
        """
        A description of the Chi-squared distribution.
            
        :param Chi-squared self:
            An instance of the Chi-squared class.
        :return:
            A string describing the Chi-squared distribution.
        """
        text = "A Chi-squared distribution is characterised by its degrees of freedom, which here is"+str(self.dofs)+"."
        return text

    def getPDF(self, N):
        """
        A Chi-squared  probability density function.
        
        :param Chi-squared  self:
            An instance of the Chi-squared  class.
        :param integer N:
            Number of points for defining the probability density function.
        :return:
            An array of N equidistant values over the support of the Chi-squared distribution.
        :return:
            Probability density values along the support of the Chi-squared distribution.
        """
        xreal = np.linspace(0.0, 10.0*self.mean, N)
        wreal = 1.0 / (2.0** (self.mean / 2.0) * gamma(self.mean / 2.0)) * xreal**(self.mean/2.0  - 1.0) * np.exp(-xreal / 2.0)
        return xreal, wreal

    def getCDF(self, N):
        """
        A Chi-squared cumulative density function.
        
        :param Chi-squared self:
            An instance of the Chi-squared class.
        :param integer N:
            Number of points for defining the cumulative density function.
        :return:
            An array of N equidistant values over the support of the Chi-squared distribution.
        :return:
            Cumulative density values along the support of the Chi-squared distribution.
        """
        xreal = np.linspace(0.0, 10.0*self.mean, N)
        wreal = 1.0 / (gamma(self.mean / 2.0)) * gammainc(self.mean / 2.0 , xreal / 2.0)
        return xreal, wreal