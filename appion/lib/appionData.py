# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license
 
try:
	import sinedon.data
	import leginondata
	Data = sinedon.data.Data
except:	
	import data as leginondata
	Data = data.Data

### Particle selection tables ###

class ApParticleData(Data):
	def typemap(cls):
		return Data.typemap() + (
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
leginondata.ApParticleData=ApParticleData

class ApSelectionRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('params', ApSelectionParamsData),
			('dogparams', ApDogParamsData),
			('manparams', ApManualParamsData),
			('dbemdata|SessionData|session', int),
			('name', str), 
		)
	typemap = classmethod(typemap)
leginondata.ApSelectionRunData=ApSelectionRunData

class ApSelectionParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('diam', int),
			('bin', int),
			('manual_thresh', float),
			('auto_thresh', int),
			('lp_filt', int),
			('hp_filt', int),
			('max_peaks', int),
		)
	typemap = classmethod(typemap)
leginondata.ApSelectionParamsData=ApSelectionParamsData

class ApDogParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
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
leginondata.ApDogParamsData=ApDogParamsData

class ApManualParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('diam', int),
			('bin', int),
			('lp_filt', int),
			('hp_filt', int),
		)
	typemap = classmethod(typemap)
leginondata.ApManualParamsData=ApManualParamsData

### Template tables ###

class ApTemplateImageData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('project|projects|project', int),
			('templatepath', str),
			('templatename', str),
			('apix', float),
			('diam', int),
			('description', str),
		)
	typemap = classmethod(typemap)
leginondata.ApTemplateImageData=ApTemplateImageData

class ApTemplateRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('template', ApTemplateImageData),
			('selectionrun', ApSelectionRunData),
			('range_start', int),
			('range_end', int),
			('range_incr', int),
		)
	typemap = classmethod(typemap)
leginondata.ApTemplateRunData=ApTemplateRunData

### Transformation/shift tables ###

class ApImageTransformationData(Data):
	def typemap(cls):
		return Data.typemap() + (
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
leginondata.ApImageTransformationData=ApImageTransformationData

### Mask tables ###

class ApMaskMakerRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('params', ApMaskMakerParamsData),
			('session', leginondata.SessionData),
			('name', str), 
			('path', str),
		)
	typemap = classmethod(typemap)

class ApMaskRegionData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('maskrun', ApMaskMakerRunData),
			('image', leginondata.AcquisitionImageData),
			('x', int),
			('y', int),
			('area', int),
			('perimeter', int),
			('mean', float),
			('stdev', float),
			('label', int),
			
		)
	typemap = classmethod(typemap)

class ApMaskMakerParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
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

### Stack tables ###

class ApStackData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('stackPath', str),
			('name' , str),
			('description', str),
		)
	typemap = classmethod(typemap)
leginondata.ApStackData=ApStackData

class ApRunsInStackData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('stack', ApStackData),
			('stackRun' , ApStackRunData),
		)
	typemap = classmethod(typemap)
leginondata.ApRunsInStackData=ApRunsInStackData

class ApStackRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('stackRunName', str),
			('stackParams', ApStackParamsData),
			('dbemdata|SessionData|session', int),
		)
	typemap = classmethod(typemap)
leginondata.ApStackRunData=ApStackRunData

class ApStackParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('boxSize', int),
			('bin', int),
			('phaseFlipped', bool),
			('aceCutoff', float),
			('correlationMin', float),
			('correlationMax', float),
			('checkCrud', bool),
			('checkImage', bool),
			('minDefocus', float),
			('maxDefocus', float),
			('fileType', str),
			('inverted', bool),
			('normalized', bool),
		)
	typemap = classmethod(typemap)
leginondata.ApStackParamsData=ApStackParamsData

class ApStackParticlesData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('particleNumber', int),
			('stack', ApStackData),
			('stackRun', ApStackRunData),
			('particle', ApParticleData),
	        )
	typemap = classmethod(typemap)
leginondata.ApStackParticlesData = ApStackParticlesData

### Reference-free Classification tables ###

class ApNoRefRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('stack', ApStackData), #Redundant
			('norefParams', ApNoRefParamsData),
			('norefPath', str),
			('description', str),
		)
	typemap = classmethod(typemap)
leginondata.ApNoRefRunData=ApNoRefRunData

class ApNoRefParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('particle_diam', float),
			('mask_diam', float),
			('lp_filt', int),
			('num_particles', int), #Redundant?
#			('norefalign_method', str),
#			('pca_method', str),
		)
	typemap = classmethod(typemap)
leginondata.ApNoRefParamsData=ApNoRefParamsData

class ApNoRefAlignParticlesData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('norefRun', ApNoRefRunData),
			('stack_particle', ApStackParticlesData),
			('shiftx', float),
			('shifty', float),
			('inplane_rotation', float),
		)
	typemap = classmethod(typemap)
