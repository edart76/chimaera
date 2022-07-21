

from __future__ import annotations

import random, colorsys, traceback
from weakref import WeakKeyDictionary

from typing import TYPE_CHECKING, Union, Dict, List
import typing as T

from tree import Tree
from PySide2 import QtCore, QtWidgets, QtGui


if TYPE_CHECKING:
	from chimaera.ui.view import ChimaeraGraphView
	from chimaera.ui.graphwidget import ChimaeraGraphWidget

from treegraph.ui.style import (VIEWER_BG_COLOR,
                                      VIEWER_GRID_COLOR,
                                      VIEWER_GRID_OVERLAY)
from treegraph.ui import relax
from tree.ui.lib import KeyState, keyDict
from tree.ui.graphics.lib import allGraphicsSceneItems, allGraphicsChildItems
from tree.lib.inheritance import superClassLookup, containsSuperClass
from tree.ui.libwidget.draggraphicsscene import MouseDragScene


import networkx as nx
from chimaera import ChimaeraGraph, ChimaeraNode
from chimaera.lib.delta import GraphEdgeDelta, GraphNodeDelta
from chimaera.lib.query import GraphQuery
from chimaera.ui.base import GraphicsItemChange
from chimaera.ui.delegate import NodeDelegate, EdgeDelegate, PlugNodeDelegate, PlugTreeDelegate, PointPath
from chimaera.lib.topology import orderNodes
from chimaera.ui.delegate.abstract import ConnectionPointGraphicsItemMixin, ConnectionPointSceneMixin, GraphItemDelegateAbstract, AbstractNodeContainer

from chimaera.ui import graphItemType
from chimaera.ui.constant import SelectionStatus
from chimaera.ui.lib.connection import curvedPoints

debugEvents = False

def randomPastel(seed):
	random.seed(a=seed)
	h = random.random()
	s = 0.5 + ((random.random()) / 3.0)
	v = 0.7 + ((random.random()) / 5.0)
	rgb = colorsys.hsv_to_rgb(h, s, v)
	return rgb

