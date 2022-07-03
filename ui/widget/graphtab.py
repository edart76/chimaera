from __future__ import annotations

from PySide2 import QtCore, QtWidgets, QtGui

from treegraph.glimport import *
if Ty.TYPE_CHECKING:
	from treegraph.tesserae.mainwidget import TesseraeWidget

from treegraph.graph import Graph
from treegraph.tesserae.selector import GraphSelector
from chimaera.ui.graphwidget import ChimaeraGraphWidget
from tree import TreeWidget
from treegraph.ui.scene import GraphScene


class GraphTabWidget(QtWidgets.QTabWidget):
	"""container widget for tabs, each pointing to a separate graph
	"""

	activeGraphChanged = QtCore.Signal(dict)
	def __init__(self, parent=None, initGraph:Graph=None):
		super(GraphTabWidget, self).__init__(parent)

		self.tabs = {}
		self.makeLayout()
		self.setBaseSize(1200, 400)

		self.selector = GraphSelector(parent=self,
		                           )
		self.selector.move(0, 20)
		self.selector.setFixedSize(200, 80)

		self.selector.setTree(self.parent().graphIndex)

		self.selector.currentBranchChanged.connect(
			self.onSelectorBranchChanged
		)


	def parent(self) -> TesseraeWidget:
		return super(GraphTabWidget, self).parent()

	def tessApp(self):
		"""return the top level widget of this tesserae session"""
		return self.parent()

	def onSelectorBranchChanged(self, data):
		"""receives {newBranch, oldBranch} from selector widget"""
		view = self.currentWidget() #type:GraphView

		newBranch = data["newBranch"]
		#print("newBranch", newBranch)
		if newBranch is self.selector.tree: # ignore selecting root branch
			print("is selector")
			return
		graphBranch = self.tessApp().graphFromSelectorBranch(newBranch)
		#print("graphBranch", graphBranch)
		if graphBranch is view.graph:
			print("selected", graphBranch, "is current graph, skipping")
		else:
			view.setGraph(graphBranch)


	def allGraphs(self)->Ty.Dict[str, Graph]:
		"""return uuid map of loaded graphs"""
		return self.parent().graphs

	@property
	def openGraphs(self)->Ty.Dict[str:GraphView]:
		"""return map of {name : graph view widget}
		for each open graph tab of this window"""
		nameMap = {}
		if self.count() == 0:
			return None
		#try:
		for i in range(self.count()):
			graphView = self.widget(i) #type:GraphView
			if not isinstance(graphView, GraphView):
				continue
			nameMap[graphView.graph.uid] = graphView
		return nameMap
		# except:
		# 	return None

	@property
	def currentGraph(self)->Graph:
		if self.openGraphs is None:
			return None
		key = list(self.openGraphs.keys())[self.currentIndex()]
		return self.openGraphs[key].graph

	def addGraphView(self, graph:Graph):
		if self.openGraphs is None:
			self.removeTab(0)
		newView = GraphView(parent=None, graph=graph)
		self.addTab(newView, graph.name)
		#print("added graph", graph)



	def tabForGuid(self, guid:str):
		pass

	def setTabs(self, graphUuids:Ty.List[str]):
		"""this ignores unsaved work for now, not sure how best
		to structure tabs"""

	def openTab(self, uuid:str):
		graph = self.allGraphs()[uuid]

	def closeTab(self):
		"""add here any checks for graphs with unsaved work"""
		self.removeTab()




	def makeLayout(self):

		# vl = QtWidgets.QVBoxLayout()
		# # vl.addWidget(self.bar)
		# # vl.addWidget(self.tabWidget)
		# # #vl.addWidget(self.view)
		# #vl.setContentsMargins(0, 0, 0, 0)
		# self.setLayout(vl)
		pass





