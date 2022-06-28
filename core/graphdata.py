from __future__ import annotations

from dataclasses import dataclass
import typing as T

import networkx as nx

from tree import FailToFind
from tree.lib.sequence import flatten
from tree.lib.uid import toUid
from .nodedata import NodeDataTree

if T.TYPE_CHECKING:
	from .node import ChimaeraNode


@dataclass
class GraphData:
	"""data object representing node or subgraph of nodes within a reference
	or transform pipeline

	this is also the only format in which any kind of params
	may pass through the graph between nodes
	"""
	# datas for nodes contained in subgraph - may be any format of tree, from any use
	nodeDatas : list[NodeDataTree] = ()

	# tuples of edges of those nodes' uids
	edges : set[tuple[str, str]] = ()

	@classmethod
	def fromChimaeraSubgraph(cls, subgraph:nx.Graph)->GraphData:
		datas = []
		for node in subgraph: #type:ChimaeraNode
			datas.append(node.baseParams)
		edges = {(i[0].uid, i[1].uid) for i in subgraph.edges}
		return cls(datas, edges)


	def __post_init__(self):
		"""build a map of {treeUid : tree} from nodeDatas
		if the same uid is used for multiple data uses, this will be insufficient -
		should GraphData know about DataUse for each tree?
		"""
		self.nodeDatas = self.nodeDatas or []
		self.uidTreeMap = {toUid(nodeData): nodeData for nodeData in self.nodeDatas}


	def __getitem__(self, item:(str, ChimaeraNode, NodeDataTree))->NodeDataTree:
		"""get node data tree by uid or node object"""
		return self.uidTreeMap[toUid(item)]

	def get(self, key:(str, ChimaeraNode, NodeDataTree), default=None)->NodeDataTree:
		"""get node data tree by uid or node object"""
		result = self.uidTreeMap.get(toUid(key), FailToFind)
		return default if result is FailToFind else result

	def resultGraph(self, graphCls=nx.DiGraph)->nx.DiGraph:
		"""return a result nx graph object built from this params
		result is graph of uid strings, not active node objects
		"""
		newGraph = graphCls()
		for uid, trees in self.nodeDatas.items():
			newGraph.add_node(uid)
		newGraph.add_edges_from(self.edges)
		return newGraph

	@classmethod
	def combine(cls, *graphDatas:T.Sequence[(GraphData, NodeDataTree)]):
		"""initialise new graph data object from arbitrary inputs"""
		datas = []
		edges = set()
		#print("combine", tuple(graphDatas), graphDatas)

		graphDatas = flatten(graphDatas)
		#print("combine", tuple(graphDatas), graphDatas)
		for i in graphDatas:
			#print("i", i)
			if isinstance(i, GraphData):
				datas.extend([i.copy() for i in i.nodeDatas])
				edges.update(i.edges)
			elif isinstance(i, NodeDataTree):
				datas.append(i.copy())
		return cls(datas, set(edges))
