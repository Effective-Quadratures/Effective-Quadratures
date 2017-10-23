"""Computing Statistics from Polynomial Expansions"""
import numpy as np
from .plotting import barplot
#from .parameter import Parameter
from .polyint import Polyint
from .indexset import IndexSet
from itertools import *
class Statistics(object):
    """
    :param numpy-matrix coefficients: Coefficients from a polynomial expansion. Can be computed using any technique.
    :param IndexSet index_set: Polynomial index set. If an index set is not given, the constructor uses a tensor grid basis of polynomials. For total order and hyperbolic index sets, the user needs to explicity input an index set.

    Attributes:
        * **self.mean**: (double) Mean of the polynomial expansion.
        * **self.variance**: (double) Variance of the polynomial expansion.
        * **self.sobol**:(dict) Sobol' indices of order up to number of dimensions.

    **Notes:** 
    In a future release we will be incorporating second order Sobol indices, skewness and kurtosis based indices. Stay tuned!
    """

    # constructor
    def __init__(self, coefficients, index_set, parameters):
        self.coefficients = coefficients
        self.index_set = index_set
        self.parameters = parameters #should be a list containing instances of Parameter
        
        self.mean = getMean(self.coefficients)
        self.variance = getVariance(self.coefficients)
        self.sobol = getAllSobol(self.coefficients, self.index_set)
        
        #Prepare evals of polynomials for skewness and kurtosis
        polyint = Polyint(parameters, index_set)
        quad_pts, quad_wts = polyint.getPointsAndWeights()
        evals,deriv = polyint.getMultivariatePolynomial(quad_pts)
        self.weighted_evals = evals * coefficients
        self.quad_wts = quad_wts
        
        self.skewness = getSkewness(self.quad_wts, self.weighted_evals, self.index_set, self.variance)
        self.kurtosis = getKurtosis(self.quad_wts, self.weighted_evals, self.index_set, self.variance)
        
    
    def plot(self, filename=None):
        """
        Produces a bar graph of the first order Sobol indices

        :param Statistics object: An instance of the Statistics class.
        :param string filename: A file name in case the user wishes to save the bar graph. The default output is an eps file.

        **Sample usage:** 
        For useage please see the ipython-notebooks at www.effective-quadratures.org
        """
        # A bar graph plot of thae Sobol indices!
        dimensions = self.index_set.dimension
        xbins = range(0, dimensions)
        barplot(xbins, self.fosi, 'Parameters', 'Sobol indices')
    
    def getSobol(self, order = 1):
        """
        Get Sobol' indices at specified order. 

        :param order int: The order at which Sobol' indices are computed. By default, computes first order Sobol' indices.
        :return: indices, Dictionary where keys specify non-zero dimensions and values represent Sobol' indices.
        :rtype: dict

        **Sample usage:**
        stats = Statistics(coeffcients, index_set)
        fosi = stats.getSobol(1)        
        
        """
        return {key: value for key, value in self.sobol.iteritems() if len(key) == order}
        
        
    def getCondSkewness(self, order = 1):
        """
        Get conditional skewness indices at specified order. 

        :param order int: The order at which conditional skewness indices are computed. By default, computes first order conditional skewness.
        :return: indices, Dictionary where keys specify non-zero dimensions and values represent conditional skewness indices.
        :rtype: dict

        **Sample usage:**
        stats = Statistics(coeffcients, index_set)
        first_order_skewness = stats.getCondSkewness(1)        
        
        """
        return CondSkewness(order, self.quad_wts, self.weighted_evals, self.index_set, self.variance)
    def getCondKurtosis(self, order = 1):
        """
        Get conditional kurtosis indices at specified order. 

        :param order int: The order at which conditional kurtosis indices are computed. By default, computes first order conditional kurtosis.
        :return: indices, Dictionary where keys specify non-zero dimensions and values represent conditional kurtosis indices.
        :rtype: dict

        **Sample usage:**
        stats = Statistics(coeffcients, index_set)
        first_order_kurtosis = stats.getCondKurtosis(1)        
        
        """
        return CondKurtosis(order, self.quad_wts, self.weighted_evals, self.index_set, self.variance)
            
        
