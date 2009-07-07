import gui.wx.TiltRotate
import leginondata
import targetrepeater

class TiltRotateRepeater(targetrepeater.TargetRepeater):
	transformtype = 'rotation'
	panelclass = gui.wx.TiltRotate.Panel
	settingsclass = leginondata.TiltRotateSettingsData
	defaultsettings = targetrepeater.TargetRepeater.defaultsettings
	defaultsettings.update({
		'tilts': '(0,)',
	})

	def __init__(self, *args, **kwargs):
		super(TiltRotateRepeater, self).__init__(*args, **kwargs)
		self.start()

	def makeStates(self):
		## list of tilts entered by user in degrees, converted to radians
		tiltstr = self.settings['tilts']
		try:
			alphatilts = eval(tiltstr)
		except:
			self.logger.error('Invalid tilt list')
			return
		## check for singular value
		if isinstance(alphatilts, float) or isinstance(alphatilts, int):
			alphatilts = (alphatilts,)
		if len(alphatilts) == 0:
			self.logger.warning("Please set to Bypass if you do not want to repeat")
			return []
		states = []
		self.logger.info('tilt series =' + str(alphatilts))
		for a in alphatilts:
			rad = a * 3.14159 / 180.0
			scope = leginondata.ScopeEMData()
			scope['stage position'] = {'a': rad}
			states.append(scope)
		return states
