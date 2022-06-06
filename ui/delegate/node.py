
from __future__ import annotations

"""drawing nodes in chimaera graph"""

import typing as T
from PySide2 import QtCore, QtWidgets, QtGui

from tree import TreeWidget
from tree.ui.lib import AllEventEater
from tree.ui.atomicwidget import AtomicWidget, StringWidget
from tree.ui.libwidget.atomicproxywiget import AtomicProxyWidget

#from treegraph.node import GraphNode
import typing as T
from chimaera import ChimaeraGraph, ChimaeraNode
from chimaera.constant import DataUse
from chimaera.ui.base import GraphicsItemChange

if T.TYPE_CHECKING:
	from chimaera.ui.scene import ChimaeraGraphScene

class SettingsProxy(QtWidgets.QGraphicsProxyWidget):
	"""class specific to holding tree widget for node"""


class PlugDelegate(QtWidgets.QGraphicsEllipseItem):
	"""basic circle with description of data use"""
	def __init__(self, name:str, parent=None):
		super(PlugDelegate, self).__init__(parent)
		self.name = name
		self.nameTag = QtWidgets.QGraphicsTextItem(self.name, self)
		self.setRect(0, 0, 20, 20)

class NodeDelegate(QtWidgets.QGraphicsItem):
	""" drawing for individual chimaera nodes

	connection points for edges are consistent heights on node
	 """

	def __init__(self, node:ChimaeraNode=None,  parent=None,
	             ):
		super(NodeDelegate, self).__init__(parent)
		self.node = node
		self.settingsProxy :SettingsProxy = None
		self.settingsWidg : TreeWidget = None


		self.nameTag = StringWidget(value=self.node.name)
		self.nameTagProxy = AtomicProxyWidget(self.nameTag, parent=self)
		self.classTag = QtWidgets.QGraphicsTextItem(
			self.node.__class__.__name__, self)


		self.addSettings(self.node.params() )
		self.settingsWidg.expandAll()

		self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
		self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

		# appearance
		self.colour = (50, 50, 120)
		self.borderColour = (200,200,250)
		textColour = QtGui.QColor(200, 200, 200)
		self.classTag.setDefaultTextColor(textColour)
		self.classTag.setPos(self.boundingRect().width() + 2, 0)

		self.settingsProxy.setPos(0,
		                          self.nameTagProxy.rect().bottom() + 10)

		self.makeConnections()

	def scene(self) -> ChimaeraGraphScene:
		return super(NodeDelegate, self).scene()


	def makeConnections(self):
		self.nameTag.atomValueChanged.connect(self._onNameTagChanged)

	def _onNameTagChanged(self, text:str):
		self.node.name = text

	def syncFromNode(self):
		"""reset ui state to match that of node"""
		self.nameTag.setAtomValue(self.node.name)

	def onNodeEval(self):
		self.syncFromNode()

	def onNodeNameChanged(self, branch, newName, oldName):
		"""updates from python"""
		self.nameTag.value = newName

	@property
	def width(self):
		return self.boundingRect().width()

	@property
	def height(self):
		return self.boundingRect().height()

	def edgePointMap(self)->dict[DataUse, tuple[QtCore.QPoint, QtCore.QPoint]]:
		pointMap = {}
		nMembers = len(DataUse)
		increment = self.boundingRect().height() / (nMembers + 2)
		for i, member in enumerate(DataUse):
			height = increment * (i + 1)
			pointMap[member] = (QtCore.QPointF(0, height) + self.scenePos(),
			                    QtCore.QPointF(self.boundingRect().width(), height) + self.scenePos())
		return pointMap

	def itemChange(self, change:QtWidgets.QGraphicsItem.GraphicsItemChange, value):
		if self.scene():
			self.scene().itemChanged.emit(GraphicsItemChange(self, change, value))
		return super(NodeDelegate, self).itemChange(change, value)


	def onSceneItemChange(self, change:GraphicsItemChange):
		if change.item is self:
			return

	def getSize(self):
		"""
		calculate minimum node size.
		"""
		minRect = self.nameTag.rect()
		minWidth = minRect.x() + 150
		#minWidth = minRect.x()
		minHeight = minRect.y() + 20

		minRect = minRect.united(self.settingsProxy.rect().toRect())

		#minHeight += self.settingsProxy.rect().height()

		return minRect.width(), minRect.height()

	def boundingRect(self):
		minWidth, minHeight = self.getSize()
		return QtCore.QRect(0, 0, minWidth, minHeight)

	def paint(self, painter, option, widget):
		"""Paint the main background shape of the node"""
		painter.save()
		self.getSize()

		baseBorder = 1.0
		rect = QtCore.QRectF(0.5 - (baseBorder / 2),
							 0.5 - (baseBorder / 2),
							 self.width + baseBorder,
							 self.height + baseBorder)
		radius_x = 2
		radius_y = 2
		path = QtGui.QPainterPath()
		path.addRoundedRect(rect, radius_x, radius_y)
		painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 255), 1.5))
		painter.drawPath(path)

		rect = self.boundingRect()
		bg_color = QtGui.QColor(*self.colour)
		painter.setBrush(bg_color)
		painter.setPen(QtCore.Qt.NoPen)
		#painter.drawRoundRect(rect, radius_x, radius_y)
		painter.drawRect(rect)

		# if self.isSelected():
		# 	painter.setBrush(QtGui.QColor(*NODE_SEL_COLOR))
		# 	painter.drawRoundRect(rect, radius_x, radius_y)

		label_rect = QtCore.QRectF(rect.left() + (radius_x / 2),
								   rect.top() + (radius_x / 2),
								   self.width - (radius_x / 1.25),
								   28)
		path = QtGui.QPainterPath()
		path.addRoundedRect(label_rect, radius_x / 1.5, radius_y / 1.5)
		painter.setBrush(QtGui.QColor(0, 0, 0, 50))
		painter.fillPath(path, painter.brush())

		border_width = 0.8
		border_color = QtGui.QColor(*self.borderColour)
		# if self.isSelected():
		# 	border_width = 1.2
		# 	border_color = QtGui.QColor(*NODE_SEL_BORDER_COLOR)
		border_rect = QtCore.QRectF(rect.left() - (border_width / 2),
									rect.top() - (border_width / 2),
									rect.width() + border_width,
									rect.height() + border_width)
		path = QtGui.QPainterPath()
		path.addRoundedRect(border_rect, radius_x, radius_y)
		painter.setBrush(QtCore.Qt.NoBrush)
		painter.setPen(QtGui.QPen(border_color, border_width))
		painter.drawPath(path)
		painter.restore()

	def addSettings(self, tree):
		"""create a new abstractTree widget and add it to the bottom of node"""
		self.settingsProxy = SettingsProxy(self)

		topWidg = QtWidgets.QApplication.topLevelWidgets()[0]
		self.settingsWidg = TreeWidget(
			tree=tree,
			scanForWidgets=True,
		                               )
		self.settingsProxy.setWidget(self.settingsWidg)
		self.settingsWidg.resizeToTree()

		return self.settingsWidg

	# def getActions(self)->List[Action]:
	# 	return self.node.getAllActions()

	def onSceneSelectionChanged(self):
		pass

	def serialise(self):
		"""save position in view"""
		return {
			"pos" :	(self.pos().x(), self.pos().y()),
			}




