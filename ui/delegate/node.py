
from __future__ import annotations

"""drawing nodes in chimaera graph"""

import typing as T
from PySide2 import QtCore, QtWidgets, QtGui

from tree import TreeWidget
from tree.ui.lib import AllEventEater
from tree.ui.graphics.lib import allGraphicsSceneItems, allGraphicsChildItems
from tree.ui.atomicwidget import AtomicWidget, StringWidget
from tree.ui.libwidget.atomicproxywiget import AtomicProxyWidget

#from treegraph.node import GraphNode
import typing as T
from chimaera import ChimaeraGraph, ChimaeraNode
from chimaera.constant import DataUse, NodeDataKeys
from chimaera.ui import graphItemType
from chimaera.ui.base import GraphicsItemChange
from chimaera.ui.constant import SelectionStatus
from chimaera.ui.delegate.abstract import ConnectionPointGraphicsItemMixin, GraphItemDelegateAbstract, AbstractNodeContainer
from chimaera.ui.delegate.knob import Knob

if T.TYPE_CHECKING:
	from chimaera.ui.scene import ChimaeraGraphScene

class SettingsProxy(QtWidgets.QGraphicsProxyWidget):
	"""class specific to holding tree widget for node"""


class PlugDelegate(QtWidgets.QGraphicsEllipseItem):
	"""basic circle with description of data use
	this will NOT represent a full item in chimaera graph"""
	def __init__(self, name:str, parent=None):
		super(PlugDelegate, self).__init__(parent)
		self.name = name
		self.nameTag = QtWidgets.QGraphicsTextItem(self.name, self)
		self.setRect(0, 0, 20, 20)

