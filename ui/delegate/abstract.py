from __future__ import annotations

from chimaera.ui import graphItemType
from chimaera.ui.base import GraphicsItemChange


"""abstract mixin classes defining logic and inheritance for drawing in chimaera graph scene
"""
from collections import defaultdict
from enum import Enum
from tree import Tree
from tree.lib.object import UidElement
#from tree.lib.object import ExEnum
from chimaera import ChimaeraGraph, ChimaeraNode, DataUse, DataType

import typing as T
if T.TYPE_CHECKING:
	from chimaera.ui.scene import ChimaeraGraphScene

from PySide2 import QtCore, QtWidgets, QtGui



class ConnectionPointGraphicsItemMixin( # type hinting
	*((UidElement, QtWidgets.QGraphicsRectItem) if T.TYPE_CHECKING else (UidElement, ))
                                       ):
	"""mixin for graphics items that provide
	 connection points - does not itself track connected items
	 """

	# class VisualConnectionReceptivity(Enum):
	# 	"""enum for visual connection receptivity - change drawing state
	# 	when user is dragging possible edge to connect"""
	# 	NotReceptive = 0
	# 	Receptive = 0

	class VisualConnectionState(Enum):
		NotConnected = 0
		Connected = 1


	ns = Tree("namespace")
	ns.default = lambda tree, key: {}

	def __init__(self, uid=None):
		UidElement.__init__(self, uid)
		self.receptiveToConnections = True
		self.connected = False

	def connectionPosition(self)->QtCore.QPoint:
		"""return position of connection point in relative coords"""
		return self.boundingRect().center()

	def connectionDirection(self)->QtCore.QPoint:
		"""return vector direction for lines connected to this point"""
		return QtCore.QPoint(0, 1)

	# def connectedElements(self, nsKey=None):
	# 	ns = self.ns(nsKey) if nsKey is not None else self.ns
	# 	return ns.v.get(self.uid, [])

	def acceptsConnection(self, sourcePoint:ConnectionPointGraphicsItemMixin)->bool:
		"""returns true if this item can connect to the given point"""
		return False

	def addConnectionToPoint(self, otherPoint:ConnectionPointGraphicsItemMixin):
		raise NotImplementedError()


	def setReceptiveToConnections(self, state=True):
		self.receptiveToConnections = state
		self.sync()

	def setConnected(self, state=True):
		"""set visual state to connected or not"""
		self.connected = state
		self.sync()
		pass

	def sync(self):
		"""sync visual state with internal state"""
		pass


class ConnectionPointSceneMixin(
	QtWidgets.QGraphicsScene if T.TYPE_CHECKING else object):

	def __init__(self):
		self.connectionPointItemMap : defaultdict[ConnectionPointGraphicsItemMixin, list[QtWidgets.QGraphicsItem]] = defaultdict(list)


	def connectionPoints(self)->list[ConnectionPointGraphicsItemMixin]:
		"""likely just iterate over all items in scene and pick out the ones
		that define connection points"""
		# duck typing more like suck typing
		return [i for i in self.items() if isinstance(i, ConnectionPointGraphicsItemMixin)]

	def addConnection(self, fromPoint:ConnectionPointGraphicsItemMixin,
	                  toItem:QtWidgets.QGraphicsItem):
		self.connectionPointItemMap[fromPoint].append(toItem)

	def removeConnection(self, fromPoint:ConnectionPointGraphicsItemMixin,
	                     toItem:QtWidgets.QGraphicsItem=None):
		self.connectionPointItemMap[fromPoint].remove(toItem)

	def connectedItems(self, fromPoint:ConnectionPointGraphicsItemMixin)->list[QtWidgets.QGraphicsItem]:
		return self.connectionPointItemMap[fromPoint]

	# def onConnectionPointUpdated(self, connectionPoint:ConnectionPointGraphicsItemMixin):
	# 	"""fires whenever connectionpoint moves - """
	# 	raise NotImplementedError()

class AbstractNodeContainer:
	"""this is close to being able to inherit from GraphItemDelegateAbstract,
	but this specifies only nodes, where the other can include
	other elements as well"""

	def __init__(self, nodes:[ChimaeraNode]):
		self.nodes = nodes

	@property
	def node(self):
		return self.nodes[0]

	def connectionPointForDataUse(self, dataUse:DataUse, asOutput=False) -> ConnectionPointGraphicsItemMixin:
		"""return a connectionPoint to use for this data, on this node,
		as input or output
		very debatable if this should be here, still not happy with the way drawing
		classes are structured"""
		raise NotImplementedError()


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

	@property
	def node(self):
		return self.graphItems[0]

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

	def connectionPointForDataUse(self, dataUse:DataUse, asOutput=False) -> ConnectionPointGraphicsItemMixin:
		"""return a connectionPoint to use for this data, on this node,
		as input or output

		this absolutely should not be a base method here but the drawing classes
		are a mess
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
		return self.boundingRect().heightOffset()

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