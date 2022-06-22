from __future__ import annotations

import typing as T
from tree.dev.treefacade import TreeFacade, TreeType

from chimaera.constant import DataUse, NodeDataKeys, NodeRefModes
from chimaera.node import ChimaeraNode

class TreeNodeDataKeys(NodeDataKeys):
	treeValue = "treeValue"
	treeProperties = "treeProperties"

class TreeNode(ChimaeraNode, TreeFacade):
	"""merging tree syntax with Chimaera
	ordering and indexing are going to be super tricky with this,
	avoid if not needed

	no checking if names are valid, no checking against duplicates
	"""

	value = ChimaeraNode.NodeParamDescriptor(TreeNodeDataKeys.treeValue)
	properties = ChimaeraNode.NodeParamDescriptor(TreeNodeDataKeys.treeProperties)

	def __call__(self, *address, create=None):
		super(TreeNode, self).__call__(*address, create)

	@property
	def parent(self) ->TreeType:
		return (self.graph().sourceNodesForUse(self, DataUse.Tree) or [None])[0]

	@property
	def branchMap(self) ->T.Dict[str, TreeType]:
		nodes = self.graph().destNodesForUse(self, DataUse.Tree)
		return {i.name : i for i in nodes}

	def setName(self, name:str):
		self.name = name

	def setValue(self, val):
		self.value = val

	def addChild(self, newBranch:TreeType) ->TreeType:
		self.graph().addNode(newBranch)
		self.graph().connectNodes(self, newBranch,
		                        fromUse=DataUse.Tree, toUse=DataUse.Tree)
		newBranch._setParent(self)
		return newBranch

	def _createChildBranch(self, name, kwargs) ->TreeType:
		return


