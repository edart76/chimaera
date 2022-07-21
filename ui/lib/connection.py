from __future__ import annotations

"""different algorithms for drawing connections in node
graph"""

import typing as T


from PySide2 import QtCore, QtWidgets, QtGui
if T.TYPE_CHECKING:
	from chimaera.ui.scene import ChimaeraGraphScene
	from chimaera.ui.delegate.abstract import GraphItemDelegateAbstract, AbstractNodeContainer, ConnectionPointGraphicsItemMixin

def curvedPoints(posA, dirA:QtCore.QPoint, posB,  dirB, scene:ChimaeraGraphScene):
	"""draw a curved connection between two points"""
	# normalise directions - ish
	dirA = dirA / dirA.manhattanLength()
	dirB = dirB / dirB.manhattanLength()

	posSpan = posB - posA
	height, width = posSpan.x(), posSpan.y()

	midA = posA + dirA * posSpan.manhattanLength() / 2
	midB = posB + dirB * posSpan.manhattanLength() / 2
	return posA, midA, posB, midB






