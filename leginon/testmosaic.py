#!/usr/bin/env python
import node
import data
import event
import Numeric
import math
import random
import Image
import time
import math
import sys
import Mrc

class TestMosaic(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		node.Node.__init__(self, id, nodelocations, **kwargs)
		self.addEventOutput(event.TileImagePublishEvent)
		self.start()

	def main(self):
		import time
		time.sleep(3.0)
		self.makeTiles()

	def makeTiles(self):
		path = 'mosaic\\'
		fp = open(path + '02jun18a.pre.gonpos')
		filelines = fp.readlines()
		fp.close

		neighbors = []
		for line in filelines[:16]:
			fields = line.split()
			filename = fields[0]
			x = float(fields[1])
			y = float(fields[2])

			print 'reading', filename
			tile = Mrc.mrc_to_numeric(path + filename)
			print 'type =', tile.typecode()
#			tile = source.astype(Numeric.Float32)

			time.sleep(1.0)
			print 'publishing'
			newid = self.ID()
			self.publish(data.TileImageData(newid, tile,
						{'stage position': {'x': x, 'y': y}}, None, neighbors),
																				event.TileImagePublishEvent)
			neighbors = [newid]

#	def defineUserInterface(self):
#		nodespec = node.Node.defineUserInterface(self)
#
#		self.registerUISpec('Test Mosaic', (nodespec,))

