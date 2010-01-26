#!/usr/bin/env python

import numpy

import workflow
import targetingsteps
from pyami.ordereddict import OrderedDict

########################################################
#### Define the steps of my targeting algorithm
########################################################

## This step takes input image and rotates it (n * 90) degrees
class RotN90(targetingsteps.ImageProducer):
	# user modified parameters
	param_def = [
		{'name': 'multiplier', 'type': int, 'default': 1},
	]

	# The _run method defines what we actually want to do.
	def _run(self):
		# get dependencies
		image = self.depresults['image']

		# get parameters
		n = self.params['multiplier']

		# rotate image
		result = numpy.rot90(image, n)
	
		return result

## This step just finds the maximum pixel in an image.
class MaximumPixel(targetingsteps.PointProducer):
	# We could define parameters here in the future...

	# The _run method defines what we actually want to do.
	def _run(self):
		# get dependencies
		image = self.depresults['image']

		# get parameters
		# (none defined for this class)

		# find the maximum pixel row and column
		index = image.argmax()
		row = index / image.shape[0]
		column = index - row * image.shape[0]

		# The final result for a PointProducer is a list of dictionaries.
		result = []
		result.append({'row': row, 'column': column})

		return result

## This step takes an input list of points and generates another one shifted.
class Shifter(targetingsteps.PointProducer):
	param_def = [
		{'name': 'rows', 'type': int, 'default': 10},
		{'name': 'columns', 'type': int, 'default': 10},
	]

	def _run(self):
		# get dependencies
		points = self.depresults['points']

		# get parameters
		rows = self.params['rows']
		columns = self.params['columns']

		## generate new points shifted by rows, columns
		results = []
		for point in points:
			newrow = point['row'] + rows
			newcolumn = point['column'] + columns
			newpoint = {'row': newrow, 'column': newcolumn}
			results.append(newpoint)

		return results

##############################################################
###  Create instances of those classes and build my workflow.
###  Also using the class InputImage from targetingsteps.py
##############################################################

## The complete workflow will contain 4 steps.  I create the instances and
## give them each a unique name.
input = targetingsteps.ImageInput('input')
rotate = RotN90('rotate')
maximum = MaximumPixel('maximum')
shift = Shifter('shift')

## connect them together properly:
rotate.setDependency('image', input)
maximum.setDependency('image', rotate)
shift.setDependency('points', maximum)

## Group them together into a container.  Use our OrderedDict class:
myworkflow = OrderedDict()
myworkflow['input'] = input
myworkflow['rotate'] = rotate
myworkflow['maximum'] = maximum
myworkflow['shift'] = shift

## Now we have a complete workflow.  We can plug it into Leginon (not yet)
## Or we can test it using our command line interface...
test = workflow.WorkflowCLI(myworkflow)
test.loop()
