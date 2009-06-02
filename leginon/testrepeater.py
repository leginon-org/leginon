
import leginondata
import targetrepeater

class TestRepeater(targetrepeater.TargetRepeater):
	def __init__(self, *args, **kwargs):
		super(TestRepeater, self).__init__(*args, **kwargs)
		self.start()

	def makeStates(self):
		# repeate the current state 3 times
		mystate = self.instrument.getData(leginondata.ScopeEMData)
		return [mystate for i in range(3)]
