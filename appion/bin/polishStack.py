#!/usr/bin/env python

#python
import os
import re
import time
import math
import subprocess
#appion
from appionlib import apRemoteJob
from appionlib import appionScript
from appionlib import appiondata
from appionlib import apDisplay
from appionlib import apDDprocess
from appionlib import apDatabase
from appionlib import apStack
from appionlib import apProject
from appionlib import apConfig
from appionlib import apParallelTasks
import sinedon

#class stackPolisher(apRemoteJob.RemoteJob):
class stackPolisherScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
#		super(stackPolisher,self).setupParserOptions()
		self.parser.set_usage("Usage: %prog --stackid=ID [options]")

		# appion stack & ddstack ids
		self.parser.add_option("-s", "--stackid", dest="stackid", type="int",
			help="Stack database id", metavar="ID")
		self.parser.add_option("--ddstackid", dest="ddstackid", type="int",
			help="ID for ddstack run to make aligned & polished stack (required)", metavar="INT")

		# job splitting
		self.parser.add_option("--micrographs_per_job", dest="micperjob", type="int", default=1,
			help="number of micrographs per job. Will create and submit N/(this_value) job files, \
				where N is the number of micrographs in the dataset", metavar="INT")

		# general options

		# program options
		self.parser.add_option("--particleradius", dest="particleradius", type=int,
			help="radius for particles within box (in Angstroms)", metavar="INT")
		self.parser.add_option("--framefirstali", dest="framefirstali", type=int, default=0,
		   help="first frame to be used in alignment, default = 0", metavar="")
		self.parser.add_option("--framelastali", dest="framelastali", type=int,
			help="last frame to be used in alignment, default = use all", metavar="")
		self.parser.add_option("--framefirstave", dest="framefirstave", type=int, default=0,
			help="first frame to be used in average of frames, default = 0", metavar="")
		self.parser.add_option("--framelastave", dest="framelastave", type=int,
			help="last frame to be used in average of frames, default = use all", metavar="")
		self.parser.add_option("--smooth", dest="smooth", type=float, default=1.0,
			help="specifies the amount of smoothing forced on trajectories of particles", metavar="")
		self.parser.add_option("--exaggerate", dest="exaggerate", type=int, default=10,
			help="factor by which particle trajectories should be exaggerated in vector file", metavar="")
		self.parser.add_option("--invertoutput", dest="invertoutput", default=False, action="store_true",
			help="inverts output from movie densities", metavar="")
		self.parser.add_option("--localavg", dest="localavg", default=False, action="store_true",
			help="performs local averaging of trajectories", metavar="")
		self.parser.add_option("--localavgsigma", dest="localavgsigma", type=int, default=500,
			help="the standard deviation used to weight local averaging", metavar="")
		self.parser.add_option("--expweight", dest="expweight", default=False, action="store_true",
			help="turns on exposure weighting, dont specify option to turn off exposure weighting", metavar="")
		self.parser.add_option("--expperframe", dest="expperframe", type=float,
			help="Exposure per frame in electrons per Angstrom squared", metavar="")
		self.parser.add_option("--rmax1", dest="rmax1", type=int, default=500,
			help="Low resolution cutoff (in Angstroms) used for alignment", metavar="")
		self.parser.add_option("--rmax2", dest="rmax2", type=int, default=20,
			help="High resolution cutoff (in Angstroms) used for alignment", metavar="")
		self.parser.add_option("--bfactor", dest="bfactor", type=int, default=2000,
			help="B-factor (in A**2) used for alignment", metavar="")
		self.parser.add_option("--total_dose", dest="total_dose", type=float, 
			help="Total dose for all frames, if value not saved in database (optional)", metavar="")
