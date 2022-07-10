
from __future__ import annotations

"""higher version of data use, for plug trees - """

import typing as T
from enum import Enum
from dataclasses import dataclass

from tree.lib.object import NamedClassMixin
from tree.lib.python import iterSubClasses

from tree.lib.object import ExEnum

knownTypes = {}

# class DataTypeMeta(type):
# 	"""meta-class for data use types
# 	unfortunately we miss out on type hinting"""
# 	def __getattr__(self, item:str):
# 		return knownTypes.get(item) or object.__getattribute__(self, item)
# 	def __getitem__(self, item):
# 		return knownTypes[item]

@dataclass(frozen=True)
class DataType(ExEnum):
	"""string key constants used widely"""
	name : str
	colour : tuple = (128, 128, 128)

	# def __post_init__(self):
	# 	knownTypes[self.name] = self



Int = DataType("Int", colour=(255, 0, 0))
Float = DataType("Float", colour=(0, 255, 0))
String = DataType("String", colour=(0, 0, 255))