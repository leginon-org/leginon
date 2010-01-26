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

import pyami.mrc
import numpy
import workflow

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

def paramToDBName(step, paramname):
	return ' '.join(step.name, paramname)


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
