import os
import comtypes
import comtypes.client
com_module =  comtypes

# message name, comnames
items = [
		('TEM Scripting', ('Tecnai.Instrument', 'TEMScripting.Instrument.1')),
		('TOM Moniker', ('TEM.Instrument.1',)),
		('Tecnai Low Dose Kit', ('LDServer.LdSrv',)),
		('Tecnai Exposure Adaptor', ('adaExp.TAdaExp',)),
		('Gatan CCD Camera', ('TecnaiCCD.GatanCamera.2',)),
		('TIA', ('ESVision.Application',)),

]

def getTlbFromComname(comname):
	try:
		comobj = comtypes.client.CreateObject(comname)
		return comname, comobj
	except:
		pass
	return None

def makeFile(item):
	typelibInfo = None
	message, comnames = item
	for i, comname in enumerate(comnames):
		typelibInfo = getTlbFromComname(comname)
		if typelibInfo is not None:
			print '\nFound COM typelib named: %s' % comname
			break
	if typelibInfo is None:
		print '\nError, cannot find typelib for "%s"\n' % (message,)
		return

def run():
	print 'Looking for COM module files from type libraries...\n'
	for item in items:
		print 'checking', item[0],
		makeFile(item)
		print '\n'
	raw_input('enter to quit.')

if __name__ == '__main__':
	run()

