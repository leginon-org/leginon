#!/usr/bin/env python

import os
import re
import subprocess
import math
import time
import numpy
import apDisplay
import appionData
import appionScript
import apFile
import apStack
import apEMAN
import apIMAGIC

class iterateCommonLinesScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):

		self.parser.set_usage("Usage: %prog --stack=ID [ --num-part=# ]")

		### necessary input values
		self.parser.add_option("--clusterid", dest="clusterid", type="int",
			help="cluster id from database", metavar="#")
		self.parser.add_option("--templatestackid", dest="templatestackid", type="int",
			help="templatestackid id from database", metavar="#")
		self.parser.add_option("--numimgs", dest="numimgs", type="int",
			help="number of class averages or forward projections in input file", metavar="#")
		self.parser.add_option("--numbest", dest="numbest", type="int", default=50,
			help="number of best combinations to output", metavar="#")

		return		
	
	
	#=====================
	def checkConflicts(self):

		if self.params['templatestackid'] is not None and self.params['clusterid'] is not None:
			apDisplay.printError("Please use only one class average stack")
			

		return
		
	#=====================
	def setRunDir(self):

		# get cluster stack parameters
		if self.params['clusterid'] is not None:
			clusterdata = appionData.ApClusteringStackData.direct_query(self.params['clusterid'])
			path = clusterdata['path']['path']
		elif self.params['templatestackid'] is not None:
			tsdata = appionData.ApTemplateStackData.direct_query(self.params['templatestackid'])
			path = tsdata['path']['path']
		else:
			apDisplay.printError("class averages not in the database")

		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "commonLines", self.params['runname'])

	#=====================
	def executeImagicBatchFile(self, projections):

