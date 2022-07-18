from __future__ import annotations
"""delegate for plug tree drawing"""

from chimaera import ChimaeraNode, ChimaeraGraph
from chimaera.plugtree import PlugTree
from chimaera.plugnode import PlugNode
from chimaera.constant import INPUT_NAME, OUTPUT_NAME, DataUse, DataType
from chimaera.datause import DataUse, UiPlugPosition

from PySide2 import QtCore, QtWidgets, QtGui
from chimaera.ui.delegate import GraphItemDelegateAbstract
from chimaera.ui.delegate.abstract import ConnectionPointGraphicsItemMixin


class Knob(QtWidgets.QGraphicsRectItem,
               ConnectionPointGraphicsItemMixin):
	"""handle marking inputs and outputs for common chimaera nodes

	in normal use, hide knobs on chimaera nodes
	when hovering near knobs, show them
	when hovering over them, grow them

	when dragging edge, hide all illegal knobs, and show all legal knobs

	"""
	def __init__(self, node:ChimaeraNode,
	             dataUse:DataUse,
	             isOutput=False,
	             parent=None,):

		self.node = node
		self.dataUse = dataUse
		self.isOutput = isOutput
		self.uid = node.uid + "-" + str(dataUse) + ("-output" if isOutput else "-input")

		self.baseSize = 5
		self.showRange = 50

		super(Knob, self).__init__(parent)
		ConnectionPointGraphicsItemMixin.__init__(self, self.uid)

		self.setRect(0,0, self.baseSize, self.baseSize)


		# set up child items
		self.text = QtWidgets.QGraphicsTextItem(self.dataUse.name, parent=self)

		self.pen = QtGui.QPen()
		self.pen.setStyle(QtCore.Qt.NoPen)
		self.brush = QtGui.QBrush(self.colour(),
		                          bs=QtCore.Qt.SolidPattern)
		self.setPen(self.pen)
		self.setBrush(self.brush)
		self.setAcceptHoverEvents(True)

		# align text
		textY = self.rect().height() / 2
		if isOutput:
			textX = -self.rect().width() - self.text.textWidth()
		else:
			textX = self.rect().width()
		self.text.setPos(textX, textY)
		self.text.setRotation(45)

		self.hide()

	def graph(self)->ChimaeraGraph:
		return self.node.graph()

	def colour(self):
		return QtGui.QColor(*self.dataUse.edgeColour)

	def visibilityOverride(self):
		"""return whether this knob should be visible"""
		return self.scene().knobVisibilityOverrides.get(self)

	def sceneMouseMoveEvent(self, event:QtWidgets.QGraphicsSceneMouseEvent):
		"""when mouse is moved, check if it is anywhere near this knob"""
		pos = event.scenePos()
		if self.visibilityOverride() is None: # no scene override
			if (pos - self.scenePos()).manhattanLength() < self.showRange:
				self.show()
			else:
				self.hide()
		else:
			self.setVisible(self.visibilityOverride())

	def connectionDirection(self) ->QtCore.QPoint:
		"""return the direction of the connection from this knob"""
		if self.isOutput:
			return QtCore.QPoint(1, 0)
		else:
			return QtCore.QPoint(-1, 0)

	def acceptsConnection(self, sourcePoint:Knob) ->bool:
		"""return whether this knob accepts connections from the given knob"""
		if self.isOutput: # this plug is an output
			return not sourcePoint.isOutput # source plug is an input
		else: # this plug is an input
			return sourcePoint.isOutput # source plug is an output

	def addConnectionToPoint(self, otherPoint:Knob):
		"""try to add a new edge to the graph from this point to toPoint"""
		assert isinstance(otherPoint, Knob)
		if self.isOutput:
			tie = (otherPoint, self)
		else:
			tie = (self, otherPoint)

		dataTie = (tie[0].getNodeAndDataUse(), tie[1].getNodeAndDataUse())

		self.graph().connectNodes(fromNode=dataTie[0][0], toNode=dataTie[1][0],
		                          fromUse=dataTie[0][1], toUse=dataTie[1][1])


	def getNodeAndDataUse(self)->(ChimaeraNode, DataUse):
		return self.node, self.dataUse

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
