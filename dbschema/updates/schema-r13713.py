#!/usr/bin/env python

import sys
import time
import random
from sinedon import dbupgrade, maketables

def getAppionDatabases(projectdb):
	"""
	Get list of appion databases to upgrade
	"""
	if projectdb.columnExists('processingdb', 'appiondb'):
		colname = 'appiondb'
	elif projectdb.columnExists('processingdb', 'db'):
		colname = 'db'
	else:
		print "could not find appion tables"
		return []

	selectq = "SELECT DISTINCT "+colname+" FROM processingdb ORDER BY `REF|projects|project` ASC"
	results = projectdb.returnCustomSQL(selectq)
	appiondblist = []
	for result in results:
		appiondblist.append(result[0])
	#random.shuffle(appiondblist)
	return appiondblist

#===================
#===================
# APPION UPGRADE
#===================
#===================
def upgradeAppionDB(appiondbname, projectdb, backup=True):
	print ""
	print "========================"
	print "Upgrading appion database: "+appiondbname
	time.sleep(0.1)

	appiondb = dbupgrade.DBUpgradeTools('appiondata', appiondbname, drop=True)
	if backup:
		appiondb.backupDatabase(appiondbname+".sql", data=True)

	#===================
	# rename tables: when renaming table you must rename all columns linking to that table
	#===================
	### refinement tables
	appiondb.renameTable('ApRefinementData', 'ApRefineIterData', updaterefs=False)
	appiondb.renameTable('ApRefinementRunData', 'ApRefineRunData', updaterefs=False)
	appiondb.renameTable('ApParticleClassificationData', 'ApRefineParticleData', updaterefs=False)
	appiondb.renameTable('ApRefinementParamsData', 'ApEmanRefineIterData', updaterefs=False)
	### plural particles tables
	appiondb.renameTable('ApStackParticlesData', 'ApStackParticleData', updaterefs=False)
	appiondb.renameTable('ApAlignParticlesData', 'ApAlignParticleData', updaterefs=False)
	appiondb.renameTable('ApClusteringParticlesData', 'ApClusteringParticleData', updaterefs=False)
	### no long required to be on a cluster
	appiondb.renameTable('ApClusterJobData', 'ApAppionJobData', updaterefs=False)

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
	appiondb.renameColumn('ApTiltsInAlignRunData', 
		'primary', 'primary_tiltseries')

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
			appiondb.updateColumn('ApRefineParticleData', 'refine_keep', 
				"MOD(IFNULL(`thrown_out`,0)+1,2)", "")
			appiondb.dropColumn('ApRefineParticleData', 'thrown_out')

		if (appiondb.columnExists('ApRefineParticleData', 'postRefine_keep') 
		 and appiondb.columnExists('ApRefineParticleData', 'msgp_keep')):
			appiondb.updateColumn('ApRefineParticleData', 'postRefine_keep', 
				"`msgp_keep`", "`postRefine_keep` IS NULL AND `msgp_keep` IS NOT NULL")

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

	appiondb.renameColumn('ApProtomoParamsData', 'series name', 'series_name')

	appiondb.renameColumn('ApProtomoAlignerParamsData', 'REF|ApProtomoRefinementParamsData|refine cycle',
		'REF|ApProtomoRefinementParamsData|refine_cycle')
	appiondb.renameColumn('ApProtomoAlignerParamsData', 'REF|ApProtomoRefinementParamsData|good cycle',
		'REF|ApProtomoRefinementParamsData|good_cycle')
	appiondb.renameColumn('ApProtomoAlignerParamsData', 'good start', 'good_start')
	appiondb.renameColumn('ApProtomoAlignerParamsData', 'good end', 'good_end')

	appiondb.renameColumn('ApTomoAlignerParamsData', 'REF|ApProtomoRefinementParamsData|refine cycle',
		'REF|ApProtomoRefinementParamsData|refine_cycle')
	appiondb.renameColumn('ApTomoAlignerParamsData', 'REF|ApProtomoRefinementParamsData|good cycle', 
		'REF|ApProtomoRefinementParamsData|good_cycle')
	appiondb.renameColumn('ApTomoAlignerParamsData', 'good start', 'good_start')
	appiondb.renameColumn('ApTomoAlignerParamsData', 'good end', 'good_end')

	appiondb.renameColumn('ApTomoAvgParticleData', 'REF|ApAlignParticlesData|aligned particle', 
		'REF|ApAlignParticlesData|aligned_particle')
	appiondb.renameColumn('ApTomoAvgParticleData', 'z shift', 'z_shift')

	appiondb.renameColumn('ApInitialModelData', 'REF|Ap3dDensityData|original density', 'REF|Ap3dDensityData|original_density')
	appiondb.renameColumn('ApInitialModelData', 'REF|ApInitialModelData|original model', 'REF|ApInitialModelData|original_model')


	#===================
	# special fix for symmetry tables that are mis-described
	#===================
	appiondb.updateColumn('ApSymmetryData', 'description', 
		"'7-fold symmetry along the z axis'",
		"`symmetry` = 'C7 (z)' AND `description` LIKE '3-fold symmetry%'")

	#===================
	# clarify icosahedral symmetry
	#===================
	appiondb.updateColumn('ApSymmetryData', 'symmetry', 
		"'Icos (2 3 5) Viper/3DEM'", "`symmetry` = 'Icos (2 3 5)'")
	appiondb.updateColumn('ApSymmetryData', 'symmetry', 
		"'Icos (5 3 2) EMAN'", "`symmetry` = 'Icos (5 3 2)'")
	appiondb.updateColumn('ApSymmetryData', 'symmetry', 
		"'Icos (2 5 3) Crowther'", "`symmetry` = 'Icos (2 5 3)'")

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
			appiondb.updateColumn('ApAppionJobData', 'jobtype', 
				"'"+jobmap[key]+"'", "`jobtype` = '"+key+"' ")

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

	#===================
	# set all boolean columns to TINYINT(1), there was an old bug
	#===================
	appiondb.changeColumnDefinition('ApAssessmentData', 'selectionkeep', appiondb.bool)
	appiondb.indexColumn('ApAssessmentData', 'selectionkeep')
	appiondb.changeColumnDefinition('ApAlignParticleData', 'mirror', appiondb.bool)
	print "DONE"

