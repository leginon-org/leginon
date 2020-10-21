#!/usr/bin/env python
import time
from pyami import moduleconfig
from pyscope import instrumenttype
import inspect
search_for = 'Camera'

def test(cam_inst, attr_name, arg=None):
	if arg is None:
		try:
			result = getattr(cam_inst, attr_name)()
		except Exception as e:
			raise RuntimeError('Error testing %s: %s' % (attr_name,e))
	else:
		try:
			result = getattr(cam_inst, attr_name)(arg)
		except Exception as e:
			raise RuntimeError('Error testing %s with %s: %s' % (attr_name, attr_name, e))			
	print 'testing %s successful' % attr_name

def testMethods(cam_inst):
	capabilities = cam_inst.getCapabilities()
	attr_names = dir(cam_inst)
	this_module = inspect.getmodule(cam_inst)
	exclusions = []
	error_count = 0
	# test all get methods
	for a in attr_names:
		try:
			if a.startswith('get'):
				attr_name = a
				args = inspect.getargspec(getattr(cam_inst,attr_name))[0]
				# handle get attributes that has specific argument to add.
				if 'shape' in args:
					shapedict = getattr(cam_inst, 'getDimension')()
					shape = (shapedict['y'],shapedict['x'])
					test(cam_inst, attr_name, shape)
				elif a.endswith('Callback'):
					pass
				elif 'Buffer' in attr_name and 'name' in args:
					if not cam_inst.buffer_ready.keys():
						pass
					else:
						name = cam_inst.buffer_ready.keys()[0]
						test(cam_inst, attr_name, name)
				elif 'Config' in attr_name and hasattr(this_module,'configs'):
					k = getattr(this_module,'configs').keys()[0]
					test(cam_inst, attr_name, k)
				elif 'MetaDataDict' in attr_name:
					# need known object to test.  pass.
					pass
				else:
					test(cam_inst, attr_name)
		except RuntimeError as e:
			print(e)
			error_count += 1
		except Exception as e:
			raise
				
	for c in capabilities:
		if c['name'] in exclusions:
			continue
		impls = c['implemented']
		if 'get' in impls:
			attr_name = 'get'+c['name']
			try:
				result = getattr(cam_inst, attr_name)()
				if 'set' in impls:
					attr_name = 'set'+c['name']
					t0 = time.time()
					print attr_name
					getattr(cam_inst, attr_name)(result)
					print 'time (s): %.6f' % (time.time()-t0)
			except Exception as e:
				print 'Error testing %s: %s' % (attr_name,e)
				error_count += 1
	print('----------------------')
	print('Number of error found: %d' % (error_count,))

t = instrumenttype.getInstrumentTypeInstance(search_for)
testMethods(t)
raw_input('Finished. Hit return to quit')
