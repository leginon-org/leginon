# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license


import sinedon.data
import leginondata
Data = sinedon.data.Data

class ApPathData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('path', str),
		)
	typemap = classmethod(typemap)
leginondata.ApPathData=ApPathData


### Particle selection tables ###

class ApParticleData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('selectionrun', ApSelectionRunData),
			('image', leginondata.AcquisitionImageData),
			('xcoord', int),
			('ycoord', int),
			('correlation', float),
			('template', ApTemplateImageData),
			('peakmoment', float),
			('peakstddev', float),
			('peakarea', int),
			('diameter', float),
		)
	typemap = classmethod(typemap)
leginondata.ApParticleData=ApParticleData

class ApSelectionRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('path', ApPathData),
			('session', leginondata.SessionData),
			('params', ApSelectionParamsData),
			('dogparams', ApDogParamsData),
			('manparams', ApManualParamsData),
			('tiltparams', ApTiltAlignParamsData),
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
			#('auto_thresh', int),
			('lp_filt', int),
			('hp_filt', int),
			('invert', int),
			('max_peaks', int),
			('max_threshold', float),
			('median', int),
			('pixel_value_limit', float),
			('maxsize', int),
			('defocal_pairs', bool),
			('overlapmult', float),
		)
	typemap = classmethod(typemap)
leginondata.ApSelectionParamsData=ApSelectionParamsData


class ApDogParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('diam', int),
			('bin', int),
			('manual_thresh', float),
			('max_threshold', float),
			('invert', int),
			('lp_filt', int),
			('hp_filt', int),
			('max_peaks', int),
			('median', int),
			('pixel_value_limit', float),
			('maxsize', int),
			('kfactor', float),
			('size_range', float),
			('num_slices', int),
			('defocal_pairs', bool),
			('overlapmult', float),
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
			('invert', int),
			('median', int),
			('pixel_value_limit', float),
			('oldselectionrun', ApSelectionRunData),
		)
	typemap = classmethod(typemap)
leginondata.ApManualParamsData=ApManualParamsData

class ApTiltAlignParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('diam', int),
			('bin', int),
			('invert', int),
			('lp_filt', int),
			('hp_filt', int),
			('median', int),
			('pixel_value_limit', float),
			('output_type', str),
			('oldselectionrun', ApSelectionRunData),
		)
	typemap = classmethod(typemap)
leginondata.ApTiltAlignParamsData=ApTiltAlignParamsData

### Template tables ###

class ApTemplateImageData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('project|projects|project', int),
			#('templatepath', str),
			('path', ApPathData),
			('templatename', str),
			('apix', float),
			('diam', int),
			('description', str),
			('md5sum', str),
			('stack', ApStackData),
			('noref', ApNoRefClassRunData),
			#('ref', ApRefRunData),
			('stack_image_number', int),
			('hidden', bool),
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
			('image1',leginondata.AcquisitionImageData),
			('image2',leginondata.AcquisitionImageData),
			('shiftx', float),
			('shifty', float),
			('correlation', float),
			('scale', float),
		)
	typemap = classmethod(typemap)
leginondata.ApImageTransformationData=ApImageTransformationData

class ApImageTiltTransformData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('image1',leginondata.AcquisitionImageData),
			('image1_x', float),
			('image1_y', float),
			('image1_rotation', float),
			('image2',leginondata.AcquisitionImageData),
			('image2_x', float),
			('image2_y', float),
			('image2_rotation', float),
			('scale_factor', float),
			('tilt_angle', float),
			('rmsd', float),
			('overlap', float),
			('tiltrun', ApSelectionRunData),
		)
	typemap = classmethod(typemap)
leginondata.ApImageTiltTransformData=ApImageTiltTransformData

class ApTiltParticlePairData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('particle1', ApParticleData),
			('particle2', ApParticleData),
			('transform', ApImageTiltTransformData),
			('error', float),
		)
	typemap = classmethod(typemap)
leginondata.ApImageTiltTransformData=ApImageTiltTransformData

### Mask tables ###

class ApMaskMakerRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('params', ApMaskMakerParamsData),
			('session', leginondata.SessionData),
			('name', str),
			#('path', str),
			('path', ApPathData),
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
			#('stackPath', str),
			('path', ApPathData),
			('name' , str),
			('description', str),
			('hidden', bool),
			('oldstack', ApStackData),
			('substackname', str),
			('pixelsize', float),
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
			('session', leginondata.SessionData),
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
			('checkMask', str),
			('checkImage', bool),
			('norejects', bool),
			('minDefocus', float),
			('maxDefocus', float),
			('fileType', str),
			('inverted', bool),
			('normalized', bool),
			('defocpair', bool),
			('lowpass', float),
			('highpass', float),
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
			('path', ApPathData),
			('description', str),
			('run_seconds', int),
			('hidden', bool),
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
			('num_factors', int),
			('first_ring', int),
			('last_ring', int),
			('skip_coran', bool),
			('init_method', str),
			('bin', int),
#			('norefalign_method', str),
		)
	typemap = classmethod(typemap)
leginondata.ApNoRefParamsData=ApNoRefParamsData

class ApCoranEigenImageData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('norefRun', ApNoRefRunData),
			('factor_num', int),
			('percent_contrib', float),
			('image_name', str),
			('path', ApPathData),
		)
	typemap = classmethod(typemap)
leginondata.ApCoranEigenImageData = ApCoranEigenImageData

class ApNoRefAlignParticlesData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('norefRun', ApNoRefRunData),
			('particle', ApStackParticlesData),
			('shift_x', float),
			('shift_y', float),
			('rotation', float),
		)
	typemap = classmethod(typemap)
leginondata.ApNoRefAlignParticlesData=ApNoRefAlignParticlesData

class ApNoRefClassRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('norefRun', ApNoRefRunData),
			('num_classes', int),
#			('cluster_method', str),
#			('classParams', ApNoRefClassParamData),
			('factor_list', str),
			('classFile', str),
			('varFile', str),
			('method', str),
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

### Reference-based Alignment tables ###

class ApRefRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('stack', ApStackData),
			('refParams', ApRefParamsData),
			('path', ApPathData),
			('description', str),
			('hidden', bool),
		)
	typemap = classmethod(typemap)
leginondata.ApRefRunData=ApRefRunData

class ApRefTemplateRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refRun', ApRefRunData),
			('refTemplate', ApTemplateImageData),
		)
	typemap = classmethod(typemap)
leginondata.ApRefRunData=ApRefRunData

class ApRefParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('mask_diam', int),
			('imask_diam', int),
			('lp', int),
			('xysearch', int),
			('csym', int),
			('num_particles', int),
		)
	typemap = classmethod(typemap)
leginondata.ApRefParamsData=ApRefParamsData

class ApRefBasedAlignParticlesData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refBasedRun', ApRefRunData),
			('particle', ApStackParticlesData),
			('rot_corr', float),
			('reference', int),
			('shift_x', float),
			('shift_y', float),
			('rotation', float),
			('mirror', bool),
			('template', ApTemplateImageData),
		)
	typemap = classmethod(typemap)
leginondata.ApRefBasedAlignParticlesData=ApRefBasedAlignParticlesData

class ApRefIterationData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refRun', ApRefRunData),
			('iteration', int),
			('name', str),
		)
	typemap = classmethod(typemap)
leginondata.ApRefIterationData=ApRefIterationData

### Reconstruction tables ###

class ApClusterJobData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('path', ApPathData),
			('name', str),
			('session', leginondata.SessionData),
			('dmfpath', ApPathData),
			('clusterpath', ApPathData),
			('cluster', str),
			('jobtype', str),
		)
	typemap = classmethod(typemap)
leginondata.ApClusterJobData=ApClusterJobData

class ApRefinementRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('jobfile', ApClusterJobData),
			('stack', ApStackData),
			('initialModel', ApInitialModelData),
			('path', ApPathData),
			('package', str),
			('description', str),
		)
	typemap = classmethod(typemap)
leginondata.ApRefinementRunData=ApRefinementRunData

