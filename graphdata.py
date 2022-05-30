from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
from .node import ChimaeraNode
from .nodedata import NodeDataTree


@dataclass
class SubgraphData:
	"""data representing subgraph of nodes within a reference
	or transform pipeline

	this is also (maybe) the only format in which any kind of data
	may pass through the graph between nodes
	"""
	# datas for nodes contained in subgraph
	nodeDatas : dict[str, tuple[NodeDataTree, NodeDataTree]] = None

	# tuples of edges of those nodes' uids
	edges : set[tuple[str, str]] = None

	@classmethod
	def fromChimaeraSubgraph(cls, subgraph:nx.Graph)->SubgraphData:
		datas = {}
		for node in subgraph: #type:ChimaeraNode
			datas[node.uid] = (node.baseData, node.overrideData)
		edges = {(i[0].uid, i[1].uid) for i in subgraph.edges}
		return cls(datas, edges)

	def resultGraph(self, graphCls=nx.DiGraph)->nx.DiGraph:
		"""return a result nx graph object built from this data
		result is graph of uid strings, not active node objects
		"""
		newGraph = graphCls()
		for uid, trees in self.nodeDatas.items():
			newGraph.add_node(uid)
		newGraph.add_edges_from(self.edges)
		return newGraph
