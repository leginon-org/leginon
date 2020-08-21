#!/usr/bin/env python
import time
from pyami import moduleconfig
from pyscope import instrumenttype
search_for = 'Camera'

def test(tem_inst, attr_name, arg=None):
	if arg is None:
		try:
			result = getattr(tem_inst, attr_name)()
		except Exception as e:
			raise RuntimeError('Error testing %s: %s' % (attr_name,e))
	else:
		try:
			result = getattr(tem_inst, attr_name)(arg)
		except Exception as e:
			raise RuntimeError('Error testing %s with %s: %s' % (attr_name, attr_name, e))			

def testMethods(tem_inst):
	capabilities = tem_inst.getCapabilities()
	attr_names = dir(tem_inst)
	exclusions = []
	error_count = 0
	# test all get methods
	for a in attr_names:
		try:
			if a.startswith('get'):
				attr_name = a
				if 'ApertureSelection' in a:
					test(tem_inst, attr_name, 'objective')
				elif a.endswith('SlotState'):
					test(tem_inst, attr_name, 1)
				else:
					test(tem_inst, attr_name)
		except RuntimeError as e:
			print(e)
			error_count += 1
				
	for c in capabilities:
		if c['name'] in exclusions:
			continue
		impls = c['implemented']
		if 'get' in impls:
			attr_name = 'get'+c['name']
			try:
				result = getattr(tem_inst, attr_name)()
				if 'set' in impls:
					attr_name = 'set'+c['name']
					t0 = time.time()
					print attr_name
					getattr(tem_inst, attr_name)(result)
					print time.time()-t0
			except Exception as e:
				print 'Error testing %s: %s' % (attr_name,e)
				error_count += 1
	print('----------------------')
	print('Number of error found: %d' % (error_count,))

t = instrumenttype.getInstrumentTypeInstance(search_for)
testMethods(t)
raw_input('Finished. Hit return to quit')
