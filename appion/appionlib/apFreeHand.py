#!/usr/bin/env python

import os
import math
import pylab
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import subprocess
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apModel
from appionlib import apIMAGIC
from appionlib import apFrealign
from appionlib import apParam
from appionlib import apThread
from pyami import peakfinder, mrc

#=====================
#=====================
class FastFreeHandTestScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		self.parser.add_option("-s", "--id", "--stackid", dest="stackid", type="int",
			help="A stack id ", metavar="#")
		self.parser.add_option("-m", "--modelid", dest="modelid", type="int",
			help="An initial model id ", metavar="#")
		self.parser.add_option('--reconiterid', dest='reconiterid', type='int',
			help="id for specific iteration from a refinement, used for retrieving particle orientations")
		self.ctfestopts = ('ace2', 'ctffind')
		self.parser.add_option('--ctfmethod', dest='ctfmethod',
			help="Only use ctf values coming from this method of estimation", metavar="TYPE",
			type="choice", choices=self.ctfestopts)
		self.parser.add_option('--paramonly', dest='paramonly', default=False, action='store_true',
			help="only create parameter file")
		self.parser.add_option('--ctftilt', dest='ctftilt', default=False, action='store_true',
			help="Use ctftilt values")
		self.parser.add_option("--minres", dest="minres", type="float", default=1000.0,
			help="minimal resolution in Angstrom")
		self.parser.add_option("--maxres", dest="maxres", type="float",default=8.0,
			help="max resolution in Angstrom")
		self.parser.add_option("--snr", dest="snr", type="float",default=0.07,
			help="signal-to-noise ratio: 0.07 for ice")
		self.parser.add_option("--angSearch", dest="angSearch", type="int",
			default=45.0, help="search angle range")
		self.parser.add_option("--radius", dest="radius", type="float",
			help="radius of the particle in Angstrom")
		scoringchoices = ("c", "C", "p", "P")
		self.parser.add_option("--scoringtype", dest="scoringtype",
			help="Scoring Method Type", metavar="TYPE",
			type="choice", choices=scoringchoices, default="c" )

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("Please provide a user id, e.g. --stackid=15")
		if not self.isStackId(self.params['stackid']):
			apDisplay.printError("Invaid user id")
		apDisplay.printMsg("User id is valid")

	#=====================
	def isStackId(self, stackid):
		"""
		Arbitrary requirements for a stackid
		"""
		if stackid < 1:
			return False
		elif stackid > 99999:
			return False
		return True

	def prepareFrealignInitialParamFile(self):
		if 'reconiterid' not in self.params.keys() or self.params['reconiterid'] == 0:
			self.params['reconiterid'] = None
		paramfile = 'params.000.par'
		apFrealign.generateParticleParams(self.params,self.model['data'],paramfile)

	def convertStackToMrc(self):
		stackdata = apStackData.getOnlyStackData(self.params['stackid'])
		stackfile = os.path.join(stackdata['path']['path'],stackdata['name'])
		stackbaseroot = os.path.basename(stackfile).split('.')[0]
		stackroot = os.path.join(stackdata['path']['path'],stackdata['name'][:-4])
		apDisplay.printMsg('converting %s from default IMAGIC stack format to MRC as %s.mrc'% (stackroot,stackbaseroot))
		self.stackfile = stackbaseroot+'.mrc'
		apIMAGIC.convertImagicStackToMrcStack(stackroot,self.stackfile)

	def getModel(self):
		modeldata = apModel.getModelFromId(self.params['modelid'])
		self.modelfile = 'initmodel.mrc'

	def createFastFreeHandInputLineTemplate(self):
		self.boxsize = apStack.getStackBoxsize(self.params['stackid'], msg=False)
		self.apix = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.apix = 6.02
		one_particledata = apStack.getOneParticleFromStackId(self.params['stackid'], particlenumber=1, msg=True)
		scopedata = one_particledata['particle']['image']['scope']
		ht_kv = scopedata['high tension'] / 1000.0
		cs_mm = scopedata['tem']['cs'] * 1000
		angSearch = self.params['angSearch']
		constant_inputlines = [
			'%.3f,%.3f,%2f,%.f' %(self.apix,self.params['snr'],cs_mm,ht_kv)
			,'1,0'
			,'../%s' %(self.stackfile)
			,'../%s' %(self.modelfile)
			,'../%s' %(self.frealign_paramfile)
			,'out.mrc'
			,'-%d,%d,-%d,%d' %(angSearch,angSearch,angSearch,angSearch)
			,'%.1f,%.2f,%.2f' %(self.params['minres'],self.params['maxres'],self.params['radius'])
			,'%s' %(self.params['scoringtype'].upper())
		]
		return constant_inputlines

	def createTiltedCtfLines(self,start_particle,end_particle):
		part_tree = apFrealign.parseFrealignParamFile(self.frealign_paramfile)
		print len(part_tree)
		print start_particle
		p = part_tree[start_particle-1]
		total_particles = end_particle - start_particle + 1
		# TO DO: the original script requires a count of particles at a given
		# ctf value followed by 1 if there are more lines
		lastcard = '%d,%d,%d,%.1f,%.1f,%.1f,0' % (total_particles,p['mag'],p['film'],p['defoc1'],p['defoc2'],p['astang'])
		return [lastcard]
			
	def writeMultipleFreeHandTestShells(self,constant_inputlines,nproc):
		scripts = []
		files = []
		last_particle = apStack.getNumberStackParticlesFromId(self.params['stackid'], msg=True)
		last_particle = 82	
		# This is integer division and will return integer
		stepsize = int(math.ceil(float(last_particle) / nproc))
		for proc in range(nproc):
			proc_start_particle = stepsize * proc + 1
			proc_end_particle = min(stepsize * (proc+1), last_particle)
			proc_inputlines = list(constant_inputlines)
			proc_inputlines.insert(8,'%d, %d' % (proc_start_particle,proc_end_particle))
			proc_inputlines.extend(self.createTiltedCtfLines(proc_start_particle,proc_end_particle))
			procpath = os.path.join(self.params['rundir'],'proc%03d' % (proc))
			apParam.createDirectory(procpath, warning=False)
			lines_before_input = [
				'#!/bin/csh',
				'# Proc %03d, Particles %d - %d' % (proc,proc_start_particle,proc_end_particle),
				'rm -rf %s' % procpath,
				'mkdir %s' % procpath,
				'cd %s' % procpath,
				'',
				'',
				'### START FREALIGN ###',
				'/home/acheng/bin/fastfreehand_v1_01.exe << EOF > freehand.proc%03d.out' % proc,
				]
			lines_after_input=[
				'EOF',
				'',
				'### END FREEHAND',
				'echo "END FREEHAND"',
				]
			alllines = lines_before_input+proc_inputlines+lines_after_input
			procfile = 'freehand.proc%03d.csh' % (proc)
			f = open(procfile,'w')
			f.writelines(map((lambda x: x+'\n'),alllines))
			f.close()
			os.chmod(procfile, 0755)
			scripts.append(procfile)
		return scripts

	def runMultipleFreeHandTest(self,commandlist):
		apThread.threadCommands(commandlist, nproc=self.params['nproc'], pausetime=1.0)

	def mergeResults(self):
		allout = 'all_out.mrc'
		for proc in range(self.params['nproc']):
			infilepath = 'proc%03d/out.mrc' % (proc)
			a = mrc.read(infilepath)
			if proc == 0:
				mrc.write(a,allout)
			else:
				mrc.append(a,allout)
		return allout


	#=====================
	def onInit(self):
		"""
		Advanced function that runs things before other things are initialized.
		For example, open a log file or connect to the database.
		"""
		self.frealign_paramfile = 'params.000.par'
		self.stackfile = 'start.mrc'
		return

	#=====================
	def onClose(self):
		"""
		Advanced function that runs things after all other things are finished.
		For example, close a log file.
		"""
		return

	#=====================
	def start(self):
		self.params['nproc'] = 6
		### get info about the model
		if self.params['modelid'] is not None:
			apDisplay.printMsg("Information about model id %d"%(self.params['modelid']))
			modeldata = apModel.getModelFromId(self.params['modelid'])
			apDisplay.printMsg("\tboxsize %d pixels"%(modeldata['boxsize']))
			apDisplay.printMsg("\tpixelsize %.3f Angstroms"%(modeldata['pixelsize']))
		apDisplay.printMsg("\n\n")
		self.getModel()
		inputlines = self.createFastFreeHandInputLineTemplate()
		free_hand_scripts = self.writeMultipleFreeHandTestShells(inputlines,self.params['nproc'])
		print free_hand_scripts
		#self.runMultipleFreeHandTest(free_hand_scripts)
		merged_outfile = self.mergeResults()
		plot = plotFreeHandTestResult(merged_outfile,self.params['angSearch'],self.params['scoringtype'])
		plot.plotResult()

