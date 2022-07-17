
from __future__ import annotations
from dataclasses import dataclass
from tree.lib.object import ExEnum


@dataclass(frozen=True)
class SelectionStatus(ExEnum):
	colour : tuple

Selected = SelectionStatus("Selected", (250, 220, 0, 255))
NotSelected = SelectionStatus("NotSelected", (0, 0, 0, 255))

