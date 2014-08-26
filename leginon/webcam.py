#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import node
import uidata
import VideoCapture
from PIL import Image
import time
import threading

class Webcam(node.Node):
	def __init__(self, id, session, managerlocation, **kwargs):
		node.Node.__init__(self, id, session, managerlocation, **kwargs)
		self.webcam = VideoCapture.Device()
		self.stop = False
		self.defineUserInterface()
		self.start()

	def exit(self):
		del self.webcam
		node.Node.exit(self)

	def uiAcquire(self):
		if self.continuous.get():
			acquirethread = threading.Thread(target=self.continuousAcquire)
			acquirethread.setDaemon(1)
			acquirethread.start()
		else:
			self.uiwebcamimage.set(self.webcam.getImage())

	def continuousAcquire(self):
		self.stop = False
		self.acquiremethod.disable()
		self.stopmethod.enable()
		while not self.stop:
			self.uiwebcamimage.set(self.webcam.getImage())
			time.sleep(0.04)
		self.stopmethod.disable()
		self.acquiremethod.enable()

	def uiStop(self):
		self.stop = True

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)

		self.continuous = uidata.Boolean('Continuous', False, 'rw')
		self.acquiremethod = uidata.Method('Acquire', self.uiAcquire)
		self.stopmethod = uidata.Method('Stop', self.uiStop)

		self.uiwebcamimage = uidata.PILImage('Image', None)
		container = uidata.LargeContainer('Webcam')
		container.addObjects((self.uiwebcamimage, self.continuous,
													self.acquiremethod, self.stopmethod))
		self.uicontainer.addObject(container)
		self.stopmethod.disable()

if __name__ == '__main__':
	import sys
	sys.coinit_flags = 0
	import pythoncom
	import MrcImagePlugin
	import cStringIO
	webcam = VideoCapture.Device()
	image = webcam.getImage()
	stream = cStringIO.StringIO()
	image.save(stream, 'jpeg')
	buffer = stream.getvalue()
	stream.close()
	bar = Image.open(cStringIO.StringIO(buffer))
	bar.show()
