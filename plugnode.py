from __future__ import annotations

"""more complex node defining multiple input and output plugs - 
all elements of this node are represented as tree nodes"""

from chimaera.constant import INPUT_NAME, OUTPUT_NAME
from chimaera import ChimaeraNode, ChimaeraGraph, GraphTree
from chimaera.plugtree import PlugTree

class PlugNode( GraphTree):

	inPlug = GraphTree.TreeBranchDescriptor(INPUT_NAME, create=False, useValue=False)
	outPlug = GraphTree.TreeBranchDescriptor(OUTPUT_NAME, create=False, useValue=False)

	def __init__(self, name:str, value=None, treeUid=None, graph=None, nodeParams=None):
		super(PlugNode, self).__init__(name, value, treeUid, graph, nodeParams)

		# create input output trees
		self.inPlug = PlugTree(INPUT_NAME)
		self.outPlug = PlugTree(OUTPUT_NAME)


	def containedPlugEdges(self)->list[tuple]:
		"""return all edges contained between this node and its plugs"""
		nBunch = self.inPlug.allBranches() + self.outPlug.allBranches() + [self]
		return self.graph().edges(nBunch)


if __name__ == '__main__':

	newNode = PlugNode("testRoot")

	print("new", newNode)
	print(newNode.allBranches())

	print(newNode.containedPlugEdges())


