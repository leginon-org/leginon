# COPYRIGHT:
# The Leginon software is Copyright 2003
# The Scripps Research Institute, La Jolla, CA
# For terms of the license agreement
# see http://ami.scripps.edu/software/leginon-license

import sinedon.data
import leginon.leginondata
Data = sinedon.data.Data

### START Job tracking tables ###
class ApPathData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('path', str),
		)
	typemap = classmethod(typemap)

class ScriptProgramRun(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('revision', str),
			('progname', ScriptProgramName),
			('username', ScriptUserName),
			('hostname', ScriptHostName),
			('rundir', ApPathData),
			('job', ApAppionJobData),
			('appion_path', ApPathData),
			('unixshell', str),
		)
	typemap = classmethod(typemap)

class ScriptProgramName(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
		)
	typemap = classmethod(typemap)

class ScriptParamName(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('progname', ScriptProgramName),
		)
	typemap = classmethod(typemap)

class ScriptParamValue(Data):
	def typemap(cls):
		return Data.typemap() + (
			('value', str),
			('usage', str),
			('paramname', ScriptParamName),
			('progrun', ScriptProgramRun),
		)
	typemap = classmethod(typemap)

class ScriptUserName(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('uid', int),
			('gid', int),
			('fullname', str),
		)
	typemap = classmethod(typemap)

class ScriptHostName(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('ip', str),
			('system', str),
			('distro', str),
			('arch', str),
			('nproc', int),
			('memory', int),
			('cpu_vendor', str),
			('gpu_vendor', str),
		)
	typemap = classmethod(typemap)

class ApAppionJobData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('cluster', str),
			('jobtype', str),
			('status', str),
			('user', str),
			('clusterjobid', int),
			('path', ApPathData),
			('session', leginon.leginondata.SessionData),
			('dmfpath', ApPathData),
			('clusterpath', ApPathData),

		)
	typemap = classmethod(typemap)

### END Job tracking tables ###
### START Particle selection tables ###

class ApParticleData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('selectionrun', ApSelectionRunData),
			('image', leginon.leginondata.AcquisitionImageData),
			('xcoord', int),
			('ycoord', int), 	
			('angle', float),
			('correlation', float),
			('template', ApTemplateImageData),
			('peakmoment', float),
			('peakstddev', float),
			('peakarea', int),
			('diameter', float),
			('label', str),
			('helixnum', int),
		)
	typemap = classmethod(typemap)

class ApSelectionRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('hidden', bool),
			('path', ApPathData),
			('session', leginon.leginondata.SessionData),
			('description', str),
			('params', ApSelectionParamsData),
			('dogparams', ApDogParamsData),
			('manparams', ApManualParamsData),
			('tiltparams', ApTiltAlignParamsData),
		)
	typemap = classmethod(typemap)

class ApSelectionParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('diam', int),
			('bin', int),
			('manual_thresh', float),
			# ('auto_thresh', int),
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
			('trace', bool),
			('helicalstep', int),
			('tomocenter', bool),
		)
	typemap = classmethod(typemap)

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

class ApContourData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('image', leginon.leginondata.AcquisitionImageData),
			('x', float),
			('y', float),
			('version', int),
			('method', str),
			('particleType', str),
			('runname', str),
			('selectionrun', ApSelectionRunData),
		)
	typemap = classmethod(typemap)

class ApContourPointData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('contour', ApContourData),
			('x', float),
			('y', float),
		)
	typemap = classmethod(typemap)

class ApSizingRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('path', ApPathData),
			('method', str),
			('tracerun', ApSelectionRunData),
		)
	typemap = classmethod(typemap)

### END Particle selection tables ###
### START Template tables ###

class ApTemplateImageData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('REF|projectdata|projects|project', int),
			('path', ApPathData),
			('templatename', str),
			('apix', float),
			('diam', int),
			('description', str),
			('md5sum', str),
			('stack', ApStackData),
			('alignstack', ApAlignStackData),
			('clusterstack', ApClusteringStackData),
			('stack_image_number', int),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

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

class ApTemplateStackData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('clusterstack', ApClusteringStackData),
			('alignstack', ApAlignStackData),
			('templatename', str),
			('cls_avgs', bool),
			('forward_proj', bool),
			('origfile', str),
			('description', str),
			('session', leginon.leginondata.SessionData),
			('apix', float),
			('boxsize', int),
			('numimages', int),
			('hidden', bool),
			('path', ApPathData),
			('REF|projectdata|projects|project', int),
		)
	typemap = classmethod(typemap)

### END Template tables ###
### START Transformation/shift tables ###

class ApImageTransformationData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('image1', leginon.leginondata.AcquisitionImageData),
			('image2', leginon.leginondata.AcquisitionImageData),
			('shiftx', float),
			('shifty', float),
			('correlation', float),
			('scale', float),
		)
	typemap = classmethod(typemap)

class ApImageTiltTransformData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('image1', leginon.leginondata.AcquisitionImageData),
			('image1_x', float),
			('image1_y', float),
			('image1_rotation', float),
			('image2', leginon.leginondata.AcquisitionImageData),
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

class ApTiltParticlePairData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('particle1', ApParticleData),
			('particle2', ApParticleData),
			('transform', ApImageTiltTransformData),
			('error', float),
		)
	typemap = classmethod(typemap)

### END Transformation/shift tables ###
### START CTF tables ###

class ApAceRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('aceparams', ApAceParamsData),
			('ctftilt_params', ApCtfTiltParamsData),
			('xmipp_ctf_params', ApXmippCtfParamsData),
			('ace2_params', ApAce2ParamsData),
			('ctffind4_params', ApCtfFind4ParamsData),
			('session', leginon.leginondata.SessionData),
			('path', ApPathData),
			('name', str),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

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

class ApAce2ParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('bin', int),
			('reprocess', float),
			('cs', float),
			('stig', bool),
			('min_defocus', float),
			('max_defocus', float),
			('edge_thresh', float),
			('edge_blur', float),
			('rot_blur', float),
			('refine2d', bool),
			('onepass', float),
			('zeropass', float),
		)
	typemap = classmethod(typemap)

class ApXmippCtfParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('fieldsize', int),
		)
	typemap = classmethod(typemap)


class ApCtfTiltParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('medium', str),
			('ampcarbon', float),
			('ampice', float),
			('fieldsize', int),
			('cs', float),
			('bin', int),
			('resmin', float),
			('resmax', float),
			('defstep', float),
			('dast', float),
		)
	typemap = classmethod(typemap)

class ApCtfFind4ParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('bestdb', bool),
			('ampcontrast', float),
			('fieldsize', int),
			('cs', float),
			('resmin', float),
			('defstep', float),
		)
	typemap = classmethod(typemap)

class ApCtfData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('acerun', ApAceRunData),
			('image', leginon.leginondata.AcquisitionImageData),
			('cs', float),  # in millimeters
			('defocusinit', float),  # initial defocus
			('amplitude_contrast', float),  # sqrt(1-A^2)sin + A*cos format
			('defocus1', float),  # in negative meters for underfocus |def1| < |def2|
			('defocus2', float),  # in negative meters for underfocus
			('angle_astigmatism', float),  # in counter-clockwise degrees from x-axis
			('ctffind4_resolution', float),  # in counter-clockwise degrees from x-axis			
			('confidence', float),  # classic confidence
			('confidence_d', float),  # classic confidence
			('confidence_30_10', float),  # defined as confidence between 1/30 and 1/10 Angstroms
			('confidence_5_peak', float),  # defined as conidence of the first 5 peaks of the CTF
			('overfocus_conf_30_10', float),  # defined as confidence between 1/30 and 1/10 Angstroms
			('overfocus_conf_5_peak', float),  # defined as conidence of the first 5 peaks of the CTF
			('resolution_80_percent', float),  # resolution at 80% confidence
			('resolution_50_percent', float),  # resolution at 50% confidence
			('graph1', str),  # 2d powerspectra
			('graph2', str),  # 1d plot showing fit
			('graph3', str),  # raw native powerspectra from software 
			('graph4', str),  # raw native 1d plot from software 
			('ctfvalues_file', str),  # used for ace2correct
			('cross_correlation', float),  # direct from ctffind/ctftilt
			('tilt_angle', float),  # from ctftilt
			('tilt_axis_angle', float),  # from ctftilt
			('mat_file', str),  # from ACE1
		)
	typemap = classmethod(typemap)

### END CTF tables ###
### START Mask tables ###

class ApMaskMakerRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('params', ApMaskMakerParamsData),
			('session', leginon.leginondata.SessionData),
			('name', str),
			# ('path', str),
			('path', ApPathData),
		)
	typemap = classmethod(typemap)

class ApMaskRegionData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('maskrun', ApMaskMakerRunData),
			('image', leginon.leginondata.AcquisitionImageData),
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
			('mask_type', str),
			('pdiam', int),
			('region_diameter', int),
			('edge_blur', float),
			('edge_low', float),
			('edge_high', float),
			('region_std', float),
			('convolve', float),
			('convex_hull', bool),
			('libcv', bool),
		)
	typemap = classmethod(typemap)

### END Mask tables ###
### START Stack tables ###

class ApStackData(Data):
	def typemap(cls):
		return Data.typemap() + (
			# ('stackPath', str),
			('path', ApPathData),
			('name', str),
			('description', str),
			('hidden', bool),
			('oldstack', ApStackData),
			('substackname', str),
			('pixelsize', float),
			('centered', bool),
			('junksorted', bool),
			('beamtilt_corrected', bool),
			('mask', int),
			('maxshift', int),
			('boxsize', int),
		)
	typemap = classmethod(typemap)

class ApRunsInStackData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('stack', ApStackData),
			('stackRun', ApStackRunData),
		)
	typemap = classmethod(typemap)

class ApStackRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('stackRunName', str),
			('stackParams', ApStackParamsData),
			('syntheticStackParams', ApSyntheticStackParamsData),
			('selectionrun', ApSelectionRunData),
			('session', leginon.leginondata.SessionData),
		)
	typemap = classmethod(typemap)

class ApSyncStackData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('stack1', ApStackData),
			('stack2', ApStackData),
			('synctype', str),
		)
	typemap = classmethod(typemap)

class ApParticleExtractorData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('boxSize', int),
			('bin', int),
			('aceCutoff', float),
			('correlationMin', float),
			('correlationMax', float),
			('checkMask', str),
			('checkImage', bool),
			('norejects', bool),
			('minDefocus', float),
			('maxDefocus', float),
			('defocpair', bool),
			('tiltangle', str),
			('rotate', bool),
		)
	typemap = classmethod(typemap)

