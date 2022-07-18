
from __future__ import annotations

"""small enum-like classes defining ways data may be used in Chimaera - 
can be extended by plugins"""

import typing as T
from enum import Enum, EnumMeta
from dataclasses import dataclass

from tree.lib.object import NamedClassMixin
from tree.lib.python import iterSubClasses

class UiPlugPosition(Enum):
	"""where a UI plug should be placed on UI node"""
	LeftRight = 0
	TopBottom = 1


knownTypes = {}

class DataUseMeta(type):
	"""meta-class for data use types
	unfortunately we miss out on type hinting"""
	def __getattr__(self, item:str):
		return knownTypes.get(item) or object.__getattribute__(self, item)
	def __getitem__(self, item:(str, DataUse)):
		if isinstance(item, DataUse):
			return item
		return knownTypes[item]
	def __iter__(self):
		return iter(knownTypes.values())
	def __len__(self):
		return len(knownTypes)

@dataclass(frozen=True)
class DataUse(metaclass=DataUseMeta):
	"""string key constants used widely"""
	name : str
	edgeColour : tuple = (128, 128, 128)
	uiPosition : UiPlugPosition = UiPlugPosition.LeftRight

	def __post_init__(self):
		knownTypes[self.name] = self

	def __str__(self):
		return f"DataUse<{self.name}>"

	def __repr__(self):
		return str(self)




Anchor = DataUse("Anchor")
Creator = DataUse("Creator", edgeColour=(100, 200, 100))
Flow = DataUse("Flow", edgeColour=(200, 70, 100))
Params = DataUse("Params", edgeColour=(100, 50, 200))
Structure = DataUse("Structure", edgeColour=(100, 100, 200))
Tree = DataUse("Tree", edgeColour=(100, 100, 100),
               uiPosition=UiPlugPosition.TopBottom)


if __name__ == '__main__':
	print(DataUse.Params)
	for i in DataUse:
		print(i)
