from __future__ import annotations

"""base class for any node that may replace the params of another node"""

import networkx as nx
from weakref import WeakSet

from .nodedata import NodeDataHolder
from .node import ChimaeraNode

class TransformNode(ChimaeraNode):
	nodeTypeId = 3
	pass

	def result(self, prevData:NodeDataHolder)->NodeDataHolder:
		"""all transformers must implement a result()
		function to return the transformed node params"""
		raise NotImplementedError

