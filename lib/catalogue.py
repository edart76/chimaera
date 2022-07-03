
from __future__ import annotations
"""object holding a list of classes looked up from modules,
eventually handling hot-reload as well"""

import importlib, importlib.util, importlib.machinery, \
		os, sys, pkgutil, inspect, pprint, types, builtins
import typing as T
from collections import namedtuple

from tree.lib.path import PurePath, Path
from tree.lib.python import safeLoadModule
from tree import Signal

from chimaera.core.node import ChimaeraNode
from chimaera.constant import ROOT_PATH

def import_file(full_name, path):
	"""Import a python module from a path. 3.4+ only.

	Does not call sys.modules[full_name] = path
	"""
	from importlib import util

	spec = util.spec_from_file_location(full_name, path)
	if spec is None:
		print("no spec for", full_name)
		return
	mod = util.module_from_spec(spec)

	spec.loader.exec_module(mod)
	return mod

def modulesInPackagePath(packagePath, rootPackageName="chimaera", includeParent=True,
						 loadModules=True):
	"""if not loadModules, returns loader objects
	else returns full loaded modules"""
	rootPath = Path(packagePath)

	results = []

	print("rootPath:", rootPath)
	#packageName = ".".join(rootPath.parts[2:])
	parentPackageName = str(rootPath)
	parentLeafName = rootPath.name
	print("packageName:", parentPackageName)
	spec = importlib.util.spec_from_file_location(
		parentLeafName, rootPath / "__init__.py")
	parentLoader = spec.loader

	#parentMod = __import__(parentLeafName)
	parentMod = sys.modules.get(parentLeafName) or __import__(rootPackageName)

	for importer, packageName, isPkg in \
			pkgutil.walk_packages([str(rootPath)], prefix=rootPackageName + "."):
		importer: importlib.machinery.FileFinder

		# loader = importer.find_module(packageName)
		spec = importlib.util.find_spec(packageName, rootPackageName)

		if spec is None:
			print("no spec for", packageName)
			continue
		results.append(spec)

	if loadModules:
		newResults = []
		for i in results:
			if i.name == rootPackageName:
				continue
			#print("i", i)
			importMod = __import__(i.name)

			# necessary to import each module before loading it, otherwise dataclasses module freaks out
			importMod = importlib.import_module(i.name,
			                                    package=rootPackageName
			                                    #package=parentMod
			                                    )
			mod = importMod
			newResults.append(mod)
		results = newResults
	return results


