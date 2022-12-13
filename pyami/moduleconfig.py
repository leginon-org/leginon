#!/usr/bin/env python
'''
Config file selection and parameter parsing.

combine = True use three levels of dictionary structure.
i.e. like sinedon.cfg, leginon.cfg in sinedon.dbconfig and leginon.leginonconfigparser

combine = False choose one file in the three possible locations according
to pyami.fileutil
This is mainly used to define instrument and host-specific behavior
'''
import copy
import sys
import configparser
import os
import imp
import pyami.fileutil

class ModuleConfigParser(object):
	def __init__(self,filename,package='pyscope', combine=False):
		self.configparser = configparser.ConfigParser()
		self.configured = {}
		self.config_filename = filename
		self.configfiles = None
		self.configpath = None
		self.package = package
		self.combine = combine


	def newHierarchyDict(self,keys,value):
		d = list(map((lambda x:{}),list(range(len(keys)+1))))
		d[0] = value
		keys.reverse()
		for i in range(len(keys)):
			d[i+1][keys[i]] = d[i]
		return copy.deepcopy(d[len(keys)])

	def formatValue(self,name, key):
		'''
		Return value in python format.
		Integer
		Float
		Boolean : True/False
		List: comma-seperated values
		String: anything else.
		'''
		value = None
		try:
			value = int(self.configparser.get(name, key))
		except:
			try:
				value = float(self.configparser.get(name, key))
			except:
				try:
					value = self.configparser.getboolen(name,key)
				except:
					valuestring = self.configparser.get(name,key)
					if valuestring.lower() == 'true':
						value = True
					elif valuestring.lower() == 'false':
						value = False
					elif ',' in valuestring:
						items = self.configparser.get(name,key).split(',')
						
						try:
							#list of floats for aparture sizes
							value = list(map((lambda x: float(x)), items))
							#test last value since first might be 0
							if int(value[-1]) == value[-1]:
								#list of integers for lens or deflector neutrals
								value = list(map((lambda x: int(x)), value))
						except:
							#list of strings for mag mode 
							value = list(map((lambda x: x.strip()), items))
					else:
						value = valuestring
		return value

	def addHierarchyValue(self,name,levels,value):
		'''
		Add values to configured up to 3 levels.
		'''
		# This can be written perttier, but will do for now.
		if len(list(self.configured[name].keys())) == 0:
			self.configured[name] = self.newHierarchyDict(levels,value)
			return
		if len(levels) == 1:
			self.configured[name][levels[0]] = value
		else:
			if len(levels) == 2:
				if levels[0] not in list(self.configured[name].keys()):
					self.configured[name][levels[0]]={}
				self.configured[name][levels[0]][levels[1]]=value
			if len(levels) == 3:
				if levels[0] not in list(self.configured[name].keys()):
					self.configured[name].update(self.newHierarchyDict(levels,value))
					return
				elif levels[1] not in list(self.configured[name][levels[0]].keys()):
					self.configured[name][levels[0]].update(self.newHierarchyDict(levels[1:],value))
					return
				else:
					self.configured[name][levels[0]][levels[1]][levels[2]]=value

	def convertKeys(self,keys):
		newkeys = []
		for key in keys:
			try:
				newkey = int(key)
			except:
				newkey = key
			newkeys.append(newkey)
		return newkeys

	def _getConfigModuleName(self):
		'''
		return the name used in environment variable before _CFG_PATH
		for fileutil.get_config_dirs
		If None is return, then package name is used.
		'''
		#print("parsing %s" % self.config_filename)
		if self.config_filename.endswith('.cfg'):
			module_name = self.config_filename[:-4]
		else:
			module_name = None
		return module_name

	def getConfigPath(self):
		# read module_name.cfg
		module_name = self._getConfigModuleName()
		confdirs = pyami.fileutil.get_config_dirs(module_name=module_name, package_name=self.package)
		filenames = [os.path.join(confdir, self.config_filename) for confdir in confdirs]
		# refs Issue #10221. Use the last filename if exists.
		filenames.reverse()
		one_exists = False
		for filename in filenames:
			if os.path.exists(filename):
				one_exists = True
				self.configpath = filename
				return filename
		if not one_exists:
			raise IOError('please configure at least one of these:  %s' % (filenames,))

	def getConfigPaths(self):
		if self.combine == False:
			return self.getConfigPath()
		else:
			# combine all confdirs
			module_name = self._getConfigModuleName()
			confdirs = pyami.fileutil.get_config_dirs(module_name=module_name, package_name=self.package)
			filenames = [os.path.join(confdir, self.config_filename) for confdir in confdirs]
			one_exists = sum(map((lambda x:os.path.exists(x)),filenames))
			if not one_exists:
				raise IOError('please configure at least one of these:  %s' % (filenames,))
			return filenames

	def parse(self):
		'''
		Select one of the three possible filepath and parse
		for parameters.
		'''
		configpaths = self.getConfigPaths()
		try:
			self.configfiles = self.configparser.read(configpaths)
		except:
			raise IOError('error reading %s' % (configpaths,))

		# parse
		names = self.configparser.sections()
		for name in names:
			self.configured[name] = {}
			hierarchy_keys = self.configparser.options(name)
			for hi_key in hierarchy_keys:
				value = self.formatValue(name,hi_key)
				levels = hi_key.split('%')
				levels = self.convertKeys(levels)
				self.addHierarchyValue(name,levels,value)
		return self.configured

def getConfigPath(config_file='jeol.cfg', package='pyscope'):
	'''
	External call for getting the config path to use.
	'''
	app = ModuleConfigParser(config_file, package=package)
	configpath = app.getConfigPath()
	return configpath

def getConfigured(config_file='jeol.cfg', package='pyscope', combine=False):
	'''
	External call for getting the parameter dictionary from config_file.
	'''
	app = ModuleConfigParser(config_file, package=package, combine=combine)
	configured = app.configured
	if not configured:
		configured = app.parse()
	return configured

def testOneConfig(config_file,package_name, combine=False):
	from pyami import testfun
	module = 'moduleconfig loading %s in %s subpackage' % (config_file, package_name)
	try:
		configs = getConfigured(config_file, package=package_name, combine=combine)
		if type(configs) == type({}) and list(configs.keys()):
			testfun.printResult(module,True)
		else:
			testfun.printResult(module,False,'config not read')
	except Exception as e:
		testfun.printResult(module,False,e)

def test():
	testOneConfig('leginon.cfg','leginon', True)
	testOneConfig('instruments.cfg','pyscope', False)
	#print(getConfigured('instruments.cfg', 'pyscope', False))
	print(getConfigured('leginon.cfg', 'leginon', True))

if __name__ == '__main__':
	test()
	if sys.platform == 'win32':
		input('Hit any key to quit.')
