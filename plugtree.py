
from __future__ import annotations
"""individual plug nodes defining a plugNode's interface
in general look to Maya for inspiration regarding array and compound plugs

arrays have a minimum length of 1, with the first plug being the template
for further copies

having each of these plugs be a separate node is a bit overkill, since we're
PROBABLY not going to reference or instance the attributes of a node,
but it lets the plugs play nice with graph addressing, lookups, mutators etc 
"""

import typing as T
from chimaera import GraphTree, DataUse, NodeDataKeys, ChimaeraNode
from chimaera.constant import DataType, INPUT_NAME, OUTPUT_NAME


class PlugTree(GraphTree):

	separatorChar = "."

	plugArrayKey = "_plugArray"

	array : bool = GraphTree.TreePropertyDescriptor(plugArrayKey, default=False,
	                                         inherited=False, breakTags=("main", ),
	                                         desc="Is this plug an array?")

	dataType : DataType = GraphTree.TreePropertyDescriptor("dataType", default=DataType.Int,
	                                            inherited=False, breakTags=("main", ),
	                                            desc="Data type of this plug")

	def isInput(self)->bool:
		"""if this is an input plug"""
		return INPUT_NAME in self.address(includeSelf=True)
	def isOutput(self)->bool:
		"""if this is an output plug"""
		return OUTPUT_NAME in self.address(includeSelf=True)
	def isInvalid(self)->bool:
		"""if this is an invalid plug"""
		return not (self.isInput() or self.isOutput())

	pass







