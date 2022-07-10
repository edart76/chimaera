
from __future__ import annotations
import pprint
import typing as T
from chimaera import ChimaeraGraph
from PySide2 import QtCore, QtWidgets, QtGui
from treegraph.glimport import *

# from treegraph.graph import Graph
# from treegraph.node import GraphNode, NodeAttr

from chimaera.ui.widget.graphtab import GraphTabWidget

from treegraph.plugin import registerNodes, registerNodeDelegate


def setStyleFile(widget, filePath=r"../ui/style/dark/stylesheet.qss"):
	stylePath = filePath
	settingFile = QtCore.QFile(stylePath)
	settingFile.open(QtCore.QFile.ReadOnly | QtCore.QFile.Text)
	stream = QtCore.QTextStream(settingFile)
	widget.setStyleSheet(stream.readAll())


class ChimaeraMainWidget(QtWidgets.QWidget):
	"""top level window for Chimaera application
	holds master register of loaded paths and graphs
	"""

	appName = "chimaera"

	graphsChanged = QtCore.Signal(dict)

	defaultGraphCls = ChimaeraGraph

	def __init__(self, parent=None):
		super(ChimaeraMainWidget, self).__init__(parent)

		#self.graphs = WeakValueDictionary() # {uuid : graph }

		self.graphIndex = Tree("tessGraphIndex")
		#topBranch = self.defaultGraphCls.globalTree(self.appName, create=True)

		self.setObjectName("chimaera")
		self.setWindowTitle("chimaera")

		# make these dockable eventually
		self.tabWidgets = [GraphTabWidget(parent=self)]
		self.makeLayout()
		self.makeSignals()

		self.setBaseSize(600, 600)

	def makeSignals(self):
		pass

	def makeLayout(self):
		vl = QtWidgets.QVBoxLayout()
		vl.addWidget(self.tabWidgets[0])
		vl.setContentsMargins(0, 0, 0, 0)
		self.setLayout(vl)

	def currentGraph(self)->ChimaeraGraph:
		return self.tabWidgets[0].currentGraph()

	def _instanceStartup(self, graph=None, newGraphName="newGraph", graphCls=None):
		#print("instanceStartup", graph, newGraphName, graphCls)
		if not graph:
			graphCls = graphCls or self.defaultGraphCls
			graph = graphCls.create(graphName=newGraphName)

		#print("instanceStartup", graph, "default cls", self.defaultGraphCls)
		self.tabWidgets[0].addGraph(graph)

	@classmethod
	def startup(cls, parent:QtWidgets.QWidget=None, graph=None, newGraphName="newGraph",
	            graphCls=None)->ChimaeraMainWidget:
		"""
		if specific graph is provided, opens on that
		graphCls is class of main root graph to show"""

		widget = cls(parent)
		widget._instanceStartup(graph, newGraphName, graphCls)

		return widget



def testWindow():
	#return

	from tree.test.constant import midTree
	#return



	widg = ChimaeraMainWidget.startup()
	setStyleFile(widg)


	from treegraph.example import pluginnode
	return widg



def testWithApp():
	import sys
	app = QtWidgets.QApplication(sys.argv)

	tessWidg = testWindow()

	win = QtWidgets.QMainWindow()
	tessWidg.setParent(win)
	win.setCentralWidget(tessWidg)

	win.show()
	win.setFixedSize(1000, 600)


	sys.exit(app.exec_())


if __name__ == "__main__":
	from treegraph.example import pluginnode
	w = testWindow()





