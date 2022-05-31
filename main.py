from __future__ import annotations
import networkx as nx
from weakref import WeakSet
import typing as T

from .nodedata import NodeDataHolder, NodeDataTree
from .constant import NodeDataKeys, DataUse
from .graphdata import SubgraphData
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

	def nodeData(self, node:ChimaeraNode):
		"""retrieve or resolve the final params object for given node"""
		if not self.predecessors(node):
			return node.baseParams

		# node i reference or result of transform chain
		data = node.baseParams
		for inputNode in self.predecessors(node):
			data = inputNode.transformData(data)

		# apply any override params set on the node itself to result params
		data = node.applyOverride(data)
		return data

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
	                 fromUse=DataUse.Flow, toUse=DataUse.Flow):
		"""edge keys are always destination uses, since the graph mainly looks back"""
		return self.add_edge(fromNode, toNode, key=toUse, fromUse=fromUse, toUse=toUse)

	def flowSource(self, node:ChimaeraNode)->ChimaeraNode:


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
		subgraphData = SubgraphData.fromChimaeraSubgraph(subgraph)


	def nodeValid(self, node)->bool:
		return node in self.nodes





