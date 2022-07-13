

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
from chimaera.lib.query import GraphQuery
from chimaera.ui.base import GraphicsItemChange
from chimaera.ui.delegate import GraphItemDelegateAbstract, NodeDelegate, EdgeDelegate, PlugNodeDelegate, PlugTreeDelegate
from chimaera.lib.topology import orderNodes

from chimaera.ui import graphItemType

debugEvents = False

def randomPastel(seed):
	random.seed(a=seed)
	h = random.random()
	s = 0.5 + ((random.random()) / 3.0)
	v = 0.7 + ((random.random()) / 5.0)
	rgb = colorsys.hsv_to_rgb(h, s, v)
	return rgb

class ChimaeraGraphScene(MouseDragScene):
	"""graphics scene for ChimaeraGraph
	different specific views (tree node view, treeGraph node view) may define
	their own drawing delegates - all should inherit from this

	only top-level items are visible to scene - GraphDelegate items can change internally,
	but if the element of a top-level item is deleted, remove that item

	"""

	#delegateMap = {ChimaeraNode : NodeDelegate} #type:T.Dict[T.Type[GraphItemDelegateAbstract] : T.Type[NodeDelegate]]

	# set of delegate types that this particular scene or view may show
	validDelegates : set[T.Type[GraphItemDelegateAbstract]] = {
		NodeDelegate, EdgeDelegate, PlugNodeDelegate
	}

	# region plugin stuff
	@classmethod
	def registerDrawingDelegate(cls, delegateCls:T.Type[GraphItemDelegateAbstract],
	                            ):
		"""register a new drawing delegate class - no need to wire in specific real
		classes, since the delegate selection system is delegated"""
		cls.validDelegates.add(delegateCls)

	itemChanged = QtCore.Signal(GraphicsItemChange)


	def __init__(self, parent:ChimaeraGraphWidget=None
	             ):
		super(ChimaeraGraphScene, self).__init__(parent)

		self.graphDelegateItems : set[GraphItemDelegateAbstract] = set()

		self.background_color = VIEWER_BG_COLOR
		self.grid = VIEWER_GRID_OVERLAY
		self.grid_color = VIEWER_GRID_COLOR

		self.graphQuery : GraphQuery = None

		# signal hookups
		self.selectionChanged.connect(self.onSceneSelectionChanged)

	def setGraph(self, graph:ChimaeraGraph):
		"""connect signals"""
		graph.signalComponent.nodesChanged.connect(self.onGraphElementsChanged)
		graph.signalComponent.edgesChanged.connect(self.onGraphElementsChanged)
		self.sync()

	def setQuery(self, nodeQuery:GraphQuery):
		self.graphQuery = nodeQuery
		self.onQueryChanged()
		pass

	def onQueryChanged(self):
		"""update scene based on query"""
		self.sync()

	def parent(self) -> ChimaeraGraphWidget:
		return super(ChimaeraGraphScene, self).parent()

	def graph(self)->ChimaeraGraph:
		return self.parent().graph

	def elementDelegateMap(self)->dict[graphItemType, GraphItemDelegateAbstract]:
		"""return map of {graph element : drawing delegate}
		for every singular thing in chimaera graph
		multiple graph elements may map to the same delegate"""
		itemMap = {}
		for delegate in self.graphDelegateItems:
			itemMap.update({subItem : delegate for subItem in delegate.graphItems})
		return itemMap

	def mainElementDelegateMap(self)->dict[graphItemType, GraphItemDelegateAbstract]:
		"""return map of {graph element : drawing delegate}
		for every singular thing in chimaera graph"""
		itemMap = {}
		for delegate in self.graphDelegateItems:
			itemMap[delegate.mainGraphElement()] = delegate
		return itemMap

	def tiles(self)->dict[ChimaeraNode, NodeDelegate]:
		return {element : delegate for element, delegate in self.elementDelegateMap().items() if isinstance(delegate, NodeDelegate)}
	def pipes(self)->dict[tuple, EdgeDelegate]:
		return {edge : delegate for edge, delegate in self.elementDelegateMap().items() if isinstance(delegate, EdgeDelegate)}

	def elementForDelegate(self, delegate:GraphItemDelegateAbstract)->graphItemType:
		"""return graph element for delegate"""
		return delegate.mainGraphElement()

	# drawing and item creation logic
	def instanceDelegateGeneratorClasses(self)->T.List[T.Type[GraphItemDelegateAbstract]]:
		"""return list of delegate types whose instance objects might create
		more delegates when graph items are added"""
		return [delegateCls for delegateCls in self.validDelegates if delegateCls.instancesMayCreateDelegates]

	def sortDelegateClsPriority(self)->list[T.Type[GraphItemDelegateAbstract]]:
		"""may not be necessary, but sort the order in which items are passed to
		delegate classes in order to be drawn"""
		return list(sorted(self.validDelegates, key=lambda x: x.delegatePriority, reverse=True))

	def sortedDelegateGenerators(self)->list[GraphItemDelegateAbstract]:

		# collect possible generators of delegates to check over
		# instances first
		instanceGeneratorClasses = tuple(self.instanceDelegateGeneratorClasses())
		generatorDelegateInstances = [i for i in self.mainElementDelegateMap().values() if isinstance(i, instanceGeneratorClasses)]
		# sort by class priority
		generatorDelegateInstances = list(sorted(generatorDelegateInstances, key=lambda x: x.delegatePriority, reverse=True))

		# then delegate classes
		generatorDelegateClasses = self.sortDelegateClsPriority()
		return generatorDelegateInstances + generatorDelegateClasses


	def generateItemsForGraphElements(self, elements:T.Sequence[graphItemType])->list[GraphItemDelegateAbstract]:
		"""given elements of graph to sync with,
		pass selection to successive delegate classes and return any
		items generated

		check first with delegate instances, then with delegate classes

		"""
		elementSet = set(elements)
		result = []

		delegateGenerators = self.sortedDelegateGenerators()

		# iterate
		# ensure elements are removed from set when delegates generated for them
		baseSetLen = len(elementSet)
		while elementSet and delegateGenerators:
			testGenerator = delegateGenerators.pop(0)
			if isinstance(testGenerator, GraphItemDelegateAbstract):
				genFn = testGenerator.instanceDelegatesForElements
			else:
				genFn = testGenerator.delegatesForElements
			newItems = genFn(scene=self, itemPool=elementSet)
			print("delegate cls", testGenerator, "items", newItems)

			# check set lengths are valid
			assert baseSetLen <= (len(elementSet) + len(newItems)), f"delegate {testGenerator} did not properly remove items from new element pool \n{elementSet}\n when making new items \n{newItems}"
			baseSetLen = len(elementSet)

			result.extend(newItems)

		# check if any left over
		if elementSet:
			raise TypeError(f"no delegate found for graph elements {elementSet}")

		return result

	def addGraphItemDelegate(self, delegate:GraphItemDelegateAbstract):
		"""add a uniform delegate type, connect its signals"""
		self.graphDelegateItems.add(delegate)
		self.itemChanged.connect(delegate.onSceneItemChange)
		self.addItem(delegate)
		delegate.sync()

	def removeGraphItemDelegate(self, delegate:GraphItemDelegateAbstract):
		self.graphDelegateItems.remove(delegate)
		self.removeItem(delegate)



	### region graph signal functions, direct match to tree signals
	def onGraphElementsChanged(self, delta:GraphNodeDelta):
		"""called when graph nodes or edges changed, updates visual
		elements

		query by query first
		"""
		if self.graphQuery is None:
			nodes, edges = set(self.graph().nodes), set(self.graph().edges)
		else:
			nodes, edges = self.graphQuery.filterGraph(self.graph())

		combinedElements = nodes.union(edges)

		# query added elements by query
		added = delta.added.intersection(combinedElements)

		# add any new elements
		items = self.generateItemsForGraphElements(added)
		for i in items:
			self.addGraphItemDelegate(i)

		# query any removed elements to delete delegates
		for i in delta.removed:
			# check if removed graph element is a main one for any delegates
			if i in self.mainElementDelegateMap():
				# if so, remove it
				self.removeGraphItemDelegate(
					self.mainElementDelegateMap()[i])


	def sync(self):
		"""fully clears and resets scene - may be costly
		use until we need more targeted processing"""
		self.clear()
		# add node delegates
		nodeDelta = GraphNodeDelta(added=set(self.graph().nodes))
		self.onGraphElementsChanged(nodeDelta)

		# add edge delegates
		edgeDelta = GraphEdgeDelta(added=set(self.graph().edges))
		self.onGraphElementsChanged(edgeDelta)

		self.layoutTiles()

	# endregion

	# def layoutNodes(self, nodes:list[NodeDelegate]):
	# 	"""moves around given nodes to avoid intersections (if possible)"""


	# def clearSelectionAttr(self):
	# 	"""clears "selected" attr for tiles and pipes that are not selected"""

	def onSceneSelectionChanged(self, *args, **kwargs):
		"""passed no arguments, just fires every change
		iterate through nodes - call the selected signal on each"""
		for i in self.tiles().values():
			i.onSceneSelectionChanged()

	#region events
	def mousePressEvent(self, event):
		if debugEvents: print("scene mousePress")
		super(ChimaeraGraphScene, self).mousePressEvent(event)
		if event.isAccepted():
			if debugEvents: print("scene mousePress accepted, returning")
			return True
		selected_nodes = self.selectedTiles()
		# if self.activeView:
		# 	self.activeView.beginDrawPipes(event)

	def mouseReleaseEvent(self, event):
		super(ChimaeraGraphScene, self).mouseReleaseEvent(event)

	def keyPressEvent(self, event):
		super(ChimaeraGraphScene, self).keyPressEvent(event)
		if event.isAccepted():
			return True

		self.keyState.dispatchKeyEventFunctions(event, forObject=self, pressed=True)

	def onEnterPressed(self, event:QtGui.QKeyEvent, pressed=True):
		"""attempt to 'dive in' to node if it can represent a subgraph"""

	def onTabPressed(self, event: QtGui.QKeyEvent, pressed=True):
		""""""

	def onDeletePressed(self, event:QtGui.QKeyEvent, pressed=True):
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
			if tile not in self.tiles().keys():
				return
			tile = self.tiles()[tile]

		# delete any necessary edges
		for k, v in self.pipes().items():
			if tile.node in k:
				self.deletePipe(v)
		self.tiles().pop(tile.node)
		self.removeItem(tile)
		self.update()


	def deletePipe(self, pipe:(EdgeDelegate, tuple[ChimaeraNode, ChimaeraNode, str])):
		if not isinstance(pipe, EdgeDelegate):
			if not pipe in self.pipes().keys():
				return
			pipe = self.pipes()[pipe]
		if debugEvents: print("scene deletePipe")
		self.pipes().pop(pipe.edgeTuple)
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
		tiles = tiles or set(self.tiles().values())
		nodes = set(i.node for i in tiles)
		islands = nx.strongly_connected_components(self.graph())
		for index, island in enumerate(islands):
			ordered = orderNodes(self.graph(), island)
			# only x for now

			baseTile = self.tiles()[ordered[0]]
			separation = 75
			baseX = baseTile.pos().x() + baseTile.sceneBoundingRect().width() + separation
			x = baseX
			for i in ordered[1:]:
				tile = self.tiles()[i]
				tile.setX(x)
				x += tile.sceneBoundingRect().width() + separation
		#self.updatePipePaths(tiles)



	### region drawing

	# endregion

	def serialiseUi(self, graphData):
		"""adds ui information to serialised output from graph
		no idea where better to put this"""
		for node, tile in self.tiles().items():
			graphData["nodes"][node.uid]["ui"] = tile.serialise()

	def regenUi(self, graphData):
		"""reapplies saved ui information to tiles"""
		for uid, info in graphData["nodes"].items():
			node = self.graph.nodeFromUID(uid)
			tile = self.tiles()[node]
			tile.setPos(QtCore.QPointF(*info["ui"]["pos"]))

