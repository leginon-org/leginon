#!/usr/bin/env python
import node
import data
import event
import Numeric
import math
import random
import Image
import time

class TestMosaic(node.Node):
	def __init__(self, id, nodelocations):
		node.Node.__init__(self, id, nodelocations)
		self.addEventOutput(event.PublishEvent)
		self.start()

	def main(self):
		import time
		time.sleep(3.0)
		self.makeTiles()

	def makeTiles(self):
		#testimage = Numeric.ones((64, 64))
		#for i in range(testimage.shape[0]):
		#	for j in range(testimage.shape[1]):
		#		testimage[i, j] = random.randrange(50, 1024)
		#print testimage

		im = Image.open('c:\\dev\\pyleginon\\test.jpg')
		testimage = Numeric.fromstring(im.tostring(), Numeric.UnsignedInt8)
		testimage.shape = im.size[1], im.size[0]
		#print testimage.shape

		ntiles = (3, 3)
		overlap = 0.9

		tilesize = (int(math.floor(testimage.shape[0]/(1 + (ntiles[0] - 1)
									* (1 - overlap)))),
								int(math.floor(testimage.shape[1]/(1 + (ntiles[1] - 1)
									* (1 - overlap)))))

		pixeloverlap = (int(tilesize[0]*overlap), int(tilesize[1]*overlap))
#		print 'tile size =', tilesize
#		print 'pixel overlap =', pixeloverlap
		idmatrix = []
		tileoffset = (0, 0)
		for i in range(ntiles[0]):
			idmatrix.append([])
			for j in range(ntiles[1]):
				#print 'i =', i, 'j =', j, 'tileoffset =', tileoffset
				tile = testimage[tileoffset[0]:tileoffset[0] + tilesize[0],
													tileoffset[1]:tileoffset[1] + tilesize[1]]
				if tile.shape != tilesize:
					return

				idmatrix[i].append(self.ID())
				neighbors = []
				for ni in range(i - 1, i + 2):
					if ni >= 0:
						for nj in range(j - 1, j + 2):
							if nj >= 0 and (ni != i or nj != j):
								try:
									neighbors.append(idmatrix[ni][nj])
								except IndexError:
									pass

				self.publish(data.ImageTileData(idmatrix[i][j], tile, neighbors))
				time.sleep(1.0)
				tileoffset = (tileoffset[0], tileoffset[1] + tilesize[1] - pixeloverlap[1])
			tileoffset = (tileoffset[0] + tilesize[0] - pixeloverlap[0], 0)

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)

		self.registerUISpec('Test Mosaic', (nodespec,))

