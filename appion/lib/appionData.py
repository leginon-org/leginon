# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
 
import data

### Particle Selection Tables

class ApParticleData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('selectionrun', ApSelectionRunData),
			('dbemdata|AcquisitionImageData|image', int),
			('xcoord', int),
			('ycoord', int),
			('correlation', float),
		)
	typemap = classmethod(typemap)
data.ApParticleData=ApParticleData

class ApSelectionRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('params', ApSelectionParamsData),
			('templaterun', ApTemplateRunData),
			('dbemdata|SessionData|session', int),
			('name', str), 
		)
	typemap = classmethod(typemap)
data.ApSelectionRunData=ApSelectionRunData

class ApSelectionParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('diam', int),
			('bin', int),
			('manual_thresh', float),
			('auto_thresh', int),
			('lp_filt', int),
			('hp_filt', int),
		)
	typemap = classmethod(typemap)
data.ApSelectionParamsData=ApSelectionParamsData

class ApTemplateImageData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('project|projects|project', int),
			('templatepath', str),
			('templatename', str),
			('apix', float),
			('diam', int),
			('description', str),
		)
	typemap = classmethod(typemap)
data.ApTemplateImageData=ApTemplateImageData

class ApTemplateRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('template', ApTemplateImageData),
			('range_start', int),
			('range_end', int),
			('range_incr', int),
		)
	typemap = classmethod(typemap)
data.ApTemplateRunData=ApTemplateRunData



### Shift Table(s)

class ApImageTransformationData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|AcquisitionImageData|image1', int),
			('dbemdata|AcquisitionImageData|image2', int),
			('shiftx', float),
			('shifty', float),
			('correlation', float),
			('scale', float),
			('inplane_rotation', float),
			('tilt', float),
		)
	typemap = classmethod(typemap)
data.ApImageTransformationData=ApImageTransformationData


### Mask Tables 

class ApMaskMakerRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('params', ApMaskMakerParamsData),
			('dbemdata|SessionData|session', int),
			('name', str), 
			('path', str),
		)
	typemap = classmethod(typemap)
data.ApMaskMakerRunData=ApMaskMakerRunData

class ApMaskRegionData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('maskrun', ApMaskMakerRunData),
			('dbemdata|AcquisitionImageData|image', int),
			('x', int),
			('y', int),
			('area', int),
			('perimeter', int),
			('mean', float),
			('stdev', float),
			
		)
	typemap = classmethod(typemap)
data.ApMaskRegionData=ApMaskRegionData

class ApMaskMakerParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
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
data.ApMaskMakerParamsData=ApMaskMakerParamsData


### Stack Tables

class ApStackParamsData(data.Data):
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
data.ApStackParamsData=ApStackParamsData

class ApStackParticlesData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('particleNumber', int),
			('stack', ApStackParamsData),
			('particle', ApParticleData),
	        )
	typemap = classmethod(typemap)
data.ApStackParticlesData = ApStackParticlesData

### Reconstruction Tables ###

class ApReconRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('name', str),
			('stack', ApStackParamsData),
			('initialModel', ApInitialModelData),
			('path', str),
			('package', str),
		)
	typemap = classmethod(typemap)
data.ApReconRunData=ApReconRunData

class ApInitialModelData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('path', str),
			('name', str),
			('symmetry', ApSymmetryData),
			('pixelsize', float),
			('boxsize', int),
			('description', str),
		)
	typemap = classmethod(typemap)
data.ApInitialModelData=ApInitialModelData

class ApSymmetryData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('symmetry', str),
			('description', str),
		)
	typemap = classmethod(typemap)
data.ApSymmetryData=ApSymmetryData

class ApRefinementData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('reconRun', reconRun),
			('refinementParams', ApRefinementParamsData),
			('iteration', int),
			('resolution', resolution),
			('classAverage', str),
			('classVariance', str),
			('numClassAvg', int),
			('numClassAvgKept', int),
			('numBadParticles', int),
			('volumeSnapshot', str),
			('volumeDensity',str),
		)
	typemap = classmethod(typemap)
data.ApRefinementData=ApRefinementData

class ApRefinementParamsData(data.Data):
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
data.ApRefinementParamsData=ApRefinementParamsData

class ApResolutionData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('fscfile', str),
			('half', float),
		)
	typemap = classmethod(typemap)
data.ApResolutionData=ApResolutionData

class ApParticleClassificationData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('refinement', ApRefinementData),
			('particle', ApParticleData),
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
data.ApParticleClassificationData=ApParticleClassificationData


### ACE/CTF Tables

class ApAceRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('aceparams', ApAceParamsData),
			('dbemdata|SessionData|session', int),
			('name', str), 
		)
	typemap = classmethod(typemap)
data.ApAceRunData=ApAceRunData

class ApAceParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
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
data.ApAceParamsData=ApAceParamsData

class ApCtfData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('acerun', ApAceRunData),
			('dbemdata|AcquisitionImageData|image', int),
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
data.ApCtfData=ApCtfData

class ApTestParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('name', str),
			('bin', int),
			('param1', int), 
			('param2', int), 
		)
	typemap = classmethod(typemap)
data.ApTestParamsData=ApTestParamsData

class ApTestRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('params', ApTestParamsData),
			('dbemdata|SessionData|session', int),
			('name', str), 
			('path', str),
		)
	typemap = classmethod(typemap)
data.ApTestRunData=ApTestRunData
