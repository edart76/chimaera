
from __future__ import annotations

"""base class for literally anything in chimaera graph - 
it it ha to be referenced, transformed etc, it has to be a node"""

import networkx as nx
from weakref import WeakSet
import typing as T
if T.TYPE_CHECKING:
	from .graph import ChimaeraGraph
	from chimaera.transform import TransformNode
from tree import Tree

from tree.lib.object import DataFacade, UidElement, PostInitMixin
from tree import Signal



from .graphdata import GraphData
from .nodedata import NodeDataHolder, NodeDataTree
from chimaera.constant import NodeDataKeys, DataUse

class NodeParamDescriptor:
	"""descriptor for values that can be read and set from node params -
	if necessary creating an override"""
	def __init__(self, key:str):
		self.key = key

	def __get__(self, instance:ChimaeraNode, owner):
		return instance.getParam(self.key)

	def __set__(self, instance:ChimaeraNode, value):
		instance.setParam(self.key, value)


class ChimaeraNode(DataFacade, #PostInitMixin
                   ):
	"""active node object

	ONLY a chimaeraNode object can BE REFERENCED,
	or CAN BE A REFERENCE

	where possible, add to this class rather than subclassing - would be handy if
	every kind of node in chimaera had behaviour defined totally by its own params
	"""

	validDataTypes = DataUse

	name = NodeParamDescriptor(NodeDataKeys.nodeName)
	NodeParamDescriptor = NodeParamDescriptor

	uid : str = DataFacade.FacadeDescriptor("", getFn=lambda x : x.uid,
	                                        objectName=NodeDataKeys.paramTree)

	nodeTypeId = 1

	dataCls = NodeDataHolder

	@classmethod
	def defaultParamTree(cls, name:str, uid=None)->NodeDataTree:
		"""default parametre format for this type of node
		for now this will remain a class method - until we meet a case
		that it restricts I'm fine with it,
		and it prevents any messing around with half-initialised node objects
		"""
		dataTree = NodeDataTree(name="root", treeUid=uid)
		dataTree.lookupCreate = True
		dataTree.nodeName = name
		return dataTree

	@classmethod
	def create(cls, name:str, uid=None, graph:ChimaeraGraph=None)->ChimaeraNode:
		"""create a new node of this type"""
		nodeParams = cls.defaultParamTree(name, uid)
		return cls(graph, nodeParams)


	def __init__(self, graph:ChimaeraGraph, nodeParams:NodeDataTree):
		super(ChimaeraNode, self).__init__()

		#print("node init tree", nodeParams.displayStr())
		self._dataObjects[NodeDataKeys.paramTree] = nodeParams
		#print("node data tree", self.baseParams)

		self._graph : ChimaeraGraph = None
		self.setGraph(graph)

		self.nodeEvaluated = Signal("nodeEvaluated")
		self.dirty = False

		self.paramsChanged = Signal()
		# connect tree signals to node changed signal
		for signal in nodeParams.signals():
			signal.connect(self.paramsChanged)

		# action hierarchy for context menu - this at least won't be instanced
		self.baseActionTree = Tree(name="actions") #type:Tree[str, partial]
		self.baseActionTree.lookupCreate = True


	# def __postInit__(self):
	# 	"""run any post init code after subclassed inits are complete"""
	# 	pass

	def setGraph(self, graph:ChimaeraGraph):
		self._graph = graph
	def graph(self)->ChimaeraGraph:
		return self._graph


	@property
	def baseParams(self)->NodeDataTree:
		"""return param tree before any composition or resolving is done on it"""
		return self.dataObject(NodeDataKeys.paramTree)


	def __hash__(self):
		return self.baseParams.__hash__()

	def __repr__(self):
		# return "<{} {}, params: \n{}>".format(self.__class__.__name__, self.name,		                                  self.baseParams.displayStr())
		try:
			name = self.getParam(NodeDataKeys.nodeName)
		except:
			name = self.baseParams[NodeDataKeys.nodeName]
		return "<{} {}>".format(self.__class__.__name__, name)

	def outputDataForUse(self, use:DataUse)->GraphData:
		"""get output information on node"""
		if use == DataUse.Params:
			dataTrees = [self.params()]
			outGraphData = GraphData(dataTrees)
		elif use == DataUse.Flow:
			outGraphData = self.outputFlowData()
		else:
			outGraphData = GraphData()
		return outGraphData

	def params(self)->NodeDataTree:
		"""return either this node's base params or the result of its
		input
		no caching yet
		"""
		# check if node has any direct inputs for params
		if self.isReference():
			# may be multiple inputs
			refGraphData = self.graph().incomingDataForUse(self, DataUse.Params)

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
		if self.graph().nodeInputMap(self)[DataUse.Flow]:
			incomingData = self.graph().incomingDataForUse(self, DataUse.Flow)
		else:
			# by default we run the node's own transform on its own param tree if no data is given -
			# I think this is inkeeping with expected behaviour of a transformer
			incomingData = GraphData([self.params()])
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
		#self.overrideParams(key).value = value
		self.baseParams(key).value = value

	def getParam(self, key:str, default:(None, Exception)=None, errorNotFound=True):
		params = self.params()
		branch = params.getBranch(key)
		if branch is None:
			if errorNotFound:
				raise KeyError("Key {} not found in params {} of node {}".format(key, self.params(), self))
			return default
		return branch.value


	def applyOverride(self, dataToOverride: NodeDataTree,
	                  overrideData:NodeDataTree=None) -> NodeDataTree:
		"""apply information in baseParams.override to dataToOverride
		should act on holder's baseParams
		"""
		overrideData = overrideData or self.baseParams
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
		return inputData.copy()

	def inputNodes(self) -> list[ChimaeraNode]:
		return self.graph().predecessors(self)

	def isReference(self) -> bool:
		"""return True if this node has a live input to its parametres"""
		return bool(self.graph().nodeInputMap(self)[DataUse.Params])

	def inputData(self, use:DataUse)->GraphData:
		return self.graph().incomingDataForUse(self, use)

	def execute(self, inputFlowData:GraphData)->GraphData:
		"""Runs any transform operation on input data - the output of this function
		(if not None) is saved as the Flow data of this node
		"""


	def nodeValid(self):
		return self.graph().nodeValid(self)



