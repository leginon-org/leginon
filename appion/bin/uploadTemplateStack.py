#!/usr/bin/env python
# Python script to upload a template to the database, and prepare images for import

#python
import os
import sys
import re
import pprint
import time
import shutil
import subprocess
#appion
from appionlib import appionScript
from appionlib import apTemplate
from appionlib import apStack
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import appiondata
from appionlib import apEMAN
from appionlib import apFile
from appionlib import apProject

#=====================
class uploadTemplateScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --template=<name> --apix=<pixel> --session=<session> --diam=<int> "
			+"--description='<text>' [options]")

		### required info
		self.parser.add_option("-s", "--session", dest="session",
			help="Session name associated with template (e.g. 06mar12a)", metavar="INT")

		### template stack input
		self.parser.add_option("-t", "--templatestack", dest="templatestack",
			help="Filename of the template stack", metavar="FILE")
		self.parser.add_option("--templatetype", dest="templatetype", type="str",
                        help="the type of template stack (i.e. class averages (clsavg) or forward projections (forward_proj))", metavar="STR")
#		self.parser.add_option("--runname", "--name", dest="runname", type="str",
#                       help="new name of the template stack, as it will be stored in the templatestacks directory", metavar="STR")
		self.parser.add_option("--apix", dest="apix", type="float",
                        help="angstroms per pixel of the file", metavar="FLOAT")
		self.parser.add_option("--boxsize", dest="boxsize", type="float",
                        help="boxsize of the file", metavar="FLOAT")

		### if modifying a previous stack
		self.parser.add_option("--clusterId", dest="clusterId", type="int",
			help="ID for particle clustering (optional)", metavar="INT")
		self.parser.add_option("-k", "--keep-file", dest="keepfile",
			help="File listing which particles to keep, EMAN style 0,1,...", metavar="FILE")
		self.parser.add_option("--first", dest="first", type="int",
			help="First class average to include")
		self.parser.add_option("--last", dest="last", type="int",
			help="Last class average to include")
		self.parser.add_option("--exclude", dest="exclude",
			help="EMAN style class averages to EXCLUDE in the new stack (0,5,8)", metavar="0,1,...")
		self.parser.add_option("--include", dest="include",
			help="EMAN style class averages to INCLUDE in the new stack (0,2,7)", metavar="0,1,...")


	#=====================
	def checkConflicts(self):
		### make sure the necessary parameters are set
		if self.params['description'] is None:
			apDisplay.printError("enter a template description")
		if self.params['templatestack'] is None and self.params['clusterId'] is None:
			apDisplay.printError("enter a template stack file or a clusterId")
		if self.params['templatetype'] is None and self.params['templatetype'] is not "clsavg" and self.params['templatetype'] is not "forward_proj":
			apDisplay.printError("enter the template type (i.e. class averages / forward projections)")
		if self.params['runname'] is None:
			templatestacksq = appiondata.ApTemplateStackData()
			templatestacks = templatestacksq.query()
			num_templatestacks = len(templatestacks)
			new_num = num_templatestacks + 1
			self.params['runname'] = "templatestack"+str(new_num)+"_"+str(self.params['session'])

		### get apix value
		if (self.params['apix'] is None and self.params['clusterId'] is None):
			apDisplay.printError("Enter value for angstroms per pixel")
		elif (self.params['apix'] is None and self.params['clusterId'] is not None):
			clusterdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterId'])
			self.params['apix'] = clusterdata['clusterrun']['pixelsize']
		print self.params['apix']

		### get boxsize if not specified
		if self.params['boxsize'] is None and self.params['templatestack'] is not None:
			emancmd = "iminfo "+self.params['templatestack']
			proc = subprocess.Popen(emancmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			results = proc.stdout
			proc.wait()
			for line in results:
				res = re.search("([0-9]+)x([0-9]+)x([0-9])", line)
				if res:
					num1 = int(res.groups()[0])
					num2 = int(res.groups()[1])
					if num1 == num2:
						self.params['boxsize'] = num1
		elif self.params['boxsize'] is None and self.params['clusterId'] is not None:
			clusterdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterId'])
			self.params['boxsize'] = clusterdata['clusterrun']['boxsize']

		### check for session
		if self.params['session'] is None:
			if self.params['clusterId'] is not None:
				clusterdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterId'])
				stackid = clusterdata['clusterrun']['alignstack']['stack'].dbid
				sessiondata = apStack.getSessionDataFromStackId(stackid)
				self.params['session'] = sessiondata['name']
		if self.params['session'] is None:
			apDisplay.printError("Could not find session")

		if self.params['templatestack'] is not None:
			self.params['templatestack'] = os.path.abspath(self.params['templatestack'])

		### exclusions and inclusions, if modifying previous stack
		if self.params['clusterId'] is not None:
			if self.params['first'] is None and self.params['last'] is None:
				if self.params['keepfile'] is None and self.params['exclude'] is None and self.params['include'] is None:
					apDisplay.printError("Please define either keepfile, exclude or include")
				elif self.params['keepfile']:
					self.params['keepfile'] = os.path.abspath(self.params['keepfile'])
					if not os.path.isfile(self.params['keepfile']):
						apDisplay.printError("Could not find keep file: "+self.params['keepfile'])
			if self.params['keepfile'] and (self.params['exclude'] is not None or self.params['include'] is not None):
				apDisplay.printError("Please define only either keepfile, exclude or include")
			if self.params['exclude'] and (self.params['keepfile'] is not None or self.params['include'] is not None):
				apDisplay.printError("Please define only either keepfile, exclude or include")
			if self.params['include'] and (self.params['exclude'] is not None or self.params['keepfile'] is not None):
				apDisplay.printError("Please define only either keepfile, exclude or include")

	#=====================
	def setRunDir(self):
		#auto set the output directory
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])
		path = os.path.abspath(sessiondata['image path'])
		path = re.sub("leginon","appion",path)
		path = re.sub("/rawdata","",path)
		self.params['rundir'] = os.path.join(path,"templatestacks", self.params['runname'])

	#=====================
	def useClusterForTemplateStack(self):

		# if exclude or include lists are not defined...
		if self.params['exclude'] is None and self.params['include'] is None:
			# if first and last are specified, create a file
			if self.params['first'] is not None and self.params['last'] is not None:
				stp = str(self.params['first'])
				enp = str(self.params['last'])
				fname = str(self.params['runname'])+'_'+stp+'-'+enp+'.lst'
				self.params['keepfile'] = os.path.join(self.params['rundir'],fname)
				apDisplay.printMsg("Creating keep list: "+self.params['keepfile'])
				f=open(self.params['keepfile'],'w')
				for i in range(self.params['first'],self.params['last']+1):
					f.write('%i\n' % i)
				f.close()

			# otherwise, just copy the file
			elif not os.path.isfile(os.path.basename(self.params['keepfile'])):
				shutil.copy(self.params['keepfile'], os.path.basename(self.params['keepfile']))

		# if either exclude or include lists is defined
		elif self.params['exclude'] or self.params['include']:

			### list of particles to be excluded
			excludelist = []
			if self.params['exclude'] is not None:
				excludestrlist = self.params['exclude'].split(",")
				for excld in excludestrlist:
					excludelist.append(int(excld.strip()))
			apDisplay.printMsg("Exclude list: "+str(excludelist))

			### list of particles to be included
			includelist = []
			if self.params['include'] is not None:
				includestrlist = self.params['include'].split(",")
				for incld in includestrlist:
					includelist.append(int(incld.strip()))
			apDisplay.printMsg("Include list: "+str(includelist))


		newclusterstack = os.path.join(self.params['rundir'], str(self.params['runname'])+".img")
		oldclusterstack = os.path.join(self.clusterdata['path']['path'], self.clusterdata['avg_imagicfile'])

		#if include or exclude list is given...
		if self.params['include'] is not None or self.params['exclude'] is not None:

			#old stack size
			stacksize = apFile.numImagesInStack(oldclusterstack)

			includeParticle = []
			excludeParticle = 0

			for partnum in range(stacksize):
				if includelist and partnum in includelist:
					includeParticle.append(partnum)
				elif excludelist and not partnum in excludelist:
					includeParticle.append(partnum)
				else:
					excludeParticle += 1
			includeParticle.sort()

			### write kept particles to file
			self.params['keepfile'] = os.path.join(self.params['rundir'], "keepfile-"+self.timestamp+".list")
			apDisplay.printMsg("writing to keepfile "+self.params['keepfile'])
			kf = open(self.params['keepfile'], "w")
			for partnum in includeParticle:
				kf.write(str(partnum)+"\n")
			kf.close()

			#get number of particles
			numparticles = len(includeParticle)
			if excludelist:
				self.params['description'] += ( " ... %d particle subcluster of clusterid %d"
				% (numparticles, self.params['clusterId']))
			elif includelist:
				self.params['description'] += ( " ... %d particle subcluster of clusterid %d"
				% (numparticles, self.params['clusterId']))

		ogdescr = self.params['description']
