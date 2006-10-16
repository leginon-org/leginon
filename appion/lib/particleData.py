# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
 
import data
import dbdatakeeper

db=dbdatakeeper.DBDataKeeper(db='dbparticledata')

class run(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session', int),
			('name', str), 
		)
	typemap = classmethod(typemap)
data.run=run

class image(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|AcquisitionImageData|image', int),
			('dbemdata|SessionData|session', int),
			('dbemdata|PresetData|preset', int),
		)
	typemap = classmethod(typemap)
data.image=image

class shift(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|AcquisitionImageData|image1', int),
			('dbemdata|AcquisitionImageData|image2', int),
			('shiftx', float),
			('shifty', float),
			('correlation', float),
		)
	typemap = classmethod(typemap)
data.shift=shift

class particle(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('runId', run),
			('imageId', image),
			('shiftId', shift),
			('selexonId', selexonParams),
			('xcoord', int),
			('ycoord', int),
			('correlation', float),
			('insidecrud', int),
		)
	typemap = classmethod(typemap)
data.particle=particle

class selexonParams(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('runId', run),
			('template', str),
			('diam', int),
			('bin', int),
			('range_start', int),
			('range_end', int),
			('range_increment', int),
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
data.selexonParams=selexonParams
