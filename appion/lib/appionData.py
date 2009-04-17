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
			('name', str),
			('hidden', bool),
			('path', ApPathData),
			('session', leginondata.SessionData),
			('params', ApSelectionParamsData),
			('dogparams', ApDogParamsData),
			('manparams', ApManualParamsData),
			('tiltparams', ApTiltAlignParamsData),
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
			('alignstack', ApAlignStackData),
			('clusterstack', ApClusteringStackData),
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
			('mirror', bool),
		)
	typemap = classmethod(typemap)
leginondata.ApTemplateRunData=ApTemplateRunData

class ApTemplateStackData(Data):
        def typemap(cls):
                return Data.typemap() + (
			('clusterstack', ApClusteringStackData),
                        ('templatename', str),
			('cls_avgs', bool),
			('forward_proj', bool),
                        ('origfile', str),
			('description', str),
			('session', leginondata.SessionData),
			('apix', float),
			('boxsize', int),
			('numimages', int),
			('hidden', bool),
			('path', ApPathData),
			('project|projects|project', int),
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
			('centered', bool),
			('mask', int),
			('maxshift', int),
			('project|projects|project', int),
		)
	typemap = classmethod(typemap)
leginondata.ApStackData=ApStackData

class ApRunsInStackData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('stack', ApStackData),
			('stackRun' , ApStackRunData),
			('project|projects|project', int),
		)
	typemap = classmethod(typemap)
leginondata.ApRunsInStackData=ApRunsInStackData

class ApStackRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('stackRunName', str),
			('stackParams', ApStackParamsData),
			('syntheticStackParams', ApSyntheticStackParamsData),
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
			('fliptype', str),
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
			('tiltangle', str),
		)
	typemap = classmethod(typemap)
leginondata.ApStackParamsData=ApStackParamsData

class ApSyntheticStackParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('modelid', ApInitialModelData),
			('boxsize' , int),
			('apix', float),
			('projcount', int),
			('projstdev', float),
			('shiftrad', float),
			('rotang', int),
			('flip', bool),
			('kilovolts', int),
			('spher_aber', float),
			('defocus_x', float),
			('defocus_y', float),
			('randomdef', bool),
			('randomdef_std', float),
			('astigmatism', float),
			('snr1', float),
			('snrtot', float),
			('envelope', str),
			('ace2correct', bool),
			('ace2correct_rand', bool),
			('ace2correct_std', float),
			('ace2estimate', bool),
			('lowpass', int),
			('highpass', int),
			('norm', bool),
		)
	typemap = classmethod(typemap)

class ApStackParticlesData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('particleNumber', int),
			('stack', ApStackData),
			('stackRun', ApStackRunData),
			('particle', ApParticleData),
			('mean', float),
			('stdev', float),
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

### Improved alignment run tables

class ApMaxLikeJobData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('timestamp', str),
			('path', ApPathData),
			('project|projects|project', int),
			('finished', bool),
			('hidden', bool),
		)
	typemap = classmethod(typemap)
leginondata.ApMaxLikeJobData=ApMaxLikeJobData

class ApMaxLikeRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('mirror', bool),
			('mask_diam', int),
			('init_method', str),
			('fast', bool),
			('fastmode', str),
			('run_seconds', int),
			('job', ApMaxLikeJobData),
		)
	typemap = classmethod(typemap)
leginondata.ApMaxLikeRunData=ApMaxLikeRunData

class ApRefBasedRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('mask_diam', int),
			('xysearch', int),
			('xystep', int),
			('first_ring', int),
			('last_ring', int),
			('num_iter', int),
			('invert_templs', bool),
			('num_templs', int),
			('csym', int),
			('run_seconds', int),
		)
	typemap = classmethod(typemap)
leginondata.ApRefBasedRunData=ApRefBasedRunData

class ApSpiderNoRefRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('particle_diam', float),
			('first_ring', int),
			('last_ring', int),
			('run_seconds', int),
			('init_method', str),
		)
	typemap = classmethod(typemap)
leginondata.ApSpiderNoRefRunData=ApSpiderNoRefRunData

class ApMultiRefAlignRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('lowpass_refs', int),
			('thresh_refs', int),
			('maskrad_refs', float),
			('mirror', bool),
			('max_shift_orig', float),
			('max_shift_this', float),
			('samp_param', float),
			('min_radius', float),
			('max_radius', float),
			('numiter', int),
		)
	typemap = classmethod(typemap)
