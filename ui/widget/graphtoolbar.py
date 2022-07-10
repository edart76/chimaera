from __future__ import annotations

"""holder for query widget and any other options needed"""

from chimaera.lib.query import GraphQuery

from PySide2 import QtCore, QtGui, QtWidgets

from .querywidget import GraphQueryWidget

class GraphToolbar(QtWidgets.QWidget):
	"""quite bare for now, just a holder for query widget"""

	def __init__(self, parent:QtWidgets.QWidget=None):
		super(GraphToolbar, self).__init__(parent)

		self.filterWidget = GraphQueryWidget(parent=self)

		# promote signals
		self.queryChanged = self.filterWidget.queryChanged
		self.setQuery = self.filterWidget.setQuery

	def makeLayout(self):
		layout = QtWidgets.QHBoxLayout()
		layout.addWidget(self.filterWidget)
		self.setLayout(layout)

	def graphQuery(self)->GraphQuery:
		return self.filterWidget.getQuery()


