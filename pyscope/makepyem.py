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
		print 'Error: cannot find typelib for "%s"' % desc
		return

	try:
		file = open(filename, 'w')
	except:
		print 'Error: cannot open file "%s"' % filename
		return

	makepy.GenerateFromTypeLibSpec(typelibInfo, file)
	print '%s -> %s' % (desc, filename)

if __name__ == '__main__':
	info = [
					('adaExp Library', 'adacom.py'),
					('TecnaiCCD 1.0 Type Library', 'gatancom.py'),
					('Tecnai Scripting', 'tecnaicom.py'),
					('CAMC4 1.0 Type Library', 'tietzcom.py')
					]
	for desc, filename in info:
		makeFile(desc, filename)

