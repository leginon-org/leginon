#!/usr/bin/env python
from appionlib import appiondata
from appionlib import apParam

def getScriptProgramRunFromRunname(runname,jobdata=None):
	q = appiondata.ScriptProgramRun(runname=runname,job=jobdata)
	results = q.query()
	if len(results) == 1:
		return results[0]
	else:
		apDisplay.printError('More than one ScriptProgramRun is found for runname %s' % runname)

def getScriptParamValuesFromRunname(runname,jobdata=None):
	params = {}
	program = getScriptProgramRunFromRunname(runname, jobdata)
	if program is not None:
		q = appiondata.ScriptParamValue(progrun=program)
		results = q.query()
		for result in results:
			params[result['paramname']['name']]=apParam.tc(result['value'])
	return params

