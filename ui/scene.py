

from __future__ import annotations

import random
import colorsys
from tree import Tree

from typing import TYPE_CHECKING, Union, Dict, List
import typing as T


from PySide2 import QtCore, QtWidgets, QtGui

if TYPE_CHECKING:
	from chimaera.ui.view import ChimaeraGraphView
	from chimaera.ui.widget import ChimaeraGraphWidget

from treegraph.ui.style import (VIEWER_BG_COLOR,
                                      VIEWER_GRID_COLOR,
                                      VIEWER_GRID_OVERLAY)
from treegraph.ui import relax
from tree.ui.lib import KeyState, keyDict
from tree.lib.inheritance import superClassLookup, containsSuperClass
from tree.ui.libwidget.draggraphicsscene import MouseDragScene


import networkx as nx
from chimaera import ChimaeraGraph, ChimaeraNode
from chimaera.lib.delta import GraphEdgeDelta, GraphNodeDelta
from chimaera.ui.delegate import NodeDelegate, EdgeDelegate

debugEvents = False

def randomPastel(seed):
	random.seed(a=seed)
	h = random.random()
	s = 0.5 + ((random.random()) / 3.0)
	v = 0.7 + ((random.random()) / 5.0)
	rgb = colorsys.hsv_to_rgb(h, s, v)
	return rgb

