from __future__ import annotations
"""execution component governing state of graph and nodes"""
import traceback, pprint
import networkx as nx
import typing as T
from collections import defaultdict
if T.TYPE_CHECKING:
	from chimaera.core.graph import ChimaeraGraph
	from chimaera.core.node import ChimaeraNode
	from chimaera.lib.delta import GraphNodeDelta, GraphEdgeDelta, GraphDeltaSignalComponent, GraphDeltaTracker

from tree import Signal

from chimaera.constant import GraphEvalModes
from chimaera import GraphData, DataUse

toUid = lambda x: x if isinstance(x, str) else x.uid

class GraphExecutionContext:
	"""not sure if this should be specific for each node,
	for each entire evaluation queue, or whatever"""
	def __init__(self):
		pass
	def __enter__(self):
		pass
	def __exit__(self, exc_type, exc_val, exc_tb):
		if exc_type is not None:
			traceback.print_exc()
			raise exc_type(exc_val)
		pass

class GraphExecutionComponent:
	"""track state of nodes in graph - if they have been eval'd
	are dirty

	on node data requested, evaluate all dirty nodes in its history
	on node data changed, set all nodes in its future dirty

	queue up nodes and evaluate them one by one -
	party like it's maya 4.0

	however this component must be robust to changing graph topology during
	eval - from gathering, collapsing or regenerating nodes

	if graph structure changes while a node queue is being evaluated,
	mark all new nodes as dirty -
	rerun the lookup check from the requested node, add any new ones to the
	queue, and continue eval

	"""

	def __init__(self, graph:ChimaeraGraph):
		self.graph = graph
		self.evalMode = GraphEvalModes.Active

		self.dirtyMap : dict[str, bool] = defaultdict(lambda : True)

		# state flags
		self.executingQueue = False
		self._executingNode : ChimaeraNode = None # node currently being evaluated
		self.graphMutatedDuringExec = False

		# state signals
		self.executingNodeChanged = Signal()


	def isDirty(self, node:(str, ChimaeraNode)):
		return self.dirtyMap[toUid(node)]

	def setDirty(self, node:(str, ChimaeraNode), dirty=True,
	             allFuture=True):
		"""mark a node as dirty"""
		self.dirtyMap[toUid(node)] = dirty
		# optionally apply to all nodes in future
		if allFuture:
			for futureNode in nx.descendants(self.graph, node):
				self.setDirty(futureNode, dirty, allFuture=False)



	@property
	def executingNode(self)->(ChimaeraNode, None):
		return self._executingNode

	def setExecutingNode(self, node:(ChimaeraNode, None)):
		self._executingNode = node
		self.executingNodeChanged.emit(node)

	def evalNode(self, node:ChimaeraNode, markClean=True):
		"""evaluate a single node
		first gather flow data of all preceding nodes, combine data into GraphData object,
		then pass to node
		does not check for dirtyness"""
		# combine trees from input plugs
		graphDatas = []
		for inputNode in self.graph.nodeInputMap(node)[DataUse.Flow]:
			inputData = self.graph.nodeData(inputNode, DataUse.Flow)
			graphDatas.append(inputData)
		combinedData = GraphData.combine(*graphDatas)

		# eval node
		resultData = node.execute(combinedData)

		# set result data in graph
		self.graph.setNodeData(node, resultData, DataUse.Flow)

		if markClean:
			self.setDirty(node, False)

	def onGraphDelta(self, delta:(GraphNodeDelta, GraphEdgeDelta)):
		"""flag that graph structure has changed"""
		if self.executingQueue:
			self.graphMutatedDuringExec = True

	def nodeQueueToEvalNodes(self, nodesToEval:set[ChimaeraNode])->list[ChimaeraNode]:
		"""given a set of requested nodes to evaluate,
		return a list of nodes to evaluate, in order

		we first find generations of nodes that can be done in parallel
		just in case
		"""
		# gather all nodes in history
		allNodes = set(nodesToEval)
		for endNode in nodesToEval:
			allNodes.update(nx.ancestors(self.graph, endNode))

		# build subgraph
		subgraph = self.graph.subgraph(allNodes)
		generationSets = nx.topological_generations(subgraph)
		result = [ genNode for generationSet in generationSets for genNode in generationSet  ]
		return result


	def evalNodes(self, nodesToEval:set[ChimaeraNode]):
		"""main entry function - pass a load of nodes, sit back, watch magic happen
		"""
		# get initial queue
		queue = self.nodeQueueToEvalNodes(nodesToEval)
		self.executingQueue = True
		self.graphMutatedDuringExec = False
		while queue:
			# get next node to eval
			node = queue.pop(0)
			self.setExecutingNode(node)
			if not self.isDirty(node): # skip if clean
				continue

			# eval node
			self.evalNode(node)

			# check for graph mutation
			if self.graphMutatedDuringExec:
				self.graphMutatedDuringExec = False

				""" look up new queue in new graph structure -
				if renewed uids are consistent, any regenerated nodes
				will still be marked as dirty / clean,
				so will be skipped if nothing more to be done
				"""
				# no complex checking for destination eval nodes yet -
				# if they get regenerated too, this will miss them
				queue = self.nodeQueueToEvalNodes(nodesToEval)

		# clear executing queue
		self.executingQueue = False
		self.setExecutingNode(None)




	def onNodeChanged(self, node:ChimaeraNode):
		"""called when a node is changed - set all nodes in its future dirty """


if __name__ == '__main__':
	from chimaera import ChimaeraGraph
	from chimaera.core.node import ChimaeraNode

	graph = ChimaeraGraph()
	nodeA = graph.createNode("a")
	nodeB = graph.createNode("b")
	nodeC = graph.createNode("c")
	graph.connectNodes(nodeA, nodeB)
	graph.connectNodes(nodeB, nodeC)
	print(*nx.topological_sort(graph))
	print(graph.pred)
	print(graph.pred[nodeC])

	#print(nx.ancestors(graph, nodeC))


