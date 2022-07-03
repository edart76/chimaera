from __future__ import annotations
from dataclasses import dataclass
import typing as T

from tree.lib.object import UidElement
from tree import Tree

from tree.lib.delta import DeltaAtom

from tree.util import TreeUiMixin

from chimaera.constant import dataKeyType, NodeDataKeys

if T.TYPE_CHECKING:
	pass


@dataclass
class NodeDataDeltaAtom(DeltaAtom):
	key : dataKeyType
	newValue = None
	oldValue = None


class NodeDataTree(Tree, TreeUiMixin):
	"""why not"""
	nodeName = Tree.TreeBranchDescriptor(NodeDataKeys.nodeName, create=True, useValue=True)
	@classmethod
	def defaultBranchCls(cls):
		return NodeDataTree


	@staticmethod
	def createParamTree(name:str, uid=None)->NodeDataTree:
		"""return starting param tree for any chimaera node
		todo: allow node classes to define their own default param layout"""
		dataTree = NodeDataTree(name=NodeDataKeys.paramTree, treeUid=uid)
		dataTree.lookupCreate = True
		dataTree.nodeName = name
		return dataTree


@dataclass
class NodeDataHolder(UidElement):
	"""base class for passive node params - store minimal amount of
	rich information here

	all information directly returned by this object is from the "base"
	params, no compositing or overriding is done here
	"""

	_name: str # only used at init

	#uid : str = ""

	# # inputs is optional list of uids (likely just one)
	# inputUids : list[str] = field(default_factory=list)

	# actual params of node
	dataTree : NodeDataTree = None

	# overrides is dict of (key, value) to override params passed by inputs
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
		"""copy params object and trees"""
		newDataTree = self.dataTree.copy()
		newOverrideTree = self.overrideTree.copy()
		return NodeDataHolder(self._name, newDataTree, newOverrideTree)





