import targetfilter
import leginondata
import gui.wx.SampleTargetFilter

class SampleTargetFilter(targetfilter.TargetFilter):
	panelclass = gui.wx.SampleTargetFilter.Panel
	settingsclass = leginondata.SampleTargetFilterSettingsData
	defaultsettings = dict(targetfilter.TargetFilter.defaultsettings)
	# add user settings here
	defaultsettings.update({
		'square length':50,
		'dark number':1,
		'dark number':1,
		'medium number':1,
	})

	def __init__(self, *args, **kwargs):
		targetfilter.TargetFilter.__init__(self, *args, **kwargs)
		if self.__class__ == SampleTargetFilter:
			self.start()

	def filterTargets(self, targetlist):
		self.logger.info('filtering target list:  sampling extreme and median intensity stats')
		newlist = []
		meanlist = []
		targetmeans = {}
		half_length = self.settings['square length'] / 2
		for target in targetlist:
			oldtarget = leginondata.AcquisitionImageTargetData(initializer=target)
			imagearray = oldtarget['image']['image']
			shape = imagearray.shape
			row,col = oldtarget['delta row']+shape[0]/2,oldtarget['delta column']+shape[1]/2
			rowrange = (max(0,row-half_length),min(shape[0],row+half_length))
			colrange = (max(0,col-half_length),min(shape[0],col+half_length))
			mean = imagearray[rowrange[0]:rowrange[1],colrange[0]:colrange[1]].mean()
			stdv = imagearray[rowrange[0]:rowrange[1],colrange[0]:colrange[1]].std()
			#make an unique key for the dictionary targetmeans
			while mean in targetmeans.keys():
				mean = mean+0.0001
			targetmeans[mean] = target
			meanlist.append(mean)
		meanlist.sort()

		targetnumber = len(meanlist)
		outputnumbers = []
		outputnumbers.extend(range(0,self.settings['dark number']))
		outputnumbers.extend(range(targetnumber-self.settings['bright number'],targetnumber))
		median_start = targetnumber/2-self.settings['median number']/2
		outputnumbers.extend(range(median_start,median_start+self.settings['median number']))
		# get unique and sorted list
		outputnumbers = list(set(outputnumbers))
		# create a new target list with these filtered targets
		for i in outputnumbers:
			mean = meanlist[i]
			target = targetmeans[mean]
			newtarget = leginondata.AcquisitionImageTargetData(initializer=target)
			newtarget['fromtarget'] = target
			newlist.append(newtarget)
		return newlist