#leginondata.ApMultiRefAlignRunData=ApMultiRefAlignRunData

### Improved alignment data tables

class ApAlignRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('bin', int),
			('hp_filt', int),
			('lp_filt', int),
			('description', str),
			('norefrun', ApSpiderNoRefRunData),
			('refbasedrun', ApRefBasedRunData),
			('maxlikerun', ApMaxLikeRunData),
			('imagicMRA', ApMultiRefAlignRunData),
			('hidden', bool),
			('project|projects|project', int),
			('path', ApPathData),
		)
	typemap = classmethod(typemap)
leginondata.ApAlignRunData=ApAlignRunData

class ApAlignStackData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('imagicfile', str),
			('spiderfile', str),
			('avgmrcfile', str),
			('refstackfile', str),
			('iteration', int),
			('path', ApPathData),
			('stack', ApStackData),
			('alignrun', ApAlignRunData),
			('boxsize', int),
			('pixelsize', float),
			('description', str),
			('hidden', bool),
			('num_particles', int),
			('project|projects|project', int),
		)
	typemap = classmethod(typemap)
leginondata.ApAlignStackData=ApAlignStackData

class ApAlignParticlesData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('partnum', int),
			('alignstack', ApAlignStackData),
			('stackpart', ApStackParticlesData),
			('xshift', float),
			('yshift', float),
			('rotation', float),
			('mirror', bool),
			('spread', float),
			('correlation', float),
			('score', float),
			('ref', ApAlignReferenceData),
		)
	typemap = classmethod(typemap)
leginondata.ApAlignParticlesData=ApAlignParticlesData

class ApAlignReferenceData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refnum', int),
			('iteration', int),
			('mrcfile', str),
			('varmrcfile', str),
			('ssnr_resolution', float),
			('alignrun', ApAlignRunData),
			('path', ApPathData),
			('template', ApTemplateImageData),
		)
	typemap = classmethod(typemap)
leginondata.ApAlignReferenceData=ApAlignReferenceData

### Analysis data tables

class ApAlignAnalysisRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('description', str),
			('hidden', bool),
			('path', ApPathData),
			('coranrun', ApCoranRunData),
			('imagicMSArun', ApImagicAlignAnalysisData),
			('alignstack', ApAlignStackData),
			('project|projects|project', int),
		)
	typemap = classmethod(typemap)
leginondata.ApAlignAnalysisRunData=ApAlignAnalysisRunData

class ApCoranRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('mask_diam', float),
			('run_seconds', int),
			('num_factors', int),
		)
	typemap = classmethod(typemap)
leginondata.ApCoranRunData=ApCoranRunData

class ApCoranEigenImageData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('norefRun', ApNoRefRunData),
			('coranRun', ApCoranRunData),
			('factor_num', int),
			('percent_contrib', float),
			('image_name', str),
			('path', ApPathData),
		)
	typemap = classmethod(typemap)
leginondata.ApCoranEigenImageData = ApCoranEigenImageData

class ApImagicAlignAnalysisData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('run_seconds', int),
			('bin', int),
			('highpass', int),
			('lowpass', int),
			('mask_radius', float),
			('mask_dropoff', float),
			('numiters', int),
			('overcorrection', float),
			('MSAmethod', str),
			('eigenimages', str),
		)
	typemap = classmethod(typemap)

### Improved cluster class data tables

class ApSpiderClusteringParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('factor_list', str),
			('method', str),
		)
	typemap = classmethod(typemap)
leginondata.ApSpiderClusteringParamsData=ApSpiderClusteringParamsData

class ApKerDenSOMParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('mask_diam', float),
			('x_dimension', int),
			('y_dimension', int),
			('convergence', str),
			('run_seconds', int),
		)
	typemap = classmethod(typemap)
leginondata.ApKerDenSOMParamsData=ApKerDenSOMParamsData

class ApClusteringRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('description', str),
			('boxsize', int),
			('pixelsize', float),
			('num_particles', int),
			('alignstack', ApAlignStackData),
			('analysisrun', ApAlignAnalysisRunData),
			('spiderparams', ApSpiderClusteringParamsData),
			('kerdenparams', ApKerDenSOMParamsData),
			('project|projects|project', int),
		)
	typemap = classmethod(typemap)
leginondata.ApClusteringRunData=ApClusteringRunData

class ApClusteringStackData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('num_classes', int),
			('hidden', bool),
			('avg_imagicfile', str),
			('var_imagicfile', str),
			('path', ApPathData),
			('clusterrun', ApClusteringRunData),
			('ignore_images', int),
			('ignore_members', int),
		)
	typemap = classmethod(typemap)