# Private functions!
def getMean(coefficients):
    mean = coefficients[0,0]
    return mean
        
def getVariance(coefficients):
    m, n = coefficients.shape
    if m > n:
        coefficients = coefficients.T
    variance = np.sum(coefficients[0][1:m]**2)
    return variance



# Function that computes the Sobol' indices of all orders up to dimension of i/p
def getAllSobol(coefficients, index_set):
    m, n = coefficients.shape
    variance = getVariance(coefficients)
    if m > n:
        coefficients = coefficients.T
    
    if not(isinstance(index_set, np.ndarray)):
        index_set = index_set.elements
    m, dimensions = index_set.shape
    if dimensions == 1:
        return {0:1.0}
    else:
        index_set_entries = m

        #Build dict to contain the Sobol' indices
        #Keys contain the non-zero indices
        #Values contain the Sobol' indices
                
        combo_index = {}
        for order in range(1,dimensions+1): #loop over order            
            for i in combinations(range(dimensions),order):
                #initialize each index to be 0                
                combo_index[i] = 0
                
            for i in range(0,index_set_entries): #loop over rows
                row = index_set[i,:]
                non_zero_entries = np.nonzero(row)[0]
                non_zero_entries.sort()    #just in case
                if len(non_zero_entries) == order and coefficients[0][i]**2 > 1e-5: #neglect entries that should actually be zero (what constitutes as zero?)
                    combo_index[tuple(non_zero_entries)] = combo_index[tuple(non_zero_entries)] + coefficients[0][i]**2 / variance
        
        check_sum = sum(combo_index.values())
        if (abs(check_sum - 1.0) >= 1e-2):
            print "Possible discrepancy in calculation, sum of indices = " + str(check_sum) 
        
        return combo_index

# Return global skewness        
def getSkewness(quad_wts, weighted_evals, index_set, variance):    
    total_evals = np.sum(weighted_evals[1:],0)
    third_total_evals = total_evals**3
      
    return np.dot(third_total_evals,quad_wts)/(variance**1.5)

# Return global kurtosis
def getKurtosis(quad_wts, weighted_evals, index_set, variance):    
    total_evals = np.sum(weighted_evals[1:],0)
    fourth_total_evals = total_evals**4
    
    return np.dot(fourth_total_evals,quad_wts)/(variance**2)

# Return conditional skewness of specified order, in dictionary format similar to Sobol' indices
#Unfortunately, to compute conditional indices, this slow method must be used! 
def CondSkewness(order, quad_wts, weighted_evals, index_set, variance):
    #Get all polynomials evaluated at the quad. pts and corresponding wts
    
    dimensions = index_set.elements.shape[1]
    norm_ind = index_set.elements.copy()
    norm_ind = map(tuple,(norm_ind > 0).astype(int))
    
    combo_index = {}
    for tot_order in range(1,dimensions+1): #loop over order            
        for i in product([0,1], repeat = dimensions):
            #initialize each index of the specified order to be 0                
            if sum(i) != order:
                continue
            combo_index[i] = 0.0   
    
    #1st term
    cubed_evals = weighted_evals**3
    integral1 = np.dot(cubed_evals, quad_wts)
    for i in range(1, integral1.shape[0]):
        if sum(norm_ind[i]) == order:
            combo_index[norm_ind[i]] = combo_index[norm_ind[i]] + integral1[i] /(variance**1.5)
    
    #2nd term (Can we avoid for loops in the future?)
    for p in range(1,index_set.cardinality):
        for q in range(1,index_set.cardinality):           
            summed_norm_index =tuple(np.logical_or(norm_ind[p], norm_ind[q]).astype(int))
            if sum(summed_norm_index) != order:
                continue            
            #check if selection function is zero, in which case delta = True
            delta = False
            for d in range(dimensions):
                if (index_set.elements[p,d] == 0 and index_set.elements[q,d] != 0) or p == q:
                    delta = True
                    break
            if delta:
                continue

            evals2 = (weighted_evals[p,:]**2)*weighted_evals[q,:]
            integral2 = np.sum(evals2* quad_wts)            
            combo_index[summed_norm_index] = combo_index[summed_norm_index] + 3 * integral2 /(variance**1.5)
    
    temp_ind = index_set.elements.copy()
    #3rd term (Can we avoid for loops in the future?)
    for p in range(1,index_set.cardinality):
        for q in range(p+1, index_set.cardinality):
            for r in range(q+1, index_set.cardinality):
                summed_norm_index =tuple(np.logical_or(np.logical_or(norm_ind[p], norm_ind[q]), norm_ind[r]).astype(int))
                if sum(summed_norm_index) != order:
                    continue
                #check if selection function is zero, in which case delta = True
                delta = False
                for d in range(dimensions):
                    if delta_pqr([temp_ind[p,:],temp_ind[q,:],temp_ind[r,:]]):
                        delta = True
                        break
                if delta:
                    continue
                evals3 = weighted_evals[p,:]*weighted_evals[q,:]*weighted_evals[r,:]
                
                integral3 = np.dot(evals3, quad_wts)
                
                combo_index[summed_norm_index] = combo_index[summed_norm_index] + 6 * integral3 /(variance**1.5)

    return combo_index