class ApStackParamsData(ApParticleExtractorData):
	def typemap(cls):
		return ApParticleExtractorData.typemap() + (
			('phaseFlipped', bool),
			('fliptype', str),
			('fileType', str),
			('inverted', bool),
			('normalized', bool),
			('normalizemethod', str),
			('lowpass', float),
			('highpass', float),
			('pixlimit', float),
			('startframe', int),
			('nframe', int),
			('driftlimit', float),
		)
	typemap = classmethod(typemap)

class ApSyntheticStackParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('modelid', ApInitialModelData),
			('boxsize', int),
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

class ApStackParticleData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('particleNumber', int),
			('stack', ApStackData),
			('stackRun', ApStackRunData),
			('particle', ApParticleData),
			('mean', float),
			('stdev', float),
			('min', float),
			('max', float),
			('skew', float),
			('kurtosis', float),
			('edgemean', float),
			('edgestdev', float),
			('centermean', float),
			('centerstdev', float),
		)
	typemap = classmethod(typemap)

class ApStackImageFrameListData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('stack', ApStackData),
			('image', leginon.leginondata.AcquisitionImageData),
			('frames', list),
		)
	typemap = classmethod(typemap)

class ApStackFormatData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('stack', ApStackData),
			('eman', ApPathData),
			('spider', ApPathData),
			('xmipp', ApPathData),
			('frealign', ApPathData),
		)
	typemap = classmethod(typemap)

class ApParticleMovieRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('movieRunName', str),
			('movieParams', ApParticleMovieParamsData),
			('selectionrun', ApSelectionRunData),
			('session', leginon.leginondata.SessionData),
			('path', ApPathData),
		)
	typemap = classmethod(typemap)


class ApParticleMovieParamsData(ApParticleExtractorData):
	def typemap(cls):
		return ApParticleExtractorData.typemap() + (
			('frameavg', int),
			('framestep', int),
		)
	typemap = classmethod(typemap)

class ApParticleMovieData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('movieNumber', int),
			('movieRun', ApParticleMovieRunData),
			('particle', ApParticleData),
			('format', str),
		)
	typemap = classmethod(typemap)

class ApDDStackRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('params', ApDDStackParamsData),
			('session', leginon.leginondata.SessionData),
			('path', ApPathData),
		)
	typemap = classmethod(typemap)

class ApDDStackParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('preset', str),
			('align', bool),
			('bin', int),
			('unaligned_ddstackrun', ApDDStackRunData),
			('stack', ApStackData),
			('method', str),
			('de_aligner', ApDEAlignerParamsData),
		)
	typemap = classmethod(typemap)

class ApDDAlignImagePairData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('source', leginon.leginondata.AcquisitionImageData),
			('result', leginon.leginondata.AcquisitionImageData),
			('ddstackrun', ApDDStackRunData),
		)
	typemap = classmethod(typemap)

class ApDEAlignerParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('alignment_correct', bool),
			('alignment_quanta', int),
			('radiationdamage_compensate', bool),
			('radiationdamage_multiplier', float),
			('output_sumranges', str)
		)
	typemap = classmethod(typemap)

### END Stack tables ###
### START alignment tables  ###

class ApMaxLikeJobData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('timestamp', str),
			('path', ApPathData),
			('REF|projectdata|projects|project', int),
			('finished', bool),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class ApMaxLikeRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('mirror', bool),
			('student', bool),
			('mask_diam', int),
			('init_method', str),
			('fast', bool),
			('fastmode', str),
			('run_seconds', int),
			('job', ApMaxLikeJobData),
		)
	typemap = classmethod(typemap)

class ApSparxISACJobData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('timestamp', str),
			('path', ApPathData),
			('REF|projectdata|projects|project', int),
			('finished', bool),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class ApSparxISACRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('job', ApSparxISACJobData),
			('alignstackid', ApAlignStackData),
		)
	typemap = classmethod(typemap)

class ApCL2DRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('fast', str),
			('run_seconds', int),
			('timestamp', str),
			('REF|projectdata|projects|project', int),
			('path', ApPathData),
			('finished', bool),
			('max-iter', int),
			('num-ref', int),
			('correlation', bool),
			('correntropy', bool),
			('classical_multiref', bool),
			('intracluster_multiref', bool),
		)
	typemap = classmethod(typemap)

class ApXMIPP3CL2DRunData(Data):  # need to work on this
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('run_seconds', int),
			('timestamp', str),
			('REF|projectdata|projects|project', int),
			('path', ApPathData),
			('finished', bool),
			('max-iter', int),
			('num-ref', int),
			('correlation', bool),
			('correntropy', bool),
			('classical_multiref', bool),
			('intracluster_multiref', bool),
		)
	typemap = classmethod(typemap)
	
class ApSIMPLEClusterRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('run_seconds', int),
			('timestamp', str),
			('REF|projectdata|projects|project', int),
			('path', ApPathData),
			('finished', bool),
			('max-iter', int),
			('num-ref', int),
			('kmeans', bool),
			('center', bool),
		)
	typemap = classmethod(typemap)

class ApSIMPLEOrigamiRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('path', ApPathData),
			('REF|projectdata|projects|project', int),
			('timestamp', str),
			('simple_params', ApSIMPLEOrigamiParamsData),
			('stack', ApStackData),
			('alignstack', ApAlignStackData),
			('clusteringstack', ApClusteringStackData),
			('box', int),
			('apix', float),
			('description', str),
		)
	typemap = classmethod(typemap)

class ApSIMPLEOrigamiParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
# 			('runname', str),
# 			('timestamp', str),
# 			('REF|projectdata|projects|project', int),
# 			('path', ApPathData),
# 			('box', int),
# 			('apix', float),
# 			('stack', ApStackData),
# 			('alignstack', ApAlignStackData),
			('lp', int),
			('hp', int),
			('froms', int),
			('tos', int),
			('maxits', int),
			('msk', int),
			('mw', int),
			('amsklp', int),
			('edge', int),
			('trs', int),
			('pgrp', str),
		)
	typemap = classmethod(typemap)

class ApTopolRepJobData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('timestamp', str),
			('path', ApPathData),
			('REF|projectdata|projects|project', int),
			('finished', bool),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class ApTopolRepRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('mask', int),
			('itermult', float),
			('learn', float),
			('ilearn', float),
			('age', int),
			('mramethod', str),
			('job', ApTopolRepJobData),
		)
	typemap = classmethod(typemap)

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

class ApEdIterRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('radius', int),
			('num_iter', int),
			('freealigns', int),
			('invert_templs', bool),
			('num_templs', int),
			('run_seconds', int),
		)
	typemap = classmethod(typemap)

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

class ApEMANRefine2dRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('num_iters', int),
			('num_classes', int),
			('run_seconds', int),
		)
	typemap = classmethod(typemap)

class ApMultiRefAlignRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('lowpass_refs', int),
			('thresh_refs', int),
			('maskrad_refs', float),
			('mirror', bool),
			('center', bool),
			('alignment_type', str),
			('first_alignment', str),
			('num_orientations', int),
			('max_shift_orig', float),
			('max_shift_this', float),
			('samp_param', float),
			('min_radius', float),
			('max_radius', float),
			('numiter', int),
		)
	typemap = classmethod(typemap)

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
			('isacrun', ApSparxISACRunData),
			('refine2drun', ApEMANRefine2dRunData),
			('imagicMRA', ApMultiRefAlignRunData),
			('editerrun', ApEdIterRunData),
			('topreprun', ApTopolRepRunData),
			('cl2drun', ApCL2DRunData),
			('xmipp3cl2drun', ApXMIPP3CL2DRunData),			
			('simplerun', ApSIMPLEClusterRunData),
			('hidden', bool),
			('path', ApPathData),
		)
	typemap = classmethod(typemap)

class ApAlignStackData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('imagicfile', str),
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
		)
	typemap = classmethod(typemap)

class ApAlignParticleData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('partnum', int),
			('alignstack', ApAlignStackData),
			('stackpart', ApStackParticleData),
			('xshift', float),
			('yshift', float),
			('rotation', float),
			('mirror', bool),
			('spread', float),
			('correlation', float),
			('score', float),
			('ref', ApAlignReferenceData),
			('bad', bool),
		)
	typemap = classmethod(typemap)

class ApAlignReferenceData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refnum', int),
			('iteration', int),
			('mrcfile', str),
			('varmrcfile', str),
			('imagicfile', str),
			('isac_generation', int),			
			('ssnr_resolution', float),
			('alignrun', ApAlignRunData),
			('path', ApPathData),
			('template', ApTemplateImageData),
			('templatestack', ApTemplateStackData),
		)
	typemap = classmethod(typemap)

### END alignment tables  ###
### START classification tables  ###

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
		)
	typemap = classmethod(typemap)

class ApCoranRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('mask_diam', float),
			('run_seconds', int),
			('num_factors', int),
		)
	typemap = classmethod(typemap)

class ApCoranEigenImageData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('coranRun', ApCoranRunData),
			('factor_num', int),
			('percent_contrib', float),
			('image_name', str),
			('path', ApPathData),
		)
	typemap = classmethod(typemap)

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
			('MSAdistance', str),
			('eigenimages', str),
		)
	typemap = classmethod(typemap)

class ApSpiderClusteringParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('factor_list', str),
			('method', str),
		)
	typemap = classmethod(typemap)

class ApAffinityPropagationClusterParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('mask_diam', float),
			('preference_type', str),
			('run_seconds', int),
		)
	typemap = classmethod(typemap)

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

class ApRotKerDenSOMParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('mask_diam', float),
			('x_dimension', int),
			('y_dimension', int),
			('convergence', str),
			('run_seconds', int),
			('initregulfact', float),
			('finalregulfact', float),
			('incrementregulfact', int),
			('spectrainnerradius', int),
			('spectraouterradius', int),
			('spectralowharmonic', int),
			('spectrahighharmonic', int),
		)
	typemap = classmethod(typemap)

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
			('rotkerdenparams', ApRotKerDenSOMParamsData),
			('affpropparams', ApAffinityPropagationClusterParamsData),
			('cl2dparams', ApCL2DRunData),
			('xmipp3cl2drun', ApXMIPP3CL2DRunData),						
			('simpleparams', ApSIMPLEClusterRunData),
		)
	typemap = classmethod(typemap)

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
			('num_factors', int),
		)
	typemap = classmethod(typemap)

class ApClusteringParticleData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('partnum', int),
			('refnum', int),
			('clusterreference', ApClusteringReferenceData),
			('clusterstack', ApClusteringStackData),
			('alignparticle', ApAlignParticleData),
			('imagic_cls_quality', float),
		)
	typemap = classmethod(typemap)

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

### END classification tables  ###
### START 3d Volume tables ###