#		rundir = "/export/home/dlyumkis/common_lines/"
		batchfile = os.path.join(self.params['rundir'], "angrecon.batch")

		f = open(batchfile, "w")
		f.write("#!/bin/csh -f\n")
		f.write("setenv IMAGIC_BATCH 1\n")
		f.write("/usr/local/IMAGIC/angrec/euler.e <<EOF > angrecon.log \n")
		f.write("C1\n")
		f.write("C1_STARTUP\n")
		f.write("start\n")
		f.write(str(projections)+"\n")
		f.write("ordered\n")
		f.write("sino_ordered\n")
		f.write("YES\n")
		f.write(".9\n")
		f.write("my_sine\n")
		f.write("5.0\n")
		f.write("0.1\n")
		f.write("NO\n")
		f.write("EOF\n")
		f.close()

		proc = subprocess.Popen("chmod 775 "+batchfile, shell=True)
		proc.wait()
		path = os.path.dirname(batchfile)
		os.chdir(path)
		process = subprocess.Popen(batchfile, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		waittime = 0.01
		while process.poll() is None:
			if waittime > 0.05:
				waited = True
				waittime *= 1.02
				time.sleep(waittime)
#		apIMAGIC.executeImagicBatchFile(batchfile)
		
	#=====================
	def calculateInterEulerDistance(self, eulers):
		euler1 = float(eulers[0])
		euler2 = float(eulers[1])
		euler3 = float(eulers[2])
		distance = math.sqrt(math.fabs(euler1-90)**2 + math.fabs(euler2-90)**2 + math.fabs(euler3-90)**2)
	#	distance = (euler1 + euler2 + euler3) / 3
	#	distance = math.pow(math.sqrt(euler1) + math.sqrt(euler2) + math.sqrt(euler3), 2)
		
		return distance	

	#=====================
	def readAngReconParams(self, file):
		f = open(file, "r")
		lines = f.readlines()
		stripped = [line.strip() for line in lines]
		f.close()
		
		### sometimes common lines fails, so set initially to 0
		eulerdist1_2 = 0
		eulerdist2_3 = 0
		eulerdist3_1 = 0
		alpha1 = 0
		beta1 = 0
		gamma1 = 0
		alpha2 = 0
		beta2 = 0
		gamma2 = 0
		alpha3 = 0
		beta3 = 0
		gamma3 = 0
		
		for line in stripped:
			if re.search("Angular distance between direction 1 <--> 2", str(line)):
				split = line.split()
				eulerdist1_2 = float(split[-1])
			if re.search("Angular distance between direction 2 <--> 3", str(line)):
				split = line.split()
				eulerdist2_3 = float(split[-1])
			if re.search("Angular distance between direction 3 <--> 1", str(line)):
				split = line.split()
				eulerdist3_1 = float(split[-1])
			if re.search("Euler angle alpha #1", str(line)):
				split = line.split()
				alpha1 = float(split[-1])
			if re.search("Euler angle beta  #1", str(line)):
				split = line.split()
				beta1 = float(split[-1])
			if re.search("Euler angle gamma #1", str(line)):
				split = line.split()
				gamma1 = float(split[-1])
			if re.search("Euler angle alpha #2", str(line)):
				split = line.split()
				alpha2 = float(split[-1])
			if re.search("Euler angle beta  #2", str(line)):
				split = line.split()
				beta2 = float(split[-1])
			if re.search("Euler angle gamma #2", str(line)):
				split = line.split()
				gamma2 = float(split[-1])
			if re.search("Euler angle alpha #3", str(line)):
				split = line.split()
				alpha3 = float(split[-1])
			if re.search("Euler angle beta  #3", str(line)):	
				split = line.split()
				beta3 = float(split[-1])
			if re.search("Euler angle gamma #3", str(line)):
				split = line.split()
				gamma3 = float(split[-1])
	
		return eulerdist1_2, eulerdist2_3, eulerdist3_1, alpha1, beta1, gamma1, alpha2, beta2, gamma2, alpha3, beta3, gamma3

	#=====================		
	def upload(self):
		iterclq = appionData.ApIterCommonLinesData()
		iterclq['project|projects|project'] = self.params['projectid']
		iterclq['runname'] = self.params['runname']
		if self.params['clusterid'] is not None:
			iterclq['clusterid'] = appionData.ApClusteringStackData.direct_query(self.params['clusterid'])
		else:
			iterclq['templatestackid'] = appionData.ApTemplateStackData.direct_query(self.params['templatestackid'])
		iterclq['numimgs'] = self.params['numimgs']
		iterclq['numbest'] = self.params['numbest']
		iterclq['description'] = self.params['description']
		iterclq['path'] = appionData.ApPathData(path=os.path.abspath(self.params['rundir']))
		iterclq['summaryfile'] = "summary.txt"
		
		if self.params['commit'] is True:
			iterclq.insert()
		else:
			apDisplay.printColor("NOT inserting to Database", "cyan")
		
	#=====================		
	def start(self):
		if self.params['clusterid'] is not None:
			clusterdata = appionData.ApClusteringStackData.direct_query(self.params['clusterid'])
			stack = os.path.join(clusterdata['path']['path'], clusterdata['avg_imagicfile'])
		elif self.params['templatestackid'] is not None:
			tsdata = appionData.ApTemplateStackData.direct_query(self.params['templatestackid'])
			stack = os.path.join(tsdata['path']['path'], tsdata['templatename'])
		
		newstack = os.path.join(self.params['rundir'], "start.img")
		while os.path.isfile(newstack):
			apFile.removeStack(newstack)
		emancmd = "proc2d "+stack+" "+newstack
		apEMAN.executeEmanCmd(emancmd)
		apIMAGIC.copyFile(self.params['rundir'], "start.hed")

		if self.params['numimgs'] is None:
				self.params['numimgs'] = apFile.numImagesInStack(newstack)

		projlist = []
		eulerdistlist = []
		eulerlist = []
		distances = []
		count = 1

		### get total number of iterations
		itercount = 0
		for i in range(1,self.params['numimgs']+1):
			y = i + 1
			for j in range(y, self.params['numimgs']+1):
				z = j + 1
				for k in range(z, self.params['numimgs']+1):
					itercount += 1

		### now perform actual job
		eulerfile = open(os.path.join(self.params['rundir'], "eulersummary.txt"), "w")
		eulerfile.write("### locations in original file, corresponding euler angles (alpha,beta,gamma), & inter-angle distances\n")
		timestart = time.time()
		for i in range(1,self.params['numimgs']+1):
			y = i + 1
			for j in range(y, self.params['numimgs']+1):
				z = j + 1
				for k in range(z, self.params['numimgs']+1):
					projections = str(i)+";"+str(j)+";"+str(k)
					split = projections.split(";")
					proj1 = split[0]
					proj2 = split[1]
					proj3 = split[2]
					self.executeImagicBatchFile(projections)
					projlist.append(projections)
					eulerparams = self.readAngReconParams(file=os.path.join(self.params['rundir'], "angrecon.log"))
					intereulerdistances = (eulerparams[0], eulerparams[1], eulerparams[2])
					eulerdistlist.append(intereulerdistances)
					distance = self.calculateInterEulerDistance(intereulerdistances)
					distances.append(distance)
					eulers = (eulerparams[3], eulerparams[4], eulerparams[5], 
						eulerparams[6], eulerparams[7], eulerparams[8], 
						eulerparams[9], eulerparams[10], eulerparams[11])
					eulerlist.append(eulers)
					eulerfile.write(str(int(proj1)-1)+","+str(int(proj2)-1)+","+str(int(proj3)-1)+"    "+\
						str(eulers[0])+","+str(eulers[1])+","+str(eulers[2])+"    "+\
						str(eulers[3])+","+str(eulers[4])+","+str(eulers[5])+"    "+\
						str(eulers[6])+","+str(eulers[7])+","+str(eulers[8])+"    "+\
						str(eulerparams[0])+","+str(eulerparams[1])+","+str(eulerparams[2])+"\n")
					if count % 100 == 0:
						apDisplay.printMsg("Now working on iteration "+str(count)+" using projections "+projections+" ... "+str(itercount - count)+" iterations remaining")
					count += 1
		eulerfile.close()
		timeend = time.time() - timestart
		

		### sort distances based on minimization of distance between orthogonal class averages
		maxdistances = []
		maxdistanceskeys = []

		for i in range(self.params['numbest']):
			maxdist = 270
			for index, dist in enumerate(distances):
				if dist < maxdist and index not in maxdistanceskeys:
					maxdist = dist
					distkey = index
			maxdistances.append(maxdist)
			maxdistanceskeys.append(distkey)
			
		### output file with best class averages
		bestavgdir = os.path.join(self.params['rundir'], "bestavgs")
		if not os.path.isdir(bestavgdir):
			os.mkdir(bestavgdir)
	
		sumfile = open(os.path.join(self.params['rundir'], "summary.txt"), "w")	
		sumfile.write("### min tot distance b/w angles, orig image locations, & corresponding projection file\n")
		for i in range(self.params['numbest']):
			projections = projlist[maxdistanceskeys[i]]
			split = projections.split(";")
			proj1 = split[0]
			proj2 = split[1]
			proj3 = split[2]
			f = open(os.path.join(bestavgdir, "list.lst"), "w")
			### eman lists start with 0, imagic starts with 1, subtract 1
			f.write(str(int(proj1)-1)+"\n")
			f.write(str(int(proj2)-1)+"\n")
			f.write(str(int(proj3)-1)+"\n")
			f.close()
			projfile = os.path.join(bestavgdir, "proj"+str(i+1)+".img")
			while os.path.isfile(projfile):
				apFile.removeStack(projfile)
			emancmd = "proc2d "+os.path.join(self.params['rundir'], "start.hed")+" "+projfile+" list="+os.path.join(bestavgdir, "list.lst")
			apEMAN.executeEmanCmd(emancmd)
			os.remove(os.path.join(bestavgdir, "list.lst"))
			sumfile.write(str(maxdistances[i])+"\t")
			sumfile.write(str(int(proj1)-1)+","+str(int(proj2)-1)+","+str(int(proj3)-1)+"\t")
			sumfile.write("bestavgs/proj"+str(i+1)+".img"+"\n")
		sumfile.close()
		apFile.removeStack(os.path.join(self.params['rundir'], "sino_ordered.hed"))
		apFile.removeStack(os.path.join(self.params['rundir'], "ordered.hed"))
		apFile.removeStack(os.path.join(self.params['rundir'], "my_sine.hed"))
		
		self.upload()


if __name__ == "__main__":
	iterateCommonLines = iterateCommonLinesScript(True)
	iterateCommonLines.start()
	iterateCommonLines.close()





	
	
	
	
	
	
				
