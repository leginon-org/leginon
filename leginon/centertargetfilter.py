import targetfilter
import data
import gui.wx.CenterTargetFilter

class CenterTargetFilter(targetfilter.TargetFilter):
	'''
	Example of a TargetFilter subclass
	'''
	panelclass = gui.wx.CenterTargetFilter.Panel
	settingsclass = data.CenterTargetFilterSettingsData
	defaultsettings = {
		'limit':1,
		'bypass':True,
	}

	def __init__(self, *args, **kwargs):
		targetfilter.TargetFilter.__init__(self, *args, **kwargs)
		if self.__class__ == CenterTargetFilter:
			self.start()

	def filterTargets(self, targetlist):
		limit = self.settings['limit']
		self.logger.info('filtering target list:  use center %d targets' %limit)
		newlist = []
		distlist = []
		targetdistances = {}
		for target in targetlist:
			oldtarget = data.AcquisitionImageTargetData(initializer=target)
			dist = oldtarget['delta row']**2+oldtarget['delta column']**2
			targetdistances[dist] = target
			distlist.append(dist)
		distlist.sort()

		targetnumber = len(distlist)
		outputnumber=min([targetnumber,limit])

		for i in range(0,outputnumber):
			target = targetdistances[distlist[i]]
			newtarget = data.AcquisitionImageTargetData(initializer=target)
			newtarget['fromtarget'] = target
			newlist.append(newtarget)
		return newlist
