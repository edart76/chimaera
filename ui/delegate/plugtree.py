from __future__ import annotations
"""delegate for plug tree drawing"""


from chimaera.plugtree import PlugTree
from chimaera.plugnode import PlugNode
from chimaera.constant import INPUT_NAME, OUTPUT_NAME, DataUse, DataType

from PySide2 import QtCore, QtWidgets, QtGui
from chimaera.ui.delegate.node import NodeDelegate
from chimaera.ui.delegate.abstract import GraphItemDelegateAbstract, AbstractNodeContainer, ConnectionPointGraphicsItemMixin
from chimaera.ui.delegate.knob import Knob

class PlugKnob(Knob):
	"""handle marking inputs and outputs"""
	def __init__(self, plug:PlugTree, parent=None,):
		super(PlugKnob, self).__init__(node=plug,
		                               dataUse=DataUse.Flow,
		                               isOutput=plug.isOutput(),
		                               parent=parent)
		#ConnectionPointGraphicsItemMixin.__init__(self, plug.uid)
		self.baseSize = 20
		self.setRect(0,0, self.baseSize, self.baseSize)
		if not plug:
			raise RuntimeError("no attrItem supplied")

		self.text.setPlainText(self.node.name)
		self.text.setRotation(0.0)


	def colour(self):
		return QtGui.QColor(*self.node.dataType.colour)



#class PlugTreeDelegate(QtWidgets.QGraphicsItem):
class PlugTreeDelegate(QtWidgets.QGraphicsRectItem, GraphItemDelegateAbstract,
                       AbstractNodeContainer):
	"""draw tree of plugs for plug node"""

	def __init__(self, plug:PlugTree, treeDepthOffset:int=20, height=20, parent=None):

		super(PlugTreeDelegate, self).__init__(parent)
		GraphItemDelegateAbstract.__init__(self, [plug])
		AbstractNodeContainer.__init__(self, [plug])

		self.depthOffset = treeDepthOffset
		self.heightOffset = height
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, False)

		self.childDelegates : list[QtWidgets.QGraphicsItem] = []
		self.knob = PlugKnob(plug=self.node, parent=self)
		self.sync()


	def isInput(self) -> bool:
		"""return true if this is an input tree"""
		return self.node.isInput()

	def connectionPointForDataUse(self, dataUse:DataUse, asOutput=False) -> ConnectionPointGraphicsItemMixin:
		"""return the connection point for the given data use"""
		if dataUse != DataUse.Flow: # only flow is visible on plug nodes
			return None
		if asOutput != self.node.isOutput():
			return None
		return self.knob

	def arrange(self):
		"""arrange the plug items"""
		if self.isInput():
			self.knob.setPos(self.depthOffset * self.node.depth(), 0)
		else:
			self.setPos(-self.depthOffset * self.node.depth(), 0)

		childY = self.heightOffset
		for i in self.childDelegates:
			i.arrange()
			i.setPos(0, childY)
			childY += i.boundingRect().height()

	def sync(self, *args, **kwargs):
		"""clear and rebuild all plug items below this"""
		self.arrange()
		for child in self.childDelegates:
			self.scene().removeItem(child)
		self.childDelegates = [PlugTreeDelegate(i, parent=self) for i in self.node.branches]
		self.arrange()


	def paint(self, painter:QtGui.QPainter, option:QtWidgets.QStyleOptionGraphicsItem, widget:QtWidgets.QWidget=...) -> None:
		"""paint the delegate"""
		return QtWidgets.QGraphicsRectItem.paint(self, painter, option, widget)



