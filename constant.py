from __future__ import annotations
from enum import Enum
import typing as T


from tree.lib.path import Path
dataKeyType = (str, T.Sequence[str], T.FrozenSet[str])

from chimaera.datause import DataUse
from chimaera.datatype import DataType


class NodeDataKeys:
	"""string key constants used widely"""
	paramTree = "params"
	overrideTree = "override"
	nodeName = "nodeName"
	treeValue = "nodeValue"
	treeProperties = "nodeProperties"


class GraphEvalModes(Enum):
	"""different modes for graph evaluation"""
	Lazy = 0
	Active = 1
	Dormant = 2

class NodeRefModes(Enum):
	"""one to one match between member names and values"""
	Single = "Single"
	Multi = "Multi"


# constants for node plug systems
INPUT_NAME = "in"
OUTPUT_NAME = "out"

# main path for this module
ROOT_PATH = Path(__file__).parent

if __name__ == '__main__':
	print(NodeRefModes["Single"])