class NodeDelegate(GraphItemDelegateAbstract, AbstractNodeContainer,
                   QtWidgets.QGraphicsItem):
	""" drawing for individual chimaera nodes

	connection points for edges are consistent heights on node

	node shape is determined by tree widget

	this should extend a base node container class, adding plugs and settings widget

	 """
	instancesMayCreateDelegates = True

	@classmethod
	def delegatesForElements(cls, scene:ChimaeraGraphScene, itemPool:set[graphItemType]) ->T.Sequence[GraphItemDelegateAbstract]:
		"""return basic node delegate for any nodes left over here"""
		result = []
		for i in set(itemPool):
			if isinstance(i, ChimaeraNode):
				result.append(cls(i))
				itemPool.remove(i)
		return result

	def __init__(self, node:ChimaeraNode=None,  parent=None,
	             ):
		QtWidgets.QGraphicsItem.__init__(self, parent=parent)
		GraphItemDelegateAbstract.__init__(self, graphItems=[node])
		AbstractNodeContainer.__init__(self, [node])


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
		self.edgePadding = 2
		self.colour = (50, 50, 120)
		self.borderColour = (200,200,250)
		self.nameTagProxy.setPos(self.edgePadding, self.edgePadding)
		textColour = QtGui.QColor(200, 200, 200)
		self.classTag.setDefaultTextColor(textColour)
		self.classTag.setPos(self.boundingRect().width() + 2, 0)

		#self.settingsProxy.setGeometry(QtCore.QRectF(0, 0, 300, 300))

		self.settingsProxy.setPos(self.edgePadding,
		                          self.detailHeightLevel())

		self.knobs = self.makeKnobs()


		self.makeConnections()

	def detailHeightLevel(self):
		return self.nameTagProxy.rect().bottom() + 10

	@property
	def node(self)->ChimaeraNode:
		return self.mainGraphElement()

	def scene(self) -> ChimaeraGraphScene:
		return super(NodeDelegate, self).scene()

	def makeKnobs(self)->dict[str, dict[DataUse, Knob]]:
		"""return a list of all knobs on this node"""
		return {
			"in": {dataUse: Knob(self.node, dataUse, isOutput=False, parent=self) for dataUse in DataUse},
			"out": {dataUse: Knob(self.node, dataUse, isOutput=True, parent=self) for dataUse in DataUse},
		}


	def arrangeKnobs(self):
		for i, v in enumerate(self.knobs.values()):
			# get number of data uses
			horizontalKnobs = {use : knob for use, knob in v.items() if use.uiPosition == DataUse.UiPlugPosition.LeftRight}
			verticalKnobs = {use : knob for use, knob in v.items() if use.uiPosition == DataUse.UiPlugPosition.TopBottom}

			heightIncrement = self.boundingRect().height() / (len(horizontalKnobs) + 2)
			widthIncrement = self.boundingRect().width() / (len(verticalKnobs) + 1)

			for n, (dataUse, knob) in enumerate(horizontalKnobs.items()):
				if i == 0:
					knob.setPos(self.boundingRect().left() - knob.childrenBoundingRect().width(), n * heightIncrement)
				else:
					knob.setPos(self.boundingRect().right(), n * heightIncrement)

			for n, (dataUse, knob) in enumerate(verticalKnobs.items()):
				if i == 0:
					knob.setPos((1 + n) * widthIncrement,
					            self.boundingRect().top() - knob.boundingRect().height())
				else:
					knob.setPos((1 + n) * widthIncrement,
					            self.boundingRect().bottom())


	def makeConnections(self):
		self.nameTag.atomValueChanged.connect(self._onNameTagChanged)

	def _onNameTagChanged(self, text:str):
		self.node.name = text

	def connectionPointForDataUse(self, dataUse:DataUse, asOutput=False) -> ConnectionPointGraphicsItemMixin:
		"""return a connectionPoint to use for this data, on this node,
		as input or output"""
		if asOutput:
			return self.knobs["out"][dataUse]
		else:
			return self.knobs["in"][dataUse]


	def sync(self, *args, **kwargs):
		self.syncFromNode()
		self.arrange()

	def syncFromNode(self):
		"""reset ui state to match that of node"""
		self.nameTag.setAtomValue(self.node.name)

	def arrange(self):
		"""place plugs properly on borders of node"""
		#self.set
		self.arrangeKnobs()


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
		pointMap = {"in" : {}, "out" : {}}

		nMembers = len(DataUse)
		horizontalUses = [use for use in DataUse if use.uiPosition == DataUse.UiPlugPosition.LeftRight]
		verticalUses = [use for use in DataUse if use.uiPosition == DataUse.UiPlugPosition.TopBottom]

		nHorizontal = len(horizontalUses)
		nVertical = len(verticalUses)

		heightIncrement = self.boundingRect().height() / (nHorizontal + 2)
		widthIncrement = self.boundingRect().width() / (nVertical + 1)
		for i, member in enumerate(horizontalUses):
			height = heightIncrement * (i + 1)
			pointMap["in"][member] = (QtCore.QPointF(0, height) + self.scenePos(),
			                    QtCore.QPointF(self.boundingRect().width(), height) + self.scenePos())
			pointMap["out"][member] = (QtCore.QPointF(0, height) + self.scenePos(),
			                          QtCore.QPointF(self.boundingRect().width(), height) + self.scenePos())
		for i, member in enumerate(verticalUses):
			height = widthIncrement * (i + 1)
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

		settingsRect = self.settingsProxy.boundingRect().toRect()
		settingsRect.moveTo(self.settingsProxy.pos().toPoint())
		minRect = minRect.united(settingsRect)

		#minHeight += self.settingsProxy.rect().height()

		return minRect.width() + self.edgePadding, minRect.height() + self.edgePadding

	def boundingRect(self):
		minWidth, minHeight = self.getSize()
		return QtCore.QRect(-self.edgePadding, -self.edgePadding, minWidth + self.edgePadding, minHeight + self.edgePadding)


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
		#painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 255), 1.5))
		#painter.drawPath(path)

		rect = self.boundingRect()
		bg_color = QtGui.QColor(*self.colour)
		painter.setBrush(bg_color)
		painter.setPen(QtCore.Qt.NoPen)
		#painter.drawRoundRect(rect, radius_x, radius_y)
		painter.drawRect(rect)

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

		if self.isSelected():
			path = QtGui.QPainterPath()
			path.addRoundedRect(border_rect, radius_x, radius_y)
			pen = QtGui.QPen(QtGui.QColor(*SelectionStatus.Selected.colour), 2)
			painter.setPen(pen)
			painter.drawPath(path)


		painter.restore()

	def addSettings(self, tree):
		"""create a new abstractTree widget and add it to the bottom of node"""
		self.settingsProxy = SettingsProxy(self)

		#topWidg = QtWidgets.QApplication.topLevelWidgets()[0]
		self.settingsWidg = TreeWidget(
			tree=tree,
			scanForWidgets=True,
		                               )
		self.settingsProxy.setWidget(self.settingsWidg)
		self.settingsWidg.resizeToTree()

		self.settingsProxy.setGeometry(self.settingsWidg.geometry())

		# hide common node params
		self.settingsWidg.setKeyVisibilityMap({NodeDataKeys.nodeName : False,
		                                       NodeDataKeys.treeValue : False,
		                                       NodeDataKeys.treeProperties : False})
		print("settings vis", self.settingsWidg.keyVisibilityPresetMap)

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