leginondata.ApClusteringRunData=ApClusteringRunData

class ApClusteringParticlesData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('partnum', int),
			('refnum', int),
			('clusterreference', ApClusteringReferenceData),
			('clusterstack', ApClusteringStackData),
			('alignparticle', ApAlignParticlesData),
			('imagic_cls_quality', float),
		)
	typemap = classmethod(typemap)
leginondata.ApClusteringParticlesData=ApClusteringParticlesData

class ApClusteringReferenceData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refnum', int),
			('avg_mrcfile', str),
			('var_mrcfile', str),
			('ssnr_resolution', float),
			('num_particles', int),
			('clusterrun', ApClusteringRunData),
			('path', ApPathData),
		)
	typemap = classmethod(typemap)
leginondata.ApClusteringReferenceData=ApClusteringReferenceData

### Reconstruction tables ###

class ApClusterJobData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('cluster', str),
			('jobtype', str),
			('status', str),
			('user', str),
			('clusterjobid', int),
			('path', ApPathData),
			('session', leginondata.SessionData),
			('dmfpath', ApPathData),
			('clusterpath', ApPathData),

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

class ApImodXcorrParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('RotationAngle', float),
			('FilterSigma1', float),
			('FilterRadius2', float),
			('FilterSigma2', float),
		)
	typemap = classmethod(typemap)
leginondata.ApImodXcorrParamsData=ApImodXcorrParamsData

class ApTomoAlignmentRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginondata.SessionData),
			('tiltseries', leginondata.TiltSeriesData),
			('coarseLeginonParams', leginondata.TomographySettingsData),
			('coarseImodParams', ApImodXcorrParamsData),
			('bin', int),
			('name', str),
		)
	typemap = classmethod(typemap)
leginondata.ApTomoAlignmentRunData=ApTomoAlignmentRunData

class ApSubTomogramRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginondata.SessionData),
			('pick', ApSelectionRunData),
			('stack', ApStackData),
			('runname', str),
			('bin', int),
		)
	typemap = classmethod(typemap)
leginondata.ApSubTomogramRunData=ApSubTomogramRunData

class ApFullTomogramData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginondata.SessionData),
			('tiltseries', leginondata.TiltSeriesData),
			('alignment', ApTomoAlignmentRunData),
			('combined', list),
			('path', ApPathData),
			('name', str),
			('description', str),
			('zprojection', leginondata.AcquisitionImageData),
		)
	typemap = classmethod(typemap)
leginondata.ApFullTomogramData=ApFullTomogramData

class ApTomogramData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginondata.SessionData),
			('tiltseries', leginondata.TiltSeriesData),
			('fulltomogram', ApFullTomogramData),
			('subtomorun', ApSubTomogramRunData),
			('path', ApPathData),
			('center', ApParticleData),
			('offsetz', int),
			('dimension', dict),
			('name', str),
			('number', int),
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
			('original density', Ap3dDensityData),
			('original model', ApInitialModelData),
		)
	typemap = classmethod(typemap)
leginondata.ApInitialModelData=ApInitialModelData

class Ap3dDensityData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('boxsize', int),
			('mask', int),
			('imask', int),
			('pixelsize', float),
			('lowpass', float),
			('highpass', float),
			('maxfilt', float),
			('resolution', float),
			('rmeasure', float),
			('handflip', bool),
			('norm', bool),
			('invert', bool),
			('hidden', bool),
			('md5sum', str),
			('pdbid', str),
			('emdbid', str),
			('eman', str),
			('description', str),
			('ampName', str),
			('path', ApPathData),
			('ampPath', ApPathData),
			('symmetry', ApSymmetryData),
			('iterid', ApRefinementData),
			('rctrun', ApRctRunData),
			('session', leginondata.SessionData),
		)
	typemap = classmethod(typemap)
leginondata.Ap3dDensityData=Ap3dDensityData

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
			('EMAN_filt3d', int),
			('EMAN_shrink', int),
			('EMAN_euler2', int),
			('EMAN_xfiles', float),
			('EMAN_median', bool),
			('EMAN_phasecls', bool),
			('EMAN_fscls', bool),
			('EMAN_refine', bool),
			('EMAN_goodbad', bool),
			('EMAN_perturb', bool),
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
			('type', str),
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
			('shiftx', float),
			('shifty', float),
			('euler1', float),
			('euler2', float),
			('euler3', float),
			('quality_factor', float),
			('mirror', bool),
			('thrown_out',bool),
			('msgp_keep',bool),
			('coran_keep',bool),
			('euler_convention', str),
		)
	typemap = classmethod(typemap)
