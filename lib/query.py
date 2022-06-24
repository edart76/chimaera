from __future__ import annotations
"""lib for querying graphs
might all be better written fully as object methods 


querying a graph to return nodes via string syntax
try a basic bracket syntax for logical set operations


eg

for graph containing "Apple", "Bee", "Cider"

ls( "*e" ) -> Apple, Bee

ls( " *e* - *er " ) -> (Apple, Bee, Cider) - (Cider) = Apple, Bee

ls( " $n.outNodes() " ) -> all outputs of the current query context?

"""

from dataclasses import dataclass
import typing as T


