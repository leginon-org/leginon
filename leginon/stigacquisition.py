#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

from leginon import leginondata
from leginon import acq as acquisition
import leginon.gui.wx.StigAcquisition

class StigAcquisition(acquisition.Acquisition):
	panelclass = leginon.gui.wx.StigAcquisition.Panel
	settingsclass = leginondata.StigAcquisitionSettingsData
	defaultsettings = dict(acquisition.Acquisition.defaultsettings)
	defaultsettings.update({
		'stig0x': 0.0,
		'stig0y': 0.0,
		'stig1x': 0.0,
		'stig1y': 0.0,
		'stigcount': 5,
	})

	def _setStig(self, stigdict):
		stig = {'objective': stigdict}
		self.instrument.tem.Stigmator = stig

	def setStig(self, index):
		if index == 0:
			newstig = {'x':self.settings['stig0x'], 'y':self.settings['stig0y']}
		else:
			newstig = {'x':self.settings['stig1x'], 'y':self.settings['stig1y']}
		self._setStig(newstig)

	def setStigIndex(self):
		if not hasattr(self, 'stigcounter'):
			self.stigcounter = -1
		if not hasattr(self, 'stig_index'):
			self.stig_index = 1
		self.stigcounter += 1
		if self.stigcounter % self.settings['stigcount']:
			return
		if self.stig_index == 1:
			self.stig_index = 0
		else:
			self.stig_index = 1
		self.logger.info('switched to stig %s' % (self.stig_index,))

	def acquire(self, *args, **kwargs):
		self.setStigIndex()
		self.setStig(self.stig_index)
		ret = acquisition.Acquisition.acquire(self, *args, **kwargs)
		self.setStig(0)
		return ret