leginondata.ApNoRefAlignParticlesData=ApNoRefAlignParticlesData

#class ApNoRefEigenVectorData(Data):
#class ApNoRefEigenValueParticlesData(Data):

class ApNoRefClassRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('norefRun', ApNoRefRunData),
			('num_classes', int),
#			('cluster_method', str),
#			('classParams', ApNoRefClassParamData),
			('classFile', str),
		)
	typemap = classmethod(typemap)
leginondata.ApNoRefClassRunData=ApNoRefClassRunData

class ApNoRefClassParticlesData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('classRun', ApNoRefClassRunData),
			('noref_particle', ApNoRefAlignParticlesData),
			('classNumber', int),
		)
	typemap = classmethod(typemap)
leginondata.ApNoRefClassParticlesData=ApNoRefClassParticlesData

### Reconstruction tables ###

class ApRefinementRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('stack', ApStackData),
			('initialModel', ApInitialModelData),
			('path', str),
			('package', str),
		)
	typemap = classmethod(typemap)
leginondata.ApRefinementRunData=ApRefinementRunData

class ApInitialModelData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('project|projects|project', int),
			('path', str),
			('name', str),
			('symmetry', ApSymmetryData),
			('pixelsize', float),
			('boxsize', int),
			('description', str),
		)
	typemap = classmethod(typemap)
leginondata.ApInitialModelData=ApInitialModelData

class ApSymmetryData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('symmetry', str),
			('description', str),
		)
	typemap = classmethod(typemap)
leginondata.ApSymmetryData=ApSymmetryData

class ApRefinementData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refinementRun', ApRefinementRunData),
			('refinementParams', ApRefinementParamsData),
			('iteration', int),
			('resolution', ApResolutionData),
			('classAverage', str),
			('classVariance', str),
			('volumeDensity',str),
		)
	typemap = classmethod(typemap)
leginondata.ApRefinementData=ApRefinementData

class ApRefinementParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
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
leginondata.ApRefinementParamsData=ApRefinementParamsData

class ApResolutionData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('fscfile', str),
			('half', float),
		)
	typemap = classmethod(typemap)
leginondata.ApResolutionData=ApResolutionData

class ApParticleClassificationData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refinement', ApRefinementData),
			('particle', ApStackParticlesData),
			('eulers', ApEulerData),
			('shiftx', float),
			('shifty', float),
			('inplane_rotation', float),
			('quality_factor', float),
			('mirror', bool),
			('thrown_out',bool),
		)
	typemap = classmethod(typemap)
leginondata.ApParticleClassificationData=ApParticleClassificationData

class ApEulerData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('euler1', float),
			('euler2', float),
			('euler3', float),
	        )
	typemap = classmethod(typemap)
leginondata.ApEulerData=ApEulerData
	
class ApFSCData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refinementData', ApRefinementData),
			('pix', int),
			('value', float),
		)
	typemap = classmethod(typemap)
leginondata.ApFSCData=ApFSCData

### ACE/CTF tables ###

class ApAceRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('aceparams', ApAceParamsData),
			('dbemdata|SessionData|session', int),
			('name', str), 
		)
	typemap = classmethod(typemap)
leginondata.ApAceRunData=ApAceRunData

class ApAceParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
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
leginondata.ApAceParamsData=ApAceParamsData

class ApCtfData(Data):
	def typemap(cls):
		return Data.typemap() + (
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
leginondata.ApCtfData=ApCtfData

### Testing tables ###

class ApTestParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('bin', int),
		)
	typemap = classmethod(typemap)
leginondata.ApTestParamsData=ApTestParamsData

class ApTestRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('params', ApTestParamsData),
			('dbemdata|SessionData|session', int),
			('name', str), 
			('path', str),
		)
	typemap = classmethod(typemap)
leginondata.ApTestRunData=ApTestRunData

class ApTestResultData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('testrun', ApTestRunData),
			('dbemdata|AcquisitionImageData|image', int),
			('x', float), 
			('y', float),
		)
	typemap = classmethod(typemap)
leginondata.ApTestResultData=ApTestResultData

### Assessment tables ###

class ApAssessmentRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('dbemdata|SessionData|session',int),
			('name',str),
		)
	typemap = classmethod(typemap)
leginondata.ApAssessmentRunData=ApAssessmentRunData

class ApAssessmentData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('assessmentrun', ApAssessmentRunData),
			('dbemdata|AcquisitionImageData|image', int),
			('selectionkeep', int),
		)
	typemap = classmethod(typemap)
leginondata.ApAssessmentData=ApAssessmentData

class ApMaskAssessmentRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session',leginondata.SessionData),
			('name',str),
			('maskrun', ApMaskMakerRunData),
		)
	typemap = classmethod(typemap)

class ApMaskAssessmentData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('run', ApMaskAssessmentRunData),
			('region', ApMaskRegionData),
			('keep', int),
		)
	typemap = classmethod(typemap)
