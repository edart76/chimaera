from __future__ import annotations

from dataclasses import dataclass
import typing as T
from networkx import Graph

from tree import Signal

if T.TYPE_CHECKING:
	from chimaera import ChimaeraNode
	from chimaera.core.graph import ChimaeraGraph
from tree.lib.delta import DeltaAtom, DeltaTracker




@dataclass
class GraphNodeDelta(DeltaAtom):
	"""only for structural changes in graph - nodes also define their
	own signals for internal data changes

	TEST - only allow this specific object to actually modify the graph
	"""
	added : set[ChimaeraNode] = frozenset()
	removed : set[ChimaeraNode] = frozenset()

	def doDelta(self, target:ChimaeraGraph):
		target.signalComponent.pauseDeltaGathering()
		if self.added:
			target.add_nodes_from(self.added)
		if self.removed:
			target.remove_nodes_from(self.removed)
		target.signalComponent.unPauseDeltaGathering()

	def undoDelta(self, target:ChimaeraGraph):
		target.signalComponent.pauseDeltaGathering()
		if self.added:
			target.remove_nodes_from(self.added)
		if self.removed:
			target.add_nodes_from(self.removed)
		target.signalComponent.unPauseDeltaGathering()


@dataclass
class GraphEdgeDelta(DeltaAtom):
	"""deltas concerning edges - this will not pick up changes
	in edge data, we use a """
	added : set[tuple] = frozenset()
	removed : set[tuple] = frozenset()


	def doDelta(self, target:ChimaeraGraph):
		target.signalComponent.pauseDeltaGathering()
		if self.added:
			target.add_edges_from(self.added)
		if self.removed:
			target.remove_edges_from(self.removed)
		target.signalComponent.unPauseDeltaGathering()


	def undoDelta(self, target:ChimaeraGraph):
		target.signalComponent.pausedDeltaGathering()
		if self.added:
			target.remove_edges_from(self.added)
		if self.removed:
			target.add_edges_from(self.removed)
		target.signalComponent.unPauseDeltaGathering()

class GraphDeltaTracker(DeltaTracker):
	pass


class GraphSignalContext:
	"""weird intermediate object returned from
	'with graph.signals.mute()'
	"""
	def __init__(self, signalComponent:GraphDeltaSignalComponent, muteSignals=True):
		self.component = signalComponent
		self.muteSignals = muteSignals

	def __enter__(self):
		self.component.pauseDeltaGathering()

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.component.unPauseDeltaGathering()
		if exc_type is not None:
			raise exc_type


class GraphDeltaSignalComponent:
	"""emit signals when graph structure changes to keep UI
	in sync

	node delta must call the same superclass functions that generate deltas -
	manage pauseDeltaGathering state properly here

	"""
	nodeFns = (Graph.add_node, Graph.add_nodes_from,
	           Graph.remove_node, Graph.remove_nodes_from,
	           Graph.update, Graph.clear)

	edgeFns = (Graph.add_edge, Graph.add_edges_from,
	           Graph.remove_edge, Graph.remove_edges_from,
	           )

	allFns = set(nodeFns).union(edgeFns)
	def __init__(self, graph:Graph):
		self.graph = graph
		self.pausedDeltaGathering = False

		# signal for user change to graph
		self.deltaAdded = Signal(name="deltaAdded")

		# end signals for final state of graph
		self.nodesChanged = Signal(name="nodesChanged")
		self.edgesChanged = Signal(name="edgesChanged")

		self.prevNodes : set[ChimaeraNode] = set()
		self.prevEdges : set[tuple] = set()

		# wrap graph instance
		for i in self.allFns:
			setattr(self.graph, i.__name__, self.wrapGraphFn(self.graph,
				getattr(self.graph, i.__name__)))


	def pauseDeltaGathering(self):
		self.pausedDeltaGathering = True
		return GraphSignalContext(self, muteSignals=True)

	def unPauseDeltaGathering(self):
		self.pausedDeltaGathering = False

	def emitDelta(self, delta:(GraphNodeDelta, GraphEdgeDelta)):
		"""called to add a new delta
		only add the delta if deltaGathering is not paused"""
		if not self.pausedDeltaGathering:
			self.deltaAdded.emit(delta)
		if isinstance(delta, GraphNodeDelta):
			self.nodesChanged.emit(delta)
		if isinstance(delta, GraphEdgeDelta):
			self.edgesChanged.emit(delta)
		pass

	def gatherNodeSet(self, graph:Graph)->set[ChimaeraNode]:
		"""run before a node-altering function to gather list of pre-change nodes to compare"""
		return set(graph.nodes)

	def gatherEdgeSet(self, graph:Graph):
		#print("gather edge set", graph.edges)
		return set(graph.edges)

	def _deltaFromSets(self, baseSet, newSet, deltaCls:T.Type[DeltaAtom]):
		added = newSet - baseSet
		removed = baseSet - newSet
		if not added and not removed:
			return None
		return deltaCls(added=added, removed=removed)

	def deltaFromNodeSets(self, baseSet:set[ChimaeraNode], newSet:set[ChimaeraNode])-> GraphNodeDelta:
		return self._deltaFromSets(baseSet, newSet, GraphNodeDelta)
	def deltaFromEdgeSets(self, baseSet:set[tuple], newSet:set[tuple])-> GraphEdgeDelta:
		return self._deltaFromSets(baseSet, newSet, GraphEdgeDelta)

	def wrapGraphFn(self, graphInstance:Graph, instanceFn:T.Callable):
		"""apply decorator to the given graph cls function
		nodes may also remove edges when they remove"""
		# print("wrapGraphFn", graphInstance, instanceFn)
		def wrapperFn(*args, **kwargs):
			# print("wrapper", args, kwargs)

			baseNodeSet = self.gatherNodeSet(graphInstance)
			baseEdgeSet = self.gatherEdgeSet(graphInstance)
			# run base function
			baseResult = instanceFn(*args, **kwargs)
			# compare new node set
			newNodeSet = self.gatherNodeSet(graphInstance)
			newEdgeSet = self.gatherEdgeSet(graphInstance)
			# build deltas
			nodeDelta = self.deltaFromNodeSets(baseNodeSet, newNodeSet)
			edgeDelta = self.deltaFromEdgeSets(baseEdgeSet, newEdgeSet)
			if nodeDelta:
				if nodeDelta.added or nodeDelta.removed:
					self.emitDelta(nodeDelta)
			if edgeDelta:
				if edgeDelta.added or edgeDelta.removed:
					self.emitDelta(edgeDelta)
			return baseResult
		return wrapperFn
