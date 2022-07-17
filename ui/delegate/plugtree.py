from __future__ import annotations
"""delegate for plug tree drawing"""


from chimaera.plugtree import PlugTree
from chimaera.plugnode import PlugNode
from chimaera.constant import INPUT_NAME, OUTPUT_NAME, DataUse, DataType

from PySide2 import QtCore, QtWidgets, QtGui
from chimaera.ui.delegate import GraphItemDelegateAbstract
from chimaera.ui.delegate.node import NodeDelegate
from chimaera.ui.delegate.connectionpoint import ConnectionPointGraphicsItemMixin
from chimaera.ui.delegate.knob import Knob

class PlugKnob(Knob):
	"""handle marking inputs and outputs"""
	def __init__(self, plug:PlugTree, parent=None,):
		super(PlugKnob, self).__init__(parent)
		ConnectionPointGraphicsItemMixin.__init__(self, plug.uid)
		self.baseSize = 20
		self.setRect(0,0, self.baseSize, self.baseSize)
		if not plug:
			raise RuntimeError("no attrItem supplied")
		self.plug = plug

		self.text.setPlainText(self.plug.name)
		self.text.setRotation(0.0)


	def colour(self):
		return QtGui.QColor(*self.plug.dataType.colour)



#class PlugTreeDelegate(QtWidgets.QGraphicsItem):
class PlugTreeDelegate(QtWidgets.QGraphicsRectItem, NodeDelegate):
	"""draw tree of plugs for plug node"""

	def __init__(self, plug:PlugTree, treeDepthOffset:int=20, height=20, parent=None):
		super(PlugTreeDelegate, self).__init__(parent)
		self.plug = plug
		self.depthOffset = treeDepthOffset
		self.height = height
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, False)

		self.childDelegates : list[QtWidgets.QGraphicsItem] = []
		self.knob = PlugKnob(plug=plug, parent=self)
		self.sync()

	@property
	def node(self):
		return self.plug

	def isInput(self) -> bool:
		"""return true if this is an input tree"""
		return self.plug.isInput()

	def arrange(self):
		"""arrange the plug items"""
		if self.isInput():
			self.knob.setPos(self.depthOffset * self.plug.depth(), 0)
		else:
			self.setPos(-self.depthOffset * self.plug.depth(), 0)

		childY = self.height
		for i in self.childDelegates:
			i.arrange()
			i.setPos(0, childY)
			childY += i.boundingRect().height()

	def sync(self, *args, **kwargs):
		"""clear and rebuild all plug items below this"""
		self.arrange()
		for child in self.childDelegates:
			self.scene().removeItem(child)
		self.childDelegates = [PlugTreeDelegate(i) for i in self.plug.branches]


	def paint(self, painter:QtGui.QPainter, option:QtWidgets.QStyleOptionGraphicsItem, widget:QtWidgets.QWidget=...) -> None:
		"""paint the delegate"""
		return QtWidgets.QGraphicsRectItem.paint(self, painter, option, widget)



