#!/usr/bin/env python
# Upload pik or box files to the database

import os
import sys
import time
import re
import shutil
from appionlib import appionScript
from appionlib import apSymmetry
from appionlib import apParam
from appionlib import apFile
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apChimera
from appionlib import apVolume
from appionlib import apModel
from appionlib import apProject
from appionlib import appiondata



#=====================
#=====================
class UploadModelScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --file=<filename> --session=<name> --symm=<#> --apix=<#> \n\t "
			+" --res=<#> --description='text' [--contour=<#>] [--zoom=<#>] \n\t "
			+" [--rescale=<model ID,scale factor> --boxsize=<#>] ")
		self.parser.add_option("-f", "--file", dest="file",
			help="MRC file to upload", metavar="FILE")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("--sym", "--symm", "--symmetry", dest="symmetry",
			help="Symmetry id in the database", metavar="INT")
		self.parser.add_option("--old-apix", dest="oldapix", type="float",
			help="Original pixel size in Angstroms if oldapix != apix, it will be rescaled", metavar="FLOAT")
		self.parser.add_option("-a", "--apix", dest="newapix", type="float",
			help="Pixel size in Angstroms", metavar="FLOAT")
		self.parser.add_option("--res", "--resolution", dest="res", type="float",
			help="Map resolution in Angstroms", metavar="FLOAT")
		self.parser.add_option("-z", "--zoom", dest="zoom", type="float", default=1.0,
			help="Zoom factor for snapshot rendering (1.75 by default)", metavar="FLOAT")
		self.parser.add_option("-c", "--contour", dest="contour", type="float", default=1.5,
			help="Sigma level at which snapshot of density will be contoured (1.5 by default)", metavar="FLOAT")
		self.parser.add_option("--mass", dest="mass", type="int",
			help="Mass (in kDa) at which snapshot of density will be contoured", metavar="FLOAT")
		self.parser.add_option("--chimera-only", dest="chimeraonly", default=False, action="store_true",
			help="Do not do any reconstruction calculations only run chimera")
		self.parser.add_option("-b", "--boxsize", "--newbox", dest="newbox", type="int",
			help="Boxsize of new model", metavar="INT")
		self.parser.add_option("-m", "--modelid", "--old-model-id", dest="oldmodelid", type="int",
			help="Initial model id in the database to rescale", metavar="INT")
		self.parser.add_option("--densityid", dest="densityid", type="int",
			help="3D Density id in the database to upload as an accepted model", metavar="INT")
		self.parser.add_option("--name", dest="name",
			help="Prefix name for new model, automatically append res_pixelsize_box.mrc in the program")
		self.parser.add_option("--viper2eman", dest="viper2eman", default=False,
			action="store_true", help="Convert VIPER orientation to EMAN orientation")

	#=====================
	def checkConflicts(self):
		if self.params['session'] is None:
			apDisplay.printError("Enter a session ID")
		if self.params['projectid'] is not None:
			projid = apProject.getProjectIdFromSessionName(self.params['session'])
			if projid != self.params['projectid']:
				apDisplay.printError("Project ID and Session name do not match")
		if self.params['description'] is None:
			apDisplay.printError("Enter a description of the initial model")
		if self.params['chimeraonly'] is True:
			self.params['commit'] = False
		if self.params['newbox'] is not None and self.params['newbox'] % 16 != 0:
			apDisplay.printWarning("Box size is not a multiple of 16")
		if self.params['newbox'] is None:
			self.params['rescale'] = False
		else:
			self.params['rescale'] = True
		### program requires either a model id or density id or filename
		checkvalue = int(self.params['file'] is not None)
		checkvalue += int(self.params['oldmodelid'] is not None)
		checkvalue += int(self.params['densityid'] is not None)
		if checkvalue != 1:
			apDisplay.printError("Either provide a modelid or densityid or file, but not more than one of them")
		elif self.params['oldmodelid'] is not None and self.params['rescale'] is False:
			apDisplay.printError("Please specify either a new boxsize or scale for your model")
		elif self.params['densityid'] is not None:
			self.getDensityParams()
		elif self.params['oldmodelid'] is not None:
			self.getModelParams()
		elif self.params['file'] is not None:
			if not os.path.isfile(self.params['file']):
				apDisplay.printError("could not find file: "+self.params['file'])
			if self.params['file'][-4:] != ".mrc":
				apDisplay.printError("uploadModel.py only supports MRC files")
			self.params['file'] = os.path.abspath(self.params['file'])
		else:
			apDisplay.printError("Please provide either a --modelid=112 or --file=initmodel.mrc")
		### required only if now model id is provided
		if self.params['newapix'] is None:
			apDisplay.printError("Enter the pixel size of the model")
		if self.params['symmetry'] is None:
			apSymmetry.printSymmetries()
			apDisplay.printError("Enter a symmetry ID, e.g. --symm=19")
		self.params['symdata'] = apSymmetry.findSymmetry(self.params['symmetry'])
		if self.params['res'] is None:
			apDisplay.printError("Enter the resolution of the initial model")

	#=====================
	def setRunDir(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		self.params['rundir'] = os.path.join(path,"models","accepted",self.params['runname'])

	#=====================
	def setFileName(self):
		if self.params['name'] is None:
			### assign provided name
			if self.params['oldmodelid'] is not None:
				basename = "model%04d-%s" % (self.params['oldmodelid'], self.timestamp)
			elif self.params['densityid'] is not None:
				basename = "density%04d-%s" % (self.params['densityid'], self.timestamp)
			else:
				oldbasename = os.path.splitext(os.path.basename(self.params['file']))[0]
				basename = "upload-%s-%s" % (oldbasename, self.timestamp)
		else:
			### clean up provided name
			basename = os.path.splitext(os.path.basename(self.params['name']))[0]
		self.params['name'] = os.path.join(self.params['rundir'], basename)
		apDisplay.printColor("Naming density model: "+self.params['name'], "cyan")
		return

	#=====================
	def getDensityParams(self):
		densitydata = appiondata.Ap3dDensityData.direct_query(self.params['densityid'])
		self.params['oldapix'] = float(densitydata['pixelsize'])
		if self.params['symmetry'] is None:
			self.params['symdata'] = densitydata['symmetry']
			self.params['symmetry'] = self.params['symdata']['eman_name']
		if densitydata['resolution']:
			self.params['res'] = float(densitydata['resolution'])
		self.params['file'] = os.path.join(densitydata['path']['path'], densitydata['name'])
		if self.params['newapix'] is None:
			self.params['newapix'] = self.params['oldapix']
		if self.params['newapix'] is None:
			self.params['newapix'] = self.params['oldapix']

	#=====================
	def getModelParams(self):
		modeldata = apModel.getModelFromId(self.params['oldmodelid'])
		self.params['oldapix'] = float(modeldata['pixelsize'])
		if self.params['symmetry'] is None:
			self.params['symdata'] = modeldata['symmetry']
			self.params['symmetry'] = self.params['symdata']['eman_name']
		self.params['res'] = float(modeldata['resolution'])
		self.params['file'] = os.path.join(modeldata['path']['path'], modeldata['name'])

	#=====================
	def checkExistingFile(self):
		mrcname = os.path.join(self.params['rundir'], self.params['name']+".mrc")
		origmodel = self.params['file']
		apDisplay.printWarning("a model by the same filename already exists: '"+mrcname+"'")
		### a model by the same name already exists
		mdnew = apFile.md5sumfile(mrcname)
		mdold = apFile.md5sumfile(origmodel)
		if mdnew != mdold:
			### they are different, make unique name
			self.setFileName(unique=True)
			apDisplay.printWarning("the models are different, cannot overwrite, so using new name: %s" % (self.params['name'],))
			# restart
			self.start()
			return True
		elif apDatabase.isModelInDB(mdnew):
			### they are the same and its in the database already
			apDisplay.printWarning("same model with md5sum '"+mdnew+"' already exists in the DB!")
			apDisplay.printWarning("creating new images, but skipping upload for file: '"+mrcname+"'")
			self.params['commit'] = False
			self.params['chimeraonly'] = True
		else:
			### they are the same, but its not in the database
			apDisplay.printWarning("the same model with name '"+mrcname+"' already exists, but is not uploaded!")
			if self.params['commit'] is True:
				apDisplay.printMsg("inserting model into database")
		if self.params['rescale'] is True:
			apDisplay.printError("cannot rescale an existing model")

	#===========================
	def insertModel(self):
		apDisplay.printMsg("commiting model to database")
		modq=appiondata.ApInitialModelData()
		modq['project|projects|project'] = self.params['projectid']
		modq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		modq['name'] = self.params['name']
		modq['symmetry'] = self.params['symdata']
		modq['pixelsize'] = self.params['newapix']
		modq['boxsize'] = self.params['newbox']
		modq['resolution'] = self.params['res']
		modq['hidden'] = False
		filepath = os.path.join(self.params['rundir'], self.params['name'])
		modq['md5sum'] = apFile.md5sumfile(filepath)
		modq['description'] = self.params['description']
		if self.params['densityid'] is not None:
			modq['original density'] = appiondata.Ap3dDensityData.direct_query(self.params['densityid'])
		if self.params['oldmodelid'] is not None:
			modq['original model'] = appiondata.ApInitialModelData.direct_query(self.params['oldmodelid'])
		if self.params['commit'] is True:
			modq.insert()
		else:
			apDisplay.printWarning("not commiting model to database")

	#=====================
	def start(self):
		self.setFileName()
		self.params['oldbox'] = apVolume.getModelDimensions(self.params['file'])
		if self.params['newbox'] is None:
			self.params['newbox'] = self.params['oldbox']
		if self.params['oldapix'] is None:
			self.params['oldapix'] = self.params['newapix']
		self.params['scale'] =  float(self.params['oldapix'])/self.params['newapix']

		mrcname = os.path.join(self.params['rundir'], self.params['name']+".mrc")
		origmodel = self.params['file']
		if os.path.isfile(mrcname):
			### rescale old model to a new size
			### I don't think this works - neil
			if self.checkExistingFile() is True:
				apDisplay.printError("File exists")
		elif (abs(self.params['oldapix'] - self.params['newapix']) > 1.0e-2 or
			abs(self.params['oldbox'] - self.params['newbox']) > 1.0e-1):
			### rescale old model to a new size
			apDisplay.printWarning("rescaling original model to a new size")
			apDisplay.printMsg("rescaling model "+origmodel+" by "+str(round(self.params['scale']*100.0,2))+"%")
			apVolume.rescaleVolume(origmodel, mrcname,
				self.params['oldapix'], self.params['newapix'], self.params['newbox'])
		else:
			### simple upload, just copy file to models folder
			apDisplay.printMsg("copying original model to a new location: "+mrcname)
			shutil.copyfile(origmodel, mrcname)

		if self.params['viper2eman'] is True:
			apVolume.viper2eman(mrcname, mrcname, apix=self.params['apix'])

		### render chimera images of model
		contour = self.params['contour']
		if self.params['mass'] is not None:
			apChimera.setVolumeMass(mrcname, self.params['newapix'], self.params['mass'])
			contour = 1.0
		apChimera.renderSnapshots(mrcname, contour=contour,
			zoom=self.params['zoom'], sym=self.params['symdata']['eman_name'])

		self.insertModel()


#=====================
#=====================
if __name__ == '__main__':
	uploadModel = UploadModelScript()
	uploadModel.start()
	uploadModel.close()