#		for i in range(self.params['split']):
#		sb = os.path.splitext(stackdata['name'])
#		if self.params['first'] is not None and self.params['last'] is not None:
#			newname = sb[0]+'.'+str(self.params['first'])+'-'+str(self.params['last'])+sb[-1]
#		elif self.params['split'] > 1:
#			fname = 'sub'+str(self.params['stackid'])+'.'+str(i+1)+'.lst'
#			self.params['keepfile'] = os.path.join(self.params['rundir'],fname)
#			newname = sb[0]+'.'+str(i+1)+'of'+str(self.params['split'])+sb[-1]
#		newstack = os.path.join(self.params['rundir'], newname)

		#get number of particles
		f = open(self.params['keepfile'], "r")
		numparticles = len(f.readlines())
		f.close()
#		self.params['description'] = ogdescr
#		self.params['description'] += (
#			(" ... %d particle substack of stackid %d"
#			 % (numparticles, self.params['stackid']))
#		)
#		#if splitting, add to description
#		if self.params['split'] > 1:
#			self.params['description'] += (" (%i of %i)" % (i+1, self.params['split']))

		#create the new sub stack
		if os.path.isfile(newclusterstack):
			apFile.removeStack(newclusterstack)
		emancmd = "proc2d "+oldclusterstack+" "+newclusterstack+" list="+self.params['keepfile']
		apEMAN.executeEmanCmd(emancmd)
		self.numimages = apFile.numImagesInStack(newclusterstack)
