import targetfilter
import data

class ExampleTargetFilter(targetfilter.TargetFilter):
	'''
	Example of a TargetFilter subclass
	'''
	settingsclass = data.ExampleTargetFilterSettingsData
	# just using base class panel for now
	#panelclass = gui.wx.ExampleTargetFilter.Panel
	def filterTargets(self, targetlist):
		self.logger.info('filtering target list:  all targets x,y = x+1,y+1')
		newlist = []
		for target in targetlist:
			newtarget = data.AcquisitionImageTargetData(initializer=target)
			newtarget['delta row'] += 1
			newtarget['delta column'] += 1
			newlist.append(newtarget)
		return newlist
