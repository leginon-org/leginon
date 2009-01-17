# $Source: /ami/sw/cvsroot/pyleginon/reference.py,v $
# $Revision: 1.7 $
# $Name: not supported by cvs2svn $
# $Date: 2006-10-13 04:13:07 $
# $Author: suloway $
# $State: Exp $
# $Locker:  $

import reference
import leginondata
import event
import gui.wx.Reference
from pyami import arraystats

class BeamFixer(reference.Reference):
	# relay measure does events
	eventinputs = reference.Reference.eventinputs + [event.FixBeamEvent]
	panelclass = gui.wx.Reference.ReferencePanel
	def __init__(self, *args, **kwargs):
		try:
			watch = kwargs['watchfor']
		except KeyError:
			watch = []
		kwargs['watchfor'] = watch + [event.FixBeamEvent]
		reference.Reference.__init__(self, *args, **kwargs)

	def processData(self, incoming_data):
		reference.Reference.processData(self, incoming_data)
		if isinstance(incoming_data, data.FixBeamData):
			self.processRequest(incoming_data)

	def acquire(self):
		try:
			imagedata = self.instrument.getData(leginondata.CorrectedCameraImageData)
		except:
			self.logger.error('unable to get corrected image')
			return
		return imagedata

	def execute(self, request_data=None):
		# get current beam shift
		original_beamshift = self.instrument.tem.BeamShift
		bestbeamshift = original_beamshift
		maxvalue = 0

		for beamx in (-1e-6, 1e-6):
			newbeamx = original_beamshift['x'] + beamx
			for beamy in (-1e-6, 1e-6):
				newbeamy = original_beamshift['y'] + beamy

				# set scope parameters
				newbeamshift = {'x': newbeamx, 'y': newbeamy}
				self.instrument.tem.BeamShift = newbeamshift

				# acquire image
				imagedata = self.acquire()

				# check image
				meanvalue = arraystats.mean(imagedata['image'])
				if meanvalue > maxvalue:
					maxvalue = meanvalue
					bestbeamshift = newbeamshift

		# set to the best beam shift
		self.instrument.tem.BeamShift = bestbeamshift
			
		self.logger.info('Best Beam Shift: %s' % (bestbeamshift,))
