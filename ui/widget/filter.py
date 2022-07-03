from __future__ import annotations

"""widget allowing user to filter currently visible nodes in graph - 
consider combining treeview for tree nodes with text input,
allowing regex, saving previous queries, etc.

don't do any crazy ui stuff here yet until the full system works

"""


import typing as T

from chimaera.lib.query import queryTextIsValid


from PySide2 import QtCore, QtWidgets, QtGui

from tree import TreeWidget

if T.TYPE_CHECKING:
	from chimaera.ui.widget.graphtab import GraphTabWidget


class GraphFilterWidget(QtWidgets.QWidget):

	filterChanged = QtCore.Signal(str)

	def __init__(self, parent=None):
		super(GraphFilterWidget, self).__init__(parent)
		self.treeWidget = TreeWidget(self)
		self.filterLineEdit = QtWidgets.QLineEdit(self)
		self.filterLineEdit.setPlaceholderText("Filter expression...")


	def onFilterEdited(self, *args, **kwargs):
		"""triggered when user edits filter text or target branch"""
		if self.sender() is self.treeWidget:
			filterText = self.treeWidget.currentBranch().stringAddress(includeRoot=True)
		elif self.sender() is self.filterLineEdit:
			filterText = self.filterLineEdit.text()
		else:
			raise RuntimeError(f"Unknown sender for filterEdited {self.sender()}")

		if not queryTextIsValid(filterText):
			raise SyntaxError(f"Invalid graph filter text: {filterText}")

		self.filterChanged.emit(filterText)








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

