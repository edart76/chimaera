from __future__ import annotations
"""the bazooka to end all mosquitoes

wrapping a Chimaera graph in tree syntax to allow referencing 

actual compatibility between normal trees and graph trees is out of the question,
and always, always will be

"""

import typing as T

from tree import TreeInterface, TreeType
from tree.lib.sequence import firstOrNone

from .constant import NodeDataKeys, NodeRefModes, DataUse
from .nodedata import NodeDataTree
from .graphdata import GraphData
from .node import ChimaeraNode
if T.TYPE_CHECKING:
	from .graph import ChimaeraGraph


class GraphTree(TreeInterface, ChimaeraNode):
	"""wrapping chimaera node and its relatives in tree syntax"""

	#graph = TreeInterface.TreePropertyDescriptor()

	def __init__(self, name=None, graph:ChimaeraGraph=None, nodeDataArgs:NodeDataTree=None):
		ChimaeraNode.__init__(self, graph=None, nodeParams=None)

	# at lowest level, changes to node name need to be funnelled into chimaera node params
	@property
	def _name(self)->str:
		return self.getParam(NodeDataKeys.nodeName)

	def _setName(self, name:str):
		"""set node's name on internal Params data"""
		self.setParam(NodeDataKeys.nodeName, name)

	@property
	def value(self):
		return self.getParam(NodeDataKeys.treeValue)

	def _setValue(self, value):
		self.setParam(NodeDataKeys.treeValue, value)

	@property
	def parent(self)->TreeType:
		return self._parent

	@property
	def _parent(self)->TreeType:
		return firstOrNone(self.graph.sourceNodesForUse(self, DataUse.Tree))


	@_parent.setter
	def _parent(self, newParent:GraphTree=None):
		"""set input on this node - rely on parent remove() function to ensure that
		connections between nodes are unique?"""
		self.connectTreeNodes(newParent, self)


	@staticmethod
	def connectTreeNodes(parentNode:GraphTree, childNode:GraphTree, newIndex=-1):
		"""single function to connect tree nodes uniquely
		this might be better off in a lib or something"""
		graph = parentNode.graph
		oldParent = childNode._parent
		if oldParent is not None:
			# remove existing edge
			graph.remove_edge(oldParent, childNode, key=DataUse.Tree)
		# add new edge
		graph.add_edge(parentNode, childNode, key=DataUse.Tree, index=newIndex)

	@property
	def branchMap(self)-> dict[str, TreeType]:
		"""collect child nodes from graph"""
		nodes = self.graph.destNodesForUse(self, DataUse.Tree)
		# sort by edge indices
		sortedNodes = []
		edges = self.graph.edges
		for i in nodes:
			index = self.graph.edges[self, i, DataUse.Tree]["index"]
			sortedNodes.insert(index, i)
		return {i.name : i for i in sortedNodes}


