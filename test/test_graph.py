
from __future__ import annotations
"""test cases for new graph system"""
import unittest, pprint
import networkx as nx
from chimaera import ChimaeraGraph, ChimaeraNode, NodeDataHolder, DataUse

class TestGraphTree(unittest.TestCase):
	""" test for graph emulating basic tree """

	def setUp(self) -> None:
		self.graph = ChimaeraGraph()

	def test_addNode(self):
		aNode = self.graph.createNode("A")
		bNode = self.graph.createNode("B")
		cNode = self.graph.createNode("C")

		self.assertIn(aNode, self.graph)
		self.assertIn(aNode, self.graph.nodes)

		pprint.pprint(tuple(self.graph.nodes))

	def test_connectNodes(self):
		aNode = self.graph.createNode("A")
		bNode = self.graph.createNode("B")
		cNode = self.graph.createNode("C")

		self.graph.connectNodes(aNode, bNode)
		print(self.graph.edges)
		#print(self.graph.edges(aNode, keys=True))
		print(self.graph.nodeInputMap(bNode))


	def test_addNodeReference(self):
		aNode = self.graph.createNode("A")
		aNode.name = "nodeA"
		bNode = self.graph.createNode("B")
		bNode.name = "nodeB"
		cNode = self.graph.createNode("C")

		self.assertEqual(aNode.name, "nodeA")
		self.assertEqual(bNode.name, "nodeB")

		#graph.connectNodes(bNode, cNode)
		newEdge = self.graph.connectNodes(bNode, cNode,
		                   toUse=DataUse.Params)
		self.assertEqual(cNode.name, "nodeB")


		return
		# set B to be reference of A
		self.graph.connectNodes(aNode, bNode,
		                        fromUse=DataUse.Params, toUse=DataUse.Params)
		self.assertTrue(bNode.isReference())

		self.assertTrue(bNode.isReference())

		# check that node name has been changed
		self.assertEqual(bNode.name, "nodeA")





if __name__ == '__main__':
	graph = ChimaeraGraph()
	graph.createNode("A")
	graph.createNode("B")
	graph.createNode("C")

	pprint.pprint(tuple(graph.nodes))
