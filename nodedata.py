from __future__ import annotations
from dataclasses import dataclass
import typing as T

from tree.lib.object import UidElement
from tree import Tree

from tree.lib.delta import DeltaAtom
from chimaera.constant import dataKeyType, NodeDataKeys

if T.TYPE_CHECKING:
	pass


@dataclass
class NodeDataDeltaAtom(DeltaAtom):
	key : dataKeyType
	newValue = None
	oldValue = None


class NodeDataTree(Tree):
	"""why not"""
	nodeName = Tree.TreeBranchDescriptor(NodeDataKeys.nodeName, create=True)

	@staticmethod
	def createDataAndOverrideTrees(name:str, uid=None)->tuple[NodeDataTree, NodeDataTree]:
		"""return starting tuple of (data tree, override tree)
		for any chimaera node"""
		dataTree = NodeDataTree(name=NodeDataKeys.dataTree, treeUid=uid)
		dataTree.lookupCreate = True
		dataTree.nodeName = name

		# uid is unimportant for override tree
		overrideTree = NodeDataTree(name=NodeDataKeys.overrideTree)
		overrideTree.lookupCreate = True
		return dataTree, overrideTree



@dataclass
class NodeDataHolder(UidElement):
	"""base class for passive node data - store minimal amount of
	rich information here

	all information directly returned by this object is from the "base"
	data, no compositing or overriding is done here
	"""

	_name: str # only used at init

	#uid : str = ""

	# # inputs is optional list of uids (likely just one)
	# inputUids : list[str] = field(default_factory=list)

	# actual data of node
	dataTree : NodeDataTree = None

	# overrides is dict of (key, value) to override data passed by inputs
	overrideTree : NodeDataTree = None
	nodeTypeId : int = -1



	uidInstanceMap = {}



	def __hash__(self):
		return UidElement.__hash__(self)

	def __post_init__(self):
		# tree direct names are unimportant - nodeName is set in branch
		treeName = str(hash(self._name))
		self.dataTree = NodeDataTree(name=treeName)
		self.dataTree.lookupCreate = True
		self.overrideTree = self.dataTree.copy()
		self.dataTree("nodeName").v = self._name


		UidElement.__init__(self, self.dataTree.uid)

	def setUid(self, uid, replace=True):
		"""ensure container and tree uids are always in sync"""
		super(NodeDataHolder, self).setUid(uid, replace)
		self.dataTree.setUid(uid, replace)

	def name(self):
		return self.dataTree("nodeName").v

	def copy(self):
		"""copy data object and trees"""
		newDataTree = self.dataTree.copy()
		newOverrideTree = self.overrideTree.copy()
		return NodeDataHolder(self._name, newDataTree, newOverrideTree)





