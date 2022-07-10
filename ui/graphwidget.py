from __future__ import annotations

"""top-level widget for chimaera graph"""

import pprint
import typing as T
from PySide2 import QtCore, QtWidgets, QtGui


from chimaera import ChimaeraGraph, ChimaeraNode, DataUse
from chimaera.lib.query import GraphQuery
from chimaera.ui.view import ChimaeraGraphView
from chimaera.ui.scene import ChimaeraGraphScene
from .widget.graphtoolbar import GraphToolbar
from .graphviewdata import GraphViewData

class ChimaeraGraphWidget(QtWidgets.QWidget):
	"""widget holding individual scene/view of graph"""

	viewNameChanged = QtCore.Signal(str)

	def __init__(self, graph:ChimaeraGraph=None, parent=None, viewData:GraphViewData=None):
		super(ChimaeraGraphWidget, self).__init__(parent)
		self.graph:ChimaeraGraph = None
		self.viewData:GraphViewData = None
		self.scene = ChimaeraGraphScene(parent=self)
		self.view = ChimaeraGraphView(parent=self)
		self.view.setScene(self.scene)

		self.toolbar = GraphToolbar(parent=self)

		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(self.view)
		self.setLayout(layout)

		self.setGraph(graph)
		self.arrange()

		if viewData is None:
			self.viewData = GraphViewData(graph=graph,
			                              positions={},
			                              cameraTransform=(0, 0, 1),
			                              queryFilter=self.toolbar.graphQuery(),
			                              name="view")

		else:
			self.setFromViewData(viewData)


	# region widget boilerplate
	def arrange(self):
		"""run to position any floating child widgets correctly"""
		# spread tool bar across top of view
		self.toolbar.move(20, 20)

	def resizeEvent(self, event:QtGui.QResizeEvent) -> None:
		"""resize event handler"""
		self.arrange()
		super(ChimaeraGraphWidget, self).resizeEvent(event)
	# endregion

	# region higher objects
	def setGraph(self, graph:ChimaeraGraph):
		self.graph = graph
		self.scene.setGraph(graph)

	def query(self):
		return self.toolbar.graphQuery()

	def setQuery(self, query:GraphQuery):
		self.scene.setQuery(query)

	def viewName(self)->str:
		return self.viewData.name

	def setViewName(self, name:str):
		self.viewData.name = name

	def setFromViewData(self, viewData:GraphViewData):
		"""update this view to represent data held in viewData"""
		self.viewData = viewData
		self.setGraph(viewData.graph)
		self.setQuery(viewData.queryFilter)
		self.view.setFromViewData(viewData)
	# endregion

def show():

	from tree.test.constant import midTree
	import sys
	from tree.lib.constant import UI_PROPERTY_KEY
	from tree.ui.atomicwidget import AtomicWidgetParams, AtomicWidgetType



	app = QtWidgets.QApplication(sys.argv)
	win = QtWidgets.QMainWindow()

	graph = ChimaeraGraph()
	aNode = graph.createNode("A")
	aNode.name = "nodeA"
	bNode = graph.createNode("B")
	bNode.name = "nodeB"
	cNode = graph.createNode("C")
	cNode.name = "nodeC"

	graph.connectNodes(bNode, cNode )
	graph.connectNodes(bNode, cNode ,
	                   toUse=DataUse.Params)

	widg = ChimaeraGraphWidget(graph, parent=win
	                  )
	win.setCentralWidget(widg)
	win.setGeometry(400, 400, 600, 600)

	win.show()
	sys.exit(app.exec_())
	return win





if __name__ == "__main__":
	w = show()
	w.show()
