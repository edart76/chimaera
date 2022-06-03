
from __future__ import annotations

"""base class for literally anything in chimaera graph - 
it it ha to be referenced, transformed etc, it has to be a node"""

import networkx as nx
from weakref import WeakSet
import typing as T
if T.TYPE_CHECKING:
	from .main import ChimaeraGraph
	from .transform import TransformNode

from .graphdata import GraphData
from .nodedata import NodeDataHolder, NodeDataTree
from chimaera.constant import NodeDataKeys, DataUse

from tree.lib.object import DataFacade, UidElement
from tree import Signal

class NodeParamDescriptor:
	"""descriptor for values that can be read and set from node params -
	if necessary creating an override"""
	def __init__(self, key:str):
		self.key = key

	def __get__(self, instance:ChimaeraNode, owner):
		return instance.getParam(self.key)

	def __set__(self, instance:ChimaeraNode, value):
		instance.setParam(self.key, value)


class ChimaeraNode(DataFacade):
	"""active node object

	ONLY a chimaeraNode object can BE REFERENCED,
	or CAN BE A REFERENCE

	where possible, add to this class rather than subclassing - would be handy if
	every kind of node in chimaera had behaviour defined totally by its own params
	"""

	validDataTypes = DataUse

	name = NodeParamDescriptor(NodeDataKeys.nodeName)

	uid : str = DataFacade.FacadeDescriptor("", getFn=lambda x : x.uid,
	                                        objectName=NodeDataKeys.paramTree)

	nodeTypeId = 1

	dataCls = NodeDataHolder


	def __init__(self, semGraph:ChimaeraGraph, dataArgs:tuple[NodeDataTree, NodeDataTree]):
		super(ChimaeraNode, self).__init__()
		self._dataObjects[NodeDataKeys.paramTree], \
		self._dataObjects[NodeDataKeys.overrideTree] = dataArgs[0], dataArgs[1]

		self.graph = semGraph
		self.nodeEvaluated = Signal("nodeEvaluated")
		self.dirty = False

		self.paramsChanged = Signal()
		# connect tree signals to node changed signal
		for i in dataArgs:
			for signal in i.signals():
				signal.connect(self.paramsChanged)


	@property
	def baseParams(self)->NodeDataTree:
		return self.dataObject(NodeDataKeys.paramTree)
	@property
	def overrideParams(self)->NodeDataTree:
		return self.dataObject(NodeDataKeys.overrideTree)

	def __hash__(self):
		return self.baseParams.__hash__()

	def __repr__(self):
		# return "<{} {}, params: \n{}>".format(self.__class__.__name__, self.name,		                                  self.baseParams.displayStr())
		return "<{} {}>".format(self.__class__.__name__, self.name)

	def outputDataForUse(self, use:DataUse)->GraphData:
		"""get output information on node"""
		if use == DataUse.Params:
			data = [self.params()]
		elif use == DataUse.Flow:
			data = self.outputFlowData()
		return GraphData(data)

	def params(self)->NodeDataTree:
		"""return either this node's base params or the result of its
		input
		no caching yet
		"""
		# check if node has any direct inputs for params
		if self.isReference():
			# may be multiple inputs
			refGraphData = self.graph.incomingDataForUse(self, DataUse.Params)

			resultTree = None
			if len(refGraphData.nodeDatas) > 1:
				resultTree = self.compositeTrees(refGraphData.nodeDatas)
			else:
				resultTree = refGraphData.nodeDatas[0]
			return self.applyOverride(resultTree)
		return self.baseParams

	def compositeTrees(self, treeList:T.Sequence[NodeDataTree])->NodeDataTree:
		"""return a combined version of the tree list"""
		return treeList[0]

	def outputFlowData(self)->GraphData:
		"""run transformation on input data if defined, return it
		if no input, return the node's param tree instead"""
		if self.graph.nodeInputMap(self)[DataUse.Flow]:
			incomingData = self.graph.incomingDataForUse(self, DataUse.Flow)
		else:
			# by default we run the node's own transform on its own param tree if no data is given -
			# I think this is inkeeping with expected behaviour of a transformer
			incomingData = GraphData(self.params())
		return self.transform(incomingData)

	def setParam(self, key:str, value):
		"""set the value for the given parametre on the node's param trees -
		if needed, an override is created"""
		if not self.isReference():
			self.params()(key).value = value
			return
		# node is reference - check if this value already exists
		existBranch = self.params().getBranch(key)
		# is this value the same as that in live reference? If so, do not create override (for now)
		if existBranch is not None:
			if existBranch.value == value:
				return
		# create override
		self.overrideParams(key).value = value

	def getParam(self, key:str, default:(None, Exception)=None):
		result = self.params().get(key, default)
		# if issubclass(default, Exception) and default == result:
		# 	raise KeyError("Key {} not found in node {}".format(key, self))
		return result

	def applyOverride(self, dataToOverride: NodeDataTree,
	                  overrideData:NodeDataTree=None) -> NodeDataTree:
		"""apply information in baseParams.override to dataToOverride
		should act on holder's baseParams
		"""
		overrideData = overrideData or self.overrideParams
		return dataToOverride

	def transform(self, inputGraphData: GraphData) -> GraphData:
		"""default implementation of transform does not process wider
		graph structure at all, just runs transformData() on each
		node params tree in turn"""
		outputDatas = []
		for dataTree in inputGraphData.nodeDatas:
			dataTree = self.transformData(dataTree)
			outputDatas.append(dataTree)
		# regenerate new graph data object
		newGraphData = GraphData.combine(outputDatas)
		# by default edges are not modified
		newGraphData.edges = inputGraphData.edges
		return inputGraphData

	def transformData(self, inputData: NodeDataTree) -> NodeDataTree:
		"""defines any transform that this node may do on params when used
		as input to another -
		in the base class, as a direct reference, return copy of THIS NODE's params
		any modification should act on holder's baseParams
		"""
		return self.graph.nodeData(self).copy()

	def inputNodes(self) -> list[ChimaeraNode]:
		return self.graph.predecessors(self)

	def isReference(self) -> bool:
		"""return True if this node has a live input to its parametres"""
		return bool(self.graph.nodeInputMap(self)[DataUse.Params])

	def inputData(self, use:DataUse)->GraphData:
		return self.graph.incomingDataForUse(self, use)

	def eval(self)->GraphData:
		"""Runs any transform operation on input data"""


	def nodeValid(self):
		return self.graph.nodeValid(self)







