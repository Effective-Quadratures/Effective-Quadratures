"""Finding coefficients via least squares"""
from parameter import Parameter
from basis import Basis
from poly import Poly
import numpy as np
from utils import evalfunction, evalgradients, cell2matrix
from scipy.linalg import qr, svd
from qr import solveCLSQ
import matplotlib.pyplot as plt
from convex import maxdet, binary2indices
class Polylsq(Poly):
    """
    This class defines a Polylsq (polynomial via least squares) object
    """
    def __init__(self, parameters, basis, mesh, optimization, oversampling, gradients=False):
        super(Polylsq, self).__init__(parameters, basis)
        self.mesh = mesh
        self.optimization = optimization
        self.oversampling = oversampling
        self.gradients = gradients
        n = self.basis.cardinality
        m_big = int(np.round(7 * n * np.log(n)))
        m_refined = int(np.round(self.oversampling * n))
        
        # Check that oversampling factor is greater than 1.2X of basis at the minimum
        if m_refined > m_big:
            raise(ValueError, 'Polylsq::__init__:: Oversampling factor should be greater than 1.')

        # Methods!
        if self.mesh.lower() == 'tensor':
            pts, wts_orig = super(Polylsq, self).getTensorQuadratureRule() # original weights sum up to 1
            wts = np.sqrt(wts_orig)  
        elif self.mesh.lower() == 'chebyshev':
            pts = np.cos(np.pi * np.random.rand(m_big, self.dimensions ))
            wts = float(n * 1.0)/float(m_big * 1.0) * 1.0/np.sum( (super(Polylsq, self).getPolynomial(pts))**2 , 0)
            wts_orig = wts * 1.0/np.sum(wts)
            wts = np.sqrt(wts_orig)
        elif self.mesh.lower() == 'uniform':
            pts = np.zeros((m_big, self.dimensions))
            for i in range(0, self.dimensions):
                univariate_samples = np.linspace(self.parameters[i].lower, self.parameters[i].upper, m_big)
                for j in range(0, m_big):
                    pts[j, i] = univariate_samples[j]
            wts =  1.0/np.sum( (super(Polylsq, self).getPolynomial(pts))**2 , 0)
            wts_orig = wts * 1.0/np.sum(wts)
            wts = np.sqrt(wts_orig)
        elif self.mesh.lower() == 'random':
            pts = np.zeros((m_big, self.dimensions))
            for i in range(0, self.dimensions):
                univariate_samples = self.parameters[i].getSamples(m_big)
                for j in range(0, m_big):
                    pts[j, i] = univariate_samples[j]
            wts = 1.0/np.sum( (super(Polylsq, self).getPolynomial(pts))**2 , 0)
            wts_orig = wts * 1.0/np.sum(wts)
            wts = np.sqrt(wts_orig)
        else:
            raise(ValueError, 'Polylsq:__init___:: Unknown mesh! Choose between tensor, chebyshev, random or induced please.')
        if self.gradients is False:
            self.__gradientsFalse(pts, wts, m_refined, wts_orig)
        elif self.gradients is True:
            self.__gradientsTrue(pts, wts, m_refined, wts_orig)  
    def __gradientsTrue(self, pts, wts, m_refined, wts_orig):
        P = super(Polylsq, self).getPolynomial(pts)
        W = np.mat( np.diag(wts))
        A = W * P.T
        if self.optimization.lower() == 'greedy-qr':    
            __, __, pvec = qr(A.T, pivoting=True)
            z = pvec[0:m_refined]
        elif self.optimization.lower() == 'greedy-svd':   
            __, __, V = svd(A.T)
            __, __, pvec = qr(V[:, 0:m_refined].T , pivoting=True )
            z = pvec[0:m_refined]
        elif self.optimization.lower() == 'newton':
            zhat, L, ztilde, Utilde = maxdet(A, m_refined)
            z = binary2indices(zhat)
        else:
            raise(ValueError, 'Polylsq:__init___:: Unknown optimization technique! Choose between greedy or newton please.')
        index = 1
        rows = 1e15
        rank = 0
        # While loop trick to get the least number of rows in Az subject to some oversampling!
        while  rank < self.basis.cardinality:
            z_chosen = z[0:index]
            refined_pts = pts[z_chosen]
            Pz = super(Polylsq, self).getPolynomial(refined_pts)
            wts_orig_normalized =  wts_orig[z_chosen] / np.sum(wts_orig[z_chosen])
            Wz = np.mat(np.diag( np.sqrt(wts_orig_normalized) ) )
            Az =  Wz * Pz.T
            dPcell = super(Polylsq, self).getPolynomialGradient(refined_pts)
            dP = cell2matrix(dPcell)
            M = np.vstack([Az, dP])
            rank = np.linalg.matrix_rank(M)
            print 'Iterating...system rank: '+str(rank)+', and the # of rows in Az: '+str(index)
            index = index + 1
            del dPcell, dP 
        index = int(np.round(self.oversampling * (index - 1) ) )
        z_chosen = z[0:index]
        refined_pts = pts[z_chosen]
        Pz = super(Polylsq, self).getPolynomial(refined_pts)
        wts_orig_normalized =  wts_orig[z_chosen] / np.sum(wts_orig[z_chosen])
        self.Wz = np.mat(np.diag( np.sqrt(wts_orig_normalized) ) )
        self.Az =  self.Wz * Pz.T
        dPcell = super(Polylsq, self).getPolynomialGradient(refined_pts)
        self.Cz = cell2matrix(dPcell)
        self.pts = refined_pts     
    def __gradientsFalse(self, pts, wts, m_refined, wts_orig):
        P = super(Polylsq, self).getPolynomial(pts)
        W = np.mat( np.diag(wts))
        A = W * P.T
        if self.optimization.lower() == 'greedy-qr':    
            __, __, pvec = qr(A.T, pivoting=True)
            z = pvec[0:m_refined]
        elif self.optimization.lower() == 'greedy-svd':   
            __, __, V = svd(A.T)
            __, __, pvec = qr(V[:, 0:m_refined].T , pivoting=True )
            z = pvec[0:m_refined]
        elif self.optimization.lower() == 'newton':
            zhat, L, ztilde, Utilde = maxdet(A, m_refined)
            z = binary2indices(zhat)
        else:
            raise(ValueError, 'Polylsq:__init___:: Unknown optimization technique! Choose between greedy or newton please.')
        refined_pts = pts[z]
        Pz = super(Polylsq, self).getPolynomial(refined_pts)
        wts_orig_normalized =  wts_orig[z] / np.sum(wts_orig[z])
        Wz = np.mat(np.diag( np.sqrt(wts_orig_normalized) ) )
        self.Az =  Wz * Pz.T
        self.A = A
        self.Wz = Wz
        self.pts = refined_pts
    def quadraturePoints(self):
        return self.pts
    def computeCoefficients(self, func, gradfunc=None, gradientmethod=None):
        # If there are no gradients, solve via standard least squares!
        if self.gradients is False:
            p, q = self.Wz.shape
            # Get function values!
            if callable(func):
                y = evalfunction(self.pts, func)
            else:
                y = func
            self.bz = np.dot( self.Wz ,  np.reshape(y, (p,1)) )
            alpha = np.linalg.lstsq(self.Az, self.bz, rcond=None) 
            self.coefficients = alpha[0]
        # If there are gradients then use a constrained least squares approach!
        elif self.gradients is True and gradfunc is not None:
            p, q = self.Wz.shape
            # Get function values!
            if callable(func):
                y = evalfunction(self.pts, func)
            else:
                y = func
            # Get gradient values!
            if callable(func):
                grad_values = evalgradients(self.pts, gradfunc, 'matrix')
            else:
                grad_values = gradfunc
            # Assemble gradients into a single long vector called dy!     
            p, q = grad_values.shape
            d = np.zeros((p*q,1))
            counter = 0
            for j in range(0,q):
                for i in range(0,p):
                    d[counter] = grad_values[i,j]
                    counter = counter + 1
            self.dy = d
            del d, grad_values
            self.bz = np.dot( self.Wz ,  np.reshape(y, (p,1)) )
            coefficients, cond = solveCLSQ(self.Az, self.bz, self.Cz, self.dy, gradientmethod)
            self.coefficients = coefficients
        elif self.gradients is True and gradfunc is None:
            raise(ValueError, 'Polylsq:computeCoefficients:: Gradient function evaluations must be provided, either a callable function or as vectors.')
        super(Polylsq, self).__setCoefficients__(self.coefficients)
    def getDesignMatrix(self):
        super(Polylsq, self).__setDesignMatrix__(self.Az)

################################
# Private functions!
################################
def rowNormalize(A):
    rows, cols = A.shape
    row_norms = np.mat(np.zeros((rows, 1)), dtype='float64')
    Normalization = np.mat(np.eye(rows), dtype='float64')
    for i in range(0, rows):
        temp = 0.0
        for j in range(0, cols):
            row_norms[i] = temp + A[i,j]**2
            temp = row_norms[i]
        row_norms[i] = (row_norms[i] * 1.0/np.float64(cols))**(-1)
        Normalization[i,i] = row_norms[i]
    A_normalized = np.dot(Normalization, A)
    return A_normalized, Normalization
