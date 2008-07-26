#!/usr/bin/env python
### From Pick-wei:
###   create model from EMAN startAny function and automatically calls uploadModel.py

import os
import sys
import re
import time
import shutil
### appion
import appionScript
import apEMAN
import apDisplay
import apUpload
import apParam
import apDatabase
import appionData
import apDB

appiondb = apDB.apdb

#=====================
#=====================
class createModelScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --template=<name> --apix=<pixel> --session=<session> --diam=<int> "
			+"--description='<text>' [options]")

		self.parser.add_option("--description", dest="description",
			help="Description of the model (must be in quotes)", metavar="TEXT")
		self.parser.add_option("--session", dest="session",
			help="Session name associated with model (e.g. 06mar12a)", metavar="TEXT")
		self.parser.add_option("--outdir", dest="outdir",
			help="Location to copy the model to", metavar="PATH")
		self.parser.add_option("--norefClass", dest="norefclass", type="int",
			help="ID for the classes of the reference-free alignment", metavar="INT")
		self.parser.add_option("--exclude", dest="exclude",
			help="Class indices to be excluded e.g. 1,0,10", metavar="TEXT")
		self.parser.add_option("--symm", dest="symm", default="c1",
			help="Cn symmetry if any, e.g. --symm=4,c3", metavar="TEXT")
		self.parser.add_option("--mask", dest="mask", type="int",
			help="Mask radius", metavar="INT")
		self.parser.add_option("--lp", dest="lp", type="float",
			help="Lowpass filter radius in Fourier pixels", metavar="INT")
		self.parser.add_option("--rounds", dest="rounds", type="int",
			help="Rounds of Euler angle determination to use", metavar="INT")
		self.parser.add_option("--apix", dest="apix", type="float",
			help="Angstrom per pixel of the images in the class average file", metavar="FLOAT")
		self.parser.add_option("--commit", dest="commit", default=True,
			action="store_true", help="Commit model to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit model to database")

	#=====================
	def checkConflicts(self):
		# make sure the necessary parameters are set
		if self.params['session'] is None:
			apDisplay.printError("enter a session ID")
		if self.params['description'] is None:
			apDisplay.printError("enter a template description")
		if self.params['norefclass'] is None:
			apDisplay.printError("enter the ID for the classes of the reference-free alignment")
		if self.params['apix'] is None:
			apDisplay.printError("enter the apix for the images of the class average file")
		if self.params['lp'] is None:
			apDisplay.printError("enter the low pass filter value for the model")

		# split self.params['symm'] into its id and name
		try:
			symlist = self.params['symm'].split(",")
			print len(symlist), str(symlist)
			self.params['symm_id']   = int(symlist[0])
			self.params['symm_name'] = symlist[1].lower()
			apDisplay.printMsg("Selected symmetry: "+str(self.params['symm_id'])+" named: "+self.params['symm_name'])
		except:
			apUpload.printSymmetries()
			apDisplay.printError("Could not parse symmetry, should be of the form"
				+" --symm=4,c3 NOT --symm="+str( self.params['symm']))

	#=====================
	def cleanup(self, norefpath, norefclassid):
		clean = "rm -fv CCL.hed CCL.img"
		for file in ("CCL.hed", "CCL.img"):
			if os.path.isfile(file):
				apDisplay.printWarning("Removing file: "+file)
				os.remove(file)
		for n in range(self.params['rounds']):
			modelpath = os.path.join(norefpath, "startAny-"+str(norefclassid)+"_"+str(n+1)+".mrc")
			if not os.path.exists(modelpath):
				break

		apDisplay.printWarning("Moving threed.0a.mrc to "+norefpath+" and renaming it startAny-"
			+str(norefclassid)+"_"+str(n)+".mrc")
		shutil.copy("threed.0a.mrc", modelpath)

		oldexcludepath = os.path.join(norefpath, "exclude.lst")
		if os.path.exists(oldexcludepath):
			newexcludepath = os.path.join(norefpath, "exclude-"+str(norefclassid)+"_"+str(n)+".mrc")
			apDisplay.printWarning("Moving "+oldexcludepath+" to "+newexcludepath)
			shutil.copy(oldexcludepath, newexcludepath)
		return modelpath

	#=====================
	def changeapix(self, mrcpath, apix):
		"""
		this doesn't do anything, but copy the file, 
		you need to use shrink=## to change pixel size
			--neil
		"""
		cmd = "proc3d "+mrcpath+" "+mrcpath+" apix="+str(apix)
		print "\nChanging the apix value of "+mrcpath+"...\n"+cmd
		apEMAN.executeEmanCmd(cmd, verbose=True)

	#=====================
	def setOutDir(self):
		#auto set the output directory
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		self.params['outdir'] = os.path.join(path, "createmodel", self.timestamp)

	#=====================
	def excludedClasses(self, classfile):
		excludelist = self.params['exclude'].split(",")
		 
		apDisplay.printMsg( "Creating exclude.lst: "+norefpath )

		excludefile = os.path.join(norefpath,"exclude.lst")
		if os.path.isfile(excludefile): 
			apDisplay.printWarning("Removing the file 'exclude.lst' from: "+norefpath)
			os.remove(excludefile)
		
		f = open(excludefile, "w")
		for excludeitem in excludelist:
			f.write(str(excludeitem)+"\n")
		f.close()
		
		newclassfile = norefClassdata['classFile']+"-new"
		# old file need to be removed or the images will be appended
		if os.path.isfile(newclassfile):
			apDisplay.printWarning("removing old image file: "+newclassfile )
			os.remove(newclassfile+".hed")
			os.remove(newclassfile+".img")

		apDisplay.printMsg("Creating new class averages "+newclass+" in "+norefpath)
		excludecmd = ( "proc2d "+classfile+".hed "+newclassfile+".hed exclude="+excludefile )
		apEMAN.executeEmanCmd(excludecmd, verbose=True)

		return newclassfile

	#=====================
	def start(self):

	 	norefClassdata=appiondb.direct_query(appionData.ApNoRefClassRunData, self.params['norefclass'])

		#Get class average file path through ApNoRefRunData
		norefpath = norefClassdata['norefRun']['path']['path']

		#Get class average file name
		norefClassFile = norefClassdata['classFile']

		if self.params['exclude'] is not None:
			#create the list of the indexes to be excluded
			classfile = self.excludedClasses(classfile)
		else:
			#complete path of the class average file
			origclassfile = os.path.join(norefpath, norefClassFile)
			classfile = origclassfile+"-orig"
			apDisplay.printMsg("copying file "+origclassfile+" to "+classfile)
			shutil.copy(origclassfile+".hed", classfile+".hed")
			shutil.copy(origclassfile+".img", classfile+".img")

		#if there is no class to be excluded
		nproc = apParam.getNumProcessors()
		startAnyCmd = "startAny "+classfile+".hed proc="+str(nproc)
		if self.params['symm_name'] is not None: 
			startAnyCmd +=" sym="+self.params['symm_name']
		if self.params['mask'] is not None: 
			startAnyCmd +=" mask="+str(self.params['mask'])
		if self.params['lp'] is not None: 
			startAnyCmd +=" lp="+str(self.params['lp'])
		if self.params['rounds'] is not None: 
			startAnyCmd +=" rounds="+str(self.params['rounds'])

		apDisplay.printMsg("Creating 3D model using class averages with EMAN function of startAny")
		apEMAN.executeEmanCmd(startAnyCmd, verbose=True)

		#cleanup the extra files, move the created model to the same folder as the class average and rename it as startAny.mrc
		modelpath = self.cleanup(norefpath, self.params['norefclass'])
		#change its apix back to be the same as the class average file
		self.changeapix(modelpath, self.params['apix'])


		#call uploadModel
		upload = ("uploadModel.py --file=%s --session=%s --apix=%.3f --res=%i --symmetry=%i --contour=1.5 --zoom=1.5 --description=\"%s\"" %
			(modelpath, self.params['session'], self.params['apix'], 
			int(self.params['lp']), int(self.params['symm_id']), self.params['description']) )	

		print "\n############################################"
		print "\nReady to upload model "+modelpath+" into the database...\n"
		print upload
		time.sleep(10)
		if self.params['commit']:	
			apEMAN.executeEmanCmd(upload, verbose=True)


#=====================
#=====================
if __name__ == '__main__':
	createModel = createModelScript()
	createModel.start()
	createModel.close()
