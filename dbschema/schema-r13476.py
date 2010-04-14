#!/usr/bin/env python


from sinedon import dbupgrade


if __name__ == "__main__":
	appiondb = dbupgrade.DBUpgradeTools('aptest', 'appiondata', drop=True)

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
		'REF|ApRefinementRunData|refinementRun', 'REF|ApRefineRunData|refineRun')
	appiondb.renameColumn('ApRefineRunData', 'name', 'runname')
	appiondb.renameColumn('ApRefineParticleData', 'thrown_out', 'refine_keep')
	### special: invert values
	if appiondb.columnExists('ApRefineParticleData', 'refine_keep'):
		updateq = ("UPDATE ApRefineParticleData AS refpart "
			+" SET "
			+"   refpart.`refine_keep` = MOD(IFNULL(refpart.`refine_keep`,0)+1,2), "
			+"   refpart.`DEF_timestamp` = refpart.`DEF_timestamp` "
		)
		appiondb.executeCustomSQL(updateq)

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
		appiondb.addColumn('ApRefineIterData', 'REF|ApSymmetryData|symmetry', appiondb.link)
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
	# add new columns calculated from old data
	#===================
	### count number of iterations
	if appiondb.addColumn('ApRefineRunData', 'num_iter', appiondb.int):
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
	if appiondb.addColumn('ApStackData', 'boxsize', appiondb.int):
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


