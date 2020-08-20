import numpy as np
from copy import deepcopy
from equadratures.parameter import Parameter
from equadratures.poly import Poly
from equadratures.basis import Basis
from urllib.parse import quote

class PolyTree(object):
	"""
    Definition of a polynomial tree object.
	
	:param str tree_type:
		The type of tree algorithm to use in the fit function. Options include ``classic`` which includes a model- split criterion and ``m5p`` which uses a standard deviation based split criterion and offers a substantial runtime improvement [1]
    :param int max_depth:
    	The maximum depth to which the tree will search to.
    :param int min_samples_leaf:
    	The minimum number of samples per leaf node.
    :param int k:
    	Determines the amount of smoothing to be done by ``predict()``. A value of 0 will disable smoothing. 
    :param int order:
    	The order of the generated orthogonal polynomials.
    :param str basis:
    	The type of index set used for the basis. Options include: ``univariate``, ``total-order``, ``tensor-grid``, ``sparse-grid``, ``hyperbolic-basis`` and ``euclidean-degree``; all basis are isotropic. 
    :param str search:
    	The method of search to be used. Options include ``uniform`` and ``exhaustive``
    :param int samples:
    	The interval between splits if ``uniform`` search is chosen
    :param bool logging:
    	Actions saved to log
	:
    **Sample constructor initialisations**::

        import numpy as np
        from equadratures import *

        tree = polytree.PolyTree()

        X = np.loadtxt('inputs.txt')
        y = np.loadtxt('outputs.txt')
        
        tree.fit(X,y)

    """
	def __init__(self, tree_type='classic', max_depth=5, min_samples_leaf=None, k=15, order=3, basis='tensor-grid', search='exhaustive', samples=50, logging=False, poly_method="least-squares", poly_solver_args=None):
		self.tree_type = tree_type
		self.max_depth = max_depth
		self.min_samples_leaf = min_samples_leaf
		self.k = k
		self.order = order
		self.basis = basis
		self.tree = None
		self.search = search
		self.samples = samples
		self.logging = logging
		self.log = []
		self.cardinality = None
		self.poly_method = poly_method
		self.poly_solver_args = poly_solver_args

		assert max_depth > 0, "max_depth must be a postive integer"
		assert k >= 0, "k must be a postive integer"
		assert order > 0, "order must be a postive integer" 
		assert samples > 0, "samples must be a postivie integer"


	def get_splits(self):
		"""
		Returns the list of splits made 

		:return:
			**splits**: A list of Splits made in the format of a nested list: [[split, dimension], ...]
		"""

		def _search_tree(node, splits):
			if node["children"]["left"] != None:
				if [node["threshold"], node["j_feature"]] not in splits:
					splits.append([node["threshold"], node["j_feature"]])
				splits = _search_tree(node["children"]["left"], splits)
							
			if node["children"]["right"] != None:
				if [node["threshold"], node["j_feature"]] not in splits:
					splits.append([node["threshold"], node["j_feature"]])
				splits = _search_tree(node["children"]["right"], splits)

			return splits
		
		return _search_tree(self.tree, [])

	def _split_data(self, j_feature, threshold, X, y):
		idx_left = np.where(X[:, j_feature] <= threshold)[0]
		idx_right = np.delete(np.arange(0, len(X)), idx_left)
		assert len(idx_left) + len(idx_right) == len(X)
		return (X[idx_left], y[idx_left]), (X[idx_right], y[idx_right])


	def get_polys(self):
		"""
		Returns the list of polynomials used in the tree

		:return:
			**polys**: A list of Poly objects
		"""

		def _search_tree(node, polys):
			if node["children"]["left"] == None and node["children"]["right"] == None:
				polys.append(node["poly"])
			
			if node["children"]["left"] != None:
				polys = _search_tree(node["children"]["left"], polys)
			
			if node["children"]["right"] != None:
				polys = _search_tree(node["children"]["right"], polys)

			return polys
		
		return _search_tree(self.tree, [])

	def fit(self, X, y):
		"""
		Fits the tree to the provided data

		:param numpy.ndarray X:
			Training input data
		:param numpy.ndarray y:
			Training output data
		"""

		def _build_tree():

			global index_node_global
		
			def _splitter(node):
				# Extract data
				X, y = node["data"]
				depth = node["depth"]
				N, d = X.shape

				# Find feature splits that might improve loss
				did_split = False
				if self.tree_type == "classic":
					loss_best = node["loss"]
				elif self.tree_type == "m5p":
					loss_best = np.inf
				else:
					raise Exception("invalid tree_type")
				data_best = None
				polys_best = None
				j_feature_best = None
				threshold_best = None

				# Perform threshold split search only if node has not hit max depth
				if (depth >= 0) and (depth < self.max_depth):

					for j_feature in range(d):

						last_threshold = np.inf

						if self.search == 'exhaustive':
							threshold_search = X[:, j_feature]
						elif self.search == 'uniform':
							if self.samples > N:
								samples = N
							else:
								samples = self.samples
							threshold_search = np.linspace(np.min(X[:,j_feature]), np.max(X[:,j_feature]), num=samples)
						else:
							raise Exception('Incorrect search type! Must be \'exhaustive\' or \'uniform\'')

						
						# Perform threshold split search on j_feature
						for threshold in np.unique(np.sort(threshold_search)):

							# Split data based on threshold
							(X_left, y_left), (X_right, y_right) = self._split_data(j_feature, threshold, X, y)
							#print(j_feature, threshold, X_left, X_right)
							N_left, N_right = len(X_left), len(X_right)

							# Do not attempt to split if split conditions not satisfied
							if not (N_left >= self.min_samples_leaf and N_right >= self.min_samples_leaf):
								continue

							# Compute weight loss function
							if self.tree_type == "classic":
								loss_left, poly_left = _fit_poly(X_left, y_left)
								loss_right, poly_right = _fit_poly(X_right, y_right)

								loss_split = (N_left*loss_left + N_right*loss_right) / N
							elif self.tree_type == "m5p":
								loss_split = np.std(y) - (N_left*np.std(y_left) + N_right*np.std(y_right)) / N

							# Update best parameters if loss is lower
							if loss_split < loss_best:
								if self.logging: self.log.append({'event': 'best_split', 'data': {'j_feature':j_feature, 'threshold':threshold, 'loss': loss_split, 'poly_left': poly_left, 'poly_right': poly_right}})
								did_split = True
								loss_best = loss_split
								if self.tree_type == "classic": polys_best = [poly_left, poly_right]
								data_best = [(X_left, y_left), (X_right, y_right)]
								j_feature_best = j_feature
								threshold_best = threshold
	
							elif self.logging: self.log.append({'event': 'try_split', 'data': {'j_feature':j_feature, 'threshold':threshold, 'loss': loss_split, 'poly_left': poly_left, 'poly_right': poly_right}})
				
				if self.tree_type == "m5p" and did_split:
					(X_left, y_left), (X_right, y_right) = self._split_data(j_feature_best, threshold_best, X, y)
					loss_left, poly_left = _fit_poly(X_left, y_left)
					loss_right, poly_right = _fit_poly(X_right, y_right)
					loss_best = (N_left*loss_left + N_right*loss_right) / N
					polys_best = [poly_left, poly_right]

				# Return the best result
				result = {"did_split": did_split,
						  "loss": loss_best,
						  "polys": polys_best,
						  "data": data_best,
						  "j_feature": j_feature_best,
						  "threshold": threshold_best,
						  "N": N}

				return result

			def _fit_poly(X, y):

				try:
					N, d = X.shape
					myParameters = []

					for dimension in range(d):
						values = X[:,dimension]
						values_min = np.amin(values)
						values_max = np.amax(values)

						if (values_min - values_max) ** 2 < 0.01:
							myParameters.append(Parameter(distribution='Uniform', lower=values_min-0.01, upper=values_max+0.01, order=self.order))
						else: 
							myParameters.append(Parameter(distribution='Uniform', lower=values_min, upper=values_max, order=self.order))
					if self.basis == "hyperbolic-basis":
						myBasis = Basis(self.basis, orders=[self.order for _ in range(d)], q=0.5)
					else:
						myBasis = Basis(self.basis, orders=[self.order for _ in range(d)])
					container["index_node_global"] += 1
					poly = Poly(myParameters, myBasis, method=self.poly_method, sampling_args={'sample-points':X, 'sample-outputs':y}, solver_args=self.poly_solver_args)
					poly.set_model()
					
					mse = np.linalg.norm(y - poly.get_polyfit(X).reshape(-1)) ** 2 / N
				except Exception as e:
					print("Warning fitting of Poly failed:", e)
					print(d, values_min, values_max)
					mse, poly = np.inf, None

				return mse, poly
					
			def _create_node(X, y, depth, container):
				poly_loss, poly = _fit_poly(X, y)

				node = {"name": "node",
						"index": container["index_node_global"],
						"loss": poly_loss,
						"poly": poly,
						"data": (X, y),
						"n_samples": len(X),
						"j_feature": None,
						"threshold": None,
						"children": {"left": None, "right": None},
						"depth": depth}
				container["index_node_global"] += 1

				return node

			def _split_traverse_node(node, container):

				result = _splitter(node)
				if not result["did_split"]:
					self.log.append({"event": "UP"})
					return

				node["j_feature"] = result["j_feature"]
				node["threshold"] = result["threshold"]

				del node["data"]

				(X_left, y_left), (X_right, y_right) = result["data"]
				poly_left, poly_right = result["polys"]

				node["children"]["left"] = _create_node(X_left, y_left, node["depth"]+1, container)
				node["children"]["right"] = _create_node(X_right, y_right, node["depth"]+1, container)
				node["children"]["left"]["poly"] = poly_left
				node["children"]["right"]["poly"] = poly_right

				# Split nodes	
				self.log.append({"event": "DOWN", "data": {"direction": "LEFT", "j_feature": result["j_feature"], "threshold": result["threshold"]}})
				_split_traverse_node(node["children"]["left"], container)
				self.log.append({"event": "DOWN", "data": {"direction": "RIGHT", "j_feature": result["j_feature"], "threshold": result["threshold"]}})
				_split_traverse_node(node["children"]["right"], container)	
				
				self.log.append({"event": "UP"})
			container = {"index_node_global": 0}
			root = _create_node(X, y, 0, container)
			_split_traverse_node(root, container)

			return root

		N, d = X.shape
		if self.basis == "hyperbolic-basis":
			self.cardinality = Basis(self.basis, orders=[self.order for _ in range(d)], q=0.5).get_cardinality()
		else:
			self.cardinality = Basis(self.basis, orders=[self.order for _ in range(d)]).get_cardinality()
		if self.min_samples_leaf == None or self.min_samples_leaf == self.cardinality:
			self.min_samples_leaf = int(np.ceil(self.cardinality * 1.25))
		elif self.cardinality > self.min_samples_leaf:
			print("WARNING: Basis cardinality ({}) greater than the minimum samples per leaf ({}). This may cause reduced performance.".format(self.cardinality, self.min_samples_leaf))

		self.tree = _build_tree()



	def prune(self, X, y):
		"""
		Prunes the tree that you have fitted.
		
		:param numpy.ndarray X:
			Training input data
		:param numpy.ndarray y:
			Training output data
		"""

		def pruner(node, X_subset, y_subset):

			if X_subset.shape[0] < 1:
				node["test_loss"] = 0
				node["n_samples"] = 0
				return node

			node["test_loss"] = np.linalg.norm(y_subset - node["poly"].get_polyfit(X_subset).reshape(-1)) ** 2 / X_subset.shape[0]

			is_left = node["children"]["left"] != None
			is_right = node["children"]["right"] != None

			if is_left and is_right:
				(X_left, y_left), (X_right, y_right) = self._split_data(node["j_feature"], node["threshold"], X_subset, y_subset)
				
				node["children"]["left"] = pruner(node["children"]["left"], X_left, y_left)
				node["children"]["right"] = pruner(node["children"]["right"], X_right, y_right)
				
				lower_loss = ( node["children"]["left"]["test_loss"] * node["children"]["left"]["n_samples"] + node["children"]["right"]["test_loss"] * node["children"]["right"]["n_samples"] ) / ( node["children"]["left"]["n_samples"] + node["children"]["right"]["n_samples"] )

				node["lower_loss"] = lower_loss

				if lower_loss > node["test_loss"]:
					node["children"]["left"] = None
					node["children"]["right"] = None

			return node

		assert self.tree is not None, "Run fit() before prune()"
		(X_left, y_left), (X_right, y_right) = self._split_data(self.tree["j_feature"], self.tree["threshold"], X, y)

		self.tree["children"]["left"] = pruner(self.tree["children"]["left"], X_left, y_left)
		self.tree["children"]["right"] = pruner(self.tree["children"]["right"], X_right, y_right)

	def predict(self, X):
		"""
		Evaluates the the polynomial tree approximation of the data.

		:param numpy.ndarray X:
			An ndarray with shape (number_of_observations, dimensions) at which the tree fit must be evaluated at.
		:return: **y**:
			A numpy.ndarray of shape (1, number_of_observations) corresponding to the polynomial approximation of the tree.
		"""
		assert self.tree is not None
		def _predict(node, x):
			no_children = node["children"]["left"] is None and \
						  node["children"]["right"] is None

			y_pred_x = node["poly"].get_polyfit(np.array(x))[0]

			if no_children:
				return y_pred_x 
			else:
				if x[node["j_feature"]] <= node["threshold"]:
					return ( _predict(node["children"]["left"], x) * node["n_samples"] + y_pred_x * self.k ) / ( self.k + node["n_samples"] )
				else:
					return ( _predict(node["children"]["right"], x) * node["n_samples"] + y_pred_x * self.k ) / ( self.k + node["n_samples"] )
		y_pred = np.array([_predict(self.tree, np.array(x)) for x in X])
		return y_pred

	def get_graphviz(self, feature_names, file_name):
		"""
		Returns a url to the rendered graphviz representation of the tree.

		:param list feature_names:
			A list of the names of the features used in the training data
		"""
		from graphviz import Digraph
		g = Digraph('g', node_attr={'shape': 'record', 'height': '.1'})

		def build_graphviz_recurse(node, parent_node_index=0, parent_depth=0, edge_label=""):

			# Empty node
			if node is None:
				return

			# Create node
			node_index = node["index"]
			if node["children"]["left"] is None and node["children"]["right"] is None:
				threshold_str = ""
			else:
				threshold_str = "{} <= {:.3f}\\n".format(feature_names[node['j_feature']], node["threshold"])
			
			try:
				label_str = "{} n_samples = {}\\n loss = {:.6f}\\n lower_loss = {}".format(threshold_str, node["n_samples"], node["test_loss"], node["lower_loss"])
			except:
				label_str = "{} n_samples = {}\\n loss = {:.6f}".format(threshold_str, node["n_samples"], node["loss"])				
			# Create node
			nodeshape = "rectangle"
			bordercolor = "black"
			fillcolor = "white"
			fontcolor = "black"
			g.attr('node', label=label_str, shape=nodeshape)
			g.node('node{}'.format(node_index),
				   color=bordercolor, style="filled",
				   fillcolor=fillcolor, fontcolor=fontcolor)

			# Create edge
			if parent_depth > 0:
				g.edge('node{}'.format(parent_node_index),
					   'node{}'.format(node_index), label=edge_label)

			# Traverse child or append leaf value
			build_graphviz_recurse(node["children"]["left"],
								   parent_node_index=node_index,
								   parent_depth=parent_depth + 1,
								   edge_label="")
			build_graphviz_recurse(node["children"]["right"],
								   parent_node_index=node_index,
								   parent_depth=parent_depth + 1,
								   edge_label="")

		# Build graph
		build_graphviz_recurse(self.tree,
							   parent_node_index=0,
							   parent_depth=0,
							   edge_label="")

		try:
			g.render(view=True)
		except:
			file_name = file_name + ".txt"
			with open(file_name, "w") as file:
				file.write(str(g.source))
				print("GraphViz source file written to " + file_name + " and can be viewed using an online renderer. Alternatively you can install graphviz on your system to render locally")

