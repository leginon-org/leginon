# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
 
import data
import dbdatakeeper

db=dbdatakeeper.DBDataKeeper()

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
			('run id', run),
			('dbemdata|AcquisitionImageData|image1', int),
			('dbemdata|AcquisitionImageData|image2', int),
			('shift x', float),
			('shift y', float),
			('correlation value', float),
		)
	typemap = classmethod(typemap)
data.shift=shift

class particle(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('run id', run),
			('image id', image),
			('shift id', shift),
			('selexon params', selexon_params),
			('x coord', int),
			('y coord', int),
			('correlation value', float),
		)
	typemap = classmethod(typemap)
data.particle=particle
