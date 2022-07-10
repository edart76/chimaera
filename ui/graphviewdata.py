
from __future__ import annotations

"""small dataclass holding information for a single view of a graph - 
current query, maybe node positions, view name etc"""

from dataclasses import dataclass

from chimaera.core.graph import ChimaeraNode, ChimaeraGraph


from chimaera.ui.delegate import NodeDelegate, EdgeDelegate
from chimaera.lib.query import GraphQuery


@dataclass
class GraphViewData:

	graph: ChimaeraGraph
	positions : dict[ChimaeraNode, tuple[int, int]]
	cameraTransform : tuple[int, int, int] # x, y, scale

	queryFilter : GraphQuery

	name : str = ""

	def shortName(self)->str:
		"""name to display in a single tab"""
		if self.name:
			return self.name
		return self.queryFilter.queryText


	def longName(self)->str:
		"""name to display in full in tooltip"""
		return self.graph.name + "::\n\t" + self.shortName()





