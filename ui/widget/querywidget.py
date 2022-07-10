from __future__ import annotations

"""widget allowing user to query currently visible nodes in graph - 
consider combining treeview for tree nodes with text input,
allowing regex, saving previous queries, etc.

don't do any crazy ui stuff here yet until the full system works

"""


import typing as T

from chimaera.lib.query import queryTextIsValid, GraphQuery


from PySide2 import QtCore, QtWidgets, QtGui

from tree import TreeWidget

if T.TYPE_CHECKING:
	from chimaera.ui.widget.graphtab import GraphTabWidget


class GraphQueryWidget(QtWidgets.QWidget):
	"""consider how we can check a user's input here is valid - should this
	widget be passed a graph object? emit a signal on text query,
	then define a function to be called if that is valid?

	testing a persistent query object rather than regenerating it
	"""

	#filterChanged = QtCore.Signal(str)
	queryChanged = QtCore.Signal(GraphQuery)

	def __init__(self, parent=None):
		super(GraphQueryWidget, self).__init__(parent)
		self.treeWidget = TreeWidget(self)
		self.filterLineEdit = QtWidgets.QLineEdit(self)
		self.filterLineEdit.setPlaceholderText("Filter expression...")


	def onFilterEdited(self, *args, **kwargs):
		"""triggered when user edits query text or target branch"""
		if self.sender() is self.treeWidget:
			filterText = self.treeWidget.currentBranch().stringAddress(includeRoot=True)
		elif self.sender() is self.filterLineEdit:
			filterText = self.filterLineEdit.text()
		else:
			raise RuntimeError(f"Unknown sender for filterEdited {self.sender()}")

		if not queryTextIsValid(filterText):
			raise SyntaxError(f"Invalid graph query text: {filterText}")

		query = self.getQuery()
		if query is not None:
			self.queryChanged.emit(self.getQuery())

	def getQuery(self)->GraphQuery:
		query = GraphQuery(self.filterLineEdit.text())
		if query.isValid():
			return query
		else:
			return None

	def setQuery(self, query:GraphQuery):
		self.filterLineEdit.setText(query.queryText)






class GraphSelector(TreeWidget):
	"""display available graphs and the files to which they are linked"""

	def __init__(self, parent: GraphTabWidget = None,
	             ):
		super(GraphSelector, self).__init__(
			parent, tree=None,
			showValues=False,
			showRoot=False,
			showHeader=False,
			alternatingRows=False,
			allowNameMerging=False,
			collapsible=True)

	pass

