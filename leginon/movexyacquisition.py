#
# COPYRIGHT:
#	   The Leginon software is Copyright under
#	   Apache License, Version 2.0
#	   For terms of the license agreement
#	   see  http://leginon.org
#
import math
import time
import moveacquisition
import leginondata
import gui.wx.MoveXYAcquisition
import threading

debug = False

class MoveXYAcquisition(moveacquisition.MoveAcquisition):
	panelclass = gui.wx.MoveXYAcquisition.Panel
	settingsclass = leginondata.MoveXYAcquisitionSettingsData
	defaultsettings = dict(moveacquisition.MoveAcquisition.defaultsettings)
	defaultsettings.update({
		'move to': ((0.0,0.0),), # (x,y) um
	})
	eventinputs = moveacquisition.MoveAcquisition.eventinputs
	eventoutputs = moveacquisition.MoveAcquisition.eventoutputs

	def __init__(self, id, session, managerlocation, **kwargs):
		moveacquisition.MoveAcquisition.__init__(self, id, session, managerlocation, **kwargs)
		self.move_params = ('x','y')

	def getStageValue(self):
		position = self.instrument.tem.StagePosition
		value = (position['x'],position['y'])
		return value

	def setStageValue(self,value):
		'''
		Set stage position defined by the
		subclass.
		'''
		# Value is xy in meters n this case
		valuedict = {'x': value[0],'y':value[1]}
		return self._setStageValue(valuedict)

	def logFinal(self, value):
		self.logger.info('stage is moved to (x,y)=%5.1f,%5.1f um' % (value[0]*1e6,value[1]*1e6))

	def moveToSettingToValue(self,setting):
		'''
		convert xy setting in um to meters
		'''
		try:
			return setting[0]*1e-6,setting[1]*1e-6
		except (TypeError,IndexError) as e:
			raise ValueError('Settings %s not valid' % (setting,))
