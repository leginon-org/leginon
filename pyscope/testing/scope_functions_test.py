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
			if 'adaExp' in str(e):
				return # let it pass
			raise RuntimeError('Error testing %s: %s' % (attr_name,e))
	else:
		try:
			result = getattr(tem_inst, attr_name)(arg)
		except Exception as e:
			if 'adaExp' in str(e):
				return # let it pass
			raise RuntimeError('Error testing %s with %s: %s' % (attr_name, attr_name, e))			


def testMethods(tem_inst):
	capabilities = tem_inst.getCapabilities()
	attr_names = dir(tem_inst)
	exclusions = []
	error_count = 0
	good_get = []
	this_module = inspect.getmodule(tem_inst)
	# test all get methods
	for a in attr_names:
		if a.startswith('get'):
			try:
				if 'ApertureSelection' in a or 'ApertureNames' in a:
					test(tem_inst, a, 'objective')
				elif a.endswith('SlotState'):
					test(tem_inst, a, 1)
				elif 'Film' in a or 'LowDose' in a:
					# don't test film or lowdose functions
					continue
				elif 'Config' in a and hasattr(this_module,'configs'):
					k = getattr(this_module,'configs').keys()[0]
					test(tem_inst, a, k)
				else:
					test(tem_inst, a)
				good_get.append(a)
			except RuntimeError as e:
				print(e)
				error_count += 1
				
	for c in capabilities:
		if c['name'] in exclusions:
			continue
		impls = c['implemented']
		if 'get' in impls:
			attr_name = 'get'+c['name']
			if attr_name not in good_get:
				continue
			# testing set method with input of get method.
			try:
				# same logic as in get tests but need the result back.
				if 'ApertureSelection' in attr_name or 'ApertureNames' in attr_name:
					result = getattr(tem_inst, attr_name)('objective')
				elif attr_name.endswith('SlotState'):
					result = getattr(tem_inst, attr_name)(1)
				elif 'Stigmator' in attr_name:
					result = {'objective': getattr(tem_inst, attr_name)()['objective']}
				else:
					result = getattr(tem_inst, attr_name)()
				# now test set
				if 'set' in impls:
					attr_name = 'set'+c['name']
					t0 = time.time()
					print attr_name
					test(tem_inst, attr_name,result)
					print 'time (s): %.6f' % (time.time()-t0)
			except Exception as e:
				if 'adaExp' in str(e):
					continue
				print 'Error testing %s: %s' % (attr_name,e)
				error_count += 1
	print('----------------------')
	print('Number of error found: %d' % (error_count,))

t = instrumenttype.getInstrumentTypeInstance(search_for)
global this_module 
t.findMagnifications()
testMethods(t)
raw_input('Finished. Hit return to quit')
