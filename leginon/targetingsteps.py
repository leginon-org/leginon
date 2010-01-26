#!/usr/bin/env python
'''
A targeting process is composed of several steps that are connected in a
pipeline.  A given step cannot be run until its dependency steps have been
run.

There are two standard processing step base classes:

ImageProducer - result is an image represented as a 2-d numpy array

PointProducer - result is a list of points, each point is a dictionary
  containing at least keys 'row' and 'column', but may contain any other
  info about the point.
'''

import pyami.arraystats
import pyami.imagefun
import pyami.mrc
import pyami.numpil
import pyami.correlator
import numpy
import scipy.ndimage
import itertools
import lattice
import workflow
from pyami.ordereddict import OrderedDict

def debugImage(step, image):
		filename = step.name + '.mrc'
		pyami.mrc.write(image.astype(numpy.float32), filename)
		print 'saved', filename

def debugPoints(step, points):
		print 'Result of', step.name
		print [(point['row'],point['column']) for point in points]

class ImageProducer(workflow.Step):
	'''_run method must return image (numpy array)'''
	param_def = []
	# override to use debug callback by default
	def __init__(self, name, result_callback=debugImage):
		workflow.Step.__init__(self, name, result_callback)

class PointProducer(workflow.Step):
	'''_run method must return list of dicts [{'row': ###, 'column': ###}, ...]'''
	param_def = []
	# override to use debug callback by default
	def __init__(self, name, result_callback=debugPoints):
		workflow.Step.__init__(self, name, result_callback)

class ImageInput(ImageProducer):
	'''result is an image, either from a file or from external dependency'''
	param_def = ImageProducer.param_def + [
		{'name': 'use file', 'type': bool, 'default': False},
		{'name': 'file name', 'type': str, 'default': 'sq_example.jpg'},
	]

	def __init__(self, *args, **kwargs):
		ImageProducer.__init__(self, *args, **kwargs)
		self.setDependency('external', None)

	def _run(self):
		if self.params['use file']:
			fname = self.params['file name']
			if fname[-3:].lower() == 'mrc':
				image = pyami.mrc.read(fname)
			else:
				image = pyami.numpil.read(fname)
		else:
			image = self.depresults['external']
		return image

class TemplateCorrelator(ImageProducer):
	'''depends on 'image' and 'template' and correlates them.'''

	param_def = ImageProducer.param_def + [
		{'name': 'correlation type', 'type': str, 'choices': ['cross','phase'], 'default': 'cross'},
		{'name': 'filter sigma', 'type': float, 'default': 1.0},
	]

	def _run(self):
		# get deps
		image = self.depresults['image']
		template = self.depresults['template']

		# get params
		cortype = self.params['correlation type']
		corfilt = self.params['filter sigma']

		# pad template to image shape and shift center to 0,0
		#newtemplate = numpy.zeros(image.shape, template.dtype)
		mean = pyami.arraystats.mean(template)
		newtemplate = mean * numpy.ones(image.shape, template.dtype)
		newtemplate[:template.shape[0], :template.shape[1]] = template
		shift = -template.shape[0] / 2.0 + 0.5, -template.shape[1] / 2.0 + 0.5
		newtemplate = scipy.ndimage.shift(newtemplate, shift, mode='wrap', order=1)
		pyami.mrc.write(newtemplate, 'newtemplate.mrc')

		if cortype == 'cross':
			cor = pyami.correlator.cross_correlate(image, newtemplate)
		elif cortype == 'phase':
			cor = pyami.correlator.phase_correlate(image, newtemplate, zero=False)
		if corfilt:
			cor = scipy.ndimage.gaussian_filter(cor, corfilt)
		return cor

class Threshold(ImageProducer):

	param_def = ImageProducer.param_def + [
		{'name': 'method', 'type': str, 'choices': ['mean + A * stdev', 'A'], 'default': 'mean + A * stdev'},
		{'name': 'value', 'type': float, 'default': 3.0},
	]

	def _run(self):
		# get dependencies
		image = self.depresults['image']

		# get params
		method = self.params['method']
		threshold = self.params['value']

		if method == 'mean + A * stdev':
			mean = pyami.arraystats.mean(image)
			std = pyami.arraystats.std(image)
			thresh = mean + threshold * std
		elif method == 'A':
			thresh = threshold
		result = pyami.imagefun.threshold(image, thresh)

		return result

class BlobFinder(PointProducer):
	param_def = PointProducer.param_def + [
		{'name': 'border', 'type': int, 'default': 20},
		{'name': 'max blob size', 'type': int, 'default': 5000},
		{'name': 'min blob size', 'type': int, 'default': 10},
		{'name': 'max blobs', 'type': int, 'default': 500},
	]

	def blobStatsTargets(self, blobs):
		targets = []
		for blob in blobs:
			target = {}
			target['x'] = blob.stats['center'][1]
			target['y'] = blob.stats['center'][0]
			target['stats'] = ordereddict.OrderedDict()
			target['stats']['Size'] = blob.stats['n']
			target['stats']['Mean'] = blob.stats['mean']
			target['stats']['Std. Dev.'] = blob.stats['stddev']
			targets.append(target)
		return targets

	def _run(self):
		# get dependencies
		image = self.depresults['image']
		mask = self.depresults['mask']

		# get parameters
		border = self.params['border']
		maxsize = self.params['max blob size']
		minsize = self.params['min blob size']
		maxblobs = self.params['max blobs']

		blobs = pyami.imagefun.find_blobs(image, mask, border, maxblobs, maxsize, minsize)
		results = []
		for blob in blobs:
			result = {}
			stats = blob.stats
			result['row'] = stats['center'][0]
			result['column'] = stats['center'][1]
			results.append(result)
		return results

class LatticeFilter(PointProducer):

	param_def = PointProducer.param_def + [
		{'name': 'tolerance', 'type': float, 'default': 0.1},
		{'name': 'spacing', 'type': float, 'default': 74},
	]

	def _run(self):
		# get deps
		points = self.depresults['input']

		# get params
		tolerance = self.params['tolerance']
		spacing = self.params['spacing']

		# make make list of blob coords:
		testpoints = []
		for point in points:
			testpoint = point['row'], point['column']
			testpoints.append(testpoint)

		best_lattice = lattice.pointsToLattice(testpoints, spacing, tolerance)

		if best_lattice is None:
			best_lattice = []
			holes = []
		else:
			best_lattice = best_lattice.points

		latpoints = [{'row': point[0], 'column': point[1]} for point in best_lattice]

		return latpoints

class ImageMarker(ImageProducer):

	param_def = PointProducer.param_def + [
		{'name': 'size', 'type': float, 'default': 5},
	]

	def _run(self):
		# get deps
		image = self.depresults['image']
		points = self.depresults['points']

		# get params
		size = self.params['size']

		newimage = numpy.array(image)
		mn = pyami.arraystats.min(image)
		mx = pyami.arraystats.max(image)
		for point in points:
			row,col = int(round(point['row'])), int(round(point['column']))
			for r in range(row-size,row+size):
				if 0 <= r < image.shape[0] and 0 <= col < image.shape[1]:
					newimage[r,col] = mn
			for c in range(col-size,col+size):
				if 0 <= c < image.shape[1] and 0 <= row < image.shape[0]:
					newimage[row,c] = mx

		return newimage


def paramToDBName(step, paramname):
	return ' '.join(step.name, paramname)

input = ImageInput('input')
input.setParam('use file', True)
input.setParam('file name', 'sq_example.jpg')

template = ImageInput('template')
template.setParam('use file', True)
template.setParam('file name', 'holetempexample.jpg')

tempcor = TemplateCorrelator('correlation', result_callback=debugImage)
tempcor.setDependency('image', input)
tempcor.setDependency('template', template)

threshold = Threshold('threshold', result_callback=debugImage)
threshold.setDependency('image', tempcor)

blobs = BlobFinder('blobs', result_callback=debugPoints)
blobs.setDependency('image', tempcor)
blobs.setDependency('mask', threshold)

blobsm = ImageMarker('blobsm', result_callback=debugImage)
blobsm.setDependency('image', input)
blobsm.setDependency('points', blobs)

latfilt = LatticeFilter('lattice', result_callback=debugPoints)
latfilt.setDependency('input', blobs)

latm = ImageMarker('latm', result_callback=debugImage)
latm.setDependency('image', input)
latm.setDependency('points', latfilt)

# first a list of steps
templatefinder = [
	input,
	template,
	tempcor,
	threshold,
	blobs,
	blobsm,
	latfilt,
	latm,
]

# then an ordered dict
templatefinder = OrderedDict([(step.name, step) for step in templatefinder])

def combinedParamName(step, param):
	return step.name + ' ' + param['name']

import leginondata
def makeSettingsClass(clsname, steps):
	newtypemap = []
	for step in steps.values():
		for param in step.param_def:
			fieldname = combinedParamName(step, param)
			newtypemap.append((fieldname, param['type']))
	newtypemap = tuple(newtypemap)
	class NewSettings(leginondata.SettingsData):
		@classmethod
		def typemap(cls):
			return leginondata.SettingsData.typemap() + newtypemap
	NewSettings.__name__ = clsname
	NewSettings.__module__ = 'leginondata'
	setattr(leginondata, clsname, NewSettings)
	return NewSettings

def makeDefaultSettings(steps):
	defaults = {}
	for step in steps.values():
		for param in step.param_def:
			fieldname = combinedParamName(step, param)
			defaultvalue = param['default']
			defaults[fieldname] = defaultvalue
	return defaults

if __name__ == '__main__':
	tf = workflow.WorkflowCLI(templatefinder)
	tf.loop()