# Return conditional kurtosis of specified order, in dictionary format similar to Sobol' indices
def CondKurtosis(order, quad_wts, weighted_evals, index_set, variance):
    #Get all polynomials evaluated at the quad. pts and corresponding wts
    dimensions = index_set.elements.shape[1]
    norm_ind = index_set.elements.copy()
    norm_ind = map(tuple,(norm_ind > 0).astype(int))
    
    combo_index = {}
    for tot_order in range(1,dimensions+1): #loop over order            
        for i in product([0,1], repeat = dimensions):
            #initialize each index to be 0                
            if sum(i) != order:
                continue
            combo_index[i] = 0.0   
    #1st term
    fourth_evals = weighted_evals**4
    integral1 = np.dot(fourth_evals, quad_wts)
    for i in range(1, integral1.shape[0]):
        if sum(norm_ind[i]) == order:
            combo_index[norm_ind[i]] = combo_index[norm_ind[i]] + integral1[i] /(variance**2)
    
    #2nd term (Can we avoid for loops in the future?)
    for p in range(1,index_set.cardinality):
        for q in range(1,index_set.cardinality):
            summed_norm_index =tuple(np.logical_or(norm_ind[p], norm_ind[q]).astype(int))
            if sum(summed_norm_index) != order:
                continue
            #check if selection function is zero, in which case delta = True
            delta = False
            for d in range(dimensions):
                if (index_set.elements[p,d] == 0 and index_set.elements[q,d] != 0) or p == q:
                    delta = True
                    break
            if delta:
                continue
            evals2 = (weighted_evals[p,:]**3)*weighted_evals[q,:]    
            integral2 = np.dot(evals2, quad_wts)            
            combo_index[summed_norm_index] = combo_index[summed_norm_index] + 4 * integral2 /(variance**2)

    #3rd term (Can we avoid for loops in the future?)
    for p in range(1,index_set.cardinality):
        for q in range(p+1,index_set.cardinality):
            summed_norm_index = tuple(np.logical_or(norm_ind[p], norm_ind[q]).astype(int))
            if sum(summed_norm_index) != order:
                continue
            evals3 = (weighted_evals[p,:]**2)*(weighted_evals[q,:]**2)
            integral3 = np.dot(evals3, quad_wts)  
            combo_index[summed_norm_index] = combo_index[summed_norm_index] + 6 * integral3 /(variance**2)
    
    
    #4th term (Can we avoid for loops in the future?)
    for p in range(1,index_set.cardinality):
        for q in range(1, index_set.cardinality):
            for r in range(q+1, index_set.cardinality):
                summed_norm_index = tuple(np.logical_or(np.logical_or(norm_ind[p], norm_ind[q]), norm_ind[r]).astype(int))                
                if sum(summed_norm_index) != order:
                    continue                
                #check if selection function is zero, in which case delta = True
                delta = False
                for d in range(dimensions):
                    if (delta_p_qr([index_set.elements[p,:], index_set.elements[q,:], index_set.elements[r,:]]))\
                    or (q==p) or (r==p):
                        delta = True

                        break
                if delta:
                    continue
                evals4 = (weighted_evals[p,:]**2)*weighted_evals[q,:]*weighted_evals[r,:]

                integral4 = np.dot(evals4, quad_wts)
                
                combo_index[summed_norm_index] = combo_index[summed_norm_index] + 12 * integral4 /(variance**2)
    
    
    

    #5th term (Can we avoid for loops in the future?) (especially this. Scales poorly!)
    temp_ind = index_set.elements.copy()
    for p in range(1,index_set.cardinality):
        for q in range(p+1, index_set.cardinality):
            for r in range(q+1, index_set.cardinality):
                for t in range(r+1, index_set.cardinality):
                    summed_norm_index = tuple(np.logical_or(np.logical_or(np.logical_or(norm_ind[p], norm_ind[q]), norm_ind[r]), norm_ind[t]).astype(int))
                    if sum(summed_norm_index) != order:
                        continue               
                    #check if selection function is zero, in which case delta = True
                    delta = False
                    for d in range(dimensions):
                        if delta_pqrs([temp_ind[p,:], temp_ind[q,:], temp_ind[r,:], temp_ind[t,:]]):
                            delta = True
    
                            break
                    if delta:
                        continue
                    evals5 = weighted_evals[p,:]*weighted_evals[q,:]*weighted_evals[r,:]*weighted_evals[t,:]
                    integral5 = np.dot(evals5, quad_wts)
                    summed_norm_index = tuple(np.logical_or(np.logical_or(np.logical_or(norm_ind[p], norm_ind[q]), norm_ind[r]), norm_ind[t]).astype(int))
                    combo_index[summed_norm_index] = combo_index[summed_norm_index] + 24 * integral5 /(variance**2)
   
    return combo_index
    
 
