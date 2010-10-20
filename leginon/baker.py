import node
import event
import leginondata
import time
import calibrationclient
from pyami import correlator, peakfinder, imagefun, ordereddict
import math
import gui.wx.Baker
import instrument
import presets
import types
import numpy
import leginondata
import threading
import player

class Baker(node.Node):
	panelclass = gui.wx.Baker.Panel
	settingsclass = leginondata.BakerSettingsData
	defaultsettings = {
		'bypass': False,
		'preset': '',
		'total bake time': 10.0,
		'manual aperture': True,
		'emission off': False,
	}
	eventinputs = node.Node.eventinputs + presets.PresetsClient.eventinputs + [event.MakeTargetListEvent,]
	eventoutputs = node.Node.eventoutputs + presets.PresetsClient.eventoutputs + [event.MakeTargetListEvent,]

	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.instrument = instrument.Proxy(self.objectservice, self.session,
																				self.panel)
		self.presetsclient = presets.PresetsClient(self)
		self.player = player.Player(callback=self.onPlayer)
		self.panel.playerEvent(self.player.state())
		self.lock = threading.RLock()
		self.addEventInput(event.MakeTargetListEvent, self.onProcessing)
		self.userpause = threading.Event()

		self.endlocation = None
		self.start()

	def checkDistance(self):
		if self.endlocation is None:
			self.logger.error('No end stage position saved')
			return False
		else:
			endx = self.endlocation['x']
			endy = self.endlocation['y']
		startstage = self.instrument.tem.StagePosition
		startx = startstage['x']
		starty = startstage['y']
		distance = math.hypot((startx-endx),(starty-endy))
		if distance < 2e-6:
			self.logger.error('Stage is at the end position')
			self.player.stop()
			return False
		self.player.play()
		return True

	def timedMoveToPosition(self):
		endx = self.endlocation['x']
		endy = self.endlocation['y']
		startstage = self.instrument.tem.StagePosition
		startx = startstage['x']
		starty = startstage['y']
		distance = math.hypot((startx-endx),(starty-endy))
		if distance < 2e-6:
			self.logger.error('Stage is at the end position')
			return
		n = 20
		locations = [(startx,starty)]
		step = (endx-startx)/(n-1), (endy-starty)/(n-1)
		steptime = self.settings['total bake time'] / n
		status = True
		for i in range(1,n):
			locations.append((locations[i-1][0]+step[0],locations[i-1][1]+step[1]))
		for i in range(n):
			start_time = time.time()
			state = self.player.wait()
			if state == 'stop':
				status = False
				break
			status = self.toScope({'x':locations[i][0],'y':locations[i][1]})
			if not status:
				break
			remaining_time = steptime - (time.time() - start_time)
			if remaining_time > 0:
				time.sleep(remaining_time)
			end_time = time.time()
		return status

	def fromScope(self):
		errstr = 'Location from instrument failed: %s'
		try:
			allstagedata = self.instrument.tem.StagePosition
		except:
			self.logger.error(errstr % 'unable to get stage position')
			return False
		stagedata = {}
		stagedata['x'] = allstagedata['x']
		stagedata['y'] = allstagedata['y']
		stagedata['z'] = allstagedata['z']
		stagedata['a'] = allstagedata['a']

		self.endlocation = stagedata
		self.logger.info('Save end location at %.1f,%.1f um (x,y)' % (stagedata['x']*1e6,stagedata['y']*1e6))
		return True

	def toScope(self, stagedict):
		try:
			self.instrument.tem.StagePosition = stagedict
		except:
			self.logger.exception(errstr % 'unable to set instrument')
			return False
		else:
			self.logger.info('Moved to location in um (x,y): %.1f,%.1f' % (stagedict['x']*1e6,stagedict['y']*1e6))
			return True

	def onPlayer(self, state):
		infostr = ''
		if state == 'stop':
			infostr += 'Aborting...'
		if infostr:
			self.logger.info(infostr)

	def resetTiltStage(self):
		zerostage = {'a':0.0}
		self.instrument.tem.setStagePosition(zerostage)
		zerostage = {'x':0.0,'y':0.0}
		self.instrument.tem.setStagePosition(zerostage)
		stageposition = self.instrument.tem.getStagePosition()
		self.logger.info('return x,y, and alhpa tilt to %.1f um,%.1f um,%.1f deg' % (stageposition['x']*1e6,stageposition['y'],stageposition['a']))

	def shutDown(self):
		self.instrument.tem.ColumnValvePosition = 'closed'
		self.logger.warning('column valves closed')
		if self.settings['emission off']:
			self.instrument.tem.Emission = False
			self.logger.warning('emission switched off')

	def startUp(self):
		if self.instrument.tem.ColumnValvePosition != 'open':
			self.logger.info('Open column valves...')
			self.instrument.tem.ColumnValvePosition = 'open'
			time.sleep(2.5)
		if self.instrument.tem.MainScreenPosition != 'down':
			self.logger.info('Screen down for baking...')
			self.instrument.tem.MainScreenPosition = 'down'
			time.sleep(2.5)

	def startNext(self):
		if self.instrument.tem.ColumnValvePosition != 'open':
			self.logger.info('Open column valves...')
			self.instrument.tem.ColumnValvePosition = 'open'
			time.sleep(2.5)
		# This uses self.instrument.ccdcamera of the baking preset.
		# It should use that of the next node
		if self.instrument.ccdcamera.hasAttribute('Inserted'):
			try:
				inserted = self.instrument.ccdcamera.Inserted
			except:
				inserted = True
			if not inserted:
				self.logger.info('inserting camera')
				self.instrument.ccdcamera.Inserted = True
				time.sleep(2.5)
		if self.instrument.tem.MainScreenPosition != 'up':
			self.logger.info('Screen up for data collection...')
			self.instrument.tem.MainScreenPosition = 'up'
			time.sleep(2.5)

	def runAll(self):
		self.setStatus('processing')
		status = self.checkDistance()
		if status is True:
			self.setStatus('processing')
			self.startUp()
			preset_name = self.settings['preset']
			self.setStatus('waiting')
			self.logger.info('Sending %s preset for baking' % (preset_name,))
			self.presetsclient.toScope(preset_name)
			self.setStatus('processing')
			status = self.timedMoveToPosition()
		if not status:
			self.logger.info('Aborted')
		else:
			self.logger.info('Baking is done')
		self.panel.onDone()
		self.setStatus('idle')
		return status

	def onPlay(self):
				self.userpause.set()

	def waitForUserCheck(self, task=''):
			self.setStatus('user input')
			self.logger.info('Waiting for user to %s...' % (task,))
			self.userpause.clear()
			self.userpause.wait()
			self.setStatus('processing')

	def outputMakeTargetListEvent(self,griddata):
		evt = event.MakeTargetListEvent()
		evt['grid'] = griddata
		if evt['grid'] is None:
			self.logger.error('Data collection event not sent')
		else:
			self.outputEvent(evt)
			self.logger.info('Data collection initiated')
		return evt['grid']

	def onProcessing(self,evt):
		if not self.settings['bypass']:
			self.waitForUserCheck('save end location')
			status = False
			while not status:
				status = self.runAll()
				self.resetTiltStage()
				if not status:
					self.waitForUserCheck('correct error')
			if self.settings['manual aperture']:
				self.shutDown()
				self.waitForUserCheck('change aperture')
		self.startNext()
		self.outputMakeTargetListEvent(evt['grid'])
		self.panel.onDone()
		self.setStatus('idle')

if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
