from __future__ import annotations
import networkx as nx
import typing as T
from dataclasses import dataclass, field
from weakref import WeakSet, WeakKeyDictionary, proxy
from networkx import Graph, DiGraph, MultiDiGraph

from .node import ChimaeraNode
from .nodedata import NodeDataHolder

if T.TYPE_CHECKING:
	from .main import ChimaeraGraph

@dataclass
class EdgeSetData(NodeDataHolder):
	nodeUids : set[str] = field(default_factory=set)
	edgeTies: set[tuple[str, str]] = field(default_factory=set)


class EdgeSet(ChimaeraNode, Graph
              ):
	"""set of chimaera edges drawn over persistent nodes
	edge sets are also nodes, which can be overridden

	using networkX stops nodes from being held in weak sets,
	which on balance is ok
	"""

	nodeTypeId = 2

	def __init__(self, semGraph:ChimaeraGraph, nodes:T.Sequence[ChimaeraNode]=()):
		super(EdgeSet, self).__init__(semGraph)
		Graph.__init__(self)
		#self.nodes : set[SetNode] = WeakSet(*nodes)
		if nodes:
			self.add_nodes_from(nodes)

	def syncGraphNodes(self,
	                   masterNodeSet: set,
	                   addMissing=True, removeTrailing=False,
	                   ):
		"""ensure that driven graph contains the given nodes
		if addMissing, any missing nodes """


	def addNodes(self, nodes:T.Sequence):
		"""any edge-set-specific logic to add a node"""
		for i in nodes:
			self.add_node(i)

	def removeNodes(self, nodes:T.Sequence):
		"""any edge-set-specific logic to add a node"""
		for i in nodes:
			self.remove_node(i)


class DependEdgeSet(ChimaeraNode, Graph):
	def __init__(self, semGraph:ChimaeraGraph, nodes:T.Sequence[ChimaeraNode]=()):
		super(DependEdgeSet, self).__init__(semGraph)
		Graph.__init__(self)
		#self.nodes : set[SetNode] = WeakSet(*nodes)
		if nodes:
			self.add_nodes_from(nodes)


