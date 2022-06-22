
from __future__ import annotations
"""test cases for new graph system"""
import unittest, pprint

from chimaera import ChimaeraGraph, ChimaeraNode, NodeDataHolder, DataUse, GraphTree

class TestGraphTree(unittest.TestCase):
	""" test for graph emulating basic tree """

	def setUp(self) -> None:
		self.tree = GraphTree("rootTree")

	def test_branchCreation(self):
		self.assertIsNotNone(self.tree)

		newBranch = self.tree("newBranch", create=True)
		self.assertIsInstance(newBranch, GraphTree)

		self.assertIs(self.tree, newBranch.parent)
		self.assertIn(newBranch, self.tree.branches)

		self.assertIs(self.tree("newBranch"), newBranch)

		self.tree.lookupCreate = True
		self.assertIn(self.tree("newBranch2"), newBranch.siblings)







