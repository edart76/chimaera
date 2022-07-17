from __future__ import annotations

"""more complex node defining multiple input and output plugs - 
all elements of this node are represented as tree nodes"""

from chimaera.constant import INPUT_NAME, OUTPUT_NAME
from chimaera import ChimaeraNode, ChimaeraGraph, GraphTree, GraphData
from chimaera.plugtree import PlugTree

class PlugNode( GraphTree):

	inPlug = GraphTree.TreeBranchDescriptor(INPUT_NAME, create=False, useValue=False)
	outPlug = GraphTree.TreeBranchDescriptor(OUTPUT_NAME, create=False, useValue=False)

	def __init__(self, name:str, value=None, treeUid=None, graph=None, nodeParams=None):
		super(PlugNode, self).__init__(name,
		                               value=value,
		                               treeUid=treeUid,
		                               graph=graph,
		                               nodeParams=nodeParams)

		# create input output trees
		# need some kind of transaction system to avoid UI interfering immediately
		self.inPlug = PlugTree(INPUT_NAME, graph=graph)
		self.outPlug = PlugTree(OUTPUT_NAME, graph=graph)

		# print("plugNode init", self.branches)
		# print("inplug", self.inPlug)


	def childNodes(self)->list[PlugNode]:
		"""return any full plug nodes that refer to this one as their parent -
		chimaera doesn't have fully nested graphs, but filtering visible
		hierarchies for this will let us imitate it"""
		return [i for i in self.branches if isinstance(i, PlugNode)]


	def syncPlugs(self):
		"""run after settings are defined / loaded - this method should populate
		input and output plugs based on current state of node
		externally will be wrapped in graph transaction, so deleting / regenerating
		is fine"""
		pass


	def containedPlugEdges(self)->list[tuple]:
		"""return all edges contained between this node and its plugs"""
		nBunch = self.inPlug.allBranches() + self.outPlug.allBranches() + [self]
		return self.graph().edges(nBunch)

	def execute(self, inputFlowData:GraphData) ->GraphData:
		"""for a plug node, we gather flow data from all input plug nodes,
		and merge it into single graphData object -
		acts as dict indexed by input plug node,
		we expect to form a graphData object indexed by output plug node
		"""




if __name__ == '__main__':

	newNode = PlugNode("testRoot")

	print("new", newNode)
	print(newNode.allBranches())

	print(newNode.containedPlugEdges())


