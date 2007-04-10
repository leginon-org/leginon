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

class maskRegion(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('mask', makeMaskParams),
			('imageId', image),
			('x', int),
			('y', int),
			('area', int),
			('perimeter', int),
			('mean', float),
			('stdev', float),
			('keep', bool),
			
		)
	typemap = classmethod(typemap)
data.maskRegion=maskRegion

class image(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|AcquisitionImageData|image', int),
			('dbemdata|SessionData|session', int),
			('dbemdata|PresetData|preset', int),
			('keep', bool),
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
			('diam', int),
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

class makeMaskParams(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session', int),
			('mask path', str),
			('name', str),
			('bin', int),
			('mask type', str),
			('pdiam', int),
			('region diameter', int),
			('edge blur', float),
			('edge low', float),
			('edge high', float),
			('region std', float),
			('convolve', float),
			('convex hull', bool),
			('libcv', bool),
		)
	typemap = classmethod(typemap)
data.makeMaskParams=makeMaskParams

class stackParams(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('stackPath', str),
			('name' , str),
			('description', str),
			('boxSize', int),
			('bin', int),
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

class MaskMakerSettingsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session', int),
			('mask path', str),
			('name', str),
			('bin', int),
			('mask type', str),
			('pdiam', int),
			('region diameter', int),
			('edge blur', float),
			('edge low', float),
			('edge high', float),
			('region std', float),
			('convolve', float),
			('convex hull', bool),
			('libcv', bool),
		)
	typemap = classmethod(typemap)
data.makeMaskParams=makeMaskParams

class stackParticles(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('particleNumber', int),
			('stackId', stackParams),
			('particleId', particle),
	        )
	typemap = classmethod(typemap)
data.stackParticles = stackParticles

### Reconstruction Tables ###

class reconRun(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('name', str),
			('stackId', stackParams),
			('initialModelId', initialModel),
			('path', str),
			('package', str),
		)
	typemap = classmethod(typemap)
data.reconRun=reconRun

class initialModel(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('path', str),
			('name', str),
			('symmetryId', symmetry),
			('pixelsize', float),
			('boxsize', int),
			('description', str),
		)
	typemap = classmethod(typemap)
data.initialModel=initialModel

class symmetry(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('symmetry', str),
			('description', str),
		)
	typemap = classmethod(typemap)
data.symmetry=symmetry

class refinement(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('reconRunId', reconRun),
			('refinementParamsId', refinementParams),
			('iteration', int),
			('resolutionId', resolution),
			('classAverage', str),
			('classVariance', str),
			('numClassAvg', int),
			('numClassAvgKept', int),
			('numBadParticles', int),
			('volumeSnapshot', str),
			('volumeDensity',str),
		)
	typemap = classmethod(typemap)
data.refinement=refinement

class refinementParams(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('angIncr', float),
			('mask', int),
			('imask', int),
			('lpfilter', int),
			('hpfilter', int),
			('fourier_padding', int),
			('EMAN_hard', int),
			('EMAN_classkeep', float),
			('EMAN_classiter', int),
			('EMAN_median', bool),
			('EMAN_phasecls', bool),
			('EMAN_refine', bool),
		)
	typemap = classmethod(typemap)
data.refinementParams=refinementParams

class resolution(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('fscfile', str),
			('half', float),
		)
	typemap = classmethod(typemap)
data.resolution=resolution

class particleClassification(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('refinementId', refinement),
			('particleId', particle),
			('classnumber', int),
			('euler1', float),
			('euler2', float),
			('euler3', float),
			('shiftx', float),
			('shifty', float),
			('inplane_rotation', float),
			('quality_factor', float),
			('thrown_out',int),
		)
	typemap = classmethod(typemap)
data.particleClassification=particleClassification