class ChimaeraGraphScene(MouseDragScene, ConnectionPointSceneMixin):
	"""graphics scene for ChimaeraGraph
	different specific views (tree node view, treeGraph node view) may define
	their own drawing delegates - all should inherit from this

	only top-level items are visible to scene - GraphDelegate items can change internally,
	but if the element of a top-level item is deleted, remove that item

	for sanity we assume one graphicsScene per graphicsView - no shame

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

	# endregion

	itemChanged = QtCore.Signal(GraphicsItemChange)




	def __init__(self, parent:ChimaeraGraphWidget=None
	             ):
		super(ChimaeraGraphScene, self).__init__(parent)

		self.graphDelegateItems : set[GraphItemDelegateAbstract] = set()
		self.itemDelegateMap : dict[ChimaeraNode, NodeDelegate] = {}

		self.grid = VIEWER_GRID_OVERLAY

		self.graphQuery : GraphQuery = None

		self.rubberBand = self.makeRubberBand()
		self.addItem(self.rubberBand)

		# element visibility rules - absolutely no idea how to set this up properly
		# self.knobVisibilityOverrides : dict[ConnectionPointSceneMixin, (bool, None)] = WeakKeyDictionary()

		# viewer states
		# if draggingEdgeSource is not None, then we are dragging an edge
		self.draggingEdgeSource : ConnectionPointGraphicsItemMixin = None
		#self.draggingEdgePath : QtWidgets.QGraphicsPathItem = QtWidgets.QGraphicsPathItem()
		self.draggingEdgePath : PointPath = PointPath(self)
		self.addItem(self.draggingEdgePath)
		pen = QtGui.QPen(QtCore.Qt.red)
		pen.setWidth(2)
		self.draggingEdgePath.setPen(pen)
		# if draggingSelectionBox, track the starting corner of a selection box
		self.draggingSelectionBox = False

		self.dragOrigin : QtCore.QPointF = None

		# signal hookups
		self.selectionChanged.connect(self.onSceneSelectionChanged)

	def makeRubberBand(self) ->QtWidgets.QGraphicsRectItem:
		"""make a rubber band item"""
		rect = QtWidgets.QGraphicsRectItem()
		pen = QtGui.QPen(QtCore.Qt.DotLine)
		pen.setColor(QtCore.Qt.lightGray)
		pen.setWidth(2)
		rect.setPen(pen)
		return rect

	#region core
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

	def elementDelegates(self)->set[GraphItemDelegateAbstract]:
		"""return set of all delegates"""
		return [ i for i in allGraphicsSceneItems(self) if isinstance(i, GraphItemDelegateAbstract)]

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
	def connectionPoints(self) ->list[ConnectionPointGraphicsItemMixin]:
		return [item for item in self.items() if isinstance(item, ConnectionPointGraphicsItemMixin)]



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

		generatorDelegateInstances = [i for i in allGraphicsSceneItems(self) if isinstance(i, instanceGeneratorClasses)]
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
		#print("sorted generators", delegateGenerators)
		baseSetLen = len(elementSet)
		while elementSet and delegateGenerators:
			testGenerator = delegateGenerators.pop(0)
			if isinstance(testGenerator, GraphItemDelegateAbstract):
				genFn = testGenerator.instanceDelegatesForElements
			else:
				genFn = testGenerator.delegatesForElements
			newItems = genFn(scene=self, itemPool=elementSet)
			#print("delegate cls", testGenerator, "items", newItems)

			# check set lengths are valid
			# assert baseSetLen <= (len(elementSet) + len(newItems)), f"delegate {testGenerator} did not properly remove items from new element pool \n{elementSet}\n when making new items \n{newItems}"
			baseSetLen = len(elementSet)

			result.extend(newItems)

		# check if any left over
		if elementSet:
			raise TypeError(f"no delegate found for graph elements {elementSet}")

		return result


	def delegateForNode(self, node:ChimaeraNode)->NodeDelegate:
		"""return the delegate for a node - may not be top level, or visible"""
		return self.itemDelegateMap[node]

	def addGraphItemDelegate(self, delegate:GraphItemDelegateAbstract):
		"""add a uniform delegate type, connect its signals"""
		self.graphDelegateItems.add(delegate)
		self.itemChanged.connect(delegate.onSceneItemChange)

		self.addItem(delegate)

		# iterate over all children to find nodes
		for i in allGraphicsChildItems(delegate):
			if isinstance(i, NodeDelegate):
				self.itemDelegateMap[i.node] = i
			elif isinstance(i, AbstractNodeContainer):
				for n in i.nodes:
					self.itemDelegateMap[n] = i
		delegate.sync()
		for i in self.connectionPoints():
			i.show()

		# print("scene post add")
		# print(allGraphicsChildItems(delegate, includeSelf=True))
		# print(allGraphicsSceneItems(self))

	def nodeContainerMap(self):
		return {node : container for node, container in allGraphicsSceneItems(self) if isinstance(container, AbstractNodeContainer)}

	def removeGraphItemDelegate(self, delegate:GraphItemDelegateAbstract):
		self.graphDelegateItems.remove(delegate)
		self.removeItem(delegate)

	def tryAddEdge(self,
	               sourcePoint:ConnectionPointGraphicsItemMixin,
	               destPoint:ConnectionPointGraphicsItemMixin,
	               ):
		"""delegate adding edge to connectionPointDelegates"""

		try:
			sourcePoint.addConnectionToPoint(destPoint)
		except Exception as e:
			print("failed to add edge to graph")
			traceback.print_exc()


	#endregion

	### region graph signal functions, direct match to tree signals
	def onGraphElementsChanged(self, delta:GraphNodeDelta):
		"""called when graph nodes or edges changed, updates visual
		elements

		query by query first
		"""
		print("graph elements changed", delta)
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
			#raise

		# query any removed elements to delete delegates
		for i in delta.removed:
			# check if removed graph element is a main one for any delegates
			if i in self.mainElementDelegateMap():
				# if so, remove it
				self.removeGraphItemDelegate(
					self.mainElementDelegateMap()[i])

	def volatileItems(self)->list[QtWidgets.QGraphicsItem]:
		"""return list of items that are not persistent"""
		return [i for i in self.items() if i not in
		        (self.rubberBand, self.draggingEdgePath)]

	def redraw(self):
		self.update(self.sceneRect())

	def sync(self):
		"""fully clears and resets scene - may be costly
		use until we need more targeted processing"""
		#self.clear()
		for i in self.volatileItems():
			self.removeItem(i)
		# add node delegates
		nodeDelta = GraphNodeDelta(added=set(self.graph().nodes))
		self.onGraphElementsChanged(nodeDelta)

		# add edge delegates
		edgeDelta = GraphEdgeDelta(added=set(self.graph().edges))
		self.onGraphElementsChanged(edgeDelta)

		self.layoutTiles()
		self.redraw()


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

	def processSelectionAction(self, newNodes:list[NodeDelegate]):
		ctrl = self.keyState.ctrl
		shift = self.keyState.shift
		newNodes = set(newNodes)
		currentNodes = set(self.selectedTiles())

		# toggle extend node selection
		# ctrl : remove
		# shift : toggle
		# ctrl + shift : add

		if shift and not ctrl:  # toggle
			toAdd = newNodes - currentNodes
			toRemove = currentNodes - newNodes
			# redo this to some kind of transaction system
			for i in toAdd:
				i.setSelected(True)
			for i in toRemove:
				i.setSelected(False)

		elif ctrl and not shift: # remove
			for i in currentNodes:
				i.setSelected(False)
		elif ctrl and shift: # add
			for i in newNodes:
				i.setSelected(True)

		else: # replace
			toKeep = newNodes.intersection(currentNodes)
			for i in currentNodes - toKeep:
				i.setSelected(False)
			for i in newNodes - toKeep:
				i.setSelected(True)

	def beginDrawingEdge(self, sourcePoint:ConnectionPointGraphicsItemMixin):
		"""begin drawing an edge from a given point to cursor position
		hide any connectionPoints in scene that aren't compatible with it"""
		self.draggingEdgeSource = sourcePoint

		# draw temp edge - not necessary to delegate to point item yet
		path = QtGui.QPainterPath()
		pen = EdgeDelegate.potentialPen()
		#self.draggingEdgePath = QtWidgets.QGraphicsPathItem()
		#self.addItem(self.draggingEdgePath)

		self.draggingEdgePath.prepareGeometryChange()
		self.draggingEdgePath.setPen(pen)
		self.draggingEdgePath.setPath(path)

		# hide connections
		for i in self.connectionPoints():
			if i is sourcePoint:
				continue
			if not i.acceptsConnection(sourcePoint):
				i.hide()

		self.draggingEdgePath.show()

	def endDrawingEdge(self, targetPoint:ConnectionPointGraphicsItemMixin=None):
		"""end drawing process - if no point is passed, edge was dragged out into
		empty space - just leave it
		if point is passed, create edge between source and target"""

		# show connections
		for i in self.connectionPoints():
			i.show()

		self.draggingEdgeSource = None
		self.draggingEdgePath.hide()



	#region events
	def mousePressEvent(self, event):
		#print("start scene mousePress sel", self.selectedTiles())
		super(ChimaeraGraphScene, self).mousePressEvent(event)
		#print("after super scene mousePress sel", self.selectedTiles())
		self.dragOrigin = event.scenePos()
		if event.isAccepted():
			#print("scene mousePress accepted, returning")
			return True

		pos = event.scenePos()
		items = self.items(pos)
		pressNodes = [i for i in items if isinstance(i, NodeDelegate)]

		if self.keyState.LMB:
			if not items: # only begin dragging selection box if no items are under cursor
				self.draggingSelectionBox = True
				self.rubberBand.setRect(pos.x(), pos.y(), 0, 0)

			# check if we need to start dragging a new edge
			points = [i for i in items if isinstance(i, ConnectionPointGraphicsItemMixin)]
			if points:
				self.beginDrawingEdge(points[0])
		self.redraw()
		#print("end scene mousePress sel", self.selectedTiles())


	def mouseMoveEvent(self, event):
		super(ChimaeraGraphScene, self).mouseMoveEvent(event)

		# check for connection points in range

		if self.keyState.LMB and self.dragOrigin is not None and self.draggingSelectionBox:
			self.rubberBand.setRect(QtCore.QRectF(
				self.dragOrigin, event.scenePos()).normalized().toRect())
			self.rubberBand.show()
		else:
			self.rubberBand.hide()

		items = self.items(event.scenePos())

		if self.draggingEdgeSource is not None:
			hoverConnectPoints = [i for i in items if isinstance(i, ConnectionPointGraphicsItemMixin)]

			# stick to connection points when you hover over them
			posA =  self.draggingEdgeSource.mapToScene(
				self.draggingEdgeSource.connectionPosition())

			dirA = self.draggingEdgeSource.connectionDirection()
			if hoverConnectPoints: # stick to connection point
				posB = hoverConnectPoints[0].mapToScene(hoverConnectPoints[0].connectionPosition())
				dirB = hoverConnectPoints[0].connectionDirection()
				self.draggingEdgePath.setPoints(
					*curvedPoints(posA, dirA, posB, dirB, self))

			else: # go straight to cursor
				posB = event.scenePos()
				dirB = -(posB - posA)
				self.draggingEdgePath.setPoints(posA, posB=posB)

		self.redraw()


	def mouseReleaseEvent(self, event):
		#print("start mouse release selection", self.selectedTiles())

		super(ChimaeraGraphScene, self).mouseReleaseEvent(event)
		#print("mouse release selection", self.selectedTiles())

		if event.isAccepted():
			#print("scene mouseRelease accepted, returning")
			return True
		#print("mouse release selection", self.selectedTiles())
		if event.button() == QtCore.Qt.MouseButton.LeftButton and self.dragOrigin is not None and self.draggingSelectionBox:
			rubberBandNodes = self.items(self.rubberBand.rect())
			rubberBandNodes = [i for i in rubberBandNodes if isinstance(i, NodeDelegate)]
			self.processSelectionAction(rubberBandNodes)
			self.draggingSelectionBox = False
			self.dragOrigin = None

			self.rubberBand.hide()
			self.rubberBand.update()
			self.redraw()

		elif event.button() == QtCore.Qt.MouseButton.LeftButton and self.draggingEdgeSource:
			self.endDrawingEdge()

		self.draggingSelectionBox = False

		#print("mouse release selection", self.selectedTiles())

	#self.removeItem(self.rubberBand)

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

