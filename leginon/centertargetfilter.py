import targetfilter
import leginondata
import gui.wx.CenterTargetFilter

class CenterTargetFilter(targetfilter.TargetFilter):
	'''
	Example of a TargetFilter subclass
	'''
	panelclass = gui.wx.CenterTargetFilter.Panel
	settingsclass = leginondata.CenterTargetFilterSettingsData
	defaultsettings = dict(targetfilter.TargetFilter.defaultsettings)
	defaultsettings.update({
		'limit':1,
	})

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
			print target.dbid
			oldtarget = leginondata.AcquisitionImageTargetData(initializer=target)
			dist = oldtarget['delta row']**2+oldtarget['delta column']**2
			while dist in distlist:
				dist += 0.0001
			targetdistances[dist] = target
			distlist.append(dist)
		distlist.sort()

		targetnumber = len(distlist)
		outputnumber=min([targetnumber,limit])

		for i in range(0,outputnumber):
			target = targetdistances[distlist[i]]
			newtarget = leginondata.AcquisitionImageTargetData(initializer=target)
			newtarget['fromtarget'] = target
			newlist.append(newtarget)
		return newlist
