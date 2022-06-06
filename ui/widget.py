from __future__ import annotations

"""top-level widget for chimaera graph"""

import pprint
import typing as T
from PySide2 import QtCore, QtWidgets, QtGui


from chimaera import ChimaeraGraph, ChimaeraNode, DataUse

from chimaera.ui.view import ChimaeraGraphView
from chimaera.ui.scene import ChimaeraGraphScene

class ChimaeraGraphWidget(QtWidgets.QWidget):
	"""widget holding individual scene/view of graph"""

	def __init__(self, graph:ChimaeraGraph=None, parent=None):
		super(ChimaeraGraphWidget, self).__init__(parent)
		self.graph:ChimaeraGraph = None
		self.scene = ChimaeraGraphScene(parent=self)
		self.view = ChimaeraGraphView(parent=self)
		self.view.setScene(self.scene)

		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(self.view)
		self.setLayout(layout)

		self.setGraph(graph)

	def setGraph(self, graph:ChimaeraGraph):
		self.graph = graph
		self.scene.setGraph(graph)

def test():

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
	w = test()
	w.show()
