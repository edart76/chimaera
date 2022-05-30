

from __future__ import annotations
"""subclass for specific node for hierarchy
this node tracks position in tree - linked data node
holds actual data?

"""
import networkx as nx
from weakref import WeakSet
import typing as T
if T.TYPE_CHECKING:
	from .main import ChimaeraGraph
	from .transform import TransformNode
from .nodedata import NodeDataHolder, NodeDataTree

class ChimaeraTreeNode:
	"""active node object"""

	nodeTypeId = 1

	# @classmethod
	# def dataFormat(cls)->dict:
	# 	"""return the format of data to use in this node"""
	# 	return {"name"}

	dataCls = NodeDataHolder


	def __init__(self, semGraph:ChimaeraGraph, data:NodeDataHolder):
		self.semGraph = semGraph
		self.baseData : NodeDataHolder = data

	def uid(self)->str:
		"""uid is ALWAYS linked to the base data"""
		return self.baseData.uid

	def name(self):
		return self.data().name

	def setDataHolder(self, data:dataCls):
		self.baseData = data

	def applyOverride(self, dataToOverride:NodeDataHolder)->NodeDataHolder:
		"""apply information in baseData.override to dataToOverride
		"""
		return dataToOverride

	def addInput(self):
		"""almost sure this should be done by graph"""

	def inputNodes(self)->list[ChimaeraNode]:
		return [self.semGraph.node(i) for i in self.baseData.inputUids]

	def data(self)->NodeDataHolder:
		"""return either this node's base data or the result of its
		input
		no caching yet
		"""
		return self.semGraph.nodeData(self)

	def dataTree(self)->NodeDataTree:










