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

class ImageProducer(workflow.Step):
	'''_run method must return image (numpy array)'''
	pass

class PointProducer(workflow.Step):
	'''_run method must return list of dicts [{'row': ###, 'column': ###}, ...]'''
	pass

class ImageInput(ImageProducer):
	'''reads a file using either mrc or numpil modules'''
	def __init__(*args, **kwargs):
		self.setDependency('assigned', 'assigned')

	def _run(self):
		if self.params['read file']:
			fname = self.params['filename']
			if fname[-3:].lower() == 'mrc':
				image = pyami.mrc.read(fname)
			else:
				image = pyami.numpil.read(fname)
			return image
		else:
			return self.external

class TemplateCorrelator(ImageProducer):
	'''depends on 'image' and 'template' and correlates them.'''
	def _run(self):
		# get deps
		image = self.depresults['image']
		template = self.depresults['template']

		# get params
		cortype = self.params['cortype']
		corfilt = self.params['corfilt']

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
		if corfilt is not None:
			cor = scipy.ndimage.gaussian_filter(cor, corfilt)
		return cor

class Threshold(ImageProducer):
	def _run(self):
		# get dependencies
		image = self.depresults['image']

		# get params
		method = self.params['method']
		threshold = self.params['threshold']

		if method == "Threshold = mean + A * stdev":
			mean = pyami.arraystats.mean(image)
			std = pyami.arraystats.std(image)
			thresh = mean + threshold * std
		elif method == "Threshold = A":
			thresh = threshold
		result = pyami.imagefun.threshold(image, thresh)

		return result

class BlobFinder(PointProducer):
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
		maxsize = self.params['maxblobsize']
		minsize = self.params['minblobsize']
		maxblobs = self.params['maxblobs']

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

def debugImage(step, image):
		filename = step.name + '.mrc'
		pyami.mrc.write(image.astype(numpy.float32), filename)
		print 'saved', filename

def debugPoints(step, points):
		print 'Result of', step.name
		print [(point['row'],point['column']) for point in points]

class TemplateFinderWorkflow(object):
	# (step_name, param_name):  setting_name
	param_setting = {
		('input','filename'): 'image filename',
		('template','filename'): 'template filename',
		('template','template size'): 'template diameter',
		('template','image size'): 'file diameter',
		('template','cortype'): 'template type',
		('template','lpf'): ('template lpf','sigma'),
		('threshold','threshold'): 'threshold',
		('threshold','method'): 'threshold method',
		('blobs','border'): 'blobs border',
		('blobs','max'): 'blobs max',
		('blobs','maxsize'): 'blobs max size',
		('blobs','minsize'): 'blobs min size',
		('lattice','spacing'): 'lattice spacing',
		('lattice','tolerance'): 'lattice tolerance',
	}
	setting_param = [(value,key) for key,value in param_setting.items()]
	setting_param = dict(setting_param)

'''
		'ice min mean': 0.05,
		'ice max mean': 0.2,
		'ice max std': 0.2,
		'focus hole': 'Off',
		'target template': False,
		'focus template': [(0, 0)],
		'acquisition template': [(0, 0)],
		'focus template thickness': False,
		'focus stats radius': 10,
		'focus min mean thickness': 0.05,
		'focus max mean thickness': 0.5,
		'focus max stdev thickness': 0.5,
'''

	def __init__(self):
		self.steps = {}

		self.steps['input'] = targetingprocess.ImageReader('input')
		self.steps['template'] = targetingprocess.ImageReader('template')

		self.steps['correlation'] = targetingprocess.TemplateCorrelator('template')
		self.steps['correlation'].setDependency('image', self.steps['input'])
		self.steps['correlation'].setDependency('template', self.steps['template'])

		self.steps['threshold'] = targetingprocess.Threshold('threshold')
		self.steps['threshold'].setDependency('image', self.steps['correlation'])

		self.steps['blobs'] = targetingprocess.BlobFinder('blobs')
		self.steps['blobs'].setDependency('image', self.steps['correlation'])
		self.steps['blobs'].setDependency('mask', self.steps['threshold'])

		self.steps['lattice'] = targetingprocess.LatticeFilter('lattice')
		self.steps['lattice'].setDependency('input', self.steps['blobs'])

	def configure(leg_settings):
		for setting_name, value in settings.items():
			if isinstance(value, dict):
				for dsetting_name, dvalue in value.items():
					stepname, paramname = setting_param[(setting_name,dsetting_name)]
					self.steps[stepname].setParam(paramname, dvalue)
			else:
				stepname, paramname = setting_param[setting_name]
				self.steps[stepname].setParam(paramname, value)
