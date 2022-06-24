from __future__ import annotations

"""node topology functions"""

import typing as T
from itertools import product, chain, combinations
import networkx as nx



from chimaera import ChimaeraNode

if T.TYPE_CHECKING:
	from chimaera import ChimaeraGraph

def rootsEnds(graph:ChimaeraGraph, nodes:set[ChimaeraNode]):
	"""generate (roots, ends) for the given graph"""
	return ([i for i in nodes if graph.in_degree(i) == 0],
	        [i for i in nodes if graph.out_degree(i) == 0])

def nodesBetween(graph, nodeSet:T.Sequence[ChimaeraNode], inclusive=True)->set[ChimaeraNode]:
	"""get all nodes included between extremities of given node set"""
	nodeSet = set(nodeSet)
	roots, ends = rootsEnds(graph, nodeSet)
	resultSet = set(nodeSet)
	for (source, target) in product(roots, ends):
		allPaths = nx.all_simple_paths(graph, source=source, target=target)
		for pathSeq in allPaths:
			resultSet.update(set(pathSeq))
	if not inclusive:
		resultSet = resultSet - nodeSet
	return resultSet

def _setIndexBranchSafe(indexMap:dict, index, node, graph:ChimaeraGraph):
	if node in indexMap.values():
		return index
	for i in graph.predecessors(node):
		# capture changes to index made on each node
		index = _setIndexBranchSafe(indexMap, index, i, graph)
	indexMap[index] = node
	index += 1
	return index


def orderNodes(graph:ChimaeraGraph, nodeSet:T.Sequence[ChimaeraNode])->list[ChimaeraNode]:
	"""given graph and arbitrary set of node, sort them such that each executes
	before its dependents"""
	roots, ends = rootsEnds(graph, nodeSet)
	between = nodesBetween(graph, nodeSet, inclusive=True)
	index = 0
	indexMap = {}
	for i in nodeSet:
		index = _setIndexBranchSafe(indexMap, index, i, graph)
	return [indexMap[i] for i in range(len(indexMap))]



