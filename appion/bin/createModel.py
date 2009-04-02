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
import apChimera
import apStack
import apUpload
import apFile
import apParam
import apDatabase
import appionData

#=====================
#=====================
class createModelScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --template=<name> --apix=<pixel> --session=<session> --diam=<int> "
			+"--description='<text>' [options]")

		self.parser.add_option("--session", dest="session",
			help="Session name associated with model (e.g. 06mar12a)", metavar="TEXT")
		self.parser.add_option("--norefClass", dest="norefclass", type="int",
			help="ID for the classes of the reference-free alignment", metavar="INT")
		self.parser.add_option("--exclude", dest="exclude",
			help="Class indices to be excluded e.g. 1,0,10", metavar="TEXT")
		self.parser.add_option("--method", dest="method",
			help="EMAN method for commonline backprojection: startIcos, startCSym, startAny, startOct", metavar="TEXT")
		self.parser.add_option("--apix", dest="apix", type="float",
			help="Angstrom per pixel of the images in the class average file", metavar="FLOAT")

		#===================
		#Common Parameters
		#===================
		self.parser.add_option("--symm", dest="symm", default="c1",
			help="startAny, startCSym & startIcos: Cn symmetry if any, e.g. --symm=4,c3", metavar="TEXT")

		#===================
		#StartAny Parameters
		#===================
		self.parser.add_option("--mask", dest="mask", type="int",
			help="startAny: Mask radius", metavar="INT")
		self.parser.add_option("--lp", dest="lp", type="float",
			help="startAny: Lowpass filter radius in Fourier pixels", metavar="INT")
		self.parser.add_option("--rounds", dest="rounds", type="int",
			help="startAny: Rounds of Euler angle determination to use", metavar="INT")

		#===================
		#StartCSym Parameters
		#===================
		self.parser.add_option("--partnum", dest="partnum",
			help="startCSym & startIcos & starOct: Number of particles to use for each view. ~10% of the total particle", metavar="INT")
		self.parser.add_option("--imask", dest="imask",
			help="startCSym & startIcos: Inside mask used to exclude inside regions", metavar="INT")

		#===================
		#StartOct Parameters
		#===================

	#=====================
	def checkConflicts(self):
		# make sure the necessary parameters are set
		if self.params['session'] is None:
			apDisplay.printError("enter a session ID")
		else:
			self.sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])

		if self.params['description'] is None:
			apDisplay.printError("enter a template description")
		if self.params['norefclass'] is None:
			apDisplay.printError("enter the ID for the classes of the reference-free alignment")
		if self.params['apix'] is None:
			apDisplay.printError("enter the apix for the images of the class average file")
		if self.params['method'] is None:
			apDisplay.printError("enter the EMAN commonline method")

		print self.params['method']

		# make sure each of the method has its required options
		if self.params['method'] != 'startAny' and self.params['method'] != 'startCSym' and self.params['method'] != 'startOct' and self.params['method'] != 'startIcos':
			apDisplay.printError("enter a correct EMAN commonline method: startAny, startCSym, startOct, startIcos")

		if self.params['method'] == 'startAny' and (self.params['lp'] is None or self.params['symm'] is None):
			apDisplay.printError("Make sure options lp, mask, rounds and symm are provided")

		if self.params['method'] == 'startCSym'and (self.params['partnum'] is None or self.params['symm'] is None):
			apDisplay.printError("Make sure options partnum and symm are provided")

		if self.params['method'] == 'startIcos' and (self.params['partnum'] is None):
			apDisplay.printError("Make sure options partnum is provided")

		if self.params['method'] == 'startAny' or self.params['method'] == 'startCSym':
			# split self.params['symm'] into its id and name
				apUpload.find
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
	def cleanup(self, norefpath, norefclassid, method):
		clean = "rm -fv CCL.hed CCL.img"
		for file in ("CCL.hed", "CCL.img"):
			if os.path.isfile(file):
				apDisplay.printWarning("Removing file: "+file)
				os.remove(file)
		if self.params['rounds']:
			for n in range(self.params['rounds']):
				modelpath = os.path.join(norefpath, method+"-"+str(norefclassid)+"_"+str(n+1)+".mrc")
				if not os.path.exists(modelpath):
					break

			apDisplay.printWarning("Moving threed.0a.mrc to "+norefpath+" and renaming it "+method+"-"
				+str(norefclassid)+"_"+str(n)+".mrc")
			shutil.copy("threed.0a.mrc", modelpath)

			oldexcludepath = os.path.join(norefpath, "exclude.lst")
			if os.path.exists(oldexcludepath):
				newexcludepath = os.path.join(norefpath, "exclude-"+str(norefclassid)+"_"+str(n)+".mrc")
				apDisplay.printWarning("Moving "+oldexcludepath+" to "+newexcludepath)
				shutil.copy(oldexcludepath, newexcludepath)
		else:
			modelpath = os.path.join(norefpath, method+"-"+str(norefclassid)+".mrc")

			apDisplay.printWarning("Moving threed.0a.mrc to "+norefpath+" and renaming it "+method+"-"
				+str(norefclassid)+".mrc")
			shutil.copy("threed.0a.mrc", modelpath)

			oldexcludepath = os.path.join(norefpath, "exclude.lst")
			if os.path.exists(oldexcludepath):
				newexcludepath = os.path.join(norefpath, "exclude-"+str(norefclassid)+".mrc")
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
	def setRunDir(self):
		#auto set the output directory
		self.sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		self.params['rundir'] = os.path.join(path, "createmodel", self.timestamp)

	#=====================
	def excludedClasses(self, origclassfile, norefpath):
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

		newclassfile = origclassfile+"-new"
		# old file need to be removed or the images will be appended
		if os.path.isfile(newclassfile):
			apDisplay.printWarning("removing old image file: "+newclassfile )
			os.remove(newclassfile+".hed")
			os.remove(newclassfile+".img")

		apDisplay.printMsg("Creating new class averages "+newclassfile)
		excludecmd = ( "proc2d "+origclassfile+".hed "+newclassfile+".hed exclude="+excludefile )
		apEMAN.executeEmanCmd(excludecmd, verbose=True)

		return newclassfile

	#=====================
	def uploadDensity(self, volfile):
		### insert 3d volume density
		densq = appionData.Ap3dDensityData()
		densq['path'] = appionData.ApPathData(path=os.path.dirname(os.path.abspath(volfile)))
		densq['name'] = os.path.basename(volfile)
		densq['hidden'] = False
		densq['norm'] = True
		#densq['symmetry'] = appionData.ApSymmetryData.direct_query(25)
		densq['pixelsize'] = self.params['apix']
		densq['boxsize'] = self.params['box']
		densq['lowpass'] = self.params['lp']
		#densq['highpass'] = self.params['highpasspart']
		#densq['mask'] = self.params['radius']
		densq['description'] = self.params['description']
		densq['resolution'] = self.params['lp']
		densq['session'] = self.sessiondata
		densq['md5sum'] = apFile.md5sumfile(volfile)
		densq['eman'] = self.params['method']
		if self.params['commit'] is True:
			densq.insert()
		return

	#=====================
	def start(self):

		norefClassdata=appionData.ApNoRefClassRunData.direct_query(self.params['norefclass'])

		#Get class average file path through ApNoRefRunData
		norefpath = norefClassdata['norefRun']['path']['path']

		self.params['box'] = apStack.getStackBoxsize((norefClassdata['norefRun']['stack']).dbid)

		#Get class average file name
		norefClassFile = norefClassdata['classFile']
		origclassfile = os.path.join(norefpath, norefClassFile)

		if self.params['exclude'] is not None:
			#create the list of the indexes to be excluded
			classfile = self.excludedClasses(origclassfile, norefpath)
		else:
			#complete path of the class average file
			classfile = origclassfile+"-orig"
			apDisplay.printMsg("copying file "+origclassfile+" to "+classfile)
			shutil.copy(origclassfile+".hed", classfile+".hed")
			shutil.copy(origclassfile+".img", classfile+".img")

		#warn if the number of particles to use for each view is more than 10% of the total number of particles
		if self.params['exclude'] is not None:
			numclass = norefClassdata['num_classes'] - len(self.params['exclude'].split(","))
		else:
			numclass = norefClassdata['num_classes']

		if self.params['partnum'] is not None and numclass/10 < int(self.params['partnum']):
			apDisplay.printWarning("particle number of "+ self.params['partnum'] + " is greater than 10% of the number of selected classes")


		nproc = apParam.getNumProcessors()

		#construct command for each of the EMAN commonline method
		if self.params['method']=='startAny':
			startCmd = "startAny "+classfile+".hed proc="+str(nproc)
			if self.params['symm_name'] is not None:
				startCmd +=" sym="+self.params['symm_name']
			if self.params['mask'] is not None:
				startCmd +=" mask="+str(self.params['mask'])
			if self.params['lp'] is not None:
				startCmd +=" lp="+str(self.params['lp'])
			if self.params['rounds'] is not None:
				startCmd +=" rounds="+str(self.params['rounds'])

		elif self.params['method']=='startCSym':
			startCmd = "startcsym "+classfile+".hed "
			if self.params['partnum'] is not None:
				startCmd +=" "+self.params['partnum']
			if self.params['symm_name'] is not None:
				startCmd +=" sym="+self.params['symm_name']
			if self.params['imask'] is not None:
				startCmd +=" imask="+self.params['imask']

		elif self.params['method']=='startOct':
			startCmd = "startoct "+classfile+".hed "
			if self.params['partnum'] is not None:
				startCmd +=" "+self.params['partnum']

		elif self.params['method']=='startIcos':
			startCmd = "starticos "+classfile+".hed "
			if self.params['partnum'] is not None:
				startCmd +=" "+self.params['partnum']
			if self.params['imask'] is not None:
				startCmd +=" imask="+self.params['imask']

		apDisplay.printMsg("Creating 3D model using class averages with EMAN function of"+self.params['method']+"")
		print startCmd
		apEMAN.executeEmanCmd(startCmd, verbose=False)

		#cleanup the extra files, move the created model to the same folder as the class average and rename it as startAny.mrc
		modelpath = self.cleanup(norefpath, self.params['norefclass'], self.params['method'])
		#change its apix back to be the same as the class average file
		self.changeapix(modelpath, self.params['apix'])

		### chimera imaging
		apChimera.renderSnapshots(modelpath, contour=1.5, zoom=1.0, sym='c1')
		apChimera.renderAnimation(modelpath, contour=1.5, zoom=1.0, sym='c1')

		### upload it
		self.uploadDensity(modelpath)

#		#call uploadModel
#		upload = ("uploadModel.py --file=%s --session=%s --apix=%.3f --res=%i --symmetry=%i --contour=1.5 --zoom=1.5 --description=\"%s\"" %
#			(modelpath, self.params['session'], self.params['apix'],
#			int(self.params['lp']), int(self.params['symm_id']), self.params['description']) )

#		print "\n############################################"
#		print "\nReady to upload model "+modelpath+" into the database...\n"
#		if not self.params['commit']:
#			apDisplay.printWarning("Commit flag is not turned on... Model will not be uploaded!")
#		time.sleep(10)
#		if self.params['commit']:
#			apEMAN.executeEmanCmd(upload, verbose=True)


#=====================
#=====================
if __name__ == '__main__':
	createModel = createModelScript()
	createModel.start()
	createModel.close()