#		apStack.makeNewStack(oldstack, newstack, self.params['keepfile'])
		if not os.path.isfile(newclusterstack):
			apDisplay.printError("No template stack was created")
#		apStack.commitSubStack(self.params, newname)
#		apStack.averageStack(stack=newstack)


	#=====================
	def uploadTemplateStack(self, insert=False):
		sessiondata = apDatabase.getSessionDataFromSessionName(self.params['session'])

		uploadq = appiondata.ApTemplateStackData()
		uploadq['REF|projectdata|projects|project'] = self.params['projectid']
		if self.params['clusterId'] is not None:
			uploadq['clusterstack'] = appiondata.ApClusteringStackData.direct_query(self.params['clusterId'])
		elif self.params['templatestack'] is not None:
			uploadq['origfile'] = self.params['templatestack']+".hed"
		uploadq['templatename'] = self.params['runname']+".hed"
		if self.params['templatetype'] == "clsavg":
			uploadq['cls_avgs'] = True
		if self.params['templatetype'] == "forward_proj":
			uploadq['forward_proj'] = True
		uploadq['description'] = self.params['description']
		uploadq['session'] = sessiondata
		uploadq['apix'] = self.params['apix']
		uploadq['boxsize'] = self.params['boxsize']
		uploadq['numimages'] = self.numimages
		uploadq['path'] = appiondata.ApPathData(path=os.path.abspath(self.params['rundir']))
		if insert is True:
			uploadq.insert()

	#=======================
	def start(self):
		print self.params
		if self.params['clusterId'] is not None:
			self.clusterdata = appiondata.ApClusteringStackData.direct_query(self.params['clusterId'])
			self.useClusterForTemplateStack()
		else:
			apDisplay.printMsg("Using local file: '"+str(self.params['templatestack'])+"' to upload template")

			# copy templates to final location
			if str(self.params['templatestack'])[-4:] == ".img" or str(self.params['templatestack'])[-4:] == ".hed":
				self.params['templatestack'] = self.params['templatestack'][:-4]
			if str(self.params['runname'])[-4:] == ".img" or str(self.params['runname'])[-4:0] == ".hed":
				self.params['runname'] = self.params['runname'][:-4]
			shutil.copyfile(str(self.params['templatestack'])+".img", os.path.join(self.params['rundir'], str(self.params['runname'])+".img"))
			shutil.copyfile(str(self.params['templatestack'])+".hed", os.path.join(self.params['rundir'], str(self.params['runname'])+".hed"))
			self.numimages = apFile.numImagesInStack(os.path.join(self.params['rundir'], str(self.params['runname'])+".hed"))

		# insert templates to database
		if self.params['commit'] is True:
			self.uploadTemplateStack(insert=True)
		else:
			apDisplay.printWarning("not committing results to DB")

#=====================
if __name__ == "__main__":
	uploadTemplate = uploadTemplateScript()
	uploadTemplate.start()
	uploadTemplate.close()



