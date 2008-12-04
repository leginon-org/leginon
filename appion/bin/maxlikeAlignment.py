#!/usr/bin/env python
#
import os
import time
import sys
import random
import math
import shutil
import cPickle
#appion
import appionScript
import apDisplay
import apAlignment
import apFile
import apTemplate
import apStack
import apParam
import apEMAN
import apXmipp
from apSpider import alignment
import appionData
import apProject
import dbconfig
import MySQLdb

#=====================
#=====================
class MaximumLikelihoodScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int",
			help="Number of particles to use", metavar="#")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")

		### radii
		self.parser.add_option("-m", "--mask", dest="maskrad", type="float",
			help="Mask radius for particle coran (in Angstoms)", metavar="#")
		self.parser.add_option("--lowpass", "--lp", dest="lowpass", type="int",
			help="Low pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--highpass", "--hp", dest="highpass", type="int",
			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("--bin", dest="bin", type="int", default=1,
			help="Bin images by factor", metavar="#")

		self.parser.add_option("--max-iter", dest="maxiter", type="int", default=100,
			help="Maximum number of iterations", metavar="#")
		self.parser.add_option("--num-ref", dest="numrefs", type="int",
			help="Number of classes to create", metavar="#")
		self.parser.add_option("--angle-interval", dest="psistep", type="int", default=5,
			help="In-plane rotation sampling interval (degrees)", metavar="#")
		#self.parser.add_option("--templates", dest="templateids",
		#	help="Template Id for template init method", metavar="1,56,34")

		self.parser.add_option("-C", "--commit", dest="commit", default=True,
			action="store_true", help="Commit stack to database")
		self.parser.add_option("--no-commit", dest="commit", default=True,
			action="store_false", help="Do not commit stack to database")

		self.parser.add_option("-F", "--fast", dest="fast", default=True,
			action="store_true", help="Use fast method")
		self.parser.add_option("--no-fast", dest="fast", default=True,
			action="store_false", help="Do NOT use fast method")

		self.parser.add_option("-M", "--mirror", dest="mirror", default=True,
			action="store_true", help="Use mirror method")
		self.parser.add_option("--no-mirror", dest="mirror", default=True,
			action="store_false", help="Do NOT use mirror method")

		self.parser.add_option("-o", "--outdir", dest="outdir",
			help="Output directory", metavar="PATH")
		self.parser.add_option("-d", "--description", dest="description",
			help="Description of run", metavar="'TEXT'")
		self.parser.add_option("-n", "--runname", dest="runname",
			help="Name for this run", metavar="STR")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		#if self.params['description'] is None:
		#	apDisplay.printError("run description was not defined")
		if self.params['numrefs'] is None:
			apDisplay.printError("a number of classes was not provided")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
		maxparticles = 15000
		if self.params['numpart'] > maxparticles:
			apDisplay.printError("too many particles requested, max: " 
				+ str(maxparticles) + " requested: " + str(self.params['numpart']))
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		if self.params['numpart'] > apFile.numImagesInStack(stackfile):
			apDisplay.printError("trying to use more particles "+str(self.params['numpart'])
				+" than available "+str(apFile.numImagesInStack(stackfile)))
		if self.params['numpart'] is None:
			self.params['numpart'] = apFile.numImagesInStack(stackfile)

	#=====================
	def setOutDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['outdir'] = os.path.join(uppath, "maxlike", self.params['runname'])

	#=====================
	def dumpParameters(self):
		self.params['runtime'] = time.time() - self.t0
		self.params['timestamp'] = self.timestamp
		paramfile = "maxlike-"+self.timestamp+"-params.pickle"
		pf = open(paramfile, "w")
		cPickle.dump(self.params, pf)
		pf.close()

	#=====================
	def insertMaxLikeJob(self):
		maxjobq = appionData.ApMaxLikeJobData()
		maxjobq['runname'] = self.params['runname']
		maxjobq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
		maxjobdatas = maxjobq.query(results=1)
		if maxjobdatas:
			alignrunq = appionData.ApAlignRunData()
			alignrunq['runname'] = self.params['runname']
			alignrunq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['outdir']))
			alignrundata = alignrunq.query(results=1)
			if maxjobdatas[0]['finished'] is True or alignrundata:
				apDisplay.printError("This run name already exists as finished in the database, please change the runname")
		maxjobq['project|projects|project'] = apProject.getProjectIdFromStackId(self.params['stackid'])
		maxjobq['timestamp'] = self.timestamp
		maxjobq['finished'] = False
		maxjobq['hidden'] = False
		maxjobq.insert()
		self.params['maxlikejobid'] = maxjobq.dbid
		print "self.params['maxlikejobid']",self.params['maxlikejobid']
		return

	#=====================
	def readyUploadFlag(self):	
		config = dbconfig.getConfig('appionData')
		dbc = MySQLdb.Connect(**config)
		cursor = dbc.cursor()
		query = (
			"  UPDATE ApMaxLikeJobData "
			+" SET `finished` = '1' "
			+" WHERE `DEF_id` = '"+str(self.params['maxlikejobid'])+"'"
		)
		cursor.execute(query)
		cursor.close()
		dbc.close()

	#=====================
	def estimateIterTime(self):
		secperiter = 0.12037
		calctime = (
			(self.params['numpart']/1000.0)
			*self.params['numrefs']
			*(self.stack['boxsize']/self.params['bin'])**2
			/self.params['psistep']
			*secperiter
		)
		if self.params['mirror'] is True:
			calctime *= 2.0
		self.params['estimatedtime'] = calctime
		apDisplay.printColor("Estimated first iteration time: "+apDisplay.timeString(calctime), "purple")

	#=====================
	def writeGaribaldiJobFile(self):
		nproc = 128
		rundir = os.path.join("/garibaldi/people-a/vossman/xmippdata", self.params['runname'])
		xmippexe = "/garibaldi/people-a/vossman/Xmipp-2.2-x64/bin/xmipp_mpi_ml_align2d"
		newoutdir = "$PBSREMOTEDIR/"
		xmippopts = ( ""
			+" -i $PBSREMOTEDIR/partlist2.doc \\\n"
			+" -o $PBSREMOTEDIR/"+self.timestamp+" \\\n"
			+" -nref "+str(self.params['numrefs'])
			+" -iter "+str(self.params['maxiter'])
			+" -psi_step "+str(self.params['psistep'])
			+" -eps 5e-4"
		)
		if self.params['fast'] is True:
			xmippopts += " -fast"
		if self.params['mirror'] is True:
			xmippopts += " -mirror"

		### write to file
		jobfile = "xmipp-"+self.timestamp+".job"
		results = rundir+"/"+self.params['runname']+"-results.tgz"
		f = open(jobfile, "w")
		f.write("#PBS -l nodes="+str(nproc/4)+":ppn=4\n")
		f.write("#PBS -l walltime=240:00:00\n")
		f.write("#PBS -l cput=240:00:00\n")
		f.write("#PBS -r n\n")
		f.write("#PBS -k oe\n")
		f.write("\n")
		f.write("## outdir: "+self.params['outdir']+"\n")
		f.write("\n")
		f.write("cd "+rundir+"\n")
		f.write("rm -fv pbstempdir "+results+"\n")
		f.write("ln -s $PBSREMOTEDIR pbstempdir\n")
		f.write("cd $PBSREMOTEDIR\n")
		f.write("tar xzf "+rundir+"/particles.tgz\n")
		f.write("\n")
		f.write("foreach line ( `cat partlist.doc | cut -f1 -d' '` )\n")
		f.write("  echo $PBSREMOTEDIR/`echo $line | sed 's/^.*partfiles/partfiles/'` 1 >> partlist2.doc\n")
		f.write("end\n")
		f.write("\n")
		f.write("setenv MPI_HOME /garibaldi/people-b/applications/openmpi-1.2.2/\n")
		f.write("setenv XMIPP_HOME /garibaldi/people-a/vossman/Xmipp-2.2-x64/\n")
		f.write("set path = ( $MPI_HOME/bin $path )\n")
		f.write("setenv LD_LIBRARY_PATH $MPI_HOME/lib:$XMIPP_HOME/lib:/usr/lib:/lib\n")
		f.write("\n")
		f.write("mpirun -np "+str(nproc)+" "+xmippexe+" \\\n")
		f.write(xmippopts+"\n")
		f.write("\n")
		f.write("tar zcf "+results+" *.???\n")
		f.write("\n")
		f.write("exit\n")
		f.close()

		apDisplay.printMsg("tar zcf particles.tgz partlist.doc partfiles/")
		apDisplay.printMsg("rsync -vaP "+jobfile+" garibaldi:"+rundir+"/")
		apDisplay.printMsg("rsync -vaP particles.tgz garibaldi:"+rundir+"/")
		#sys.exit(1)

	#=====================
	def start(self):
		self.insertMaxLikeJob()
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])
		self.estimateIterTime()
		self.dumpParameters()

		### process stack to local file
		self.params['localstack'] = os.path.join(self.params['outdir'], self.timestamp+".hed")
		proccmd = "proc2d "+self.stack['file']+" "+self.params['localstack']+" apix="+str(self.stack['apix'])
		if self.params['bin'] > 1:
			proccmd += " shrink="+str(self.params['bin'])
		if self.params['highpass'] > 1:
			proccmd += " hp="+str(self.params['highpass'])
		if self.params['lowpass'] > 1:
			proccmd += " lp="+str(self.params['lowpass'])
		proccmd += " last="+str(self.params['numpart'])
		apEMAN.executeEmanCmd(proccmd, verbose=True)

		### convert stack into single spider files
		self.partlistdocfile = apXmipp.breakupStackIntoSingleFiles(self.params['localstack'])

		### write garibaldi job file
		self.writeGaribaldiJobFile()

		### setup Xmipp command
		aligntime = time.time()
		
		xmippopts = ( " "
			+" -i "+os.path.join(self.params['outdir'], self.partlistdocfile)
			+" -nref "+str(self.params['numrefs'])
			+" -iter "+str(self.params['maxiter'])
			+" -o "+os.path.join(self.params['outdir'], "part"+self.timestamp)
			+" -psi_step "+str(self.params['psistep'])
			+" -eps 5e-4 "
		)
		if self.params['fast'] is True:
			xmippopts += " -fast "
		if self.params['mirror'] is True:
			xmippopts += " -mirror "

		nproc = apParam.getNumProcessors()
		mpirun = apParam.getExecPath("mpirun")
		if False and nproc > 3 and mpirun is not None:
			### use multi-processor
			xmippexe = apParam.getExecPath("xmipp_mpi_ml_align2d", die=True)
			mpiruncmd = mpirun+" -np "+str(nproc-1)+" "+xmippexe+" "+xmippopts
			apEMAN.executeEmanCmd(mpiruncmd, verbose=True, showcmd=True)
		else:
			### use single processor
			xmippexe = apParam.getExecPath("xmipp_ml_align2d", die=True)
			apEMAN.executeEmanCmd(xmippexe+" "+xmippopts, verbose=True, showcmd=True)
		aligntime = time.time() - aligntime
		apDisplay.printMsg("Alignment time: "+apDisplay.timeString(aligntime))

		### align references
		xmippopts = ( " "
			+" -i "+os.path.join(self.params['outdir'], "part"+self.timestamp+".sel")
			+" -nref 1 "
			+" -iter "+str(self.params['maxiter'])
			+" -o "+os.path.join(self.params['outdir'], "ref"+self.timestamp)
			+" -psi_step 1 "
			+" -eps 5e-4 "
		)
		xmippexe = apParam.getExecPath("xmipp_ml_align2d")
		apEMAN.executeEmanCmd(xmippexe+" "+xmippopts, verbose=True)

		### create a quick mrc
		emancmd = "proc2d ref"+self.timestamp+"_ref000001.xmp average.mrc"
		apEMAN.executeEmanCmd(emancmd, verbose=True)

		self.readyUploadFlag()
		self.dumpParameters()

#=====================
if __name__ == "__main__":
	maxLike = MaximumLikelihoodScript()
	maxLike.start()
	maxLike.close()


