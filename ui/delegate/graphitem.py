
from __future__ import annotations

"""base class for any visual element representing any 'thing' in
chimaera graph

this is used as some drawing items may encompass multiple
individual graph nodes
"""

import typing as T
from PySide2 import QtCore, QtWidgets, QtGui

from tree import TreeWidget
from tree.ui.lib import AllEventEater
from tree.ui.atomicwidget import AtomicWidget, StringWidget
from tree.ui.libwidget.atomicproxywiget import AtomicProxyWidget

#from treegraph.node import GraphNode
from chimaera import ChimaeraGraph, ChimaeraNode
from chimaera.constant import DataUse
from chimaera.ui.base import GraphicsItemChange
from chimaera.ui import graphItemType
if T.TYPE_CHECKING:
	from chimaera.ui.scene import ChimaeraGraphScene

#class GraphItemDelegateBase()

class GraphItemDelegateAbstract:
	""" drawing for individual elements representing bits of chimaera graph
	this is an abstract class for multiple inheritance - might split out
	the logic part and the drawing part still
	 """

	delegatePriority = 0 #zero is lowest, any higher will be evaluated first

	# some complex delegates may gather new items as those items are created -
	# check first among existing delegate instances, then among delegate classes
	# instance check order is also controlled by priority above
	instancesMayCreateDelegates = False

	def __init__(self, graphItems:T.Sequence[graphItemType]=None, # parent=None,
	             ):
		self.graphItems = list(graphItems)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
		# try:
		# 	super(GraphItemDelegate, self).__init__(parent)
		# except: # multiple inheriat
		# 	pass



	# @classmethod
	# def itemsToDrawFromPool(cls, itemPool:set[ChimaeraNode, tuple]):
	# 	pass

	def instanceDelegatesForElements(self, scene:ChimaeraGraphScene, itemPool:set[graphItemType])->T.Sequence[GraphItemDelegateAbstract]:
		"""allow this instance to create delegates for new items in item pool - for
		example child items, new plugs on a tree node, etc
		make sure to remove the items from the pool as they are created"""
		return []

	@classmethod
	def delegatesForElements(cls, scene:ChimaeraGraphScene, itemPool:set[graphItemType])->T.Sequence[GraphItemDelegateAbstract]:
		"""delegatesForElements for each registered drawing class is passed item pool
		of all nodes and edges in the graph -
		to draw an item, remove it from the set and assign a new delegate object to it
		itemSet is mutable
		"""
		raise NotImplementedError

	def mainGraphElement(self)->graphItemType:
		"""return the main graph element representing this item - if this item
		is removed from chimaera graph, the main delegate is deleted"""
		return self.graphItems[0]

	def scene(self) -> ChimaeraGraphScene:
		return super(GraphItemDelegateAbstract, self).scene()

	@property
	def width(self):
		return self.boundingRect().width()

	@property
	def height(self):
		return self.boundingRect().height()

	def itemChange(self, change:QtWidgets.QGraphicsItem.GraphicsItemChange, value):
		""" pass signal to scene whenever this item is changed"""
		if self.scene():
			self.scene().itemChanged.emit(GraphicsItemChange(self, change, value))
		return super(GraphItemDelegateAbstract, self).itemChange(change, value)

	def sync(self, *args, **kwargs):
		raise NotImplementedError

	def onSceneItemChange(self, change:GraphicsItemChange):
		if change.item is self:
			return

	def onSceneSelectionChanged(self):
		pass

	def serialise(self):
		"""save position in view"""
		return {
			"pos" :	(self.pos().x(), self.pos().y()),
			}






