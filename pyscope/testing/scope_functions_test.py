#!/usr/bin/env python
from pyami import moduleconfig

search_for = 'TEM'

def getInstrumentTypeInstance(search_for):
	'''
	Return instance of the first instrument with the search_for class name.
	'''
	instruments = moduleconfig.getConfigured('instruments.cfg')
	for key in instruments:
		module_class_name = instruments[key]['class']
		if search_for in module_class_name:
			bits = module_class_name.split('.')
			import_name = 'pyscope.'+bits[0]
			module_name = bits[0]
			class_name = bits[1]
			pk = __import__(import_name)
			mod = getattr(pk, module_name)
			inst = getattr(mod, class_name)()
			print 'Testing %s' % (class_name,)
			return inst

def test(tem_inst, attr_name, arg=None):
	if arg is None:
		try:
			result = getattr(tem_inst, attr_name)()
		except Exception as e:
			print 'Error testing %s: %s' % (attr_name,e)			
	else:
		try:
			result = getattr(tem_inst, attr_name)(arg)
		except Exception as e:
			print 'Error testing %s with %s: %s' % (attr_name, attr_name, e)			

def testMethods(tem_inst):
	capabilities = tem_inst.getCapabilities()
	attr_names = dir(tem_inst)
	exclusions = []
	# test all get methods
	for a in attr_names:
		if a.startswith('get'):
			attr_name = a
			if 'ApertureSelection' in a:
				test(tem_inst, attr_name, 'objective')
			elif a.endswith('SlotState'):
				test(tem_inst, attr_name, 1)
			else:
				test(tem_inst, attr_name)
				
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
					getattr(tem_inst, attr_name)(result)

			except Exception as e:
				print 'Error testing %s: %s' % (attr_name,e)

t = getInstrumentTypeInstance(search_for)
t.findMagnifications()
testMethods(t)
raw_input('Finished. Hit return to quit')
