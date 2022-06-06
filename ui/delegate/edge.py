from __future__ import annotations

from PySide2 import QtWidgets, QtGui, QtCore
from treegraph.ui.constant import PIPE_STYLES

from treegraph.ui.style import Z_VAL_PIPE, PIPE_DEFAULT_COLOR, PIPE_STYLE_DEFAULT, PIPE_WIDTH, PIPE_ACTIVE_COLOR, \
	PIPE_HIGHLIGHT_COLOR

import typing as T
from chimaera import ChimaeraGraph, ChimaeraNode, DataUse
from chimaera.ui.delegate.node import NodeDelegate
from chimaera.ui.base import GraphicsItemChange, dataColourMap

if T.TYPE_CHECKING:
	from chimaera.ui.scene import ChimaeraGraphScene

def blendQColors(a:QtGui.QColor, b:QtGui.QColor, alpha:float):
	return QtGui.QColor(
		a.red() * (1.0 - alpha) + b.red() * alpha,
		a.blue() * (1.0 - alpha) + b.blue() * alpha,
		a.green() * (1.0 - alpha) + b.green() * alpha,
	)

def paintGradientPath(path:QtWidgets.QGraphicsPathItem,
                      startColour:QtGui.QColor,
                      endColour:QtGui.QColor,
                      steps:int,
                      basePen:QtGui.QPen,
                      painter:QtGui.QPainter, option:QtWidgets.QStyleOptionGraphicsItem, widget:QtWidgets.QWidget=...,
                      ):
	"""very very dumb way of changing olour - draw loads of lines"""
	span = 1.0 / steps
	for i in range(steps):
		frac = i * span
		col = blendQColors(startColour, endColour, frac)
		start = path.path().pointAtPercent(i * span)
		end = path.path().pointAtPercent((i + 1) * span)
		pen = QtGui.QPen(basePen)
		pen.setColor(col)
		painter.setPen(pen)
		painter.drawLine(start, end)


