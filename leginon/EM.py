#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import instrument
import node
import socket
import threading
import gui.wx.Instrument
from pyScope import tem, ccdcamera, registry, methoddict
import pythoncom

class EM(node.Node):
	panelclass = gui.wx.Instrument.Panel
	def __init__(self, name, session, managerlocation, tcpport=None, **kwargs):

		self.instruments = []

		self.pauses = {
			'magnification':  1.5,
			'spot size': 0.4,
			'image shift': 0.2,
			'beam shift': 0.1,
			'defocus': 0.4,
			'focus': 0.4,
			'intensity': 0.1,
			'main screen position': 1.0,
		}

		node.Node.__init__(self, name, session, managerlocation, **kwargs)

		# the handler thread waits for queue requests and processes them
		# scope and camera are typically COM objects and need to be initialized
		# in this thread
		self.exitevent = threading.Event()
		self.handlerthread = threading.Thread(name='EM handler thread',
																					target=self.handler)
		self.handlerthread.start()
		#self.handler()

	def refresh(self):
		pass

	def exit(self):
		node.Node.exit(self)
		for i in self.instruments:
			try:
				i.exit()
			except:
				pass
		self.exitevent.set()

	def handler(self):
		classes = registry.getClasses()
		tems = []
		ccdcameras = []
		fastccdcameras = []
		for i in classes:
			name, c = i
			if issubclass(c, tem.TEM):
				tems.append(i)
			elif issubclass(c, ccdcamera.FastCCDCamera):
				fastccdcameras.append(i)
			elif issubclass(c, ccdcamera.CCDCamera):
				ccdcameras.append(i)
		for name, c in tems + ccdcameras + fastccdcameras:
			if issubclass(c, tem.TEM):
				instrumentclass = instrument.TEM
			elif issubclass(c, ccdcamera.FastCCDCamera):
				instrumentclass = instrument.FastCCDCamera
			elif issubclass(c, ccdcamera.CCDCamera):
				instrumentclass = instrument.CCDCamera
			class ObjectClass(c, instrumentclass):
				def __init__(self):
					self._hostname = socket.gethostname().lower()
					c.__init__(self)
					instrumentclass.__init__(self)

				def getHostname(self):
					return self._hostname

			try:
				instance = ObjectClass()
				self.instruments.append(instance)
				self.objectservice._addObject(name, instance)
				self.logger.info('Added interface for %s' % name)
			except Exception, e:
				self.logger.debug('Initialization of %s failed: %s' % (name, e))
		if not self.instruments:
			self.logger.warning('No interfaces could be initiailized')

		self.start()

		# exiting this thread seems to disconnect the COM servers
		self.exitevent.wait()

