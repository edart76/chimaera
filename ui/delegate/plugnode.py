from __future__ import annotations
"""delegate for drawing full plug node"""

import typing as T

import networkx as nx
from chimaera.core.node import ChimaeraNode
from chimaera.plugtree import PlugTree
from chimaera.plugnode import PlugNode
from chimaera.constant import INPUT_NAME, OUTPUT_NAME, DataUse, DataType

from PySide2 import QtCore, QtWidgets, QtGui
from chimaera.ui.delegate.plugtree import PlugTreeDelegate
from chimaera.ui.delegate.node import NodeDelegate, GraphItemDelegateAbstract

if T.TYPE_CHECKING:
	from chimaera.ui.scene import ChimaeraGraphScene
	from chimaera.ui import graphItemType

class PlugNodeDelegate(NodeDelegate):

	delegatePriority = 1

	@classmethod
	def delegatesForElements(cls, scene:ChimaeraGraphScene, itemPool:set[graphItemType]) ->T.Sequence[GraphItemDelegateAbstract]:
		"""gather any plug nodes -
		remove node, plugs of node, and edges connecting node and plugs"""
		result = []
		for i in set(itemPool):
			if isinstance(i, PlugNode):
				result.append(cls(i))
				itemPool.remove(i)

				# gather plugs
				nodePlugs = i.inPlug.allBranches() + i.outPlug.allBranches()

				# gather any edges between them
				internalEdges = i.containedPlugEdges()
				itemPool.difference_update(nodePlugs)
				itemPool.difference_update(internalEdges)

		return result

	def __init__(self, node:PlugNode, parent=None):
		super(PlugNodeDelegate, self).__init__(node, parent)
		self.inPlugDelegate = PlugTreeDelegate(node.inPlug, parent=self)
		self.outPlugDelegate = PlugTreeDelegate(node.outPlug, parent=self)

		self.outPlugDelegate.setPos(self.boundingRect().width(), 0)


	pass

