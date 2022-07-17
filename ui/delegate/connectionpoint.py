from __future__ import annotations

"""abstract for a discrete connection point in graphics scene - 
node plug connectors, object pivots, etc

no idea how best to structure this, may move it back into tree libs
"""
import typing as T
from collections import defaultdict
from enum import Enum
from tree import Tree
from tree.lib.object import UidElement
#from tree.lib.object import ExEnum



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
