#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#
from leginon import acq as acquisition
from leginon import leginondata
import threading
from pyami import imagefun, fftfun, ordereddict
import leginon.gui.wx.DefocusSequence

def setImageFilename(imagedata, sequence_number):
	if imagedata['filename'] is not None:
		return
	listlabel = ''
	numberstr = '%05d' % (imagedata['target']['number'],)
	if imagedata['target']['list'] is not None:
		listlabel = imagedata['target']['list']['label']
	if imagedata['preset'] is None:
		presetstr = ''
	else:
		presetstr = imagedata['preset']['name']
	mystr = numberstr + presetstr
	rootname = acquisition.getRootName(imagedata, listlabel)
	parts = []
	parts.append(rootname)
	if listlabel:
		parts.append(listlabel)
	parts.append(mystr)
	if sequence_number:
		dstr = 'd%02d' % (sequence_number)
		parts.append(dstr)
	if imagedata['version']:
		vstr = 'v%02d' % (imagedata['version'],)
		parts.append(vstr)
	filename = '_'.join(parts)
	imagedata['filename'] = filename

class DefocusSequence(acquisition.Acquisition):
	'''
	This node acquires defocus sequence starting from the
	preset value for each target. It is a subclass of Acquisition
	and use the same bindings. The resulting image names has postfix of d.
	'''
	panelclass = leginon.gui.wx.DefocusSequence.Panel
	settingsclass = leginondata.DefocusSequenceSettingsData
	defaultsettings = dict(acquisition.Acquisition.defaultsettings)
	defaultsettings.update({
			'step size': 1e-6, #meters
			'nsteps': 2,
	})

	eventinputs = acquisition.Acquisition.eventinputs
	eventoutputs = acquisition.Acquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		self.sequence_number = None
		acquisition.Acquisition.__init__(self, id, session, managerlocation, **kwargs)

	def getDefocusSeries(self, presetdata):
		defocus0 = presetdata['defocus']
		step_size = self.settings['step size']
		total_number = self.settings['nsteps']
		defocii = list(map((lambda x: defocus0+step_size*x), list(range(total_number))))
		return defocii

	def acquire(self, presetdata, emtarget=None, attempt=None, target=None, channel=None):
		reduce_pause = self.onTarget
		status = self.moveAndPreset(presetdata, emtarget)
		if status == 'error':
			self.logger.warning('Move failed. skipping acquisition at this target')
			return status
		defaultchannel = self.preAcquire(presetdata, emtarget, channel, reduce_pause)

		defocii = self.getDefocusSeries(presetdata)
		try:
			for i,d in enumerate(defocii):
				self.sequence_number = i+1
				self.instrument.tem.Defocus = d
				args = (presetdata, emtarget, defaultchannel)
				if self.settings['background']:
					self.clearCameraEvents()
					t = threading.Thread(target=self.acquirePublishDisplayWait, args=args)
					t.start()
					self.waitExposureDone()
				else:
					self.acquirePublishDisplayWait(*args)
		except:
			self.resetComaCorrection()
			raise
		finally:
			is_failed = self.resetComaCorrection()
			if is_failed:
				self.player.pause()
		return status

	def setImageFilename(self, imagedata):
		setImageFilename(imagedata, self.sequence_number)