def makeAppionTables(dbname):
	sinedonname = 'appiondata'
	modulename = 'appionlib.'+sinedonname
	maketables.makeTables(sinedonname, modulename, dbname, None,False)

def upgradeProjectDB(projectdb,backup=True):
	dbname = projectdb.getDatabaseName()
	if backup:
		projectdb.backupDatabase(dbname+".sql", data=True)

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
			+"   projexp.`REF|"+leginondb.getSinedonName()+"|SessionData|session` = session.`DEF_id`, "
			+"   projexp.`DEF_timestamp` = session.`DEF_timestamp` "
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

	### set version of database
	selectq = " SELECT * FROM `install` WHERE `key`='version'"
	values = projectdb.returnCustomSQL(selectq)
	if values:
		projectdb.updateColumn("install", "value", "'1.9'", 
			"install.key = 'version'",timestamp=False)
	else:
		insertq = "INSERT INTO `install` (`key`, `value`) VALUES ('version', '2.0')"
		projectdb.executeCustomSQL(insertq)

def upgradeLeginonDB(leginondb, backup=True):
	dbname = leginondb.getDatabaseName()
	if backup:
		leginondb.backupDatabase(dbname+".sql", data=True)
	#===================
	# leginon table
	#===================
	if leginondb.tableExists('viewer_pref_image'):
		leginondb.renameTable('viewer_pref_image', 'ViewerImageStatus', updaterefs=False)
		leginondb.renameColumn('ViewerImageStatus', 'id', 'DEF_id', projectdb.defid)
		leginondb.renameColumn('ViewerImageStatus', 'timestamp', 'DEF_timestamp', projectdb.timestamp)
		leginondb.renameColumn('ViewerImageStatus', 'sessionId', 'REF|SessionData|session', projectdb.link)
		leginondb.renameColumn('ViewerImageStatus', 'imageId', 'REF|AcquisitionImageData|image', projectdb.link)
	else: 
		updateq = """CREATE TABLE IF NOT EXISTS ViewerImageStatus(
`DEF_id` INT( 11 ) NOT NULL AUTO_INCREMENT ,
`DEF_timestamp` TIMESTAMP NOT NULL ,
`REF|SessionData|session` INT( 11 ) NULL ,
`REF|AcquisitionImageData|image` INT( 11 ) NULL ,
`status` ENUM( 'hidden', 'visible', 'exemplar' ) NULL ,
PRIMARY KEY ( `DEF_id` ) ,
KEY `DEF_timestamp` ( `DEF_timestamp` ) ,
KEY `REF|SessionData|session` ( `REF|SessionData|session` ) ,
KEY `REF|AcquisitionImageData|image` ( `REF|AcquisitionImageData|image` ) ,
KEY `status` ( `status` )
);
"""
		leginondb.executeCustomSQL(updateq)
	leginondb.changeColumnDefinition('PresetData', 'exposure time', leginondb.float)
#===================
#===================
# MAIN PROGRAM
#===================
#===================
if __name__ == "__main__":
	projectdb = dbupgrade.DBUpgradeTools('projectdata', drop=True)
	leginondb = dbupgrade.DBUpgradeTools('leginondata', drop=False)
	print "\nWould you like to back up the database to local file before upgrading?"
	answer = raw_input('Yes/No (default=Yes): ')
	if answer.lower().startswith('n'):
		backup = False
	else:
		backup = True
	upgradeLeginonDB(leginondb,backup=backup)
	upgradeProjectDB(projectdb,backup=backup)

	appiondblist = getAppionDatabases(projectdb)
	for appiondbname in appiondblist:
		if not projectdb.databaseExists(appiondbname):
			print "\033[31merror database %s does not exist\033[0m"%(appiondbname)
			time.sleep(1)
			continue
		upgradeAppionDB(appiondbname, projectdb, backup=backup)
		makeAppionTables(appiondbname)
		upgradeAppionDB(appiondbname, projectdb, backup=False)

