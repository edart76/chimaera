from __future__ import annotations
import networkx as nx
from weakref import WeakSet
import typing as T

from tree.lib.sequence import flatten

from .nodedata import NodeDataHolder, NodeDataTree
from .constant import NodeDataKeys, DataUse
from .graphdata import GraphData
from .node import ChimaeraNode
from .transform import TransformNode
from .edgeset import EdgeSet, EdgeSetData
from chimaera.lib.delta import GraphNodeDelta, GraphEdgeDelta, GraphDeltaSignalComponent, GraphDeltaTracker

CREATED_BY_KEY = "createdBy" # key for edge to node that created this one


class ChimaeraGraph(nx.MultiDiGraph):
	"""uber holder for all edge sets and nodes
	A CHIMAERA GRAPH MAY NOT BE REFERENCED
	edge sets can be though

	a single node may not know what edgeset it is included in

	consider that a total adherence to this system may not be necassary?

	can the same node be referenced with deltas under one edge set,
	but not another?
	If that were so, a node may return different params() results depending on which
	edge sets are active - maybe this could be useful?

	should an active node object be specific to an edge set?
	may 2 active nodes point to the same node params?

	edgeSet concept is cool but not really compatible with networkX

	node evaluation goes like this:

	node.outputDataForUse() -> graph.incomingDataForUse



	"""

	def __init__(self):
		super(ChimaeraGraph, self).__init__()
		self.signalComponent = GraphDeltaSignalComponent(self)
		self.deltaTracker = GraphDeltaTracker()

	def uidNodeMap(self)->dict[str, ChimaeraNode]:
		return {i.uid : i for i in self}

	def node(self, fromId:(NodeDataTree, str, ChimaeraNode))->ChimaeraNode:
		"""retrieve a node"""
		uid = fromId if isinstance(fromId, str) else fromId.uid
		return self.uidNodeMap()[uid]

	def createNode(self, name:str, nodeCls=ChimaeraNode, add=True):
		"""creates new node and params"""
		dataTrees = NodeDataTree.createParamTree(name)
		node = nodeCls(self, dataTrees)
		if add:
			self.addNode(node)
		return node

	def addNode(self, node:ChimaeraNode):
		"""assumes nodes are unique per node params"""
		#self.nodeMap[node.baseParams] = node
		self.add_node(node)

	def removeNode(self, node:(ChimaeraNode, NodeDataHolder)):
		self.remove_node(node)

	# connecting nodes
	def connectNodes(self, fromNode:ChimaeraNode, toNode:ChimaeraNode,
	                 fromUse=DataUse.Flow, toUse=DataUse.Flow,
	                 index=None):
		"""edge keys are always destination uses, since the graph mainly looks back"""
		return self.add_edge(fromNode, toNode, key=toUse, fromUse=fromUse, toUse=toUse, index=index)


	# querying nodes by edges
	# def _nodeEdgeMap(self, node: ChimaeraNode, edgeFn:T.Callable) -> dict[DataUse, list[tuple[DataUse, ChimaeraNode]]]:
	#

	def nodeInputMap(self, node:ChimaeraNode)->dict[DataUse, dict[ DataUse, ChimaeraNode]]:
		"""todo: add processing for edge indices here
		leaves are dicts of [fromUse, node] - allowing item[0].outputDataForUse(item[1])
		"""
		nodeEdges = self.in_edges([node], keys=True, data=True)
		nodeMap = {}
		for i in DataUse:
			nodeTies = {}
			for edge in nodeEdges:
				if edge[2] != i:
					continue
				nodeTies[edge[3]["fromUse"]] = edge[0]
			nodeMap[i] = nodeTies
		return nodeMap

	def nodeOutputMap(self, node:ChimaeraNode)->dict[DataUse, dict[ DataUse, ChimaeraNode]]:
		"""return the output nodes for uses"""
		nodeEdges = self.out_edges([node], keys=True, data=True)
		nodeMap = {}
		for i in DataUse:
			nodeTies = {}
			for edge in nodeEdges:
				if edge[2] != i:
					continue
				nodeTies[edge[3]["toUse"]] = edge[1]
			nodeMap[i] = nodeTies
		return nodeMap

	# getting node data - unsure of what to defer to node here
	def nodeOutputDataForUse(self, node:ChimaeraNode, use:DataUse)->GraphData:
		"""return a node's data for a given DataUse"""
		return node.outputDataForUse(use)

	def incomingDataForUse(self, node:ChimaeraNode, use:DataUse)->GraphData:
		"""gathers all incoming data from input nodes for given use"""
		inTies = self.nodeInputMap(node)[use]
		outputData = [self.nodeOutputDataForUse(inputNode, inputUse) for inputUse, inputNode in inTies.items()]
		return GraphData.combine(outputData)

	def sourceNodesForUse(self, node:ChimaeraNode, use:DataUse)->set[ChimaeraNode]:
		return set(self.nodeInputMap(node)[use].values())

	def destNodesForUse(self, node:ChimaeraNode, use:DataUse)->set[ChimaeraNode]:
		return set(self.nodeOutputMap(node)[use].values())


	def addReferenceToNode(self, baseNode:ChimaeraNode, name=None):
		"""create a new node and set it to the given node as input"""
		newNode = self.createNode(name or baseNode.name(), nodeCls=type(baseNode), add=True)
		self.add_edge(baseNode, newNode)

	def createMultiReference(self, nodesToReference:T.Sequence[ChimaeraNode],
	                         refNodeName="refGraph")->ChimaeraNode:
		"""test for making multi references easier to handle -
		edges are added from all given nodes to refnode, if necessary
		we can add attributes to identify these apart from normal references

		a subgraph section is routed through the single reference node,
		which can then be expanded again to an image of the original full graph
		"""
		refNode = self.createNode(refNodeName)
		for i in nodesToReference:
			self.add_edge(i, refNode)
		return refNode

		subgraph = self.subgraph(nodesToReference)
		subgraphData = GraphData.fromChimaeraSubgraph(subgraph)


	def nodeValid(self, node)->bool:
		return node in self.nodes

	# signal setup
	def onParamsChanged(self, node:ChimaeraNode):
		"""fires when direct params changed on node -
		won't work on references"""


	# state, deltas and signals
	# this is made mode cumbersome by needing to inherit from external type
	# redefine superclass methods as "internals", redefine facade methods to emit deltas