class ApTomogramData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginondata.SessionData),
			('tiltseries', leginondata.TiltSeriesData),
			('path', ApPathData),
			('name', str),
			('pixelsize', float),
			('description', str),
			('md5sum', str),			
		)
	typemap = classmethod(typemap)
leginondata.ApTomogramData=ApTomogramData

class ApInitialModelData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('project|projects|project', int),
			('path', ApPathData),
			('name', str),
			('resolution', float),
			('symmetry', ApSymmetryData),
			('pixelsize', float),
			('boxsize', int),
			('description', str),
			('hidden', bool),
			('md5sum', str),
		)
	typemap = classmethod(typemap)
leginondata.ApInitialModelData=ApInitialModelData

class ApSymmetryData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('eman_name', str),
			('fold_symmetry', int),
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
			('rMeasure', ApRMeasureData),
			('classAverage', str),
			('classVariance', str),
			('volumeDensity',str),
			('emanClassAvg',str),
			('MsgPGoodClassAvg', str),
			('SpiCoranGoodClassAvg',str),
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
			('symmetry', ApSymmetryData),
			('EMAN_hard', int),
			('EMAN_classkeep', float),
			('EMAN_classiter', int),
			('EMAN_median', bool),
			('EMAN_phasecls', bool),
			('EMAN_refine', bool),
			('MsgP_cckeep', float),
			('MsgP_minptls', int),
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

class ApRMeasureData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('volume', str),
			('rMeasure', float),
		)
	typemap = classmethod(typemap)
leginondata.ApRMeasureData=ApRMeasureData

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
			('msgp_keep',bool),
			('coran_keep',bool),
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

class ApEulerJumpData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('particle', ApStackParticlesData),
			('refRun', ApRefinementRunData),
			('median', float),
			('mean', float),
			('stdev', float),
			('min', float),
			('max', float),
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

class ApMiscData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('project|projects|project', int),
			('refinementRun', ApRefinementRunData),
			('session', leginondata.SessionData),
			('path', ApPathData),
			('name', str),
			('description', str),
			('md5sum', str),
			('hidden', bool),
		)
	typemap = classmethod(typemap)
leginondata.ApMiscData=ApMiscData

### ACE/CTF tables ###

class ApAceRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('aceparams', ApAceParamsData),
			('session', leginondata.SessionData),
			('path', ApPathData),
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


class ApCtfTiltRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('path', ApPathData),
			('ctftilt_params', ApCtfTiltParamsData),
			('session', leginondata.SessionData),
		)
	typemap = classmethod(typemap)
leginondata.ApAceRunData=ApAceRunData

class ApCtfTiltParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('medium', str),
			('ampcarbon', float),
			('ampice', float),
			('fieldsize', int),
			('cs', float),
			('bin', int),
		)
	typemap = classmethod(typemap)
leginondata.ApAceParamsData=ApAceParamsData

class ApCtfData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('acerun', ApAceRunData),
			('ctftiltrun', ApCtfTiltRunData),
			('image', leginondata.AcquisitionImageData),
			('defocus1', float),
			('defocus2', float),
			('defocusinit', float),
			('amplitude_contrast', float),
			('angle_astigmatism', float),
			('tilt_angle', float),
			('tilt_axis_angle', float),
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
			('cross_correlation', float)
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
			('session', leginondata.SessionData),
			('name', str),
			#('path', str),
			('path', ApPathData),
		)
	typemap = classmethod(typemap)
leginondata.ApTestRunData=ApTestRunData

class ApTestResultData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('testrun', ApTestRunData),
			('image', leginondata.AcquisitionImageData),
			('x', float),
			('y', float),
		)
	typemap = classmethod(typemap)
leginondata.ApTestResultData=ApTestResultData

### Assessment tables ###

class ApAssessmentRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginondata.SessionData),
			('name',str),
		)
	typemap = classmethod(typemap)
leginondata.ApAssessmentRunData=ApAssessmentRunData

class ApAssessmentData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('assessmentrun', ApAssessmentRunData),
			('image', leginondata.AcquisitionImageData),
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

