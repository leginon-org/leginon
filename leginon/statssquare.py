#!/usr/bin/env python
"""
classes and functions for loaded blob class used in mosaicscorefinder and its
subclasses.
"""
class StatsBlob(object):
	def __init__(self, info_dict, index):
		'''Simple blob object with image and stats as attribute
			both input and output center/vertices = (row, col) on mosaic tile image
		'''
		mean = info_dict['brightness']
		stddev = 1.0
		size = info_dict['area']
		score = info_dict['score']
		center = info_dict['center'][0],info_dict['center'][1]
		vertices = info_dict['vertices']
		self.center_modified = False
		# n in blob is the same as size from Ptolemy. Need n for displaying stats
		# in gui.
		self.stats = {"label_index": index, "center":center, "n":size, "size":size, "mean":mean, "score":score}
		self.vertices = vertices
		self.info_dict = info_dict
		# imagedata of the tile if available
		self.tile_image = info_dict['tile_image']
		self.squares = []
		# pass on squares if already there
		# list of PtolemySquareData.dbids in the potentially merged blobs
		if 'squares' in info_dict:
			self.squares = info_dict['squares']
