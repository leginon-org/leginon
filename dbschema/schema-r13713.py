#!/usr/bin/env python

import sys
import time
from sinedon import dbupgrade, dbconfig

def getAppionDatabases(projectdb):
	"""
	Get list of appion databases to upgrade
	"""
	describeq = "DESCRIBE processingdb"
	fields = projectdb.returnCustomSQL(describeq)
	fieldnames = []
	for field in fields:
		fieldnames.append(field[0])
	if 'db' in fieldnames:
		selectq = "SELECT DISTINCT db FROM processingdb ORDER BY `projectId` ASC"
	else:
		if 'appiondb' in fieldnames:
			selectq = "SELECT DISTINCT appiondb FROM processingdb ORDER BY `REF|projects|project` ASC"
		else:
			return []
	results = projectdb.returnCustomSQL(selectq)
	appiondblist = []
	for result in results:
		appiondblist.append(result[0])
	return appiondblist


#===================
#===================
# APPION UPGRADE
#===================
#===================
def upgradeAppionDB(appiondbname, projectdb):
	print ""
	print "========================"
	print "Upgrading appion database: "+appiondbname
	time.sleep(0.1)

	appiondb = dbupgrade.DBUpgradeTools('appiondata', appiondbname, drop=True)

	#===================
	# rename tables: when renaming table you must rename all columns linking to that table
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
	### no long required to be on a cluster
	appiondb.renameTable('ApClusterJobData', 'ApAppionJobData')

	#===================
	# rename columns:
	#===================
	### refinement tables
	appiondb.renameColumn('ApRefineIterData', 
		'REF|ApRefinementParamsData|refinementParams', 'REF|ApEmanRefineIterData|emanParams')
	appiondb.renameColumn('ApRefineIterData', 
		'REF|ApRefinementRunData|refinementRun', 'REF|ApRefineRunData|refineRun')
	appiondb.renameColumn('ApRefineRunData', 'name', 'runname')
	appiondb.renameColumn('ApEulerJumpData', 
		'REF|ApRefinementRunData|refRun', 'REF|ApRefineRunData|refineRun')
	appiondb.renameColumn('Ap3dDensityData', 
		'REF|ApRefinementData|iterid', 'REF|ApRefineIterData|refineIter')
	appiondb.renameColumn('ApFSCData', 
		'REF|ApRefinementData|refinementData', 'REF|ApRefineIterData|refineIter')

	### special case of conflicting Xmipp columns
	if (appiondb.columnExists('ApRefineIterData', 'REF|ApXmippRefineIterationParamsData|xmippRefineParams') and 
		appiondb.columnExists('ApRefineIterData', 'REF|ApXmippRefineIterData|xmippParams')):
		appiondb.dropColumn('ApRefineIterData', 'REF|ApXmippRefineIterationParamsData|xmippRefineParams')
	else:
		appiondb.renameColumn('ApRefineIterData', 
			'REF|ApXmippRefineIterationParamsData|xmippRefineParams', 'REF|ApXmippRefineIterData|xmippParams')

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
	if appiondb.tableExists('ApRefineIterData') and appiondb.columnExists('ApRefineIterData', 'SpiCoranGoodClassAvg'):
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
		
		### special: invert values
		if appiondb.addColumn('ApRefineParticleData', 'refine_keep', appiondb.bool):
			updateq = ("UPDATE ApRefineParticleData AS refpart "
				+" SET "
				+"   refpart.`refine_keep` = MOD(IFNULL(refpart.`thrown_out`,0)+1,2), "
				+"   refpart.`DEF_timestamp` = refpart.`DEF_timestamp` "
			)
			appiondb.executeCustomSQL(updateq)
			appiondb.dropColumn('ApRefineParticleData', 'thrown_out')

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
		appiondb.changeColumnDefinition('ApRefineParticleData', 'refine_keep', appiondb.bool)
		appiondb.changeColumnDefinition('ApRefineParticleData', 'postRefine_keep', appiondb.bool)

		### index columns
		appiondb.indexColumn('ApRefineParticleData', 'refine_keep')
		appiondb.indexColumn('ApRefineParticleData', 'postRefine_keep')

	### Need to change:
	if appiondb.tableExists('ApRefineGoodBadParticleData'):
		appiondb.renameColumn('ApRefineGoodBadParticleData', 'REF|ApRefinementData|refine', 
			'REF|ApRefineIterData|refine', appiondb.link)
		appiondb.renameColumn('ApRefineGoodBadParticleData', 'good_normal', 'good_refine', appiondb.int)
		appiondb.renameColumn('ApRefineGoodBadParticleData', 'bad_normal', 'bad_refine', appiondb.int)
		appiondb.renameColumn('ApRefineGoodBadParticleData', 'good_coran', 'good_postRefine', appiondb.int)
		appiondb.renameColumn('ApRefineGoodBadParticleData', 'bad_coran', 'bad_postRefine', appiondb.int)
		appiondb.dropColumn('ApRefineGoodBadParticleData', 'good_msgp')
		appiondb.dropColumn('ApRefineGoodBadParticleData', 'bad_msgp')

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
	# repair misnamed ApAppionJobData job names
	#===================
	#selectq = "SELECT DISTINCT `jobtype` FROM `ApAppionJobData` ORDER BY `jobtype`;"
	jobmap = {
		'ace': 'pyace',
		'ace2': 'pyace2',
		'templatepicker': 'templatecorrelator',
		'makestack': 'makestack2',
		'recon': 'emanrecon',
	}
	if appiondb.tableExists('ApAppionJobData'):
		for key in jobmap.keys():
			updateq = ("UPDATE ApAppionJobData AS job "
				+" SET "
				+("   job.`jobtype` = '%s' "%(jobmap[key]))
				+" WHERE "
				+("   job.`jobtype` = '%s' "%(key))
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
		appiondb.changeColumnDefinition(tablename, 'hidden', appiondb.bool)
		appiondb.indexColumn(tablename, 'hidden')
		### old version misnamed column
		appiondb.renameColumn(tablename, 'REF|project|projects|project', 
			"REF|"+projectdb.getSinedonName()+"|projects|project")
		appiondb.renameColumn(tablename, 'project|projects|project', 
			"REF|"+projectdb.getSinedonName()+"|projects|project")
		appiondb.indexColumn(tablename, "REF|"+projectdb.getSinedonName()+"|projects|project")

		### refine tables
		appiondb.renameColumn(tablename, 'REF|ApRefinementData|refinementData', 'REF|ApRefineIterData|refineIter', appiondb.link)
		appiondb.renameColumn(tablename, 'REF|ApRefinementData|refinement', 'REF|ApRefineIterData|refineIter', appiondb.link)
		appiondb.renameColumn(tablename, 'REF|ApRefinementData|refine', 'REF|ApRefineIterData|refineIter', appiondb.link)
		appiondb.renameColumn(tablename, 'REF|ApRefinementRunData|refinementRun', 'REF|ApRefineRunData|refineRun', appiondb.link)
		appiondb.renameColumn(tablename, 'REF|ApRefinementParamsData|refinementParams', 'REF|ApEmanRefineIterData|emanParams', appiondb.link)
		### plural particles tables
		appiondb.renameColumn(tablename, 'REF|ApStackParticlesData|particle', 'REF|ApStackParticleData|particle', appiondb.link)
		appiondb.renameColumn(tablename, 'REF|ApStackParticlesData|stackpart', 'REF|ApStackParticleData|stackpart', appiondb.link)
		appiondb.renameColumn(tablename, 'REF|ApAlignParticlesData|alignparticle', 'REF|ApAlignParticleData|alignparticle', appiondb.link)
		### no long required to be on a cluster
		appiondb.renameColumn(tablename, 'REF|ApClusterJobData|job', 'REF|ApAppionJobData|job')
		appiondb.renameColumn(tablename, 'REF|ApClusterJobData|jobfile', 'REF|ApAppionJobData|job')

	appiondb.debug = olddebug

	#===================
	# set all boolean columns to TINYINT(1), there was an old bug
	#===================
	appiondb.changeColumnDefinition('ApAssessmentData', 'selectionkeep', appiondb.bool)
	appiondb.indexColumn('ApAssessmentData', 'selectionkeep')
	appiondb.changeColumnDefinition('ApAlignParticleData', 'mirror', appiondb.bool)
	print "DONE"

#===================
#===================
# MAIN PROGRAM
#===================
#===================
if __name__ == "__main__":
	projectdb = dbupgrade.DBUpgradeTools('projectdata', drop=True)
	leginondb = dbupgrade.DBUpgradeTools('leginondata', drop=False)

	appiondblist = getAppionDatabases(projectdb)
	for appiondbname in appiondblist:
		if not projectdb.databaseExists(appiondbname):
			print "\033[31merror database %s does not exist\033[0m"%(appiondbname)
			time.sleep(1)
			continue
		upgradeAppionDB(appiondbname, projectdb)
	

	#===================
	# project table
	#===================

	projectdb.renameColumn('projects', 'projectId', 'DEF_id', projectdb.defid)
	projectdb.renameColumn('projects', 'timestamp', 'DEF_timestamp', projectdb.timestamp)
	projectdb.renameColumn('projects', 'db', 'leginondb')

	projectdb.renameColumn('projectexperiments', 'projectexperimentId', 'DEF_id', projectdb.defid)
	projectdb.renameColumn('projectexperiments', 'projectId', 'REF|projects|project', projectdb.link)
	projectdb.addColumn('projectexperiments', 'DEF_timestamp', projectdb.timestamp, index=True)

	### change session name to session id
	projectdb.addColumn('projectexperiments', "REF|"+leginondb.getSinedonName()+"|SessionData|session",
		projectdb.link, index=True)
	if projectdb.columnExists('projectexperiments', 'name'):
		updateq = ("UPDATE projectexperiments AS projexp "
			+" LEFT JOIN "+leginondb.getDatabaseName()+".SessionData AS session "
			+"   ON session.`name` = projexp.`name` "
			+" SET "
			+"   projexp.`REF|"+leginondb.getSinedonName()+"|SessionData|session` = session.`DEF_id` "
		)
		projectdb.executeCustomSQL(updateq)
		projectdb.dropColumn('projectexperiments', 'name')
	projectdb.dropColumn('projectexperiments', 'experimentsourceId')

	### processingdb
	projectdb.renameColumn('processingdb', 'id', 'DEF_id', projectdb.defid)
	projectdb.addColumn('processingdb', 'DEF_timestamp', projectdb.timestamp, index=True)
	projectdb.renameColumn('processingdb', 'db', 'appiondb')
	projectdb.renameColumn('processingdb', 'projectId', 'REF|projects|project', projectdb.link)
	projectdb.indexColumn('projectexperiments', 'appiondb')

	### shareexperiments
	projectdb.renameColumn('shareexperiments', 'id', 'DEF_id', projectdb.defid)
	projectdb.addColumn('shareexperiments', 'DEF_timestamp', projectdb.timestamp, index=True)

	#===================
	# leginon table
	#===================

	leginondb.renameTable('viewer_pref_image', 'ViewerImageStatus')
	leginondb.renameColumn('ViewerImageStatus', 'id', 'DEF_id', projectdb.defid)
	leginondb.renameColumn('ViewerImageStatus', 'timestamp', 'DEF_timestamp', projectdb.timestamp)
	leginondb.renameColumn('ViewerImageStatus', 'sessionId', 'REF|SessionData|session', projectdb.link)
	leginondb.renameColumn('ViewerImageStatus', 'imageId', 'REF|AcquisitionImageData|image', projectdb.link)

	leginondb.changeColumnDefinition('PresetData', 'exposure time', leginondb.float)
	leginondb.changeColumnDefinition('AcquisitionImageTargetData', 'delta row', leginondb.float)
	leginondb.changeColumnDefinition('AcquisitionImageTargetData', 'delta column', leginondb.float)

