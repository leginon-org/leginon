
import nodenet, event

class ImageStats(nodenet.Node):
	"""
	ImageStats handles an ImagePublished event
	"""
	def __init__(self, manageraddress = None):
		nodenet.Node.__init__(self, manageraddress)

	def init_events(self):
		self.events = event.NodeEvents()
		self.events.addInput(event.ImagePublished, self.handleImagePublished)
		self.events.addInput(event.YourEvent, self.handleYourEvent)
		self.events.addOutput(event.MyEvent)
		self.events.addOutput(event.YourEvent)

	def handleImagePublished(self, eventinst):
		dataid = eventinst.dataid
		imagedata = self.research(dataid)
		## do something with image
