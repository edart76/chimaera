from __future__ import annotations
"""lib for querying graphs
might all be better written fully as object methods 


querying a graph to return nodes via string syntax
try a basic bracket syntax for logical set operations
basically this is regex for nodes

eg

for graph containing "Apple", "Bee", "Cider"

ls( "*e" ) -> Apple, Bee

ls( " *e* - *er " ) -> (Apple, Bee, Cider) - (Cider) = Apple, Bee

ls( " $n.outNodes() " ) -> all outputs of the current query context?

ls( "Apple/*" ) -> all tree children of Apple

this all has to follow on from the normal tree expressions - we need a unified syntax for all of them

for easier syntax consider using fnmatch by default, and only using regex if necessary

"""

import fnmatch

from dataclasses import dataclass
import typing as T

from chimaera.core.node import ChimaeraNode
if T.TYPE_CHECKING:
	from chimaera.core.graph import ChimaeraGraph

@dataclass
class QueryLocals:
	"""locals passed in to resolve query expression"""
	pass

@dataclass
class QueryAtom:
	"""atomic part of logical query - can be either string
	or operation?"""
	regex:str

def parseExpression(query:str)->T.List[QueryAtom]:
	"""parse a query string into a logical expression
	"""
	return [QueryAtom(query)]
	pass


def listNodes(graph:ChimaeraGraph, query:str)->set[ChimaeraNode]:
	"""query a graph for nodes matching a query string
	query string is a logical expression of nodes
	"""
	return set(filter(map(lambda x: fnmatch.fnmatch(x, query), graph.nodeNames()), graph.nodeNames()))

def resolveQuery(graph:ChimaeraGraph, query:str):
	"""query a graph for nodes matching a query string
	query string is a logical expression of nodes
	"""

def queryTextIsValid(query:str)->bool:
	"""check if a query string is valid
	"""
	return True


class GraphQuery:
	"""class encapsulating a full graph query
	no idea still how to do this properly

	not sure we should allow naming individual queries - in contexts where
	naming is appropriate (for saving specific views), the query itself
	will only be one part of the bookmarked display to shift to. Therefore
	you would name the bookmark, and not the actual query.
	"""

	def __init__(self, query:str, name:str=""):
		self.queryText = query

	def isValid(self)->bool:
		"""check if this query is valid
		"""
		return True

	def filterGraph(self, graph:ChimaeraGraph)->tuple[set[ChimaeraNode], set[tuple]]:
		"""return all nodes valid in graph that this query shows,
		and all edges valid between those nodes
		"""
		pass




