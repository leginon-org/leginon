#!/usr/bin/env python
import time
import inspect
from pyami import moduleconfig
from pyscope import instrumenttype
search_for = 'TEM'

def test(tem_inst, attr_name, arg=None):
	if arg is None:
		try:
			result = getattr(tem_inst, attr_name)()
		except Exception as e:
			if 'adaExp' in e:
				pass
			raise RuntimeError('Error testing %s: %s' % (attr_name,e))
	else:
		try:
			result = getattr(tem_inst, attr_name)(arg)
		except Exception as e:
			if 'adaExp' in e:
				pass
			raise RuntimeError('Error testing %s with %s: %s' % (attr_name, attr_name, e))			

def _testGet(tem_inst, attr_name, count=False):
	this_module = inspect.getmodule(tem_inst)
	try:
		if 'ApertureSelection' in attr_name or 'ApertureNames' in attr_name:
			test(tem_inst, attr_name, 'objective')
		elif attr_name.endswith('SlotState'):
			test(tem_inst, attr_name, 1)
		elif 'Film' in attr_name:
			# don't test film functions
			return None # skip
		elif 'Config' in attr_name and hasattr(this_module,'configs'):
			k = getattr(this_module,'configs').keys()[0]
			test(tem_inst, attr_name, k)
		else:
			test(tem_inst, attr_name)
		return True
	except RuntimeError as e:
		return False

def testMethods(tem_inst):
	capabilities = tem_inst.getCapabilities()
	attr_names = dir(tem_inst)
	exclusions = []
	error_count = 0
	good_get = []
	# test all get methods
	for a in attr_names:
		if a.startswith('get'):
			is_success = _testGet(tem_inst,a)
			if is_success == False:
				print(e)
				error_count += 1
			elif is_success == True:
				good_get.append(a)
				
	for c in capabilities:
		if c['name'] in exclusions:
			continue
		impls = c['implemented']
		if 'get' in impls:
			attr_name = 'get'+c['name']
			if attr_name not in good_get:
				continue
			try:
				if 'ApertureSelection' in a or 'ApertureNames' in a:
					result = getattr(tem_inst, attr_name)('objective')
				elif a.endswith('SlotState'):
					result = getattr(tem_inst, attr_name)(1)
				else:
					result = getattr(tem_inst, attr_name)()
				if 'set' in impls:
					attr_name = 'set'+c['name']
					t0 = time.time()
					print attr_name
					getattr(tem_inst, attr_name)(result)
					print 'time (s): %.6f' % (time.time()-t0)
			except Exception as e:
				print 'Error testing %s: %s' % (attr_name,e)
				error_count += 1
	print('----------------------')
	print('Number of error found: %d' % (error_count,))

t = instrumenttype.getInstrumentTypeInstance(search_for)
global this_module 
t.findMagnifications()
testMethods(t)
raw_input('Finished. Hit return to quit')