leginondata.ApParticleClassificationData=ApParticleClassificationData

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
leginondata.ApEulerJumpData=ApEulerJumpData

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
			('ctftilt_params', ApCtfTiltParamsData),
			('ace2_params', ApAce2ParamsData),
			('session', leginondata.SessionData),
			('path', ApPathData),
			('name', str),
			('hidden', bool),
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


class ApAce2ParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('bin', int),
			('reprocess', float),
			('cs', float),
			('stig', bool),
		)
	typemap = classmethod(typemap)
leginondata.ApAce2ParamsData=ApAce2ParamsData


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
leginondata.ApCtfTiltParamsData=ApCtfTiltParamsData

class ApCtfData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('acerun', ApAceRunData),
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
			('cross_correlation', float),
			('ctfvalues_file', str),
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

class ApRctRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('classnums', str),
			('numiter', int),
			('maskrad', int),
			('lowpassvol', float),
			('highpasspart', float),
			('median', int),
			('description', str),
			('numpart', int),
			('hidden', bool),
			('fsc_resolution', ApResolutionData),
			('rmeasure_resolution', ApResolutionData),
			('path', ApPathData),
			('tiltstack', ApStackData),
			('alignstack', ApAlignStackData),
			('clusterstack', ApClusteringStackData),
		)
	typemap = classmethod(typemap)
	
class ApOtrRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('classnum', int),
			('classnums', str),
			('numiter', int),
			('maskrad', int),
			('lowpassvol', float),
			('highpasspart', float),
			('description', str),
			('path', ApPathData),
			('tiltstack', ApStackData),
			('norefclass', ApNoRefClassRunData),
		)
	typemap = classmethod(typemap)

class ApImagicReclassifyData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('project|projects|project', int),
			('runname', str),
			('norefclass', ApNoRefClassRunData),
			('lowpass', float),
			('highpass', float),
			('maskradius', float),
			('maskdropoff', float),
			('numiter', int),
			('numaverages', int),
			('description', str),
			('path', ApPathData),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class ApImagic3d0Data(Data):
	def typemap(cls):
		return Data.typemap() + (
			('project|projects|project', int),
			('name', str),
			('runname', str),
			('norefclass', ApNoRefClassRunData),
			('reclass', ApImagicReclassifyData),
			('clusterclass', ApClusteringStackData),
			('templatestack', ApTemplateStackData),
			#('imagicclusterclass', ApClusteringStackData),
			('boxsize', int),
			('pixelsize', float),
			('symmetry', ApSymmetryData),
			('projections', str),
			('euler_ang_inc', int),
			('numpart', int),
			('num_classums', int),
			('ham_win', float),
			('obj_size', float),
			('repalignments', int),
			('amask_dim', float),
			('amask_lp', float),
			('amask_sharp', float),
			('amask_thresh', float),
			('mra_ang_inc', int),
			('forw_ang_inc', int),
			('description', str),
			('path', ApPathData),
			('hidden', bool),
			('density', Ap3dDensityData),
		)
	typemap = classmethod(typemap)

class ApImagic3dRefineRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('project|projects|project', int),
			('runname', str),
			('norefclass', ApNoRefClassRunData),
			('clusterclass', ApClusteringStackData),
			('imagic3d0run', ApImagic3d0Data),
			('templatestack', ApTemplateStackData),
			('boxsize', int),
			('pixelsize', float),
			('description', str),
			('path', ApPathData),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class ApImagic3dRefineIterationData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refinement_run', ApImagic3dRefineRunData),
			('iteration', int),
			('name', str),
			('symmetry', ApSymmetryData),
			('max_shift_orig', float),
			('max_shift_this', float),
			('sampling_parameter', int),
			('euler_ang_inc', int),
			('num_classums', int),
			('ham_win', float),
			('obj_size', float),
			('repalignments', int),
			('amask_dim', float),
			('amask_lp', float),
			('amask_sharp', float),
			('amask_thresh', float),
			('mra_ang_inc', int),
			('forw_ang_inc', int),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class ApImagicNoRefRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('mask_radius', float),
			('mask_dropoff', float),
			('numiters', int),
			('overcorrection', float),
			('MSAmethod', str),
		)
	typemap = classmethod(typemap)

