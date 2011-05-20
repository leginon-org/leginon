'''
This is the place for instrument parameter related function
'''
#leginon
import leginon.leginondata
#appion
from appionlib import apDisplay

def getCsValueFromSession(sessiondata):
	'''
	returns Spherical Aberration Constant in mm
	'''
	q = leginon.leginondata.ScopeEMData(session=sessiondata)
	results = q.query(results=1)
	if not results:
		apDisplay.printError('TEM was not used in session %s' % sessiondata['name'])
	scopedata = results[0]
	temdata = scopedata['tem']
	if not temdata:
		apDisplay.printError('No TEM referenced in last session ScopeEMData') 
	cs = temdata['cs']
	if cs is None:
		apDisplay.printError('Cs not saved for TEM %s on %s' % (temdata['name'],temdata['hostname']))
	return cs * 1e3
