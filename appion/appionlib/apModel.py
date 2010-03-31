#pythonlib
import os
import re
import time
import shutil
#appion
from appionlib import apDisplay
from appionlib import appiondata
from appionlib import apParam
from appionlib import apEMAN
from appionlib import apVolume
from appionlib import spyder

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


