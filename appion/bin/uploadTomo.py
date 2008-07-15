#!/usr/bin/python -O
# Upload pik or box files to the database

import os
import sys
import time
import re
import shutil
import appionScript
import apUpload
import apParam
import apFile
import apDisplay
import apDatabase
import apRecon
import apVolume


#=====================
#=====================
class UploadModelScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		"""
		self.params['rundir']=os.path.abspath('.')
		self.params['abspath']=os.path.abspath('.')
		self.params['outdir']=None
		self.params['scale']=None
		self.params['rescale']=False
		if (elements[0]=='outdir'):
			self.params['outdir']=elements[1]
		elif (arg=='chimeraonly'):
			self.params['chimeraonly']=True
			self.params['commit']=False
		elif (elements[0]=='rescale'):
			modinfo=elements[1].split(',')
			if len(modinfo) == 2:
				self.params['origmodel']=modinfo[0]
				self.params['newapix']=float(modinfo[1])
				self.params['rescale']=True
			else:
				apDisplay.printError("rescale must include both the original model id and a scale factor")

		# if not rescaling, make sure that the input model exists
		if (os.path.isfile(mrcfile) or self.params['rescale'] is True):
			(self.params['path'], self.params['name']) = os.path.split(mrcfile)
			self.params['path'] = os.path.abspath(self.params['path'])
			if not self.params['path']:
				self.params['path']=self.params['abspath']
		else:
			apDisplay.printError("file '"+mrcfile+"' does not exist\n")
		"""

		self.parser.set_usage("Usage: %prog --file=<filename> --session=<name> --symm=<#> --apix=<#> \n\t "
			+" --res=<#> --description='text' [--contour=<#>] [--zoom=<#>] \n\t "
			+" [--rescale=<model ID,scale factor> --boxsize=<#>] ")
		self.parser.add_option("-f", "--file", dest="file", 
			help="MRC file to upload", metavar="FILE")
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="SESSION")
		self.parser.add_option("-a", "--apix", dest="newapix", type="float",
			help="Pixel size in Angstroms", metavar="FLOAT")
		self.parser.add_option("-d", "--description", dest="description",
			help="Description of the reconstruction (must be in quotes)", metavar="'TEXT'")
		self.parser.add_option("-C", "--commit", dest="commit", default=True, action="store_true", 
			help="Commit reconstruction to database")
		self.parser.add_option("--no-commit", dest="commit", default=True, action="store_false", 
			help="Do not commit reconstruction to database")
		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Location to store uploaded model", metavar="PATH")
		self.parser.add_option("-n", "--name", dest="name",
			help="File name for new model, automatically set")

	#=====================
	def checkConflicts(self):
		if self.params['session'] is None:
			apDisplay.printError("Enter a session ID")
		if self.params['description'] is None:
			apDisplay.printError("Enter a description of the initial model")
		### program requires either a model id  or filename
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


	#=====================
	def setOutDir(self):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		print sessiondata
		print self.params
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		self.params['outdir'] = os.path.join(path,"models")

	#=====================
	def setNewFileName(self, unique=False):
		#clean up old name
		basename = os.path.basename(self.params['file'])
		basename = re.sub(".mrc", "", basename)
		# set foldname
		foldname = os.path.basename(os.path.dirname(self.params['file']))
		self.params['name'] = basename+".mrc"

	#=====================
	def getModelParams(self):
		modeldata = apVolume.getModelFromId(self.params['oldmodelid'])
		self.params['oldapix'] = float(modeldata['pixelsize'])
		self.params['file'] = os.path.join(modeldata['path']['path'], modeldata['name'])

	#=====================
	def rescaleModel(self):
		### rescale old model to a new size
		modeldata = apVolume.getModelFromId(self.params['origmodel'])
		old = os.path.join(modeldata['path']['path'], modeldata['name'])
		apDisplay.printMsg("rescaling model "+origmodelpath+" to "+newmodelpath)
		apVolume.rescaleModel(old, new, float(oldmod['pixelsize']), self.params['newapix'], self.params['newbox'])
		# set new apix of the rescaled model
		self.params['apix'] = self.params['newapix']

	#=====================
	def checkExistingFile(self):
		newmodelpath = os.path.join(self.params['outdir'], self.params['name'])
		origmodelpath = self.params['file']
		apDisplay.printWarning("a model by the same filename already exists: '"+newmodelpath+"'")
		### a model by the same name already exists
		mdnew = apFile.md5sumfile(newmodelpath)
		mdold = apFile.md5sumfile(origmodelpath)
		if mdnew != mdold:
			### they are different, make unique name
			self.setNewFileName(unique=True)
			apDisplay.printWarning("the models are different, cannot overwrite, so using new name: %s" % (self.params['name'],))
			# restart
			self.start()
			return True
		elif apDatabase.isTomoInDB(mdnew):
			### they are the same and its in the database already
			apDisplay.printWarning("same model with md5sum '"+mdnew+"' already exists in the DB!")
			apDisplay.printWarning("creating new images, but skipping upload for file: '"+newmodelpath+"'")
			self.params['commit'] = False
			self.params['chimeraonly'] = True
		else:
			### they are the same, but its not in the database
			apDisplay.printWarning("the same model with name '"+newmodelpath+"' already exists, but is not uploaded!")
			if self.params['commit'] is True:
				apDisplay.printMsg("inserting model into database")
		if self.params['rescale'] is True:
			apDisplay.printError("cannot rescale an existing model")	

	#=====================
	def start(self):
		self.params['oldapix'] = self.params['newapix']
		if self.params['name'] is None:
			self.setNewFileName()
		apDisplay.printColor("Naming initial model as: "+self.params['name'], "cyan")

		newmodelpath = os.path.join(self.params['outdir'], self.params['name'])
		origmodelpath = self.params['file']
		if os.path.isfile(newmodelpath):
			### rescale old model to a new size
			if self.checkExistingFile():
				return
		else:
			### simple upload, just copy file to models folder
			apDisplay.printMsg("copying original model to a new location: "+newmodelpath)
			shutil.copyfile(origmodelpath, newmodelpath)

		### upload Initial Model
		self.params['projectId'] = apDatabase.getProjectIdFromSessionName(self.params['session'])

		### render chimera images of model
		initmodel={}
		initmodel['pixelsize'] = self.params['newapix']
		initmodel['boxsize']   = self.params['oldbox']
		initmodel['symmetry']  = self.params['syminfo']
		apRecon.renderSnapshots(newmodelpath, self.params['res'], initmodel, self.params['contour'], self.params['zoom'])


		apUpload.insertModel(self.params)


#=====================
#=====================
if __name__ == '__main__':
	uploadModel = UploadModelScript()
	uploadModel.start()
	uploadModel.close()


