

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
from chimaera.ui.base import GraphicsItemChange
from chimaera.ui.delegate import NodeDelegate, EdgeDelegate
from chimaera.lib.topology import orderNodes

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

	itemChanged = QtCore.Signal(GraphicsItemChange)


	def __init__(self, parent:ChimaeraGraphWidget=None
	             ):
		super(ChimaeraGraphScene, self).__init__(parent)


		self.tiles = {} #type: Dict[ChimaeraNode, NodeDelegate]
		self.pipes = {} #type: Dict[tuple[ChimaeraNode, ChimaeraNode, str], EdgeDelegate]


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
		print("on nodes changed")
		for i in delta.added:
			self.makeTile(i)
		for i in delta.removed:
			self.deleteTile(i)

	def onEdgesChanged(self, delta:GraphEdgeDelta):
		"""called when an edge is created or dereferenced in the graph"""
		print("on edges changed")
		for i in delta.added:
			self.addEdge(i)
		for i in delta.removed:
			self.deletePipe(i)


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
		# add node delegates
		for node in self.graph().nodes:
			self.addTile(node)
		# add edge delegates
		print("graph edges", self.graph().edges, tuple(self.graph().edges))
		for edge in tuple(self.graph().edges):
			self.addEdge(tuple(edge))
		self.layoutTiles()

	def addEdge(self, edge:tuple[ChimaeraNode, ChimaeraNode, str])->EdgeDelegate:
		edgeDelegate = EdgeDelegate(edge)
		self.pipes[edge] = edgeDelegate
		self.addItem(edgeDelegate)
		print("edge", edgeDelegate)
		self.itemChanged.connect(edgeDelegate.onSceneItemChange)
		edgeDelegate.sync()
		return edgeDelegate



	def addTile(self, node:ChimaeraNode)->NodeDelegate:
		if node in self.tiles:
			return self.tiles[node]
		delegate = self.makeTile(node)
		self.tiles[node] = delegate
		self.addItem(delegate)
		self.itemChanged.connect(delegate.onSceneItemChange)
		return delegate

	def makeTile(self, node:ChimaeraNode=None,
	             pos:Union[
		             QtCore.QPoint, QtCore.QPointF, None]=None,
	             )->NodeDelegate:
		if isinstance(self.tiles.get(node), NodeDelegate):
			raise RuntimeError("added node already in scene")

		delegateCls = self.delegateForNode(node)

		tile = delegateCls(node, parent=None
		                   )
		self.addItem(tile)

		if pos is None:
			pos = QtCore.QPointF(random.random(), random.random())

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



	# def clearSelectionAttr(self):
	# 	"""clears "selected" attr for tiles and pipes that are not selected"""

	def onSceneSelectionChanged(self, *args, **kwargs):
		"""passed no arguments, just fires every change
		iterate through nodes - call the selected signal on each"""
		for i in self.tiles.values():
			i.onSceneSelectionChanged()

	def onDeleteCalled(self):
		"""delete selected tiles and pipes"""
		print("on delete called")
		# print("edges", self.graph().edges)
		# print("nodes", self.graph().edges)
		print("sel edges", self.selectedPipes())
		print("sel nodes", self.selectedTiles())

		for i in self.selectedPipes():
			# try:
			self.graph().remove_edge(*i.edgeTuple)
			# except:
			# 	continue
		for i in self.selectedTiles():
			# try:
			self.graph().removeNode(i.node)
			# except:
			# 	continue
			#print("node graph nodes are {}".format(self.graph.knownNames))
		#self.sync()

			#self.deletePipe(i)

		#print self.selectedTiles()


	def deleteTile(self, tile:(NodeDelegate, ChimaeraNode)):
		# check if tile has a visual item - if not, return
		if isinstance(tile, ChimaeraNode):
			if tile not in self.tiles.keys():
				return
			tile = self.tiles[tile]

		# delete any necessary edges
		for k, v in self.pipes.items():
			if tile.node in k:
				self.deletePipe(v)
		self.tiles.pop(tile.node)
		self.removeItem(tile)
		self.update()


	def deletePipe(self, pipe:(EdgeDelegate, tuple[ChimaeraNode, ChimaeraNode, str])):
		if not isinstance(pipe, EdgeDelegate):
			if not pipe in self.pipes.keys():
				return
			pipe = self.pipes[pipe]
		if debugEvents: print("scene deletePipe")
		self.pipes.pop(pipe.edgeTuple)
		self.removeItem(pipe)
		self.update()
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
		islands = nx.strongly_connected_components(self.graph())
		for index, island in enumerate(islands):
			print(self.graph().nodes)
			ordered = orderNodes(self.graph(), island)
			# only x for now
			baseTile = self.tiles[ordered[0]]
			separation = 75
			baseX = baseTile.pos().x() + baseTile.sceneBoundingRect().width() + separation
			x = baseX
			for i in ordered[1:]:
				tile = self.tiles[i]
				tile.setX(x)
				x += tile.sceneBoundingRect().width() + separation
		#self.updatePipePaths(tiles)

	def mouseReleaseEvent(self, event):
		super(ChimaeraGraphScene, self).mouseReleaseEvent(event)



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

