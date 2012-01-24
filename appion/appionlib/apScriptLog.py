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
		apDisplay.printError('More than one ScriptProgramRun is found for runname %s' % runname)

def getScriptParamValuesFromRunname(runname,pathdata,jobdata=None):
	params = {}
	program = getScriptProgramRunFromRunname(runname,pathdata, jobdata)
	if program is not None:
		q = appiondata.ScriptParamValue(progrun=program)
		results = q.query()
		for result in results:
			params[result['paramname']['name']]=apParam.tc(result['value'])
	return params

