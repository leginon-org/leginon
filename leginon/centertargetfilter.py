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

	def filterTargets(self, targetlist):
		limit = self.settings['limit']
		self.logger.info('filtering target list:  all targets x,y = x+1,y+1')
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
		if limit >= targetnumber:
			for i in range(0,targetnumber):
				newtarget = data.AcquisitionImageTargetData(initializer=target)
				newlist.append(newtarget)
		else:
			for i in range(0,limit):
				target = targetdistances[distlist[i]]
				newtarget = data.AcquisitionImageTargetData(initializer=target)
				newlist.append(newtarget)
		return newlist
