#!/usr/bin/env python

import sys
from sinedon import dbupgrade

### warning dbemdata is hardcoded as leginon database

if __name__ == "__main__":
	appiondb = dbupgrade.DBUpgradeTools('appiondata', 'aptest', drop=True)

	#===================
	# rename tables:
	#===================
	### refinement tables
	appiondb.renameTable('ApRefinementData', 'ApRefineIterData')
	appiondb.renameTable('ApRefinementRunData', 'ApRefineRunData')
	appiondb.renameTable('ApParticleClassificationData', 'ApRefineParticleData')
	appiondb.renameTable('ApRefinementParamsData', 'ApEmanRefineIterData')
	### plural particles tables
	appiondb.renameTable('ApStackParticlesData', 'ApStackParticleData')
	appiondb.renameTable('ApAlignParticlesData', 'ApAlignParticleData')
	appiondb.renameTable('ApClusteringParticlesData', 'ApClusteringParticleData')

	#===================
	# rename columns:
	#===================
	### refinement tables
	appiondb.renameColumn('ApRefineIterData', 
		'REF|ApRefinementParamsData|refinementParams', 'REF|ApEmanRefineIterData|emanParams')
	appiondb.renameColumn('ApRefineIterData', 
		'REF|ApXmippRefineIterationParamsData|xmippRefineParams', 'REF|ApXmippRefineIterData|xmippParams')
	appiondb.renameColumn('ApRefineIterData', 
		'REF|ApRefinementRunData|refinementRun', 'REF|ApRefineRunData|refineRun')
	appiondb.renameColumn('ApRefineRunData', 'name', 'runname')

	#===================
	# move columns to new table
	#===================
	"""
	3 steps:
	(1) Create new column in destination table
	(2) Run update query to insert source data into destination column
	(3) Remove old column from source table
	"""
	### Symmetry, Mask, Imask
	if (appiondb.columnExists('ApEmanRefineIterData', 'REF|ApSymmetryData|symmetry')
	 and appiondb.columnExists('ApEmanRefineIterData', 'mask')
	 and appiondb.columnExists('ApEmanRefineIterData', 'imask')):
		appiondb.addColumn('ApRefineIterData', 'REF|ApSymmetryData|symmetry', appiondb.link, index=True)
		appiondb.addColumn('ApRefineIterData', 'mask', appiondb.int)
		appiondb.addColumn('ApRefineIterData', 'imask', appiondb.int)
		updateq = ("UPDATE ApRefineIterData AS refiter "
			+" LEFT JOIN ApEmanRefineIterData AS emaniter "
			+"   ON refiter.`REF|ApEmanRefineIterData|emanParams` = emaniter.`DEF_id` "
			+" SET "
			+"   refiter.`REF|ApSymmetryData|symmetry` = emaniter.`REF|ApSymmetryData|symmetry`, "
			+"   refiter.`mask` = emaniter.`mask`, "
			+"   refiter.`imask` = emaniter.`imask`, "
			+"   refiter.`DEF_timestamp` = refiter.`DEF_timestamp` "
		)
		appiondb.executeCustomSQL(updateq)
		appiondb.dropColumn('ApEmanRefineIterData', 'REF|ApSymmetryData|symmetry')
		appiondb.dropColumn('ApEmanRefineIterData', 'mask')
		appiondb.dropColumn('ApEmanRefineIterData', 'imask')

	#===================
	# merge EMAN/Coran fields
	#===================
	if appiondb.tableExists('ApRefineIterData'):
		appiondb.addColumn('ApRefineIterData', 'postRefineClassAverages', appiondb.str)
		appiondb.addColumn('ApRefineIterData', 'refineClassAverages', appiondb.str)
		updateq = ("UPDATE ApRefineIterData AS refiter "
			+" SET "
			+"   refiter.`postRefineClassAverages` = "
			+" IF(refiter.`SpiCoranGoodClassAvg` IS NOT NULL, refiter.`SpiCoranGoodClassAvg`, NULL), "
			+"   refiter.`refineClassAverages` = "
			+" IF(refiter.`emanClassAvg` IS NOT NULL, refiter.`emanClassAvg`, refiter.`classAverage`), "
			+"   refiter.`DEF_timestamp` = refiter.`DEF_timestamp` "
		)
		appiondb.executeCustomSQL(updateq)
		appiondb.dropColumn('ApRefineIterData', 'classAverage')
		appiondb.dropColumn('ApRefineIterData', 'SpiCoranGoodClassAvg')
		appiondb.dropColumn('ApRefineIterData', 'emanClassAverage')
		appiondb.dropColumn('ApRefineIterData', 'emanClassAvg')
		appiondb.dropColumn('ApRefineIterData', 'MsgPGoodClassAvg')

	if appiondb.tableExists('ApRefineParticleData'):
		appiondb.renameColumn('ApRefineParticleData', 'coran_keep', 'postRefine_keep')
		appiondb.renameColumn('ApRefineParticleData', 'thrown_out', 'refine_keep')

		### special: invert values
		if appiondb.columnExists('ApRefineParticleData', 'refine_keep'):
			updateq = ("UPDATE ApRefineParticleData AS refpart "
				+" SET "
				+"   refpart.`refine_keep` = MOD(IFNULL(refpart.`refine_keep`,0)+1,2), "
				+"   refpart.`DEF_timestamp` = refpart.`DEF_timestamp` "
			)
			appiondb.executeCustomSQL(updateq)
		if (appiondb.columnExists('ApRefineParticleData', 'postRefine_keep') 
		 and appiondb.columnExists('ApRefineParticleData', 'msgp_keep')):
			updateq = ("UPDATE ApRefineParticleData AS refpart "
				+" SET "
				+"   refpart.`postRefine_keep` = refpart.`msgp_keep`, "
				+"   refpart.`DEF_timestamp` = refpart.`DEF_timestamp` "
				+" WHERE "
				+"   refpart.`postRefine_keep` IS NULL AND refpart.`msgp_keep` IS NOT NULL "
			)
			appiondb.executeCustomSQL(updateq)
		appiondb.dropColumn('ApRefineParticleData', 'msgp_keep')
		appiondb.indexColumn('ApRefineParticleData', 'refine_keep')
		appiondb.indexColumn('ApRefineParticleData', 'postRefine_keep')

	#===================
	# add new columns calculated from old data
	#===================
	### count number of iterations
	if appiondb.addColumn('ApRefineRunData', 'num_iter', appiondb.int, index=True):
		"""
		selectq = ("SELECT refrun.`DEF_id`, COUNT(refiter.`DEF_id`) FROM ApRefineRunData AS refrun "
			+" LEFT JOIN ApRefineIterData AS refiter "
			+"   ON refiter.`REF|ApRefineRunData|refineRun` = refrun.`DEF_id` "
			+" GROUP BY refrun.`DEF_id` "
		)
		print appiondb.returnCustomSQL(selectq)
		"""
		updateq = ("UPDATE ApRefineRunData AS refrun "
			+" SET "
			+"   refrun.`num_iter` =  "
			+"(SELECT COUNT(refiter.`DEF_id`) AS numiter "
			+" FROM ApRefineIterData AS refiter "
			+" WHERE refiter.`REF|ApRefineRunData|refineRun` = refrun.`DEF_id`), "
			+"   refrun.`DEF_timestamp` = refrun.`DEF_timestamp` "
		)
		appiondb.executeCustomSQL(updateq)

	### get boxsize
	if appiondb.addColumn('ApStackData', 'boxsize', appiondb.int, index=True):
		"""
		selectq = ("SELECT stackparams.`boxSize`, stackparams.`bin` FROM ApStackData AS stack "
			+" LEFT JOIN ApRunsInStackData AS runsinstack "
			+"   ON runsinstack.`REF|ApStackData|stack` = stack.`DEF_id` "
			+" LEFT JOIN ApStackRunData AS stackrun "
			+"   ON runsinstack.`REF|ApStackRunData|stackrun` = stackrun.`DEF_id` "
			+" LEFT JOIN ApStackParamsData AS stackparams "
			+"   ON stackrun.`REF|ApStackParamsData|stackparams` = stackparams.`DEF_id` "
		)
		print appiondb.returnCustomSQL(selectq)
		"""
		updateq = ("UPDATE ApStackData AS stack "
			+" LEFT JOIN ApRunsInStackData AS runsinstack "
			+"   ON runsinstack.`REF|ApStackData|stack` = stack.`DEF_id` "
			+" LEFT JOIN ApStackRunData AS stackrun "
			+"   ON runsinstack.`REF|ApStackRunData|stackrun` = stackrun.`DEF_id` "
			+" LEFT JOIN ApStackParamsData AS stackparams "
			+"   ON stackrun.`REF|ApStackParamsData|stackparams` = stackparams.`DEF_id` "
			+" SET "
			+"   stack.`boxsize` = stackparams.`boxSize`/stackparams.`bin`, "
			+"   stack.`DEF_timestamp` = stack.`DEF_timestamp` "
		)
		appiondb.executeCustomSQL(updateq)
	### link to stackParams via StackRun via RunsInStack to get bin, boxSize

	#===================
	# appion fields with spaces
	#===================
	appiondb.renameColumn('ApMaskMakerParamsData', 'mask type', 'mask_type')
	appiondb.renameColumn('ApMaskMakerParamsData', 'region diameter', 'region_diameter')
	appiondb.renameColumn('ApMaskMakerParamsData', 'edge blur', 'edge_blur')
	appiondb.renameColumn('ApMaskMakerParamsData', 'edge low', 'edge_low')
	appiondb.renameColumn('ApMaskMakerParamsData', 'edge high', 'edge_high')
	appiondb.renameColumn('ApMaskMakerParamsData', 'region std', 'region_std')
	appiondb.renameColumn('ApMaskMakerParamsData', 'convex hull', 'convex_hull')

	appiondb.renameColumn('ApInitialModelData', 'original density', 'original_density')
	appiondb.renameColumn('ApInitialModelData', 'original model', 'original_model')

	appiondb.renameColumn('ApProtomoParamsData', 'series name', 'series_name')

	appiondb.renameColumn('ApProtomoAlignerParamsData', 'refine cycle', 'refine_cycle')
	appiondb.renameColumn('ApProtomoAlignerParamsData', 'good cycle', 'good_cycle')
	appiondb.renameColumn('ApProtomoAlignerParamsData', 'good start', 'good_start')
	appiondb.renameColumn('ApProtomoAlignerParamsData', 'good end', 'good_end')

	appiondb.renameColumn('ApTomoAlignerParamsData', 'refine cycle', 'refine_cycle')
	appiondb.renameColumn('ApTomoAlignerParamsData', 'good cycle', 'good_cycle')
	appiondb.renameColumn('ApTomoAlignerParamsData', 'good start', 'good_start')
	appiondb.renameColumn('ApTomoAlignerParamsData', 'good end', 'good_end')

	appiondb.renameColumn('ApTomoAvgParticleData', 'aligned particle', 'aligned_particle')
	appiondb.renameColumn('ApTomoAvgParticleData', 'z shift', 'z_shift')

	#===================
	# repair misnamed ApClusterJobData job names
	#===================
	#selectq = "SELECT DISTINCT `jobtype` FROM `ApClusterJobData` ORDER BY `jobtype`;"
	jobmap = {
		'ace': 'pyace',
		'ace2': 'pyace2',
		'templatepicker': 'templatecorrelator',
		'makestack': 'makestack2',
	}
	if appiondb.tableExists('ApClusterJobData'):
		for key in jobmap.keys():
			updateq = ("UPDATE ApClusterJobData AS job "
				+" SET "
				+("   job.`name` = '%s' "%(key))
				+" WHERE "
				+("   job.`name` = '%s' "%(jobmap[key]))
			)
			appiondb.executeCustomSQL(updateq)

	#===================
	# add index to ApStackParticleData
	#===================
	appiondb.indexColumn('ApParticleData', 'label', length=8)
	appiondb.indexColumn('ApStackParticleData', 'particleNumber')
	appiondb.indexColumn('ApAlignParticleData', 'partnum')
	appiondb.indexColumn('ApClusteringParticleData', 'partnum')

	appiondb.indexColumn('ApRefineIterData', 'iteration')
	appiondb.indexColumn('ApCtfData', 'confidence')
	appiondb.indexColumn('ApCtfData', 'confidence_d')
	appiondb.indexColumn('ApPathData', 'path', length=32)

	#===================
	# index all columns named hidden
	#===================
	olddebug = appiondb.debug
	appiondb.debug -= 1
	for tablename in appiondb.getAllTables():
		appiondb.indexColumn(tablename, 'hidden')
		appiondb.renameColumn(tablename, 'project|projects|project', 'REF|projectdata|projects|projectid')
		appiondb.indexColumn(tablename, 'REF|projectdata|projects|projectid')
	appiondb.debug = olddebug

	sys.exit(1)

	#===================
	# project table
	#===================
	projectdb = dbupgrade.DBUpgradeTools('projectdata', 'projtest', drop=True)
	projectdb.renameColumn('projects', 'projectId', 'DEF_id')
	projectdb.renameColumn('projects', 'timestamp', 'DEF_timestamp')

	projectdb.renameColumn('projectexperiments', 'projectexperimentId', 'DEF_id')
	projectdb.renameColumn('projectexperiments', 'projectId', 'REF|projects|projectid')
	projectdb.addColumn('projectexperiments', 'DEF_timestamp', projectdb.timestamp, index=True)

	### change session name to session id
	projectdb.addColumn('projectexperiments', 'REF|SessionData|sessionid', projectdb.link, index=True)
	updateq = ("UPDATE projectexperiments AS projexp "
		+" LEFT JOIN dbemdata.SessionData AS session "
		+"   ON session.`name` = projexp.`name` "
		+" SET "
		+"   projexp.`REF|SessionData|sessionid` = session.`DEF_id` "
	)
	projectdb.executeCustomSQL(updateq)
	projectdb.dropColumn('projectexperiments', 'name')
	projectdb.dropColumn('projectexperiments', 'experimentsourceId')

	#===================
	# leginon table
	#===================
	leginondb = dbupgrade.DBUpgradeTools('leginondata', 'dbemtest', drop=False)
	leginondb.renameColumn('viewer_pref_image', 'id', 'DEF_id')
	leginondb.renameColumn('viewer_pref_image', 'timestamp', 'DEF_timestamp')
	leginondb.renameColumn('viewer_pref_image', 'sessionId', 'REF|SessionData|sessionid')
	leginondb.renameColumn('viewer_pref_image', 'imageId', 'REF|AcquisitionImageData|imageid')

