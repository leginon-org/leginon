#pythonlib
import os
import time
#appion
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apVolume

"""
Functions to manipulate models that involve the database
"""

#================
def getModelFromId(modelid):
	return appiondata.ApInitialModelData.direct_query(modelid)

#================
def rescaleModel(modelid, outfile, newbox=None, newapix=None, spider=False):
	"""
	take an existing model id and rescale it
	"""
	modeldata = getModelFromId(modelid)
	modelapix = modeldata['pixelsize']
	modelfile = os.path.join(modeldata['path']['path'], modeldata['name'])
	apVolume.rescaleVolume(modelfile, outfile, inapix, newapix, newbox, spider=False)
	return

#================
def isModelInDB(md5sum):
	modelq = appiondata.ApInitialModelData()
	modelq['md5sum'] = md5sum
	modeld = modelq.query(results=1)
	if modeld:
		return True
	return False