class ApInitialModelData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('REF|projectdata|projects|project', int),
			('path', ApPathData),
			('name', str),
			('resolution', float),
			('symmetry', ApSymmetryData),
			('pixelsize', float),
			('boxsize', int),
			('description', str),
			('hidden', bool),
			('md5sum', str),
			('mass', int),
			('original_density', Ap3dDensityData),
			('original_model', ApInitialModelData),
		)
	typemap = classmethod(typemap)

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
			('refineIter', ApRefineIterData),
			('hipIter', ApHipIterData),
			('rctrun', ApRctRunData),
			('otrrun', ApOtrRunData),
			('session', leginon.leginondata.SessionData),
			('hard', int),
			('sigma', float),
			('maxjump', float),
			('mass', int),
		)
	typemap = classmethod(typemap)

class ApSymmetryData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('eman_name', str),
			('fold_symmetry', int),
			('symmetry', str),
			('description', str),
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
			('lowpasspart', float),
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
			('classnums', str),
			('numiter', int),
			('euleriter', int),
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

### END 3d Volume tables ###
### START Reconstruction tables ###

# ## generic multi-model refine table for all multi-model jobs
class ApMultiModelRefineRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('num_refinements', int),
			('REF|projectdata|projects|project', int),
			('session', leginon.leginondata.SessionData),
		)
	typemap = classmethod(typemap)	

# ## this one is for all iterations
# ## generic refine table
class ApRefineRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('package', str),
			('description', str),
			('num_iter', int),
			('hidden', bool),
			('reference_number', int),
			('stack', ApStackData),
			('initialModel', ApInitialModelData),
			('path', ApPathData),
			('job', ApAppionJobData),
			('multiModelRefineRun', ApMultiModelRefineRunData),
		)
	typemap = classmethod(typemap)

# ## this one is for each iteration
# ## generic refine table
class ApRefineIterData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('iteration', int),
			('exemplar', bool),
			('angularSamplingRate', int),
			('mask', int),
			('imask', int),
			('alignmentInnerRadius', int),
			('alignmentOuterRadius', int),
			('volumeDensity', str),
			('refineClassAverages', str),
			('postRefineClassAverages', str),
			('classVariance', str),
			('symmetry', ApSymmetryData),
			('refineRun', ApRefineRunData),
			('resolution', ApResolutionData),
			('rMeasure', ApRMeasureData),
			# ## additional packages plugin here
			('emanParams', ApEmanRefineIterData),
			('xmippParams', ApXmippRefineIterData),
			('frealignParams', ApFrealignIterData),
			('xmippML3DParams', ApXmippML3DRefineIterData),
			('relionParams', ApRelionIterData),
		)
	typemap = classmethod(typemap)
	
# ## this one is for each iteration, generic reference table
class ApRefineReferenceData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('volumeDensityStart', str),
			('volumeDensityEnd', str),
			('reference_number', int),
			('path', ApPathData),
			('iteration', ApRefineIterData),
		)
	typemap = classmethod(typemap)

# ## this one is for each particle each iteration
class ApRefineParticleData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refineIter', ApRefineIterData),
			('multiModelRefineRun', ApMultiModelRefineRunData),
			('reference_number', ApRefineReferenceData),
			('particle', ApStackParticleData),
			('shiftx', float),
			('shifty', float),
			('euler1', float),
			('euler2', float),
			('euler3', float),
			('quality_factor', float),
			('phase_residual', float),
			('mirror', bool),
			('3Dref_num', int),
			('2Dclass_num', int),
			('refine_keep', bool),
			('postRefine_keep', bool),
			('euler_convention', str),
		)
	typemap = classmethod(typemap)

# ## this one is for each iteration
# ## EMAN only things
class ApEmanRefineIterData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('package', str),
			('ang', float),
			('lpfilter', int),
			('hpfilter', int),
			('mask', int),
			('imask', int),
			('pad', int),
			('EMAN_maxshift', int),
			('EMAN_hard', int),
			('EMAN_classkeep', float),
			('EMAN_classiter', int),
			('EMAN_filt3d', int),
			('EMAN_shrink', int),
			('EMAN_euler2', int),
			('EMAN_xfiles', float),
			('EMAN_amask1', float),
			('EMAN_amask2', float),
			('EMAN_amask3', float),
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

# ## this one is for all iterations
class ApRefineStackData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('preprefine', ApPrepRefineData),
			('stackref', ApStackData),
			('filename', str),
			('bin', int),
			('lowpass', float),
			('highpass', float),
			('last_part', int),
			('format', str),
			('apix', float),
			('boxsize', int),
			('cs', float),
			('recon', bool),
			('phaseflipped', bool),
		)
	typemap = classmethod(typemap)

class ApRefineInitModelData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('preprefine', ApPrepRefineData),
			('refmodel', ApInitialModelData),
			('filename', str),
			('format', str),
			('apix', float),
		)
	typemap = classmethod(typemap)

class ApRefineMaskVolData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('preprefine', ApPrepRefineData),
			('refmodel', ApInitialModelData),
			('filename', str),
			('format', str),
			('apix', float),
		)
	typemap = classmethod(typemap)

class ApPrepRefineData(Data):
	def typemap(cls):
		return Data.typemap() + (
		('name', str),
		('hidden', bool),
		('path', ApPathData),
		('stack', ApStackData),
		('job', ApAppionJobData),
		('session', leginon.leginondata.SessionData),
		('method', str),
		('description', str),
		('paramiter', ApRefineIterData),
		)
	typemap = classmethod(typemap)

