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
from chimaera.ui.delegate.node import NodeDelegate
from chimaera.ui.delegate.knob import Knob
from chimaera.ui.delegate.abstract import GraphItemDelegateAbstract, AbstractNodeContainer, ConnectionPointGraphicsItemMixin

if T.TYPE_CHECKING:
	from chimaera.ui.scene import ChimaeraGraphScene
	from chimaera.ui import graphItemType

class PlugNodeDelegate(NodeDelegate):
	"""consider leaving connection points at top and bottom to show tree hierarchy"""

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
				nodePlugs = i.inPlug.allBranches() + i.outPlug.allBranches() + [i]

				# gather any edges between them
				internalEdges = scene.graph().edges(nodePlugs, keys=True)
				itemPool.difference_update(nodePlugs)
				itemPool.difference_update(internalEdges)


		return result

	def __init__(self, node:PlugNode, parent=None):
		super(PlugNodeDelegate, self).__init__(node, parent)
		self.inPlugDelegate = PlugTreeDelegate(node.inPlug, parent=self)
		self.outPlugDelegate = PlugTreeDelegate(node.outPlug, parent=self)


		for i in (self.inPlugDelegate, self.outPlugDelegate):
			i.arrange()
			pass

		self.sync()


	def makeKnobs(self) ->dict[str, dict[DataUse, Knob]]:
		"""leave only tree hierarchy plugs"""
		return {
			"in": {
				DataUse.Tree : Knob(self.node, DataUse.Tree, isOutput=False,
				                    parent=self),
				},
			"out": {
				DataUse.Tree: Knob(self.node, DataUse.Tree, isOutput=True,
				                   parent=self),
			}
		}

	def arrange(self):

		self.inPlugDelegate.setPos(self.boundingRect().left() - self.inPlugDelegate.childrenBoundingRect().width(), self.detailHeightLevel())
		self.outPlugDelegate.setPos(self.boundingRect().right(), self.detailHeightLevel())

		self.arrangeKnobs()


	def instanceDelegatesForElements(self, scene:ChimaeraGraphScene, itemPool:set[graphItemType]) ->T.Sequence[GraphItemDelegateAbstract]:
		"""check for any internal node edges, remove them from consideration"""
		result = []
		nodePlugs = self.node.inPlug.allBranches() + self.node.outPlug.allBranches() + [self.node]
		# gather any edges between them
		internalEdges = scene.graph().edges(nodePlugs, keys=True)
		itemPool.difference_update(nodePlugs)
		itemPool.difference_update(internalEdges)
		return result

	pass

