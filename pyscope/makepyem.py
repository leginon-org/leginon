from win32com.client import selecttlb
from win32com.client import makepy

items = selecttlb.EnumTlbs()

def getTlbFromDesc(desc):
	for item in items:
		if item.desc == desc:
			return item
	return None

def makeFile(desc, filename):
	typelibInfo = getTlbFromDesc(desc)

	if typelibInfo is None:
		print 'Error, cannot find typelib for "%s"' % desc
		return

	try:
		file = open(filename, 'w')
	except:
		print 'Error, cannot create file "%s"' % filename
		return

	makepy.GenerateFromTypeLibSpec(typelibInfo, file)
	print '%s -> %s' % (desc, filename)

if __name__ == '__main__':
	info = [
					('Tecnai Scripting', 'tecnaicom.py', 'Tecnai Scripting'),
					('Low Dose Server Library', 'ldcom.py', 'Tecnai Low Dose Kit'),
					('adaExp Library', 'adacom.py', 'Tecnai Exposure Adaptor'),
					('TecnaiCCD 1.0 Type Library', 'gatancom.py', 'Gatan CCD Camera'),
					('CAMC4 1.0 Type Library', 'tietzcom.py', 'Tietz CCD Camera')
					]
	print 'Generating .py files from type libraries...'
	for desc, filename, message in info:
		print message + ':',
		makeFile(desc, filename)
	print 'Done.'

