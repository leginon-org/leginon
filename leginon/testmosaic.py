#!/usr/bin/env python
import acquisitionmosaic
import Numeric
import Mrc

def makeTiles():
	mosaic = acquisitionmosaic.Mosaic()

	tiles = [Mrc.mrc_to_numeric('test2.mrc'), Mrc.mrc_to_numeric('test2.mrc')]
	neighbors = []
	for tile in tiles:
		mosaic.addTile(tile, neighbors)
		neighbors = mosaic.tiles
	for i in mosaic.tiles:
		print i, i.position, i.image.shape
	print mosaic.getNearestTile(0, 500)

makeTiles()
