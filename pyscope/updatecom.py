import os
from win32com.client import selecttlb
from win32com.client import makepy

info = [
	('Tecnai Scripting', 'tecnaicom.py', 'Tecnai Scripting'),
	('TEM Scripting', 'tecnaicom.py', 'Tecnai Scripting'),
	('Low Dose Server Library', 'ldcom.py', 'Tecnai Low Dose Kit'),
	('adaExp Library', 'adacom.py', 'Tecnai Exposure Adaptor'),
	('TecnaiCCD 1.0 Type Library', 'gatancom.py', 'Gatan CCD Camera'),
	('CAMC4 1.0 Type Library', 'tietzcom.py', 'Tietz CCD Camera'),
]
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

	makepy.GenerateFromTypeLibSpec(typelibInfo, file,
																	progressInstance=makepy.SimpleProgress(0))
	print '%s -> %s' % (desc, filename)

def run(path=None):
	print 'Generating .py files from type libraries...'
	for desc, filename, message in info:
		if path is not None:
			filename = os.path.join(path, filename)
		print message + ':',
		makeFile(desc, filename)
	print 'Done.'

if __name__ == '__main__':
	run()