#		self.parser.add_option("", dest="", type="", default="",
#			help="", metavar="")


	#=====================
	def checkConflicts(self):
		
		### setup correct database after we have read the project id
		if 'projectid' in self.params and self.params['projectid'] is not None:
			apDisplay.printMsg("Using split database")
			# use a project database
			newdbname = apProject.getAppionDBFromProjectId(self.params['projectid'])
			sinedon.setConfig('appiondata', db=newdbname)
			apDisplay.printColor("Connected to database: '"+newdbname+"'", "green")
		
		if self.params['stackid'] is None:
			apDisplay.printError("stackid was not defined")

		if self.params['expweight'] is False:
			apDisplay.printWarning("Exposure weighting is turned off, make sure this is what you want")
		if self.params['localavg'] is False:
			apDisplay.printWarning("Trajectory local averaging is turned off, make sure this is what you want")

		# DD processes
		self.dd = apDDprocess.DDStackProcessing()
		print self.dd
	
		# get stack data
		self.stackdata = appiondata.ApStackData.direct_query(self.params['stackid'])
		self.stackparts = apStack.getStackParticlesFromId(self.params['stackid'], msg=True)
		self.sessiondata = apStack.getSessionDataFromStackId(self.params['stackid'])
		
		# query image
		qimage = self.stackparts[0]['particle']['image']

		# pixel size info
		self.params['apix'] = apStack.getMicrographPixelSizeFromStackId(self.params['stackid'])
		self.params['box'] = self.stackdata['boxsize']
		self.params['particleradius'] = self.params['particleradius'] / self.params['apix']
		if self.params['particleradius'] > self.params['box'] / 2.0:
			apDisplay.printWarning("specified particle radius greater than box radius, \
				setting particle radius to 0.8 * boxsize")

		# micrograph & frame info
		frames = qimage['use frames']
		nframes = len(frames)
		if self.params['framelastali'] is None:
			self.params['framelastali'] = frames[-1]
		if self.params['framelastave'] is None:
			self.params['framelastave'] = frames[-1]

		# microscope kV
		self.params['kv'] = qimage['scope']['high tension']/1000.0

		# query exposure per frame, if not set here
		if self.params['total_dose'] is not None:
			dose = self.params['total_dose']
		else:
			try:
				dose = apDatabase.getDoseFromImageData(qimage)
			except:
				apDisplay.printError("dose not specified and not in database, please specify explicitly")
		if self.params['expperframe'] is None and self.params['expweight'] is True:
			if dose is not None:
				self.params['expperframe'] = dose / nframes
			else:
				apDisplay.printError("exposure per frame needs to be specified, cannot find in database")
	
		# dimensions
		self.params['framex'] = int(apDatabase.getDimensionsFromImageData(qimage)['x'])
		self.params['framey'] = int(apDatabase.getDimensionsFromImageData(qimage)['y'])

		# DD info
		self.dd.setImageData(qimage)
		self.dd.setDDStackRun(self.params['ddstackid'])
		self.ddstackpath = self.dd.getDDStackRun()['path']['path']

		# check if DD stack has been corrected, it shouldn't be!
		
	#=====================
	def getExecutablePath(self):
		exename = "alignparts_lmbfgs.exe"
		prgmexe = subprocess.Popen("which %s" % exename, shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if not os.path.isfile(prgmexe):
			prgmexe = os.path.join(apParam.getAppionDirectory(), 'bin', exename)
		if not os.path.isfile(prgmexe):
			apDisplay.printError("%s was not found at: %s" % (exename, apParam.getAppionDirectory()))
		return exename

	#=====================
	def write_bash_file_for_submission(self, jobn):
		''' bash script file that will be submitted to the cluster '''

		bashfile = "alignparts_lmbfgs_%d.bash" % jobn
		print "writing bashfile: ", bashfile
		f = open(bashfile, "w")

		# set some parameters
		zeroframe = math.ceil((self.params['framelastali']-self.params['framefirstali']) / 2.0 + 1)

		# submission info
		#		f.write("#!/bin/bash\n")
		#		f.write("#$ -pe bpho_dmitry 1\n")
		#		f.write("#$ -cwd\n")
		#		f.write("#$ -V\n")
		#		f.write("#$ -S /bin/bash\n")
		
		# locations of executables provided by user
		f.write("alignparts_lmbfgs=%s\n" % self.getExecutablePath())
		
		# input/out file information
		f.write("movielist=inputs/movies_%d.txt\n" % jobn)
		f.write("coordlist=inputs/coords_%d.txt\n" % jobn)
		f.write("particlepath=Particles/\n")
		f.write("moviepath=movies/\n")
		f.write("lmbfgsflag=_lmbfgs\n")
		f.write("lmbfgsext=mrc\n")
		f.write("boxsize=%d\n" % self.params['box'])
		f.write("particleradius=%d\n" % self.params['particleradius'])
		f.write("pixelsize=%.3f\n" % self.params['apix'])
		f.write("framex=%d\n" % self.params['framex'])
		f.write("framey=%d\n" % self.params['framey'])
		f.write("framefirstali=%d\n" % self.params['framefirstali'])
		f.write("framelastali=%d\n" % self.params['framelastali'])
		f.write("framefirstave=%d\n" % self.params['framefirstave'])
		f.write("framelastave=%d\n" % self.params['framelastave'])
		f.write("smooth=%.1fd4\n" % self.params['smooth'])
		f.write("zeroframe=%d\n" % zeroframe)
		f.write("exaggerate=%d\n" % self.params['exaggerate'])
		f.write("invertoutput=%d\n" % self.params['invertoutput'])
		f.write("localavg=%d\n" % self.params['localavg'])
		f.write("localavgsigma=%d\n" % self.params['localavgsigma'])
		f.write("expweight=%d\n" % self.params['expweight'])
		f.write("akv=%d\n" % self.params['kv'])
		f.write("expperframe=%.3f\n" % self.params['expperframe'])
		f.write("motweight=0\n") # defaulted to 0, will be removed in next version
		f.write("vecext=vec\n")
		f.write("maxparts=100000\n")
		f.write("nsigma=5\n")
		f.write("rmax1=%d\n" % self.params['rmax1'])
		f.write("rmax2=%d\n" % self.params['rmax2'])
		f.write("bfactor=%d\n" % self.params['bfactor'])
		f.write("factr=1d7\n")
		f.write("\n\n\n")
		f.write("time $alignparts_lmbfgs << eot\n")
		f.write("$movielist\n")
		f.write("$coordlist\n")
		f.write("$boxsize,0,$particleradius,$pixelsize,$nsigma,$rmax1,$rmax2\n")
		f.write("$motweight,$expweight,$akv,$expperframe\n")
		f.write("$bfactor,$smooth,$exaggerate,$zeroframe,$invertoutput\n")
		f.write("$localavg,$maxparts,$localavgsigma\n")
		f.write("$framefirstali,$framelastali,$framefirstave,$framelastave\n")
		f.write("$factr\n")
		f.write("$moviepath\n")
		f.write("$particlepath\n")
		f.write("$lmbfgsflag\n")
		f.write("$vecext\n")
		f.write("$lmbfgsext\n")
		f.write("eot")


		f.close()

		return bashfile

	#=====================
	def write_inputs(self, stackparts):
		''' 
			writes inputs: particle coordinates files, movie info files, individual job submission files
			these are necessary for alignment program 
		'''

		apDisplay.printMsg("writing particle coordinates & movie info to files")
		moviefile = open(os.path.join(self.params['rundir'], "inputs", "allmovies.txt"), "w")
		oldmovieid = None
		nmic = 0
		jobn = 0 # job number
		self.joblist = []
		for part in stackparts:
			
			# split up inputs for coordinate files and movie files for faster processing
			if nmic == 0:
				splitinputscf = open(os.path.join(self.params['rundir'],"inputs","coords_%d.txt" % jobn), "w")
				splitinputsmf = open(os.path.join(self.params['rundir'],"inputs","movies_%d.txt" % jobn), "w")
			
			# get DD & image info for particle
			self.dd.setImageData(part['particle']['image'])
			movieid = part['particle']['image'].dbid
			alignpairdata = self.dd.getAlignImagePairData(None,query_source=not self.dd.getIsAligned())
			if alignpairdata is False:
				apDisplay.printWarning('Image not used for nor a result of alignment.')

			# need separate file for each movie
			if movieid != oldmovieid:
				
				# close coordfile already in loop, open new one
				if oldmovieid is not None:
					coordfile.close()
				
				# write coords to file with DD image name
				orig_dd_file = alignpairdata['source']['filename']
				coordf = os.path.join(self.params['rundir'], "movies", orig_dd_file+".coord")
				coordfile = open(coordf, "w")
				coordfile.write("%-9s%-9s%-9s\n" % ("x","y","density"))
				
				apDisplay.printMsg("writing particle & movie data for %s movie" % orig_dd_file)
				
				# write new movie to file
				ddstackfile = os.path.join("movies", orig_dd_file+"_st.mrc")
				if not os.path.exists(ddstackfile):
					error = "DD stack %s_st.mrc not found, cannot run polisher, check your inputs " % orig_dd_file
					error+= "and make sure micrographs are not hidden. May need to rerun ddstack maker "
					error+= "and remove option --no-rejects to reprocess all micrographs. "
					apDisplay.printError(error)
				moviefile.write("%s\n" % ddstackfile)

				# write split inputs
				splitinputscf.write("%s.coord\n" % orig_dd_file)
				splitinputsmf.write("%s\n" % ddstackfile)

				nmic+=1
				if nmic == self.params['micperjob']:
					bashfile = self.write_bash_file_for_submission(jobn)
					os.chmod(bashfile, 0755)
					command = os.path.join(self.params['rundir'],bashfile)
					self.joblist.append(command)
					nmic = 0
					jobn += 1
					splitinputscf.close()
					splitinputsmf.close()
			
				oldmovieid = movieid

			# get & write coordinates
			xcoord = part['particle']['xcoord']
			ycoord = part['particle']['ycoord']
			coordfile.write("%-9d%-9d%-9d\n" % (xcoord, ycoord, 0))
	
		# close last coordfile
		coordfile.close()
		moviefile.close()
		if nmic < self.params['micperjob']:
			bashfile = self.write_bash_file_for_submission(jobn)
			os.chmod(bashfile, 0755)
			command = os.path.join(self.params['rundir'],bashfile)
			self.joblist.append(command)
			splitinputscf.close()
			splitinputsmf.close()

	#=====================
	def convertAndQueryParams(self):
		return
	#=====================
	def start(self):
		# config file for multiple job submission
		self.configfile = apConfig.getAppionConfigFile()
		
		# make necessary directories
		if not os.path.exists(os.path.join(self.params['rundir'],"inputs")):
			os.makedirs(os.path.join(self.params['rundir'],"inputs"))
		if not os.path.exists(os.path.join(self.params['rundir'],"Particles")):
			os.makedirs(os.path.join(self.params['rundir'],"Particles"))
		moviedir = os.path.join(self.params['rundir'],"movies")
		if not os.path.exists(moviedir):
			os.mkdir(moviedir)
		os.system("ln -s %s/*st.mrc %s" % (self.ddstackpath, moviedir))
		
		# write particle coordinate files
		self.write_inputs(self.stackparts)
		
		# submission agent object
		a = apParallelTasks.Agent(self.configfile)
		for i in range(len(self.joblist)):
			jobfile = 'align_polish_parts_%d' % i
			task = self.joblist[i]
			a.Main(jobfile, [task])

		
		# Clean up
		apDisplay.printMsg("deleting temporary processing files")

		# Upload results
		#		if self.params['commit'] is True:
		#		apStack.commitPolishedStack(self.params, oldstackparts, newname='start.hed')
        
        
		time.sleep(1)
		return

#=====================
if __name__ == "__main__":
#	polisher = stackPolisher()
	polisher = stackPolisherScript()
	polisher.start()
	polisher.close()


