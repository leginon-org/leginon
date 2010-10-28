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
		self.makeTiltPatterns(alphatilts)
		states = []
		self.logger.info('tilt series =' + str(alphatilts))
		for a in alphatilts:
			rad = a * 3.14159 / 180.0
			scope = leginondata.ScopeEMData()
			scope['stage position'] = {'a': rad}
			states.append(scope)
		return states

	def makeTiltPatterns(self,alphatilts):
		tilts = list(alphatilts)
		if 0 not in tilts:
			tilts.append(0)
		tilts.sort()
		patterns = [(0.0,0.0),(-0.25,-0.25)]
		q = leginondata.TiltRasterPatternData(session=self.session)
		for i,tilt in enumerate(tilts):
			q['tilt'] = int(tilt)
			result = q.query(results=1)
			index = (i - tilts.index(0)) % len(patterns)
			pattern = patterns[index]
			if result and result[0]['offset']['col']==pattern[0] and result[0]['offset']['row']==pattern[1]:
				continue
			else:
				qdata = leginondata.TiltRasterPatternData(session=self.session)
				qdata['tilt'] = int(tilt)
				qdata['offset']={'col':pattern[0],'row':pattern[1]}
				qdata.insert(force=True)
