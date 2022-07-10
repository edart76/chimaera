from __future__ import annotations

from dataclasses import dataclass

from PySide2 import QtCore, QtWidgets, QtGui

from chimaera.constant import DataUse

@dataclass
class GraphicsItemChange:
	item : QtWidgets.QGraphicsItem
	changeType : QtWidgets.QGraphicsItem.GraphicsItemChange
	value : object = None


# dataColourMap = {
# 	DataUse.Flow : (200, 70, 100),
# 	DataUse.Params : (100, 50, 200),
# 	DataUse.Structure : (100, 100, 200),
# 	DataUse.Creator : (100, 200, 100),
# 	DataUse.Tree : (100, 100, 100),
#
# }

