#!/usr/bin/env python
from leginon import leginondata

class ImageHandler(object):
	'''
	nodes should inherit this if they want to work with different versions fo images
	'''
	############# DATABASE INTERACTION #################
	def researchImages(self, **kwargs):
		'''
		Returns images in order of list and versions
		'''
		imagequery = leginondata.AcquisitionImageData(**kwargs)
		images = imagequery.query()
		# organize by list, version
		organized = {}
		for image in images:
			if image['list'] is None:
				imagelist = None
			else:
				imagelist = image['list'].dbid
			if imagelist not in organized:
				organized[imagelist] = {}

			target = image['target']
			version = image['version']

			organized[imagelist][version] = image

		final = []
		tls = organized.keys()
		tls.sort()
		for imagelist in tls:
			versions = organized[imagelist].keys()
			versions.sort()
			for version in versions:
				final.append(organized[imagelist][version])
		return final