#Calculates delta^p_{qr} (Geraci)
def delta_p_qr(rows):
    #first row = p, then q, then r    
    assert(len(rows) == 3)
    dimensions = len(rows[0])
    for d in range(dimensions):
        if rows[0][d] == 0:
            if rows[1][d] != rows[2][d]:
                return True
    return False

# Calculates delta_pqrs (From Geraci)
def delta_pqrs(rows):
    assert(len(rows) == 4) #Comparison of 4 rows
    norm_rows = []
    norm_rows[:] = rows[:]
    dimensions = len(rows[0])
    for i in range(4):
        for j in range(dimensions):
            if rows[i][j] != 0:
                norm_rows[i][j] = 1
    for d in range(dimensions):
        col_sum = norm_rows[0][d] + norm_rows[1][d] + norm_rows[2][d] + norm_rows[3][d]
        if  col_sum == 1:
            return True
        elif col_sum == 2:
            indices = np.zeros((4))
            for k in range(4):
                indices[k] = rows[k][d]
            non_zeros = indices.nonzero()[0]
            assert(len(non_zeros) == 2)
            if indices[non_zeros][0] == indices[non_zeros][1]:
                return False
            else:
                return True
    return False

#Calculates delta_pqr (Geraci)
def delta_pqr(rows):
    assert(len(rows) == 3)
    norm_rows = []
    norm_rows[:] = rows[:]
    dimensions = len(rows[0])
    for i in range(3):
        for j in range(dimensions):
            if rows[i][j] != 0:
                norm_rows[i][j] = 1
    for d in range(dimensions):
        col_sum = norm_rows[0][d] + norm_rows[1][d] + norm_rows[2][d]
        if col_sum == 1:
            return True
        elif col_sum == 2:
            if (rows[0][d] == rows[1][d]) or (rows[1][d] == rows[2][d]) or (rows[0][d] == rows[2][d]): #Hack
                return False
            else:
                return True
                