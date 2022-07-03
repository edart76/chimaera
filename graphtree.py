from __future__ import annotations
"""the bazooka to end all mosquitoes

wrapping a Chimaera graph in tree syntax to allow referencing 

actual compatibility between normal trees and graph trees is out of the question,
and always, always will be

"""

import typing as T

from tree import TreeInterface, TreeType
from tree.lib.sequence import firstOrNone

from .constant import NodeDataKeys, DataUse
from chimaera.core.nodedata import NodeDataTree
from chimaera.core.node import ChimaeraNode
#if T.TYPE_CHECKING:
from chimaera.core.graph import ChimaeraGraph

TreeType = T.TypeVar("TreeType", bound="GraphTree") # type of the current class

class GraphTree(TreeInterface, ChimaeraNode):
	"""wrapping chimaera node and its relatives in tree syntax"""

	branchesInheritType = True # big old yes

	@classmethod
	def defaultParamTree(cls, name:str, uid=None)->NodeDataTree:
		"""default parametre format for this type of node
		add params for each of tree's attributes"""
		dataTree = NodeDataTree(name="root", treeUid=uid)
		dataTree.lookupCreate = True
		dataTree.nodeName = name

		# add value and properties
		dataTree(NodeDataKeys.treeValue).value = None
		dataTree(NodeDataKeys.treeProperties).value = {}

		#print("defaultParamTree", dataTree.displayStr())

		return dataTree

	@classmethod
	def create(cls, name:str, uid=None, graph:ChimaeraGraph=None)->ChimaeraNode:
		"""create a new node of this type"""
		nodeParams = cls.defaultParamTree(name, uid)
		#print("cls", cls, nodeParams.displayStr(), cls.create, cls.defaultParamTree)
		return cls(name,
		           treeUid=uid,
		           graph=graph,
		           nodeParams=nodeParams)


	def __init__(self, name:str, value=None,
	             treeUid=None,
	             graph:ChimaeraGraph=None, nodeParams:NodeDataTree=None):

		# coupled dependency here to allow creation of trees in isolation
		# can remove if needed
		if graph is None:
			from chimaera.core.graph import ChimaeraGraph
			graph = ChimaeraGraph()

		nodeParams = nodeParams or self.defaultParamTree(name, uid=treeUid)
		ChimaeraNode.__init__(self, graph, nodeParams)

		graph.addNode(self)
		self.setGraph(graph)

		#print("before tree init", self.params().serialise())

		TreeInterface.__init__(self, name, value)

	def graph(self)->ChimaeraGraph:
		"""too complicated making this an inherited property (when
		we need to use the graph to determine inheritance) -
		update it on _setParent()
		"""
		return self._graph


	# at lowest level, changes to node name need to be funnelled into chimaera node params
	@property
	def _name(self)->str:
		return self.getParam(NodeDataKeys.nodeName)
	@_name.setter
	def _name(self, name:str)->str:
		self._setName(name)

	def _setName(self, name:str):
		"""set node's name on internal Params data"""
		self.setParam(NodeDataKeys.nodeName, name)

	@property
	def _value(self):
		return self.getParam(NodeDataKeys.treeValue)

	@_value.setter
	def _value(self, value):
		self._setValue(value)


	def _setValue(self, value):
		self.setParam(NodeDataKeys.treeValue, value)

	@property
	def parent(self)->TreeType:
		return self._parent

	@property
	def _parent(self)->TreeType:
		return firstOrNone(self.graph().sourceNodesForUse(self, DataUse.Tree))

	@_parent.setter
	def _parent(self, parent:GraphTree):
		if parent is None:
			return
		self._setParent(parent)

	@staticmethod
	def connectTreeNodes(parentNode:GraphTree, childNode:GraphTree, newIndex=-1):
		"""single function to connect tree nodes uniquely
		this might be better off in a lib or something"""
		graph = parentNode.graph()
		if graph is childNode.graph():
			oldParent = childNode._parent
			if oldParent is not None:
				# remove existing edge
				graph.remove_edge(oldParent, childNode, key=DataUse.Tree)
		# add new edge
		graph.connectNodes(parentNode, childNode,
		                   fromUse=DataUse.Tree, toUse=DataUse.Tree,
		                   index=newIndex)


	@property
	def branchMap(self)-> dict[str, TreeType]:
		"""collect child nodes from graph"""
		#nodes = self.graph().destNodesForUse(self, DataUse.Tree)
		nodes = self.graph().nodeOutputsFromUse(self, fromUse=DataUse.Tree, includeToUse=False)
		# sort by edge indices
		sortedNodes = []
		edges = self.graph().edges
		for i in nodes:
			index = self.graph().edges[self, i, DataUse.Tree]["index"]
			sortedNodes.insert(index, i)
		return {i.name : i for i in sortedNodes}


	def _ownIndex(self) ->int:
		if self.parent:
			return self.graph().edges[self.parent, self, DataUse.Tree]["index"]
		return 0


	def _fixUpIndices(self):
		"""plaster method to ensure indices on edges are valid
		might instead store indices on nodes, not sure it makes much difference"""
		outEdges = self.graph().out_edges(self, key=DataUse.Tree, data=True )
		indexPool = sorted(outEdges, key="index")
		for i, val in enumerate(indexPool):
			val["index"] = i


	def _addChild(self, newBranch:GraphTree, index:int) ->TreeType:
		"""add node to graph if necessary
		then connect nodes"""
		if not newBranch in self.graph():
			self.graph().addNode(newBranch)

		newBranch._setParent(self, index)

		return newBranch

	def _setParent(self, parentBranch:GraphTree, index=-1):
		super(GraphTree, self)._setParent(parentBranch)
		self.connectTreeNodes(parentBranch, self, index)
		self.setGraph(parentBranch.graph())

	def _remove(self, branch:GraphTree):
		"""break edge between this node and branch"""
		edge = self.graph().remove_edge(self, branch, DataUse.Tree)

	@property
	def properties(self) ->dict:
		return self.getParam(NodeDataKeys.treeProperties)
