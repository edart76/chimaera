
from __future__ import annotations
"""test cases for new graph system"""
import unittest, pprint
from matplotlib import pyplot as plt
import networkx as nx
from tree.chimaeragraph import ChimaeraGraph, ChimaeraNode, NodeDataHolder

class TestGraphTree(unittest.TestCase):
	""" test for graph emulating basic tree """

	def setUp(self) -> None:
		self.graph = ChimaeraGraph()

	def test_addNode(self):
		aNode = self.graph.createNode("A")
		self.graph.createNode("B")
		self.graph.createNode("C")

		self.assertIn(aNode, self.graph)
		self.assertIn(aNode, self.graph.nodes)

		pprint.pprint(tuple(self.graph.nodes))



	def test_addNodeReference(self):
		self.graph.createNode("A")
		bNode = self.graph.createNode("B")
		self.graph.createNode("C")

		refNode = self.graph.addReferenceToNode(bNode)

		print(self.graph.nodes)

if __name__ == '__main__':
	graph = ChimaeraGraph()
	graph.createNode("A")
	graph.createNode("B")
	graph.createNode("C")

	pprint.pprint(tuple(graph.nodes))

	nx.draw(graph)
	plt.show()