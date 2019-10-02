import comtypes.client
import time

DEBUG = False

## create a single connection to TIA COM object.
## Muliple calls to get_tia will return the same connection.
## Store the handle in the com module, which is safer than in
## this module due to multiple imports.
class TIAConnection(object):
	esv = None

connection = TIAConnection()
def get_tia():
	global connection
	if connection.esv is None:
		try:
			comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
		except:
			comtypes.CoInitialize()
		connection.esv = comtypes.client.CreateObject('ESVision.Application')
	return connection

class TIA(object):
	name = 'TIA'

	def __init__(self):
		# Each camera needs its own display name
		self.tianame = 'display'
		self._connectToESVision()
		self.initSettings()

	def initSettings(self):
		pass

	def debug_print(self, msg):
		if DEBUG:
			print(msg)

	def _connectToESVision(self):
		'''
		Connects to the ESVision COM server
		'''
		connection = get_tia()
		self.esv = connection.esv

	def getActiveDisplayWindow(self):
		return self.esv.ActiveDisplayWindow()

	def getActiveDisplayWindowName(self):
		dispwin = self.getActiveDisplayWindow()
		if not dispwin:
			return None
		else:
			return dispwin.Name

	def getDisplayWindowNames(self):
		return self.esv.DisplayWindowNames()

	def closeDisplayWindow(self, name):
		if name in self.getDisplayWindowNames():
			self.esv.CloseDisplayWindow(name)
		else:
			raise ValueError('Display Window %s does not exist. Can not close' % name)

def closeActiveDisplayWindow():
	c=get_tia
	c.esv.CloseDisplayWindow(c.esv.ActiveDisplayWindow().Name)

if __name__=='__main__':
	t=TIA()
	all_dispwins = t.getDisplayWindowNames()
	for i, name in enumerate(all_dispwins):
		this = t.getActiveDisplayWindow()
		print this.Name
		t.closeDisplayWindow(name)