class plotFreeHandTestResult(object):
	def __init__(self,merged_outfile,angSearch,scoringtype='C'):
		self.params = {}
		self.params['scoringtype'] = scoringtype
		self.params['angSearch'] = angSearch
		self.merged_outfile = merged_outfile
		self.peakfile = 'peaks.txt'

	def getCCP4Path(self):
		### get the openmpi directory        
		ccp4path = subprocess.Popen("env | grep CCP4=/usr/local/ccp4-6.3.0", shell=True, stdout=subprocess.PIPE).stdout.read().strip()

		if ccp4path:
			ccp4path = ccp4path.replace("CCP4=","")
		if os.path.exists(ccp4path):
			return ccp4path
		print "ccp4 is not loaded, make sure it is in your path"
		sys.exit()

	def averageStack(self,stackfile):
		avgfile = 'avg.mrc'
		a = mrc.read(stackfile)
		a = np.sum(a,axis=0)
		a = (a-a.min())/(a.max()-a.min())
		mrc.write(a,avgfile)
		return avgfile

	def findPeak(self,stack):
		if os.path.exists(self.peakfile):
			os.remove(self.peakfile)
		out = open(self.peakfile,'w')
		stackRead = mrc.read(stack) 
		number, ydim, xdim = stackRead.shape
		for i in range(number):
			image = stackRead[i,:,:]
			output = peakfinder.findPixelPeak(image, guess=None, limit=None, lpf=None)
			coord = output['pixel peak']
			out.write('%d	%s	%s\n' %(i,coord[0],coord[1]))
		return out

	def scatter(self,data,lim,tilt,include):

		tiltX = tilt[0]
		tiltY = tilt[1]

		loadData = np.loadtxt(data)
		x = loadData[:,2]
		y = loadData[:,1]

		#Center peak vales at (0,0)
		centx = np.subtract(x,lim)
		centy = np.subtract(y,lim)

		#Calculate distance of peaks from expected angle
		dist = []
		for i in xrange(len(loadData[:,1])):
			rx = centx[i]
			ry = centy[i]
			
			distance = math.sqrt(((rx - tiltX)*(rx - tiltX)) + ((ry - tiltY)*(ry - tiltY))/2)
			dist.append(distance)

		newDist = sorted(dist)

		numReadLines = round((float(include)/100)*len(loadData[:,1]))

		includeRadius = []
		for j in xrange(numReadLines):
			includeRadius = newDist[j]
		#Create function for plotting circle
		theta = np.linspace(0,2*math.pi)
		
		incRadx = includeRadius*pylab.cos(theta) 
		incRady = includeRadius*pylab.sin(theta)

		incRadx = pylab.add(incRadx,tiltX)
		incRady = pylab.add(incRady,tiltY)
		
		#Set radii for concentric circles	
		rad1 = 10
		rad2 = 20
		rad3 = 30
		rad4 = 40
		rad5 = 50
		rad6 = 60
		
		#Create x,y coords for concentric cricles
		cx1 = rad1*pylab.cos(theta)
		cy1 = rad1*pylab.sin(theta)
		cx2 = rad2*pylab.cos(theta)
		cy2 = rad2*pylab.sin(theta)
		cx3 = rad3*pylab.cos(theta)
		cy3 = rad3*pylab.sin(theta)
		cx4 = rad4*pylab.cos(theta)
		cy4 = rad4*pylab.sin(theta)
		cx5 = rad5*pylab.cos(theta)
		cy5 = rad5*pylab.sin(theta)
		cx6 = rad6*pylab.cos(theta)
		cy6 = rad6*pylab.sin(theta)

		#Create axes
		line1 = np.linspace(-60,60,100)

		#Create zeros array
		line2 = []
		i = 1
		while i <= 100:
			line2.append('0')
			i = i + 1
		fig = plt.figure(1)

		scatter = plt.subplot(111,aspect='equal')
		majorLocator = MultipleLocator(10)
		majorFormatter = FormatStrFormatter('%d')
		minorLocator = MultipleLocator(5)
		scatter.set_xlabel('Tilt direction (degrees)',fontsize=15)
		scatter.set_ylabel('Tilt direction (degrees)',fontsize=15)
		scatter.set_title('%d'%(include) + '% ' + 'of particles are within %d degrees of expected angle'%(round(includeRadius)))
		scatter.plot(cx1,cy1,c = 'k')
		scatter.plot(cx2,cy2,c = 'k')
		scatter.plot(cx3,cy3,c = 'k')
		scatter.plot(cx4,cy4,c = 'k')
		scatter.plot(cx5,cy5,c = 'k')
		scatter.plot(cx6,cy6,c = 'k')
		scatter.plot(cx5,cy5,c = 'k')
		scatter.plot(incRadx,incRady,c = 'r')
		scatter.plot(line2,line1,c='k')
		scatter.plot(line1,line2,c='k')
		scatter.scatter(centx,centy,marker='+',c='k',edgecolor='k',s=55)
		majorLocator = MultipleLocator(10)
		majorFormatter = FormatStrFormatter('%d')
		minorLocator = MultipleLocator(5)
		scatter.xaxis.set_major_locator(majorLocator)
		scatter.xaxis.set_major_formatter(majorFormatter)
		scatter.xaxis.set_minor_locator(minorLocator)
		scatter.yaxis.set_major_locator(majorLocator)
		scatter.yaxis.set_major_formatter(majorFormatter)
		scatter.yaxis.set_minor_locator(minorLocator)
		plt.xlim(-lim,lim)
		plt.ylim(-lim,lim)
		outFILE = '%s.png' %(data[:-4])
		plt.savefig(outFILE,dpi=150,format='png')

	def totsum(self,stack,out):

		cmd = 'e2proc2d.py %s %s --average' %(stack,out)
		subprocess.Popen(cmd,shell=True).wait()

	def contour(self,image,calc,angSearch,ccp4PATH):

		outContour = '%s_contour.ps' %(image[:-4])
		if calc == 'C' or 'c':

			lim = angSearch*2
			minor1 = (float(angSearch)*2)/5
			minor2 = minor1/2

			if os.path.exists('z.plot'):
				os.remove('z.plot')
			if os.path.exists(outContour):
				os.remove(outContour)

			npo = '#!/bin/csh\n'
			npo += '#Calculate contour plot using pltdev in CCP4\n'
			npo += 'rm -f plot84.ps\n'
			npo += '%s/bin/npo mapin %s plot z.plot << eof\n' %(ccp4PATH,image)
			npo += 'NOTITLE\n'
			npo += 'MAP SCALE 1 INVERT\n'
			npo += '# For CCC\n'
			npo += 'CONTRS 0.0 to 1 by 0.02\n'
			npo += 'LIMITS 0 %d 0 %d 0 0\n' %(lim,lim)
			npo += 'SECTNS 0 0 1\n'
			npo += 'GRID  5 5\n'
			npo += 'GRID U DASHED 1.0 0.2 0 EVERY %s FULL\n' %(minor2)
			npo += 'GRID V DASHED 1.0 0.2 0 EVERY %s FULL\n' %(minor2)
			npo += 'PLOT Y\n'
			npo += 'eof\n'
			npo += '\n'
			npo += '%s/bin/pltdev -log -dev ps -abs -pen c -xp 0 -yp 0 -lan -i z.plot -o %s\n' %(ccp4PATH,outContour)
			
			tmp = open('pltdev.csh','w')
			tmp.write(npo)
			tmp.close()
			cmd = 'chmod +x pltdev.csh'
			subprocess.Popen(cmd,shell=True)
		
			cmd = './pltdev.csh'
			subprocess.Popen(cmd,shell=True).wait()

			#os.remove('pltdev.csh')
			os.remove('z.plot')
		
		elif calc == 'P' or 'p':
			lim = angSearch*2
			minor1 = (float(angSearch)*2)/5
			minor2 = minor1/2

			if os.path.exists('z.plot'):
				os.remove('z.plot')
			if os.path.exists(outContour):
				os.remove(outContour)

			npo = '#!/bin/csh\n'
			npo += '#Calculate contour plot using pltdev in CCP4\n'
			npo += 'rm -f plot84.ps\n'
			npo += '%s/bin/npo mapin %s plot z.plot << eof\n' %(ccp4PATH,image)
			npo += 'NOTITLE\n'
			npo += 'MAP SCALE 1 INVERT\n'
			npo += '# For Pres\n'
			npo += 'CONTRS 77. to 86 by .3\n'
			npo += 'LIMITS 0 %d 0 %d 0 0\n' %(lim,lim)
			npo += 'SECTNS 0 0 1\n'
			npo += 'GRID  5 5\n'
			npo += 'GRID U DASHED 1.0 0.2 0 EVERY %d FULL\n' %(minor2)
			npo += 'GRID V DASHED 1.0 0.2 0 EVERY %d FULL\n' %(minor2)
			npo += 'PLOT Y\n'
			npo += 'eof\n'
			npo += '\n'
			npo += '%s/bin/pltdev -log -dev ps -abs -pen c -xp 0 -yp 0 -lan -i z.plot -o %s\n' %(ccp4PATH,outContour)

			tmp = open('pltdev.csh','w')
			tmp.write(npo)
			tmp.close()

			cmd = 'chmod +x pltdev.csh'
			subprocess.Popen(cmd,shell=True)

			cmd = './pltdev.csh'
			subprocess.Popen(cmd,shell=True).wait()

			#os.remove('pltdev.csh')
			os.remove('z.plot')

	def convertEPS_to_PNG(self,image,out):

		im = Image.open(image)
		im.rotate(-90).save(out)

	def plotResult(self):
		#Inputs
		peaks = self.peakfile
		scoringFunction = self.params['scoringtype']	#C - CC; P - phase residual
		angSearch = self.params['angSearch']
		# hard code for now circle parameters
		includedPercentTilt = 60 
		tiltCenter = [20,0]

		#Calculate average of stack
		avgfile = self.averageStack(self.merged_outfile)
		avgroot = '.'.join(os.path.splitext(avgfile)[:-1])

                #Run & Plot peak finding
                self.findPeak(self.merged_outfile)
                self.scatter(peaks,angSearch,tiltCenter,includedPercentTilt)

		#Calculate contour
		ccp4PATH = self.getCCP4Path()
		self.contour(avgfile,scoringFunction,angSearch,ccp4PATH)
		self.convertEPS_to_PNG('%s_contour.ps' %(avgroot),'%s_contour.png' %(avgroot))

		#Clean up
		os.remove('%s_contour.ps' %(avgroot))
		os.remove(peaks)
		os.remove(avgfile)

#=====================
if __name__ == '__main__':
	examplescript = FastFreeHandTestScript()
	examplescript.start()
	examplescript.close()

