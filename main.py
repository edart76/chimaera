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

	Keep it simple for now -
		ONE TreeEdgeSet for hierarchy,
		ONE DependEdgeSet for referencing,
		ONE DependEdgeSet for normal graph dependency?

	node evaluation goes like this:

	node.outputDataForUse() -> graph.incomingDataForUse



	"""

	def __init__(self):
		super(ChimaeraGraph, self).__init__()
		#self.nodeMap : dict[NodeDataHolder, ChimaeraNode] = {}
		# self.edgeSetMap : dict[NodeData, SetNode] = {}
		#self.datas : dict[str, NodeData]

	def uidNodeMap(self)->dict[str, ChimaeraNode]:
		return {i.uid : i for i in self}

	def node(self, fromId:(NodeDataTree, str, ChimaeraNode))->ChimaeraNode:
		"""retrieve a node"""
		uid = fromId if isinstance(fromId, str) else fromId.uid
		return self.uidNodeMap()[uid]

	# def nodeData(self, node:ChimaeraNode):
	# 	"""retrieve or resolve the final params object for given node"""
	# 	if not self.predecessors(node):
	# 		return node.baseParams
	#
	# 	# node i reference or result of transform chain
	# 	data = node.baseParams
	# 	for inputNode in self.predecessors(node):
	# 		data = inputNode.transformData(data)
	#
	# 	# apply any override params set on the node itself to result params
	# 	data = node.applyOverride(data)
	# 	return data

	def createNode(self, name:str, nodeCls=ChimaeraNode, add=True):
		"""creates new node and params"""
		dataTrees = NodeDataTree.createDataAndOverrideTrees(name)
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
	                 inputIndex=None):
		"""edge keys are always destination uses, since the graph mainly looks back"""
		return self.add_edge(fromNode, toNode, key=toUse, fromUse=fromUse, toUse=toUse, inputIndex=inputIndex)

	# getting node data - unsure of what to defer to node here
	def nodeOutputDataForUse(self, node:ChimaeraNode, use:DataUse)->GraphData:
		"""return a node's data for a given DataUse"""
		return node.outputDataForUse(use)

	# querying nodes by edges
	def nodeInputMap(self, node:ChimaeraNode)->dict[DataUse, list[tuple[DataUse, ChimaeraNode]]]:
		"""todo: add processing for edge indices here
		leaves are tuples of [fromUse, node] - allowing item[0].outputDataForUse(item[1])
		"""
		nodeEdges = self.in_edges(node, keys=True, data=True)
		nodeMap = {}
		for i in DataUse:
			nodeTies = []
			for edge in nodeEdges:
				if edge[2] != i:
					continue
				nodeTies.append( (edge[0], edge[3]["fromUse"]))
			nodeMap[i] = nodeTies
		return nodeMap

	def incomingDataForUse(self, node:ChimaeraNode, use:DataUse)->GraphData:
		"""gathers all incoming data from input nodes for given use"""
		inTies = self.nodeInputMap(node)[use]
		print("inTies", inTies)
		print([self.nodeOutputDataForUse(i[0], i[1]) for i in inTies])
		return GraphData.combine([self.nodeOutputDataForUse(i[0], i[1]) for i in inTies])


	def flowSources(self, node:ChimaeraNode)->list[ChimaeraNode]:
		self.edges


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





