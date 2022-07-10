
""" a dependency graph that can think about itself
"""

from .constant import *
from .core.graphdata import GraphData
from .core.nodedata import NodeDataTree

from .core.node import ChimaeraNode
from .core.graph import ChimaeraGraph
from .graphtree import GraphTree
from .plugnode import PlugNode



# after package is initialised, scan over nodes for default catalogue
ChimaeraGraph.nodeClassCatalogue.registerClasses()
ChimaeraGraph.nodeClassCatalogue.gatherClasses()



try:
	from .ui import ChimaeraMainWidget, ChimaeraGraphWidget
except ImportError:
	print("Chimaera ui not available")
	ChimaeraWidget = None
	ChimaeraGraphWidget = None


