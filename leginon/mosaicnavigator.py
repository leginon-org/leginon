import navigator
import data
import event
import math
import node
import time

class MosaicNavigator(navigator.Navigator):
	def __init__(self, id, session, nodelocations, **kwargs):
		self.statemosaic = {}
		navigator.Navigator.__init__(self, id, session, nodelocations, **kwargs)
		self.addEventInput(event.StateMosaicPublishEvent, self.addStateMosaic)
		self.defineUserInterface()
		self.start()

	def addStateMosaic(self, ievent):
		idata = self.researchByDataID(ievent['dataid'])
		self.statemosaic.update(idata)

	def handleImageClick(self, clickevent):
		imagedataid = clickevent['image id']
		try:
			mosaicdata = self.statemosaic[imagedataid]
		except KeyError:
			self.printerror('unknown data ID for navigation, %s' % str(imagedataid))
			return

		row = clickevent['array row']
		column = clickevent['array column']
		shape = clickevent['array shape']

		# certainly not optimal
		maxmagnitude = math.sqrt(shape[0]**2 + shape[1]**2)
		nearestdelta = (0,0)
		nearesttile = None
		for tile in mosaicdata['tile states']:
			position = mosaicdata['tile states'][tile]['position']
			offset = mosaicdata['tile states'][tile]['offset']
			offsetposition = (position[0] + offset[0], position[1] + offset[1])
			shape = mosaicdata['tile states'][tile]['shape']
			deltaposition = (-(row - offsetposition[0] - shape[0]/2),
												-(column - offsetposition[1] - shape[1]/2))
			magnitude = math.sqrt((deltaposition[0])**2 + (deltaposition[1])**2)
			if magnitude < maxmagnitude:
				maxmagnitude = magnitude
				nearestdelta = deltaposition
				nearesttile = tile

		movetype = self.movetype.get()
		calclient = self.calclients[movetype]
		newstate = calclient.transform(
											{'row': nearestdelta[0]*mosaicdata['scale'],
												'col': nearestdelta[1]*mosaicdata['scale']},
															mosaicdata['tile states'][nearesttile]['scope'],
															mosaicdata['tile states'][nearesttile]['camera'])
		#emdata = data.EMData('scope', newstate)
		emdata = data.EMData('scope', em=newstate)
		self.publishRemote(emdata)

		time.sleep(self.delaydata.get())

		# hmm?
#		self.acquireImage()