class ClassCatalogue(object):
	"""object with logic for iterating over a set of packages
	and gathering all valid classesToReload defined in them
	maybe a bit specific for a generic object but it's fine

	also defines logic for reloading individual known classesToReload
	"""
	# tuples of matching length holding old and new class objects,
	# and new module objects
	ReloadEvent = namedtuple("ReloadEvent", ("oldClasses",
											 "newClasses",
											 "modules"))
	RegisterEvent = namedtuple("RegisterEvent",("newClasses",
												"newModules"))

	def __init__(self, classPackagePaths:T.List[T.Union[Path, str]], baseClasses:set[type],
				 parentPackageNames:list[str],
				 register=False):
		self.initialised = False
		self.classModuleMap = {}
		self.scanPackagePaths = list(map(Path, classPackagePaths))
		self.parentPackageNames = parentPackageNames
		self.scanBaseClasses = baseClasses
		self.classesChanged = Signal(name="classesRegistered")
		self.classesReloaded = Signal(name="classesReloaded")

		if register:
			self.registerClasses(baseClasses)

	@property
	def classes(self)->T.Set[type]:
		"""return set of known classes"""
		return set(self.classModuleMap.keys())

	def nameClassMap(self)->dict[str, type]:
		"""dict of { class name, class object } for nodes
		likely better processing needed here for namespaces, custom
		systems to extract names from type objects etc"""
		return {i.__name__ : i for i in  self.classes}

	def gatherClasses(self, force=False):
		"""iterate over class package paths,
		gather valid subclasses, add them to class package map
		this naturally has to load all modules
		"""
		# guard against recursion
		if self.initialised and not force:
			return
		self.initialised = True
		for path, parentName in zip(self.scanPackagePaths, self.parentPackageNames):
			rootPath = Path(path)
			results = modulesInPackagePath(rootPath, parentName, loadModules=True)
			# for rootPath, dirs, files in os.walk(path):
			# 	# check if it's a valid python package
			# 	if not "__init__.py" in files:
			# 		continue


			# get members in modules
			for module in results:
				classes = self.getClassesInModule(module)
				for modClass in classes:
					self.classModuleMap[modClass] = module

	def getClassesInModule(self, module):
		classes = []
		# only unique members that are classesToReload
		members = set(
			[i[1] for i in inspect.getmembers(module, lambda x: isinstance(x, type))])
		for testClass in members:
			# skip invalid classesToReload
			if not self.checkValidClass(testClass, module):
				continue
			#self.classModuleMap[testClass] = module
			classes.append(testClass)
		return classes

	def checkValidClass(self, testClass:type, module):
		"""return True if testClass is to be included in catalogue,
		False if ignored
		tested working with dynamically-generated classesToReload at module-level
		"""
		# check that class is defined in module
		if testClass in builtins.__dict__.values():
			return False
		try:
			if inspect.getsourcefile(testClass) != module.__file__:
				return False
		except TypeError:
			return False
		return any(i in testClass.__mro__ for i in self.scanBaseClasses)

	def registerClasses(self, testClasses: T.Set[type]=None):
		"""register a given class directly - attempts to work out
		module from its source
		raises TypeError if class is not valid"""
		testClasses = testClasses if testClasses is not None else self.scanBaseClasses
		registeredClasses = []
		registeredModules = []
		for testClass in testClasses:
			modName = testClass.__module__
			sourceFile = inspect.getsourcefile(testClass)
			spec = importlib.util.spec_from_file_location(
				modName, sourceFile)
			mod = importlib.util.module_from_spec(spec)
			print("mod", mod)
			if not self.checkValidClass(testClass, mod):
				raise TypeError("Class {} is invalid to register in catalogue")

			self.classModuleMap[testClass] = mod
			registeredClasses.append(testClass)
			registeredModules.append(mod)
		# emit signal
		self.classesChanged(self.RegisterEvent(
			registeredClasses, registeredModules))

	def reloadClasses(self, classesToReload:T.List[type]):
		"""reload the modules holding a set of classesToReload, then reimport them
		this may lead to some classesToReload in catalogue being out of date,
		but accessing them via the catalogue means that is actually
		ok"""
		# check only known classesToReload are passed
		unknownClasses = set(classesToReload).difference(set(self.classModuleMap.keys()))
		if unknownClasses:
			raise RuntimeError("Tried to reload unknown classesToReload {}".format(unknownClasses))

		oldClasses = []
		newClasses = []
		newModules = []

		oldNewClassMap = {i : None for i in classesToReload}
		newClassModuleMap = {}
		#testClasses = set()
		# get modules to reload
		modulesToReload = set(self.classModuleMap[i] for i in classesToReload)
		for module in modulesToReload:
			newModule = importlib.reload(module)
			foundClasses = self.getClassesInModule(newModule)
			#testClasses.update(foundClasses)
			for foundClass in foundClasses:
				newClassModuleMap[foundClass] = module

		# pair up old class, new class and module
		validClasses = set(newClassModuleMap.keys())
		for oldClass in classesToReload:
			newClass = self.getMatchingReloadedClass(oldClass, validClasses)
			newModule = newClassModuleMap[newClass]
			oldClasses.append(oldClass)
			newClasses.append(newClass)
			newModules.append(newModule)

		event = self.ReloadEvent(oldClasses,
								 newClasses,
								 newModules)
		self.classesReloaded(event)


	def getMatchingReloadedClass(self, testClass:type, classPool:T.Set[type]):
		"""associated an old class with its reloaded version
		for now just check the class __name__ - don't go renaming
		classesToReload and then hot-reloading them."""
		for poolClass in classPool:
			if poolClass.__name__ == testClass.__name__:
				return poolClass
		return None


	def displayStr(self):
		return "{} : \n".format(self) + pprint.pformat(self.classModuleMap)

	def display(self):
		print(self.displayStr())

baseChimaeraCatalogue = ClassCatalogue([ROOT_PATH],
                                       baseClasses={ChimaeraNode},
                                       parentPackageNames=["chimaera"])
