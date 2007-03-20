# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
 
import data
#import dbdatakeeper

#acedb=dbdatakeeper.DBDataKeeper(db='dbctfdata')

class run(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session', int),
			('name', str), 
		)
	typemap = classmethod(typemap)
data.run=run

class acerun(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session', int),
			('name', str), 
		)
	typemap = classmethod(typemap)
data.run=run

class ace_params(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('runId', run),
			('display', int), 
			('stig', int),
			('medium', str),
			('df_override', float),
			('edgethcarbon', float),
			('edgethice', float),
			('pfcarbon', float),
			('pfice', float),
			('overlap', int),
			('fieldsize', int),
			('resamplefr', float),
			('drange', int),
			('reprocess', float),
		)
	typemap = classmethod(typemap)
data.ace_params=ace_params

class ctf(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('runId', run),
			('aceId', ace_params),
			('imageId', image),
			('defocus1', float),
			('defocus2', float), 
			('defocusinit', float), 
			('amplitude_contrast', float), 
			('angle_astigmatism', float), 
			('noise1', float), 
			('noise2', float), 
			('noise3', float), 
			('noise4', float), 
			('envelope1', float), 
			('envelope2', float), 
			('envelope3', float), 
			('envelope4', float), 
			('lowercutoff', float), 
			('uppercutoff', float), 
			('snr', float), 
			('confidence', float), 
			('confidence_d', float), 
			('graph1', str),
			('graph2', str),
			('mat_file', str),
		)
	typemap = classmethod(typemap)
data.ctf=ctf

class ctfblob(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('ctfId', ctf),
			('imageId', image),
			('blobgraph1', float),
			('blobgraph2', float),
		)
	typemap = classmethod(typemap)
data.ctfblob=ctfblob

class image(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session', int),
			('dbemdata|AcquisitionImageData|image', int),
			('dbemdata|PresetData|preset', int),
			('dbemdata|ScopeEMData|defocus', float),
			('imagename', str),
		)
	typemap = classmethod(typemap)
data.image=image
