
from __future__ import annotations

import networkx as nx
def syncGraphNodes(masterNodeSet:set,

                   drivenGraph:nx.Graph,
                   addMissing=True, removeTrailing=False,

                   ):
	"""ensure that driven graph contains the given nodes
	if addMissing, any missing nodes """

