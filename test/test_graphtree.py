
from __future__ import annotations
"""show cases for new graph system"""
import unittest, pprint

from chimaera import ChimaeraGraph, ChimaeraNode, DataUse, GraphTree

class TestGraphTree(unittest.TestCase):
	""" show for graph emulating basic tree """

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
		self.assertIs(self.tree.graph(), self.tree("newBranch2"))







