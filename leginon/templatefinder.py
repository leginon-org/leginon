#!/usr/bin/env python
import workflow
import commonsteps
from pyami.ordereddict import OrderedDict

input = commonsteps.ImageInput('input')
input.setParam('use file', True)
input.setParam('file name', 'sq_example.jpg')

template = commonsteps.ImageInput('template')
template.setParam('use file', True)
template.setParam('file name', 'holetempexample.jpg')

tempcor = commonsteps.TemplateCorrelator('correlation')
tempcor.setDependency('image', input)
tempcor.setDependency('template', template)

threshold = commonsteps.Threshold('threshold')
threshold.setDependency('image', tempcor)

blobs = commonsteps.BlobFinder('blobs')
blobs.setDependency('image', tempcor)
blobs.setDependency('mask', threshold)

blobsm = commonsteps.ImageMarker('blobsm')
blobsm.setDependency('image', input)
blobsm.setDependency('points', blobs)

latfilt = commonsteps.LatticeFilter('lattice')
latfilt.setDependency('input', blobs)

latm = commonsteps.ImageMarker('latm')
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

if __name__ == '__main__':
	test = workflow.WorkflowCLI(templatefinder)
	test.loop()
