from __future__ import annotations
from enum import Enum
import typing as T

dataKeyType = (str, T.Sequence[str], T.FrozenSet[str])

from chimaera.core.datause import DataUse
from chimaera.core.datatype import DataType




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


# constants for node plug systems
INPUT_NAME = "in"
OUTPUT_NAME = "out"


if __name__ == '__main__':
	print(NodeRefModes["Single"])
