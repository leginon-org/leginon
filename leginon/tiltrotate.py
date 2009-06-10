
import leginondata
import targetrepeater

class TiltRotateRepeater(targetrepeater.TargetRepeater):
	transformtype = 'rotation'

	def __init__(self, *args, **kwargs):
		super(TiltRotateRepeater, self).__init__(*args, **kwargs)
		self.start()

	def makeStates(self):
		alphatilts = [0, -5, 5]
		states = []
		for a in alphatilts:
			rad = a * 3.14159 / 180.0
			scope = leginondata.ScopeEMData()
			scope['stage position'] = {'a': rad}
			states.append(scope)
		return states
