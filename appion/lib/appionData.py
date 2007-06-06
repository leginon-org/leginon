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
			('template', ApTemplateImageData),
			('peakmoment', float),
			('peakstddev', float),
			('peakarea', int),
		)
	typemap = classmethod(typemap)
data.ApParticleData=ApParticleData

class ApSelectionRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('params', ApSelectionParamsData),
			('dogparams', ApDogParamsData),
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
			('max_peaks', int),
		)
	typemap = classmethod(typemap)
data.ApSelectionParamsData=ApSelectionParamsData

class ApDogParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('diam', int),
			('bin', int),
			('threshold', float),
			('max_threshold', float),
			('invert', int),
			('lp_filt', int),
			('hp_filt', int),
			('max_peaks', int),			
		)
	typemap = classmethod(typemap)
data.ApDogParamsData=ApDogParamsData


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
			('selectionrun', ApSelectionRunData),
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
			('label', int),
			
		)
	typemap = classmethod(typemap)
data.ApMaskRegionData=ApMaskRegionData

class ApMaskMakerParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
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
			('stackparams', ApStackParamsData),
			('particle', ApParticleData),
	        )
	typemap = classmethod(typemap)
data.ApStackParticlesData = ApStackParticlesData

### Reconstruction Tables ###

class ApRefinementRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('name', str),
			('stack', ApStackParamsData),
			('initialModel', ApInitialModelData),
			('path', str),
			('package', str),
		)
	typemap = classmethod(typemap)
data.ApRefinementRunData=ApRefinementRunData

class ApInitialModelData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('project|projects|project', int),
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
			('refinementRun', ApRefinementRunData),
			('refinementParams', ApRefinementParamsData),
			('iteration', int),
			('resolution', ApResolutionData),
			('classAverage', str),
			('classVariance', str),
			('volumeDensity',str),
		)
	typemap = classmethod(typemap)
data.ApRefinementData=ApRefinementData

class ApRefinementParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('ang', float),
			('mask', int),
			('imask', int),
			('lpfilter', int),
			('hpfilter', int),
			('pad', int),
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
			('particle', ApStackParticlesData),
			('eulers', ApEulerData),
			('shiftx', float),
			('shifty', float),
			('inplane_rotation', float),
			('quality_factor', float),
			('thrown_out',bool),
		)
	typemap = classmethod(typemap)
data.ApParticleClassificationData=ApParticleClassificationData

class ApEulerData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('euler1', float),
			('euler2', float),
			('euler3', float),
	        )
	typemap = classmethod(typemap)
data.ApEulerData=ApEulerData
	
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
			('graphpath', str),
			('graph1', str),
			('graph2', str),
			('matpath', str),
			('mat_file', str),
		)
	typemap = classmethod(typemap)
data.ApCtfData=ApCtfData

class ApTestParamsData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('bin', int),
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

class ApTestResultData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('testrun', ApTestRunData),
			('dbemdata|AcquisitionImageData|image', int),
			('x', float), 
			('y', float),
		)
	typemap = classmethod(typemap)
data.ApTestResultData=ApTestResultData

### Assessment tables ###

class ApAssessmentRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session',int),
			('name',str),
		)
	typemap = classmethod(typemap)
data.ApAssessmentRunData=ApAssessmentRunData

class ApAssessmentData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('assessmentrun', ApAssessmentRunData),
			('dbemdata|AcquisitionImageData|image', int),
			('selectionkeep', int),
		)
	typemap = classmethod(typemap)
data.ApAssessmentData=ApAssessmentData

class ApMaskAssessmentRunData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('dbemdata|SessionData|session',int),
			('maskrun',ApMaskMakerRunData),
			('name',str),
		)
	typemap = classmethod(typemap)
data.ApMaskAssessmentRunData=ApMaskAssessmentRunData

class ApMaskAssessmentData(data.Data):
	def typemap(cls):
		return data.Data.typemap() + (
			('run', ApMaskAssessmentRunData),
			('region', ApMaskRegionData),
			('keep', int),
		)
	typemap = classmethod(typemap)
data.ApMaskAssessmentData=ApMaskAssessmentData
