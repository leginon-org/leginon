import os
from win32com.client import selecttlb
from win32com.client import gencache

info = [
	(('TEM Scripting','Tecnai Scripting'), 'TEM Scripting'),
	(('TOMMoniker 1.0 Type Library',), 'TOM Moniker'),
	(('Low Dose Server Library',), 'Tecnai Low Dose Kit'),
	(('adaExp Library',), 'Tecnai Exposure Adaptor'),
	(('TecnaiCCD 1.0 Type Library',), 'Gatan CCD Camera'),
	(('CAMC4 1.0 Type Library',), 'Tietz CCD Camera'),
	(('ES Vision 3.1 Type Library','ES Vision 3.0 Type Library'), 'TIA CCD Camera'),
]
items = selecttlb.EnumTlbs()

def getTlbFromDesc(desc):
	for item in items:
		if item.desc == desc:
			return item
	return None

def makeFile(descs):
	typelibInfo = None
	for desc in descs:
		typelibInfo = getTlbFromDesc(desc)
		if typelibInfo is not None:
			print '\nFound: ', desc
			break
	if typelibInfo is None:
		print '\nError, cannot find typelib for "%s"\n' % (descs,)
		return

	clsid = typelibInfo.clsid
	major = int(typelibInfo.major)
	minor = int(typelibInfo.minor)
	lcid = typelibInfo.lcid

	try:
		gencache.MakeModuleForTypelib(clsid, lcid, major, minor)
	except:
		print 'failed MakeModuleForTypelib'
		return
	else:
		print 'done.'
		print ''

def run():
	print 'Generating .py files from type libraries...'
	for desc, message in info:
		print 'initializing', message,
		makeFile(desc)
	raw_input('enter to quit.')

if __name__ == '__main__':
	run()