class ChimaeraGraphScene(MouseDragScene):
	"""graphics scene for interfacing with abstractgraph and ui
	hook directly into abstractgraph tree signals
	"""

	delegateMap = {ChimaeraNode : NodeDelegate} #type:T.Dict[T.Type[ChimaeraNode] : T.Type[NodeDelegate]]

	def __init__(self, parent:ChimaeraGraphWidget=None
	             ):
		super(ChimaeraGraphScene, self).__init__(parent)


		self.tiles = {} #type: Dict[ChimaeraNode, NodeDelegate]
		self.pipes = {} #type: Dict[tuple[ChimaeraNode, ChimaeraNode], EdgeDelegate]


		self.background_color = VIEWER_BG_COLOR
		self.grid = VIEWER_GRID_OVERLAY
		self.grid_color = VIEWER_GRID_COLOR

		# signal hookups
		self.selectionChanged.connect(self.onSceneSelectionChanged)

	def setGraph(self, graph:ChimaeraGraph):
		"""connect signals"""
		graph.signalComponent.nodesChanged.connect(self.onNodesChanged)
		graph.signalComponent.edgesChanged.connect(self.onEdgesChanged)
		self.sync()

	def parent(self) -> ChimaeraGraphWidget:
		return super(ChimaeraGraphScene, self).parent()

	def graph(self)->ChimaeraGraph:
		return self.parent().graph


	### region graph signal functions, direct match to tree signals
	def onNodesChanged(self, delta:GraphNodeDelta):
		"""match nodes to graph"""


	def onEdgesChanged(self, delta:GraphEdgeDelta):
		"""called when an edge is created or dereferenced in the graph"""


	@classmethod
	def registerNodeDelegate(cls, nodeCls, delegateCls):
		"""used to register custom node drawing class"""
		cls.delegateMap[nodeCls] = delegateCls

	@classmethod
	def delegateForNode(cls, node:ChimaeraNode)->T.Type[NodeDelegate]:
		"""look up the nearest matching delegate for
		given node"""
		result = superClassLookup(cls.delegateMap, node)
		if result is None:
			raise RuntimeError("No drawing delegate found for {} or in {}".format(
				type(node), type(node).__mro__	))
		return result

	def sync(self):
		"""fully clears and resets scene - may be costly
		use until we need more targeted processing"""
		self.clear()
		for node in self.graph().nodes:
			self.addTile(node)

	def addTile(self, node:ChimaeraNode)->NodeDelegate:
		if node in self.tiles:
			return self.tiles[node]
		delegate = self.makeTile(node)
		self.tiles[node] = delegate
		self.addItem(delegate)
		return delegate

	def makeTile(self, node:ChimaeraNode=None,
	             pos:Union[
		             QtCore.QPoint, QtCore.QPointF, None]=(0, 0),
	             )->NodeDelegate:
		if isinstance(self.tiles.get(node), NodeDelegate):
			raise RuntimeError("added node already in scene")

		delegateCls = self.delegateForNode(node)

		tile = delegateCls(node, parent=None
		                   )
		self.addItem(tile)

		if isinstance(pos, (QtCore.QPointF, QtCore.QPoint)):
			tile.setPos(pos)
		else:
			tile.setPos(*pos)
		self.tiles[node] = tile
		#self.addItem(tile.settingsProxy)
		self.relaxItems([tile], iterations=2)
		return tile

	# def addEdgePipe(self, edge:=None):
	# 	"""can only be done with an existing abstractEdge"""
	# 	if debugEvents: print("scene addEdgePipe")
	# 	if edge:
	# 		start = self.tiles[edge.source[0]].knobs[
	# 			edge.source[1].stringAddress()]
	# 		end = self.tiles[edge.dest[0]].knobs[
	# 			edge.dest[1].stringAddress()]
	# 		pipe = EdgeDelegate(start=start, end=end, edge=edge)
	#
	# 		self.pipes[edge] = pipe
	#
	# 		self.addPipe(pipe)
	#
	# 		return pipe

	# def layoutNodes(self, nodes:list[NodeDelegate]):
	# 	"""moves around given nodes to avoid intersections (if possible)"""

	def addPipe(self, pipe):
		self.addItem(pipe)
		pipe.drawPath(pipe.start, pipe.end)

	def updatePipePaths(self, tiles:List[NodeDelegate]=None):
		"""updates everything for now - if that gets laggy only redraw changed"""
		# print("scene update")
		# print("graph edges", self.graph.edges)
		if tiles:
			edges = set()
			for i in tiles:
				# edges.update(i.node.edges)
				edges.update(self.graph.nodeEdges(i.node, all=True))
			pipes = [self.pipes[i] for i in edges]
		else:
			pipes = self.pipes.values()
		for i in pipes:
			i.redrawPath()

	# def clearSelectionAttr(self):
	# 	"""clears "selected" attr for tiles and pipes that are not selected"""

	def onSceneSelectionChanged(self, *args, **kwargs):
		"""passed no arguments, just fires every change
		iterate through nodes - call the selected signal on each"""
		for i in self.tiles.values():
			i.onSceneSelectionChanged()

	def onDeleteCalled(self):
		"""delete selected tiles and pipes"""
		if debugEvents:print("scene onDeleteCalled")
		if debugEvents: print("selection is {}".format(self.selectedItems()))
		for i in self.selectedPipes():
			self.graph.deleteEdge(i.edge)
		for i in self.selectedTiles():
			self.deleteTile(i)
			self.graph.deleteNode(i.node)
			#print("node graph nodes are {}".format(self.graph.knownNames))


			#self.deletePipe(i)

		#print self.selectedTiles()


	def deleteTile(self, tile):
		"""ONLY VISUAL"""
		if isinstance(tile, GraphNode):
			if tile not in list(self.tiles.keys()):
				return
			tile = self.tiles[tile]
		for i in tile.node.edges:
			pipe = self.pipes[i]
			self.deletePipe(pipe)
		# for k, v in self.tiles.iteritems():
		# 	if v == tile:
		# 		target = k
		#self.tiles.pop(target)
		self.tiles.pop(tile.node)
		self.removeItem(tile)

	# def deleteEdgePipe(self, edge:GraphEdge):
	# 	"""called when a graph edge is deleted or dereferenced
	# 	"""


	def deletePipe(self, pipe:EdgeDelegate):
		if debugEvents: print("scene deletePipe")
		# if isinstance(pipe, GraphEdge):
		# 	if pipe not in list(self.pipes.keys()):
		# 		return
		# 	pipe = self.pipes[pipe]

		self.pipes.pop(pipe.edge)

		# remove pipe references from knobs
		for knob in pipe.start, pipe.end:
			if pipe in knob.pipes:
				knob.pipes.remove(pipe)
		self.removeItem(pipe)
		# i never want to tipe pipe


	def selectedTiles(self):
		nodes = []
		for item in self.selectedItems():
			if isinstance(item, NodeDelegate):
				nodes.append(item)
		return nodes

	def selectedPipes(self):
		return [i for i in self.selectedItems()
		        if isinstance(i, EdgeDelegate)]

	def mousePressEvent(self, event):
		if debugEvents: print("scene mousePress")
		super(ChimaeraGraphScene, self).mousePressEvent(event)
		if event.isAccepted():
			if debugEvents: print("scene mousePress accepted, returning")
			return True
		selected_nodes = self.selectedTiles()
		# if self.activeView:
		# 	self.activeView.beginDrawPipes(event)

	def relaxItems(self, items, iterations=1):
		for n in range(iterations):
			for i in items:
				force = relax.getForce(i)
				i.setPos(i.pos() + force.toPointF())

	def layoutTiles(self, tiles:List[NodeDelegate]=None):
		"""single shot layout of all given nodes
		seed nodes are only arranged vertically
		Longest critical path taken as the baseline,
		other nodes laid out relative to it


		"""
		tiles = tiles or set(self.tiles.values())
		nodes = set(i.node for i in tiles)
		islands = nx.connected_components(self.graph())
		for index, island in enumerate(islands):
			ordered = self.graph.orderNodes(island)

			# only x for now
			baseTile = self.tiles[ordered[0]]
			separation = 75
			baseX = baseTile.pos().x() + baseTile.sceneBoundingRect().width() + separation
			x = baseX
			for i in ordered[1:]:
				tile = self.tiles[i]
				tile.setX(x)
				x += tile.sceneBoundingRect().width() + separation
		self.updatePipePaths(tiles)

	def mouseReleaseEvent(self, event):
		super(ChimaeraGraphScene, self).mouseReleaseEvent(event)

	def keyPressEvent(self, event):
		"""we first dispatch event to any scene widgets,
		as event flow in graphics scene goes from outer
		to inner, not the reverse

		only run scene operations if it has NOT been accepted"""
		#print("scene keyPressEvent", keyDict[event.key()])
		super(ChimaeraGraphScene, self).keyPressEvent(event)
		if event.isAccepted():
			#print("scene event accepted")
			return

		if event.key() in ( QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace ):
			self.onDeleteCalled()



	### region drawing

	# endregion

	def serialiseUi(self, graphData):
		"""adds ui information to serialised output from graph
		no idea where better to put this"""
		for node, tile in self.tiles.items():
			graphData["nodes"][node.uid]["ui"] = tile.serialise()

	def regenUi(self, graphData):
		"""reapplies saved ui information to tiles"""
		for uid, info in graphData["nodes"].items():
			node = self.graph.nodeFromUID(uid)
			tile = self.tiles[node]
			tile.setPos(QtCore.QPointF(*info["ui"]["pos"]))

