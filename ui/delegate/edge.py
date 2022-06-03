from PySide2 import QtWidgets, QtGui, QtCore
from treegraph.ui.constant import PIPE_STYLES
from treegraph.ui.delegate.knob import Knob
from treegraph.ui.style import Z_VAL_PIPE, PIPE_DEFAULT_COLOR, PIPE_STYLE_DEFAULT, PIPE_WIDTH, PIPE_ACTIVE_COLOR, \
	PIPE_HIGHLIGHT_COLOR


class EdgeDelegate(QtWidgets.QGraphicsPathItem):
	"""tis a noble thing to be a bridge between knobs"""

	def __init__(self, start=None, end=None, edge=None):
		super(EdgeDelegate, self).__init__()
		self.setZValue(Z_VAL_PIPE)
		self.setAcceptHoverEvents(True)
		self._color = start.colour if start else PIPE_DEFAULT_COLOR
		self._style = PIPE_STYLE_DEFAULT
		self._active = False
		self._highlight = False
		self._start = start
		self._end = end
		self.pen = None
		self.setFlags(
			QtWidgets.QGraphicsItem.ItemIsSelectable
		)

		self.edge = edge


	def setSelected(self, selected):
		if selected:
			self.highlight()
		if not selected:
			self.reset()
		super(EdgeDelegate, self).setSelected(selected)

	def paint(self, painter, option, widget):
		color = QtGui.QColor(*self._color)
		pen_style = PIPE_STYLES.get(self.style)
		pen_width = PIPE_WIDTH
		if self._active:
			color = QtGui.QColor(*PIPE_ACTIVE_COLOR)
		elif self._highlight:
			color = QtGui.QColor(*PIPE_HIGHLIGHT_COLOR)
			pen_style = PIPE_STYLES.get(PIPE_STYLE_DEFAULT)

		if self.start and self.end:
			# use later for proper freezing/approval
			pass
			# in_node = self.start.node
			# out_node = self.end.node
			# if in_node.disabled or out_node.disabled:
			# 	color.setAlpha(200)
			# 	pen_width += 0.2
			# 	pen_style = PIPE_STYLES.get(PIPE_STYLE_DOTTED)

		if self.isSelected():
			#painter.setBrush(QtGui.QColor(*NODE_SEL_COLOR))
			#colour = QtGui.QColor(200, 200, 100)
			# self._highlight = True
			pen = QtGui.QPen(QtGui.QColor(*PIPE_HIGHLIGHT_COLOR), 2)
			pen.setStyle(PIPE_STYLES.get(PIPE_STYLE_DEFAULT))

		else:
			pen = QtGui.QPen(color, pen_width)
			pen.setStyle(pen_style)

		pen.setCapStyle(QtCore.Qt.RoundCap)

		painter.setPen(self.pen or pen)
		painter.setRenderHint(painter.Antialiasing, True)
		painter.drawPath(self.path())

	def drawPath(self, startPort, endPort, cursorPos=None):
		if not startPort:
			return
		offset = (startPort.boundingRect().width() / 2)
		pos1 = startPort.scenePos()
		pos1.setX(pos1.x() + offset)
		pos1.setY(pos1.y() + offset)
		if cursorPos:
			pos2 = cursorPos
		elif endPort:
			offset = startPort.boundingRect().width() / 2
			pos2 = endPort.scenePos()
			pos2.setX(pos2.x() + offset)
			pos2.setY(pos2.y() + offset)
		else:
			return

		line = QtCore.QLineF(pos1, pos2)
		path = QtGui.QPainterPath()
		path.moveTo(line.x1(), line.y1())

		# if self.viewer_pipe_layout() == PIPE_LAYOUT_STRAIGHT:
		# 	path.lineTo(pos2)
		# 	self.setPath(path)
		# 	return

		ctrOffsetX1, ctrOffsetX2 = pos1.x(), pos2.x()
		tangent = ctrOffsetX1 - ctrOffsetX2
		tangent = (tangent * -1) if tangent < 0 else tangent

		maxWidth = startPort.parentItem().boundingRect().width() / 2
		tangent = maxWidth if tangent > maxWidth else tangent

		if startPort.role == "input":
			ctrOffsetX1 -= tangent
			ctrOffsetX2 += tangent
		elif startPort.role == "output":
			ctrOffsetX1 += tangent
			ctrOffsetX2 -= tangent

		ctrPoint1 = QtCore.QPointF(ctrOffsetX1, pos1.y())
		ctrPoint2 = QtCore.QPointF(ctrOffsetX2, pos2.y())
		path.cubicTo(ctrPoint1, ctrPoint2, pos2)
		self.setPath(path)

	def redrawPath(self):
		"""updates path shape"""
		self.drawPath(self.start, self.end)

	def activate(self):
		self._active = True
		pen = QtGui.QPen(QtGui.QColor(*PIPE_ACTIVE_COLOR), 2)
		pen.setStyle(PIPE_STYLES.get(PIPE_STYLE_DEFAULT))
		self.setPen(pen)

	def active(self):
		return self._active

	def highlight(self):
		self._highlight = True
		pen = QtGui.QPen(QtGui.QColor(*PIPE_HIGHLIGHT_COLOR), 2)
		pen.setStyle(PIPE_STYLES.get(PIPE_STYLE_DEFAULT))
		self.setPen(pen)

	def highlighted(self):
		return self._highlight

	def reset(self):
		self._active = False
		self._highlight = False
		pen = QtGui.QPen(QtGui.QColor(*self.color), 2)
		pen.setStyle(PIPE_STYLES.get(self.style))
		self.setPen(pen)

	def delete(self):
		pass

