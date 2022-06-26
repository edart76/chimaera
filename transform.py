from __future__ import annotations

"""base class for any node that may replace the params of another node"""

from chimaera.core.nodedata import NodeDataHolder
from chimaera.core.node import ChimaeraNode

class TransformNode(ChimaeraNode):
	nodeTypeId = 3
	pass

	def result(self, prevData:NodeDataHolder)->NodeDataHolder:
		"""all transformers must implement a result()
		function to return the transformed node params"""
		raise NotImplementedError

