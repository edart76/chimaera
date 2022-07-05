from __future__ import annotations

import typing as T

from chimaera import ChimaeraGraph
from PySide2 import QtCore, QtWidgets, QtGui

from chimaera.ui.widget.filter import GraphFilterWidget
from chimaera.ui.graphwidget import ChimaeraGraphWidget
from tree import TreeWidget

class GraphTabWidget(QtWidgets.QTabWidget):
	"""container widget for tabs, each holding a graph view -
	each
	"""

	activeGraphChanged = QtCore.Signal(dict)
	def __init__(self, parent=None, initGraph:ChimaeraGraph=None):
		super(GraphTabWidget, self).__init__(parent)

		self.tabs = {}
		self.makeLayout()
		self.setBaseSize(1200, 400)


	# def parent(self) -> TesseraeWidget:
	# 	return super(GraphTabWidget, self).parent()

	def onSelectorBranchChanged(self, data):
		"""receives {newBranch, oldBranch} from selector widget"""
		view = self.currentWidget() #type:ChimaeraGraphWidget

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


	# def allGraphs(self)->T.Dict[str, ChimaeraGraph]:
	# 	"""return uuid map of loaded graphs"""
	# 	return self.parent().graphs

	@property
	def openGraphs(self)->T.Dict[str:ChimaeraGraphWidget]:
		"""return map of {name : graph view widget}
		for each open graph tab of this window"""
		nameMap = {}
		if self.count() == 0:
			return None
		#try:
		for i in range(self.count()):
			graphView = self.widget(i) #type:ChimaeraGraphWidget
			if not isinstance(graphView, ChimaeraGraphWidget):
				continue
			nameMap[graphView.graph.uid] = graphView
		return nameMap
		# except:
		# 	return None

	@property
	def currentGraph(self)->ChimaeraGraph:
		if self.openGraphs is None:
			return None
		key = list(self.openGraphs.keys())[self.currentIndex()]
		return self.openGraphs[key].graph

	def addGraph(self, graph:ChimaeraGraph):
		if self.openGraphs is None:
			self.removeTab(0)
		newView = ChimaeraGraphWidget(parent=None, graph=graph)
		self.addTab(newView, graph.name)
		#print("added graph", graph)



	def tabForGuid(self, guid:str):
		pass

	def setTabs(self, graphUuids:list[str]):
		"""this ignores unsaved work for now, not sure how best
		to structure tabs"""

	def openTab(self, uuid:str):
		graph = self.allGraphs()[uuid]

	def closeTab(self, index=None):
		"""add here any checks for graphs with unsaved work"""
		self.removeTab(index if index is not None else self.currentIndex())




	def makeLayout(self):

		# vl = QtWidgets.QVBoxLayout()
		# # vl.addWidget(self.bar)
		# # vl.addWidget(self.tabWidget)
		# # #vl.addWidget(self.view)
		# #vl.setContentsMargins(0, 0, 0, 0)
		# self.setLayout(vl)
		pass





