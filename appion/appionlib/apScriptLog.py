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

def getScriptParamValuesFromRunname(runname,pathdata,jobdata=None):
	params = {}
	program = getScriptProgramRunFromRunname(runname,pathdata, jobdata)
	if program is not None:
		q = appiondata.ScriptParamValue(progrun=program)
		results = q.query()
		for result in results:
			params[result['paramname']['name']]=apParam.tc(result['value'])
	return params

