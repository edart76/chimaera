
from __future__ import annotations

"""base class for literally anything in chimaera graph - 
it it ha to be referenced, transformed etc, it has to be a node"""

import networkx as nx
from weakref import WeakSet
import typing as T
if T.TYPE_CHECKING:
	from .main import ChimaeraGraph
	from .transform import TransformNode
	from .graphdata import SubgraphData
from .nodedata import NodeDataHolder, NodeDataTree
from chimaera.constant import NodeDataKeys

from tree.lib.object import DataFacade, UidElement

class ChimaeraNode(DataFacade):
	"""active node object

	ONLY a chimaeraNode object can BE REFERENCED,
	or CAN BE A REFERENCE

	where possible, add to this class rather than subclassing - would be handy if
	every kind of node in chimaera had behaviour defined totally by its own params
	"""

	name : str = DataFacade.FacadeDescriptor(NodeDataKeys.nodeName, objectName=NodeDataKeys.paramTree)

	uid : str = DataFacade.FacadeDescriptor("", getFn=lambda x : x.uid,
	                                        objectName=NodeDataKeys.paramTree)

	nodeTypeId = 1

	dataCls = NodeDataHolder


	def __init__(self, semGraph:ChimaeraGraph, dataArgs:tuple[NodeDataTree, NodeDataTree]):
		super(ChimaeraNode, self).__init__()
		self._dataObjects[NodeDataKeys.paramTree], \
		self._dataObjects[NodeDataKeys.overrideTree] = dataArgs[0], dataArgs[1]

		self.semGraph = semGraph

		self.dirty = False

	@property
	def baseParams(self)->NodeDataTree:
		return self.dataObject(NodeDataKeys.paramTree)
	@property
	def overrideParams(self)->NodeDataTree:
		return self.dataObject(NodeDataKeys.overrideTree)


	def __repr__(self):
		return "<{} {}, params: {}>".format(self.__class__.__name__, self.name,
		                                  self.baseParams.displayStr())


	def applyOverride(self, dataToOverride:NodeDataTree)->NodeDataTree:
		"""apply information in baseParams.override to dataToOverride
		should act on holder's baseParams
		"""
		return dataToOverride

	def transform(self, inputGraphData:SubgraphData)->SubgraphData:
		"""default implementation of transform does not process wider
		graph structure at all, just runs transformData() on each
		node params tree in turn"""
		for uid, (dataTree, overrideTree) in dict(inputGraphData.nodeDatas).items():
			dataTree = self.transformData(dataTree)
			inputGraphData.nodeDatas[uid] = (dataTree, overrideTree)
		return inputGraphData

	def transformData(self, inputData:NodeDataTree)->NodeDataTree:
		"""defines any transform that this node may do on params when used
		as input to another -
		in the base class, as a direct reference, return copy of THIS NODE's params
		any modification should act on holder's baseParams
		"""
		return self.semGraph.nodeData(self).copy()


	def inputNodes(self)->list[ChimaeraNode]:
		return self.semGraph.predecessors(self)

	def params(self)->NodeDataTree:
		"""return either this node's base params or the result of its
		input
		no caching yet
		"""
		return self.semGraph.nodeData(self)

	def nodeValid(self):
		return self.semGraph.nodeValid(self)







