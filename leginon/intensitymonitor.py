#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import data
import node
import EM
import gui.wx.IntensityMonitor
import camerafuncs
import imagefun
import time
import threading

class IntensityMonitor(node.Node):
	'''
	track changes in beam intensity and/or camera sensitivity
	'''
	panelclass = gui.wx.IntensityMonitor.Panel
	settingsclass = data.IntensityMonitorSettingsData
	defaultsettings = {
		'iterations': 10,
		'wait time':  60,
		'camera settings':  None,
	}
	eventinputs = node.Node.eventinputs + EM.EMClient.eventinputs
	eventoutputs = node.Node.eventoutputs + EM.EMClient.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)
		self.threadstop = threading.Event()
		self.start()

	def screenDown(self):
		# check if screen is down
		scope = data.ScopeEMData()
		scope['main screen position'] = 'down'
		self.emclient.setScope(scope)
		time.sleep(1)

	def screenUp(self):
		# check if screen is down
		scope = data.ScopeEMData()
		scope['main screen position'] = 'up'
		self.emclient.setScope(scope)
		time.sleep(1)

	def acquireData(self):
		## set camera
		self.cam.setCameraDict(self.settings['camera settings'])

		## file base name
		basename = self.session['name'] + '_' + str(int(time.time()))

		## screen down for dark image and screen current
		self.logger.info('   acquiring dark image and screen current')
		self.screenDown()
		darkim = self.cam.acquireCameraImageData(correction=False)
		darkim['filename'] = basename + '_d'
		darkim['label'] = 'dark'

		## screen up for bright image
		self.logger.info('   acquiring bright image')
		self.screenUp()
		brightim = self.cam.acquireCameraImageData(correction=False)
		brightim['filename'] = basename + '_b'
		brightim['label'] = 'bright'
		## no screen current measured because screen up, so get from dark
		screencurrent = darkim['scope']['screen current']
		brightim['scope']['screen current'] = screencurrent

		## store in DB
		self.logger.info('   publishing images: %s, %s' % (darkim['filename'],brightim['filename']))
		self.publish(darkim, database=True)
		self.publish(brightim, database=True)

		darkstats = self.publishStats(darkim)
		brightstats = self.publishStats(brightim)
		self.logger.info('   Dark: %s' % (darkstats,))
		self.logger.info('   Bright: %s' % (brightstats,))
		self.logger.info('   Screen Current: %s' % (screencurrent,))

	def publishStats(self, imagedata):
		im = imagedata['image']
		mn,mx = imagefun.minmax(im)
		mean = imagefun.mean(im)
		std = imagefun.stdev(im, mean)
		statsdata = data.CameraImageStatsData()
		statsdata['min'] = mn
		statsdata['max'] = mx
		statsdata['mean'] = mean
		statsdata['stdev'] = std
		statsdata['image'] = imagedata
		self.publish(statsdata, database=True)
		return 'min: %s, max: %s, mean: %s, stdev: %s' % (mn,mx,mean,std)

	def loop(self):
		n = self.settings['iterations']
		for i in range(n):
			self.logger.info('Iteration %s of %s' % (i+1, n))
			self.acquireData()

			if self.threadstop.isSet():
				self.logger.info('Loop breaking before all points done')
				break

			waittime = self.settings['wait time']
			self.logger.info('waiting for %s seconds...' % (waittime,))
			time.sleep(waittime)
		self.logger.info('loop done')
		self.panel.onLoopDone()

	def uiStartLoop(self):
		self.threadstop.clear()
		t = threading.Thread(target=self.loop).start()

	def uiStopLoop(self):
		self.threadstop.set()
