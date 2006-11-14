# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
 
import data
import dbdatakeeper

db=dbdatakeeper.DBDataKeeper(db='dbparticledata')

class crud(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('runId', run),
			('imageId', image),
			('x', int),
			('y', int),
		)
	typemap = classmethod(typemap)
data.crud=crud

class image(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|AcquisitionImageData|image', int),
			('dbemdata|SessionData|session', int),
			('dbemdata|PresetData|preset', int),
		)
	typemap = classmethod(typemap)
data.image=image

class particle(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('runId', run),
			('imageId', image),
			('selectionId', selectionParams),
			('xcoord', int),
			('ycoord', int),
			('correlation', float),
			('insidecrud', int),
		)
	typemap = classmethod(typemap)
data.particle=particle

class run(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session', int),
			('name', str), 
		)
	typemap = classmethod(typemap)
data.run=run

class selectionParams(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('runId', run),
			('diam', int),
			('bin', int),
			('manual_thresh', float),
			('auto_thresh', int),
			('lp_filt', int),
			('hp_filt', int),
			('crud_diameter', int),
			('crud_blur', float),
			('crud_low', float),
			('crud_high', float),
			('crud_std', float),
		)
	typemap = classmethod(typemap)
data.selectionParams=selectionParams

class shift(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|AcquisitionImageData|image1', int),
			('dbemdata|AcquisitionImageData|image2', int),
			('shiftx', float),
			('shifty', float),
			('correlation', float),
			('scale', float),
		)
	typemap = classmethod(typemap)
data.shift=shift

class templateImage(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('project|projects|projectId', int),
			('templatepath', str),
			('apix', float),
			('description', str),
		)
	typemap = classmethod(typemap)
data.templateImage=templateImage

class templateRun(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('templateId', templateImage),
			('runId', run),
			('range_start', int),
			('range_end', int),
			('range_incr', int),
		)
	typemap = classmethod(typemap)
data.templateRun=templateRun

class stackParams(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('stackPath', str),
			('name' , str),
			('description', str),
			('boxSize', int),
			('phaseFlipped', bool),
			('aceCutoff', float),
			('selexonCutoff', float),
			('checkCrud', bool),
			('checkImage', bool),
			('minDefocus', float),
			('maxDefocus', float),
			('fileType', str),
			('inverted', bool),
		)
	typemap = classmethod(typemap)
data.stackParams=stackParams

class stackParticles(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('particleNumber', int),
			('stackId', stackParams),
			('particleId', particle),
	        )
	typemap = classmethod(typemap)
data.stackParticles = stackParticles

