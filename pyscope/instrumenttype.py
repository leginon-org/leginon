#!/usr/bin/env python
from pyami import moduleconfig
def getInstrumentTypeInstance(search_for):
	'''
	Return instance of the first instrument with the search_for class type.
	'''
	instruments = moduleconfig.getConfigured('instruments.cfg')
	for key in instruments:
		if search_for.lower() == 'tem':
			if 'cs' not in instruments[key].keys():
				continue
		elif search_for.lower() == 'camera':
			if 'zplane' not in instruments[key].keys():
				continue
		else:
			raise ValueError('Invalid search type: %s' % (search_for,))

		module_class_name = instruments[key]['class']
		bits = module_class_name.split('.')
		import_name = 'pyscope.'+bits[0]
		module_name = bits[0]
		class_name = bits[1]
		pk = __import__(import_name)
		mod = getattr(pk, module_name)
		inst = getattr(mod, class_name)()
		print 'Loading %s' % (class_name,)
		return inst