class EdgeDelegate(QtWidgets.QGraphicsPathItem):
	"""tis a noble thing to be a bridge between knobs"""

	def __init__(self, edgeTuple:tuple[ChimaeraNode, ChimaeraNode, str]):
		super(EdgeDelegate, self).__init__()
		self.setZValue(Z_VAL_PIPE)
		self.setAcceptHoverEvents(True)

		self.edgeTuple = edgeTuple

		self._color = PIPE_DEFAULT_COLOR
		self._style = PIPE_STYLE_DEFAULT
		self._active = False
		self._highlight = False
		#self.pen = None
		self.setFlags(
			QtWidgets.QGraphicsItem.ItemIsSelectable
		)



	def scene(self) -> ChimaeraGraphScene:
		return super(EdgeDelegate, self).scene()

	def graph(self)->ChimaeraGraph:
		return self.scene().graph()

	@property
	def start(self)->ChimaeraNode:
		return self.edgeTuple[0]

	@property
	def startDelegate(self)->NodeDelegate:
		return self.scene().tiles[self.start]

	def startUse(self)->DataUse:
		return self.edgeData()["fromUse"]

	@property
	def end(self) -> ChimaeraNode:
		return self.edgeTuple[1]

	@property
	def endDelegate(self) -> NodeDelegate:
		return self.scene().tiles[self.end]

	def endUse(self)->DataUse:
		return self.edgeData()["toUse"]


	@property
	def key(self):
		return self.edgeTuple[2]

	def edgeData(self)->dict:
		return self.graph()[self.start][self.end][self.key]

	def startPoint(self)->QtCore.QPoint:
		"""point on start node delegate to originate edge"""
		return self.startDelegate.edgePointMap()[self.startUse()][1]

	def endPoint(self)->QtCore.QPoint:
		"""point on start node delegate to originate edge"""
		return self.endDelegate.edgePointMap()[self.endUse()][0]

	def sync(self, *args, **kwargs):
		# build gradient
		self.startCol = QtGui.QColor(*dataColourMap[self.edgeData()["fromUse"]])
		self.endCol = QtGui.QColor(*dataColourMap[self.edgeData()["toUse"]])
		gradient = QtGui.QLinearGradient(0.0, 0.0, 1.0, 1.0)
		gradient.setColorAt(0.0, self.startCol)
		gradient.setColorAt(1.0, self.endCol)
		gradBrush = QtGui.QBrush(gradient)

		pen = QtGui.QPen(gradBrush, 3.0)
		self.setPen(pen)
		self.setPath(self.path())

	def setSelected(self, selected):
		if selected:
			self.highlight()
		if not selected:
			self.reset()
		super(EdgeDelegate, self).setSelected(selected)

	def path(self)->QtGui.QPainterPath:
		path = QtGui.QPainterPath()
		path.moveTo(self.startPoint())
		path.lineTo(self.endPoint())
		return path

	def itemChange(self, change:QtWidgets.QGraphicsItem.GraphicsItemChange, value):
		if self.scene():
			self.scene().itemChanged.emit(GraphicsItemChange(self, change, value))
		return super(EdgeDelegate, self).itemChange(change, value)

	def onSceneItemChange(self, change:GraphicsItemChange):
		if change.item is self:
			return
		if change.item in (self.startDelegate, self.endDelegate):
			self.sync()
			
	def paint(self, painter:QtGui.QPainter, option:QtWidgets.QStyleOptionGraphicsItem, widget:QtWidgets.QWidget=...) -> None:
		self.setPath(self.path())
		if self.startUse() == self.endUse(): # no colour changing
			return super(EdgeDelegate, self).paint(painter, option, widget)
		return paintGradientPath(self,
		                         self.startCol,
		                         self.endCol,
		                         10,
		                         self.pen(),
		                         painter,
		                         option,
		                         widget)


	# def paint(self, painter, option, widget):
	# 	color = QtGui.QColor(*self._color)
	# 	pen_style = PIPE_STYLES.get(self.style)
	# 	pen_width = PIPE_WIDTH
	# 	if self._active:
	# 		color = QtGui.QColor(*PIPE_ACTIVE_COLOR)
	# 	elif self._highlight:
	# 		color = QtGui.QColor(*PIPE_HIGHLIGHT_COLOR)
	# 		pen_style = PIPE_STYLES.get(PIPE_STYLE_DEFAULT)
	#
	# 	if self.start and self.end:
	# 		# use later for proper freezing/approval
	# 		pass
	# 		# in_node = self.start.node
	# 		# out_node = self.end.node
	# 		# if in_node.disabled or out_node.disabled:
	# 		# 	color.setAlpha(200)
	# 		# 	pen_width += 0.2
	# 		# 	pen_style = PIPE_STYLES.get(PIPE_STYLE_DOTTED)
	#
	# 	if self.isSelected():
	# 		#painter.setBrush(QtGui.QColor(*NODE_SEL_COLOR))
	# 		#colour = QtGui.QColor(200, 200, 100)
	# 		# self._highlight = True
	# 		pen = QtGui.QPen(QtGui.QColor(*PIPE_HIGHLIGHT_COLOR), 2)
	# 		pen.setStyle(PIPE_STYLES.get(PIPE_STYLE_DEFAULT))
	#
	# 	else:
	# 		pen = QtGui.QPen(color, pen_width)
	# 		pen.setStyle(pen_style)
	#
	# 	pen.setCapStyle(QtCore.Qt.RoundCap)
	#
	# 	painter.setPen(self.pen or pen)
	# 	painter.setRenderHint(painter.Antialiasing, True)
	# 	#painter.drawPath(self.path())

	# def drawPath(self, startPort, endPort, cursorPos=None):
	# 	if not startPort:
	# 		return
	# 	offset = (startPort.boundingRect().width() / 2)
	# 	pos1 = startPort.scenePos()
	# 	pos1.setX(pos1.x() + offset)
	# 	pos1.setY(pos1.y() + offset)
	# 	if cursorPos:
	# 		pos2 = cursorPos
	# 	elif endPort:
	# 		offset = startPort.boundingRect().width() / 2
	# 		pos2 = endPort.scenePos()
	# 		pos2.setX(pos2.x() + offset)
	# 		pos2.setY(pos2.y() + offset)
	# 	else:
	# 		return
	#
	# 	line = QtCore.QLineF(pos1, pos2)
	# 	path = QtGui.QPainterPath()
	# 	path.moveTo(line.x1(), line.y1())
	#
	# 	# if self.viewer_pipe_layout() == PIPE_LAYOUT_STRAIGHT:
	# 	# 	path.lineTo(pos2)
	# 	# 	self.setPath(path)
	# 	# 	return
	#
	# 	ctrOffsetX1, ctrOffsetX2 = pos1.x(), pos2.x()
	# 	tangent = ctrOffsetX1 - ctrOffsetX2
	# 	tangent = (tangent * -1) if tangent < 0 else tangent
	#
	# 	maxWidth = startPort.parentItem().boundingRect().width() / 2
	# 	tangent = maxWidth if tangent > maxWidth else tangent
	#
	# 	if startPort.role == "input":
	# 		ctrOffsetX1 -= tangent
	# 		ctrOffsetX2 += tangent
	# 	elif startPort.role == "output":
	# 		ctrOffsetX1 += tangent
	# 		ctrOffsetX2 -= tangent
	#
	# 	ctrPoint1 = QtCore.QPointF(ctrOffsetX1, pos1.y())
	# 	ctrPoint2 = QtCore.QPointF(ctrOffsetX2, pos2.y())
	# 	path.cubicTo(ctrPoint1, ctrPoint2, pos2)
	# 	self.setPath(path)
	#
	# def redrawPath(self):
	# 	"""updates path shape"""
	# 	self.drawPath(self.start, self.end)
	#
	# def activate(self):
	# 	self._active = True
	# 	pen = QtGui.QPen(QtGui.QColor(*PIPE_ACTIVE_COLOR), 2)
	# 	pen.setStyle(PIPE_STYLES.get(PIPE_STYLE_DEFAULT))
	# 	self.setPen(pen)
	#
	# def active(self):
	# 	return self._active
	#
	# def highlight(self):
	# 	self._highlight = True
	# 	pen = QtGui.QPen(QtGui.QColor(*PIPE_HIGHLIGHT_COLOR), 2)
	# 	pen.setStyle(PIPE_STYLES.get(PIPE_STYLE_DEFAULT))
	# 	self.setPen(pen)
	#
	# def highlighted(self):
	# 	return self._highlight
	#
	# def reset(self):
	# 	self._active = False
	# 	self._highlight = False
	# 	pen = QtGui.QPen(QtGui.QColor(*self.color), 2)
	# 	pen.setStyle(PIPE_STYLES.get(self.style))
	# 	self.setPen(pen)
	#
	# def delete(self):
	# 	pass