class ApFrealignPrepareData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('name', str),
			('ppn', int),
			('rpn', int),
			('nodes', int),
			('memory', int),
			('hidden', bool),
			('tarfile', str),
			('symmetry', ApSymmetryData),
			('path', ApPathData),
			('stack', ApStackData),
			('reconstack', ApStackData),
			('model', ApInitialModelData),
			('job', ApAppionJobData),
			('refineIter', ApRefineIterData),
		)
	typemap = classmethod(typemap)

# ## this one is for each iteration in Frealign refinement
class ApFrealignIterData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('iflag', int),
			('wgh', float),
			('xstd', float),
			('pbc', float),
			('boff', float),
			('itmax', int),
			('ipmax', int),
			('target', float),
			('thresh', float),
			('cs', float),
			('rrec', float),
			('highpass', float),
			('lowpass', float),
			('rbfact', float),
		)
	typemap = classmethod(typemap)

# ## this one is for each iteration in Relion refinement
class ApRelionIterData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('ini_high', int),
			('ctf', bool),
			('offset_step', int),
			('auto_local_healpix_order', int),
			('healpix_order', int),
			('offset_range', int),
			('ctf_intact_first_peak', bool),
			('ctf_corrected_ref', bool),
		)
	typemap = classmethod(typemap)

# ## this one is for each iteration in Xmipp projection-matching refinement
class ApXmippRefineIterData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('NumberofIterations', int),
			('MaskFileName', str),
			('MaskRadius', int),
			('InnerRadius', int),
			('OuterRadius', int),
			('SymmetryGroup', str),
			('FourierMaxFrequencyOfInterest', float),
			('SelFileName', str),
			('DocFileName', str),
			('ReferenceFileName', str),
			('WorkingDir', str),
			('CleanUpFiles', bool),
			('DoCtfCorrection', bool),
			('CTFDatName', str),
			('DoAutoCtfGroup', bool),
			('CtfGroupMaxDiff', float),
			('CtfGroupMaxResol', float),
			('PaddingFactor', float),
			('WienerConstant', float),
			('DataArePhaseFlipped', bool),
			('ReferenceIsCtfCorrected', bool),
			('DoMask', bool),
			('DoSphericalMask', bool),
			('AngSamplingRateDeg', float),
			('MaxChangeInAngles', float),
			('PerturbProjectionDirections', bool),
			('MaxChangeOffset', float),
			('Search5DShift', int),
			('Search5DStep', int),
			('DoRetricSearchbyTiltAngle', bool),
			('Tilt0', float),
			('TiltF', float),
			('SymmetryGroupNeighbourhood', str),
			('OnlyWinner', bool),
			('MinimumCrossCorrelation', float),
			('DiscardPercentage', float),
			('ProjMatchingExtra', str),
			('DoAlign2D', bool),
			('Align2DIterNr', int),
			('Align2dMaxChangeOffset', float),
			('Align2dMaxChangeRot', float),
			('ReconstructionMethod', str),
			('ARTLambda', float),
			('ARTReconstructionExtraCommand', str),
			('WBPReconstructionExtraCommand', str),
			('FourierReconstructionExtraCommand', str),
			('ResolSam', float),
			('ConstantToAddToFiltration', float),
		)
	typemap = classmethod(typemap)
	
# ## this one is for each iteration in ML3D refinement
class ApXmippML3DRefineIterData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('InSelFile', str),
			('InitialReference', str),
			('WorkingDir', str),
			('DoDeleteWorkingDir', bool),
			('DoMlf', bool),
			('DoCorrectAmplitudes', bool),
			('InCtfDatFile', str),
			('HighResLimit', float),
			('ImagesArePhaseFlipped', bool),
			('InitialMapIsAmplitudeCorrected', bool),
			('SeedsAreAmplitudeCorrected', bool),
			('DoCorrectGreyScale', bool),
			('ProjMatchSampling', int),
			('DoLowPassFilterReference', bool),
			('LowPassFilter', int),
			('PixelSize', float),
			('DoGenerateSeeds', bool),
			('NumberOfReferences', int),
			('DoJustRefine', bool),
			('SeedsSelfile', str),
			('DoML3DClassification', bool),
			('AngularSampling', int),
			('NumberOfIterations', int),
			('Symmetry', str),
			('DoNorm', bool),
			('DoFourier', bool),
			('RestartIter', bool),
			('ExtraParamsMLrefine3D', str),
		)
	typemap = classmethod(typemap)

# ## this one is for each iteration
class ApResolutionData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('fscfile', str),
			('half', float),
			('type', str),
		)
	typemap = classmethod(typemap)

# ## this one is for each iteration
class ApRMeasureData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('volume', str),
			('rMeasure', float),
		)
	typemap = classmethod(typemap)

# ## this one is for each iteration
class ApRefineGoodBadParticleData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refine', ApRefineIterData),
			('good_refine', int),
			('bad_refine', int),
			('good_postRefine', int),
			('bad_postRefine', int),
		)
	typemap = classmethod(typemap)

# ## this one is for all iterations
class ApEulerJumpData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('particle', ApStackParticleData),
			('refineRun', ApRefineRunData),
			('multiModelRefineRun', ApMultiModelRefineRunData),
			('median', float),
			('mean', float),
			('stdev', float),
			('min', float),
			('max', float),
		)
	typemap = classmethod(typemap)

class ApFSCData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('refineIter', ApRefineIterData),
			('pix', int),
			('value', float),
		)
	typemap = classmethod(typemap)

### END Reconstruction tables ###
### START Testing tables ###

class ApTestParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('bin', int),
		)
	typemap = classmethod(typemap)

class ApTestRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('params', ApTestParamsData),
			('session', leginon.leginondata.SessionData),
			('name', str),
			# ('path', str),
			('path', ApPathData),
			('append_timestamp', str),
		)
	typemap = classmethod(typemap)

class ApTestResultData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('testrun', ApTestRunData),
			('image', leginon.leginondata.AcquisitionImageData),
			('x', float),
			('y', float),
		)
	typemap = classmethod(typemap)

### END Testing tables ###
### START Assessment tables ###

class ApAssessmentRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginon.leginondata.SessionData),
			('name', str),
		)
	typemap = classmethod(typemap)

class ApAssessmentData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('assessmentrun', ApAssessmentRunData),
			('image', leginon.leginondata.AcquisitionImageData),
			('selectionkeep', int),
		)
	typemap = classmethod(typemap)

class ApMaskAssessmentRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginon.leginondata.SessionData),
			('name', str),
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

### END Assessment tables ###
### START common lines tables ###

class ApAutomatedCommonLinesRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('path', ApPathData),
			('acl_params', ApAutomatedCommonLinesParamsData),
			('pixelsize', float),
			('boxsize', int),
			('templatestackid', ApTemplateStackData),
			('clusterid', ApClusteringStackData),
			('description', str),
			('hidden', bool),
			('REF|projectdata|projects|project', int),
		)
	typemap = classmethod(typemap)

class ApAutomatedCommonLinesParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('num_averages', int),
			('num_volumes', int),
			('symmetry', ApSymmetryData),
			('num_alignment_refs', int),
			('angular_increment', int),
			('keep_ordered', int),
			('threed_lpfilt', int),
			('hamming_window', int),
			('non_weighted_sequence', bool),
			('PCA', bool),
			('numeigens', int),
			('preference_type', str),
			('prealign_avgs', bool),
			('scale', bool),
			('recalculate_volumes', bool),
		)
	typemap = classmethod(typemap)

### END common lines tables ###
### START IMAGIC tables ###

class ApImagic3dRefineRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('initialModel', ApInitialModelData),
			('stackrun', ApStackData),
			('radius', int),
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
			('filt_stack', bool),
			('hp_filt', int),
			('lp_filt', int),
			('auto_filt_stack', bool),
			('auto_lp_filt_fraction', float),
			('mask_val', int),
			('mirror_refs', bool),
			('cent_stack', bool),
			('max_shift_orig', float),
			('max_shift_this', float),
			('sampling_parameter', int),
			('minrad', int),
			('maxrad', int),
			('spider_align', bool),
			('xy_search', int),
			('xy_step', int),
			('minrad_spi', int),
			('maxrad_spi', int),
			('angle_change', int),
			('ignore_images', int),
			('num_classums', int),
			('num_factors', int),
			('ignore_members', int),
			('keep_classes', int),
			('euler_ang_inc', int),
			('keep_ordered', int),
			('ham_win', float),
			('obj_size', float),
			('3d_lpfilt', int),
			('amask_dim', float),
			('amask_lp', float),
			('amask_sharp', float),
			('amask_thresh', float),
			('mra_ang_inc', int),
			('forw_ang_inc', int),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

### END IMAGIC tables ###
### START Tomography tables ###

class ApImodXcorrParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('RotationAngle', float),
			('FilterSigma1', float),
			('FilterRadius2', float),
			('FilterSigma2', float),
		)
	typemap = classmethod(typemap)

class ApRaptorParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('markersize', int),
			('markernumber', int),
		)
	typemap = classmethod(typemap)

class ApProtomoParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('series_name', str),
		)
	typemap = classmethod(typemap)

class ApProtomoRefinementParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('protomo', ApProtomoParamsData),
			('cycle', int),
			('alismp', float),
			('alibox', dict),
			('cormod', str),
			('imgref', int),
			('reference', leginon.leginondata.AcquisitionImageData),
		)
	# ## this needs to be expanded to include all protomo2 params
	typemap = classmethod(typemap)

# ApProtomoALignerParamsData is retired
class ApProtomoAlignerParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('alignrun', ApTomoAlignmentRunData),
			('protomo', ApProtomoParamsData),
			('refine_cycle', ApProtomoRefinementParamsData),
			('good_cycle', ApProtomoRefinementParamsData),
			('good_start', int),
			('good_end', int),
			('description', str),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class ApTomoAlignerParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('alignrun', ApTomoAlignmentRunData),
			('protomo', ApProtomoParamsData),
			('refine_cycle', ApProtomoRefinementParamsData),
			('good_cycle', ApProtomoRefinementParamsData),
			('good_start', int),
			('good_end', int),
			('description', str),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class ApProtomoModelData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('aligner', ApTomoAlignerParamsData),
			('psi', float),
			('theta', float),
			('phi', float),
			('azimuth', float),
		)
	typemap = classmethod(typemap)

class ApProtomoAlignmentData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('aligner', ApTomoAlignerParamsData),
			('image', leginon.leginondata.AcquisitionImageData),
			('number', int),
			('rotation', float),
			('shift', dict),
		)
	typemap = classmethod(typemap)

class ApTiltsInAlignRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('alignrun', ApTomoAlignmentRunData),
			('tiltseries', leginon.leginondata.TiltSeriesData),
			('settings', leginon.leginondata.TomographySettingsData),
			('primary_tiltseries', bool),
		)
	typemap = classmethod(typemap)

class ApTomoAlignmentRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginon.leginondata.SessionData),
			('tiltseries', leginon.leginondata.TiltSeriesData),
			('coarseLeginonParams', leginon.leginondata.TomographySettingsData),
			('coarseImodParams', ApImodXcorrParamsData),
			('fineProtomoParams', ApProtomoParamsData),
			('raptorParams', ApRaptorParamsData),
			('bin', int),
			('name', str),
			('path', ApPathData),
			('description', str),
			('hidden', bool),
			('badAlign', bool),
		)
	typemap = classmethod(typemap)

class ApFullTomogramRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginon.leginondata.SessionData),
			('runname', str),
			('path', ApPathData),
			('method', str),
		)
	typemap = classmethod(typemap)

class ApSubTomogramRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginon.leginondata.SessionData),
			('pick', ApSelectionRunData),
			('stack', ApStackData),
			('runname', str),
			('invert', bool),
			('subbin', int),
		)
	typemap = classmethod(typemap)

class ApFullTomogramData(Data):
	# path, combined, alignrun, tiltseries should be removed from here once all
	# old data not having aligner or reconrun are converted
	def typemap(cls):
		return Data.typemap() + (
			('session', leginon.leginondata.SessionData),
			('tiltseries', leginon.leginondata.TiltSeriesData),
			('aligner', ApTomoAlignerParamsData),
			('reconrun', ApFullTomogramRunData),
			('alignrun', ApTomoAlignmentRunData),
			('combined', list),
			('thickness', int),
			('bin', int),
			('path', ApPathData),
			('name', str),
			('description', str),
			('zprojection', leginon.leginondata.AcquisitionImageData),
			('hidden', bool),
			('excluded', list),
			('reconparam', ApTomoReconParamsData),
		)
	typemap = classmethod(typemap)

class ApTomogramData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginon.leginondata.SessionData),
			('tiltseries', leginon.leginondata.TiltSeriesData),
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
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class ApTomoAverageRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('path', ApPathData),
			('stack', ApStackData),
			('subtomorun', ApSubTomogramRunData),
			('xyhalfwidth', int),
			('description', str),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class ApTomoAvgParticleData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('avgrun', ApTomoAverageRunData),
			('subtomo', ApTomogramData),
			('aligned_particle', ApAlignParticleData),
			('z_shift', float),
		)
	typemap = classmethod(typemap)

class ApTomoReconParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('tilt_angle_offset', float),
			('z_shift', float),
			('tilt_axis_tilt_out_xyplane', float),
			('tilt_axis_rotation_in_xyplane', float),
		)
	typemap = classmethod(typemap)

### END Tomography tables ###

class ApMiscData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('REF|projectdata|projects|project', int),
			('refineRun', ApRefineRunData),
			('session', leginon.leginondata.SessionData),
			('fulltomogram', ApFullTomogramData),
			('path', ApPathData),
			('name', str),
			('description', str),
			('md5sum', str),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

### Helical Image Processing Tables ###

class ApHipRunData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('runname', str),
			('path', ApPathData),
			('description', str),
			('REF|projectdata|projects|project', int),
			('session', leginon.leginondata.SessionData),
			('apix', float),
			('stack', ApStackData),
			('hidden', bool),
		)
	typemap = classmethod(typemap)

class ApHipParamsData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginon.leginondata.SessionData),
			('hipRun', ApHipRunData),
			('numpart', int),
			('replen', int),
			('diam', int),
			('diaminner', int),
			('subunits', int),
			('xlngth', int),
			('yht2', int),
			('padval', int),
			('rescut', int),
			('filval', int),
			('strong', str),
			('range', str),
			('llbo', str),
			('final_stack', str),
		)
	typemap = classmethod(typemap)

class ApHipIterData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginon.leginondata.SessionData),
			('hipRun', ApHipRunData),
			('iteration', int),
			('iterpath', str),
			('volumeDensity', str),
			('resolution', ApResolutionData),
			('rMeasure', ApRMeasureData),
			('cutfit1', str),
			('cutfit2', str),
			('cutfit3', str), 	
			('chop1', str), 	
			('chop2', str), 	
			('avglist_file', str),
			('final_numpart', int),
			('asymsu', int),
			('avg_file', str),
			('map_file', str),
			('mrc_file', str),
			('ll_file', str),
			('op_file', str),
			('output_file', str),
		)
	typemap = classmethod(typemap)

class ApHipParticleData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('session', leginon.leginondata.SessionData),
			('hipRun', ApHipRunData),
			('particleNumber', int),
			('filename', str),
			('stack', ApStackData),
			('stackRun', ApStackRunData),
			('tilt', float),
			('shift', float),
			('resid', float),
			('far_phi', float),
			('far_z', float),
			('far_rscale', float),
			('far_ampscale', float),
			('ner_phi', float),
			('ner_z', float),
			('ner_rscale', float),
			('ner_ampscale', float),
			('mrc_file', str),
			('s_file', str),
			('dft_file', str),
			('colb_file', str),
			('ner_file', str),
			('far_file', str),
			('fft_file', str),
		)
	typemap = classmethod(typemap)

class ApHelicalCoordData(Data):
	def typemap(cls):
		return Data.typemap() + (
			('image', leginon.leginondata.AcquisitionImageData),
			('filno', float),
			('xlngth', float),
			('xcoord', float),
			('ycoord', float),
			('initialang', float),
		)
	typemap = classmethod(typemap)
