#!/usr/bin/env python
from appionlib import appiondata
from appionlib import apParam
from appionlib import apDisplay

def getScriptProgramRunFromRunname(runname,pathdata,jobdata=None):
	q = appiondata.ScriptProgramRun(runname=runname,rundir=pathdata,job=jobdata)
	results = q.query()
	if len(results) == 1:
		return results[0]
	else:
		if len(results) == 0:
			# Try with only runname
			q = appiondata.ScriptProgramRun(runname=runname,job=jobdata)
			if len(results) == 1:
				return results[0]
			apDisplay.printError('No ScriptProgramRun is found for runname %s' % (runname))
		else:
			apDisplay.printWarning('%d ScriptProgramRuns are found for runname %s' % (len(results),runname))
			apDisplay.printWarning('Use most recent one')
			return results[0]

def getScriptParamValuesFromRun(prog_run):
	'''
	return param values of a specific run.
	'''
	params = {}
	q = appiondata.ScriptParamValue(progrun=prog_run)
	results = q.query()
	for result in results:
		params[result['paramname']['name']]=apParam.tc(result['value'])
	return params

def getScriptUsageKeysFromRun(prog_run):
	'''
	return param values of a specific run.
	'''
	q = appiondata.ScriptParamValue(progrun=prog_run)
	results = q.query()
	usage_map = {}
	if results:
		for r in results:
			usage_map[r['paramname']['name']] = r['usage'].split('--')[1].split('=')[0]
	return usage_map

def getScriptParamValuesFromRunname(runname,pathdata,jobdata=None):
	'''
	return param values of a run with pathdata and jobdata specified.
	In rare case, this may give different result from specifying the run data
  since parallel loop runs may use different params.
	'''
	program = getScriptProgramRunFromRunname(runname,pathdata, jobdata)
	if program is not None:
		return getScriptParamValuesFromRun(program)

