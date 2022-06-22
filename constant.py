from __future__ import annotations
from enum import Enum
import typing as T

dataKeyType = (str, T.Sequence[str], T.FrozenSet[str])


class DataUse(Enum): # later replace each use with class for easier extension
	Params = "Params"
	Flow = "Flow"
	Structure = "Structure"
	Creator = "Creator"
	Tree = "Tree"
	Anchor = "Anchor"


class NodeDataKeys:
	"""string key constants used widely"""
	paramTree = "params"
	overrideTree = "override"
	nodeName = "nodeName"
	treeValue = "nodeValue"
	treeProperties = "nodeProperties"

class NodeRefModes(Enum):
	"""one to one match between member names and values"""
	Single = "Single"
	Multi = "Multi"


if __name__ == '__main__':
	print(NodeRefModes["Single"])
