from __future__ import annotations
"""delegate for plug tree drawing"""


from chimaera.plugtree import PlugTree
from chimaera.plugnode import PlugNode
from chimaera.constant import INPUT_NAME, OUTPUT_NAME, DataUse, DataType

from PySide2 import QtCore, QtWidgets, QtGui


class Knob(QtWidgets.QGraphicsRectItem):
	"""handle marking inputs and outputs"""
	def __init__(self, plug:PlugTree, parent=None,):
		super(Knob, self).__init__(parent)
		self.baseSize = 20
		self.setRect(0,0, self.baseSize, self.baseSize)
		if not plug:
			raise RuntimeError("no attrItem supplied")
		self.plug = plug

		self.text = QtWidgets.QGraphicsTextItem(self.plug.name, parent=self)

		self.pen = QtGui.QPen()
		self.pen.setStyle(QtCore.Qt.NoPen)
		self.brush = QtGui.QBrush(self.colour(),
		                          bs=QtCore.Qt.SolidPattern)
		self.setPen(self.pen)
		self.setBrush(self.brush)
		self.setAcceptHoverEvents(True)

		# align text
		textY = self.rect().height() / 2
		if self.plug.isInput():
			textX = -self.rect().width() - self.text.textWidth()
		else:
			textX = self.rect().width()
		self.text.setPos(textX, textY)


	def colour(self):
		return QtGui.QColor(*self.tree.dataType.colour)

	def __repr__(self):
		return self.name

	# visuals
	def hoverEnterEvent(self, event):
		"""tweak to allow knob to expand pleasingly when you touch it"""
		self.setTumescent()

	def hoverLeaveEvent(self, event):
		"""return knob to normal flaccid state"""
		self.setFlaccid()

	def setTumescent(self):
		scale = 1.3
		new = int(self.baseSize * scale)
		newOrigin = (new - self.baseSize) / 2
		self.setRect(-newOrigin, -newOrigin, new, new)

	def setFlaccid(self):
		self.setRect(0, 0, self.baseSize, self.baseSize)

class PlugTreeDelegate(QtWidgets.QGraphicsItem):
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
		self.knob = Knob( plug=plug, parent=self)
		self.sync()


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



