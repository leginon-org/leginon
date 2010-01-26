#!/usr/bin/env python

#python
import os
import subprocess
#appion
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apFile
from appionlib import apStack
from appionlib import apEMAN
from appionlib import apParam
from appionlib import appiondata
from appionlib.apSpider import alignment
from appionlib import spyder
from appionlib import apRecon
from appionlib import apVolume

#=====================
#=====================
class apmqRefineScript(appionScript.AppionScript):

	#=====================
	def setupParserOptions(self):
		self.parser.set_usage("Usage: %prog --stack=ID [ options ]")
		self.parser.add_option("-N", "--num-part", dest="numpart", type="int", default=0,
			help="Number of particles to use", metavar="#")
		self.parser.add_option("-s", "--stack", dest="stackid", type="int",
			help="Stack database id", metavar="ID#")
		self.parser.add_option("-m", "--modelid", dest="modelid", type="int",
			help="initial model id from database")
		self.parser.add_option("--mask", dest="rad", type="int",
			help="mask radius of the structure")
		self.parser.add_option("--imask", dest="imask", type="int",
			help="inner mask to be applied after each iterations")
		self.parser.add_option("-f", "--first-ring", dest="firstring", type="int", default=2,
			help="First ring radius for correlation (in pixels, > 2)", metavar="#")
		self.parser.add_option("-l", "--last-ring", dest="lastring", type="int",
			help="Last ring radius for correlation (in pixels, < pixel radius)", metavar="#")
		self.parser.add_option("-x", "--xy-search", dest="xysearch", type="int", default=3,
			help="XY search distance (in pixels)", metavar="#")
		self.parser.add_option("--xy-step", dest="xystep", type="int", default=1,
			help="XY step distance (in pixels)", metavar="#")
		self.parser.add_option("--lowpass", dest="lowpass", type="int", default=0,
			help="Low pass filter radius (in Angstroms)", metavar="#")
		#self.parser.add_option("--bin", dest="bin", type="int", default=1,
		#	help="Binning of the particles", metavar="#")
		self.parser.add_option("--highpass", dest="highpass", type="int", default=0,
			help="High pass filter radius (in Angstroms)", metavar="#")
		self.parser.add_option("-a", "--increment", dest="incr", type="string",
			help="Angular increments for each iteration, separated by commas")
		self.parser.add_option("--allowed-shift", dest="allowedShift", type="float", default=0.15,
			help="allowed translational particle shift, as a fraction of the image size")
		self.parser.add_option("--keepsig", dest="keepsig", type="float", default=0,
			help="# of sigmas above the mean cc value to set the cutoff")
		self.parser.add_option("--voliter", dest="voliter", type="int",
			help="iterative back projection iteration limit")
		self.parser.add_option("--bpmode", dest="bpmode", type="int", default=3,
			help="type of constraint used in back projection")
		self.parser.add_option("--eobpmode", dest="eobpmode", type="int", default=2,
			help="type of constraint used in even/odd back projection")
		self.parser.add_option("--lambda", dest="lambda", type="float", default=0.05,
			help="correction weight during iterative back projections")
		self.parser.add_option("--smoothfactor", dest="smoothfac", type="float", default=0.95,
			help="smoothing constant will be multiplied by this value after each iteration of BP")
		self.parser.add_option("--proc", dest="proc", type="int", default=1,
			help="number of processors to use")
		self.parser.add_option("--sym", dest="sym", type="string", default="c1",
			help="particle symmetry")

	#=====================
	def checkConflicts(self):
		if self.params['stackid'] is None:
			apDisplay.printError("stack id was not defined")
		if self.params['rad'] is None:
			apDisplay.printError("no particle radius set")
		if self.params['modelid'] is None:
			apDisplay.printError("model id was not defined")
		if self.params['lastring'] is None:
			apDisplay.printError("a last ring radius was not provided")
		if self.params['runname'] is None:
			apDisplay.printError("run name was not defined")
		if self.params['incr'] is None:
			apDisplay.printError("angular increments are not specified")
		stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		stackfile = os.path.join(stackdata['path']['path'], stackdata['name'])
		numstackp = apFile.numImagesInStack(stackfile)
		if self.params['numpart'] > numstackp:
			apDisplay.printError("trying to use more particles "+str(numstackp)
				+" than available "+str(numstackp))
		elif self.params['numpart'] == 0:
			apDisplay.printWarning("using all "+str(numstackp)+" particles")
			self.params['numpart'] = numstackp
		boxsize = apStack.getStackBoxsize(self.params['stackid'])
		if self.params['lastring'] > boxsize/2-2:
			apDisplay.printError("last ring radius is too big for boxsize "
				+str(self.params['lastring'])+" > "+str(boxsize/2-2))
		if self.params['lastring']+self.params['xysearch'] > boxsize/2-2:
			apDisplay.printError("last ring plus xysearch radius is too big for boxsize "
				+str(self.params['lastring']+self.params['xysearch'])+" > "+str(boxsize/2-2))
		if (self.params['xysearch'] % self.params['xystep']) > 0:
			apDisplay.printError("translational search (xy-search) must be divisible by search step (xy-step)")

	#=====================
	def setRunDir(self):
		self.stackdata = apStack.getOnlyStackData(self.params['stackid'], msg=False)
		path = self.stackdata['path']['path']
		uppath = os.path.abspath(os.path.join(path, "../.."))
		self.params['rundir'] = os.path.join(uppath, "align", self.params['runname'])

	#=====================
	def start(self):
		self.stack = {}
		self.stack['data'] = apStack.getOnlyStackData(self.params['stackid'])
		self.stack['apix'] = apStack.getStackPixelSizeFromStackId(self.params['stackid'])
		self.stack['part'] = apStack.getOneParticleFromStackId(self.params['stackid'])
		self.stack['boxsize'] = apStack.getStackBoxsize(self.params['stackid'])
		self.stack['file'] = os.path.join(self.stack['data']['path']['path'], self.stack['data']['name'])

		# symmetry info
		if self.params['sym']=='Icos':
			self.params['symtype']='I'
			self.params['symfold']=None
		else:
			self.params['symtype']=self.params['sym'][0]
			self.params['symfold']=int(self.params['sym'][1:])
			# eman "d" symmetry is spider "ci"
			if self.params['symtype'].upper()=="D":
				self.params['symtype'] = "CI"

		# create symmetry doc file
		sydoc="sym.spi"
		alignment.symmetryDoc(self.params['symtype'],self.params['symfold'],sydoc)

		# convert incr to array of increments
		ang_inc=self.params['incr'].split(',')
		self.params['numiter'] = len(ang_inc)
		self.params['increments']=[]
		for i in range(0,self.params['numiter']):
			self.params['increments'].append(int(ang_inc[i]))

		# convert stack to spider stack
		spiderstack=os.path.join(self.params['rundir'],'start.spi')
		alignment.stackToSpiderStack(
			self.stack['file'],
			spiderstack,
			apix=self.stack['apix'],
			boxsize=self.stack['boxsize'],
			numpart=self.params['numpart']
		)

		# create filtered stack
		spiderstackfilt=spiderstack
		if (self.params['lowpass']+self.params['highpass']) > 0:
			spiderstackfilt=os.path.join(self.params['rundir'],'start_filt.spi')
			alignment.stackToSpiderStack(
				self.stack['file'],
				spiderstackfilt,
				apix=self.stack['apix'],
				boxsize=self.stack['boxsize'],
				lp=self.params['lowpass'],
				hp=self.params['highpass'],
				numpart=self.params['numpart']
			)

		# rescale initial model if necessary
		outvol = os.path.join(self.params['rundir'],"vol000.spi")
		apVolume.rescaleVolume(self.params['modelid'],outvol,self.stack['boxsize'],self.stack['apix'],spider=True)

		self.params['itervol']=outvol

		for iter in range(1,self.params['numiter']+1):
			# create projections for projection matching
			apDisplay.printMsg("creating reference projections of volume: %s" % self.params['itervol'])
			projs,numprojs,ang,sel = alignment.createProjections(
				incr=self.params['increments'][iter-1],
				boxsz=self.stack['boxsize'],
				symfold=self.params['symfold'],
				invol=self.params['itervol'],
				rad=self.params['rad'],
			)

			# run reference-based alignment
			apDisplay.printMsg("running reference-based alignment (AP MQ)")

			apmqfile = "apmq%03d.spi" % iter
			outang = "angular%03d.spi" % iter
			shf = "shifts%03d.spi" % iter
			shiftedStack="parts_shifted.spi"

			alignment.checkFile(shf)

			alignment.spiderAPMQ(
				projs=projs,
				numprojs=numprojs,
				tsearch=self.params['xysearch'],
				tstep=self.params['xystep'],
				firstRing=self.params['firstring'],
				lastRing=self.params['lastring'],
				stackfile=spiderstackfilt,
				nump=self.params['numpart'],
				ang=ang,
				apmqfile=apmqfile,
				outang=outang,
				nproc=self.params['proc'],
			)
			# use cross-correlation to find the sub-pixel alignment
			# of the particles,
			# results will be saved in "peakfile.spi"

			alignment.checkFile(shiftedStack)

			# don't use MPI here - for some reason slower?
			mySpi=spyder.SpiderSession(dataext=".spi", logo=False, log=False)

			apmqlist = alignment.readDocFile(apmqfile)
			avgccrot = 0

			apDisplay.printMsg("creating shifted stack")
			for p in range(0,self.params['numpart']):
				ref=int(float(apmqlist[p][2]))
				ccrot=float(apmqlist[p][3])
				inplane=float(apmqlist[p][4])
				avgccrot+=ccrot

				# invert the sign - ref projs will be rotated
				inplane*=-1

				# get corresponding projection
				if (ref <= 0):
					# mirror projection if necessary
					ref*=-1
					refimg=spyder.fileFilter(projs)+"@"+str(ref)
					alignment.mirrorImg(refimg,"_3",inMySpi=mySpi)
					img="_3"
				else:
					img=spyder.fileFilter(projs)+"@"+str(ref)

				alignment.rotAndShiftImg(img,"_2",inplane,inMySpi=mySpi)
				alignment.maskImg("_2","_3",self.params['rad'],"D","E",
						center=int((self.stack['boxsize']/2)+1),
						inMySpi=mySpi)
				# pad ref image & stack image to twice the size
				alignment.padImg("_3","_2",2*self.stack['boxsize'],"N",1,1,0,inMySpi=mySpi)
				stackimg=spyder.fileFilter(spiderstack)+"@"+str(p+1)
				alignment.padImg(stackimg,"_1",2*self.stack['boxsize'],"B",1,1,inMySpi=mySpi)

				# calculate cross-correlation
				alignment.getCC("_1","_2","_1",inMySpi=mySpi)

				# crop the correllation image to allowable shift amount
				shift=int(self.params['allowedShift']*self.stack['boxsize'])
				dim=2*shift+1
				topleftx=self.stack['boxsize']-shift+1
				alignment.windowImg("_1","_2",dim,topleftx,topleftx,inMySpi=mySpi)

				# find the sub-pixel location of cc peak
				mySpi.toSpiderQuiet("PK x11,x12,x13,x14,x15,x16,x17","_2","0")

				# create new stack of shifted particles
				shpos=spyder.fileFilter(shiftedStack)+"@"+str(p+1)
				mySpi.toSpiderQuiet("IF(x17.EQ.0.0) THEN")
				mySpi.toSpiderQuiet("GP x17","_2",str(shift+1)+","+str(shift+1))
				alignment.copyImg(stackimg,shpos,inMySpi=mySpi)
				mySpi.toSpiderQuiet("ELSE")
				#mySpi.toSpiderQuiet("RT SQ",stackimg,shpos,inplane*-1,"-x15,-x16")
				mySpi.toSpiderQuiet("SH F",stackimg,shpos,"-x15,-x16")
				mySpi.toSpiderQuiet("ENDIF")

				# save shifts to file
				mySpi.toSpiderQuiet("SD "+str(p+1)+",x15,x16,x17",spyder.fileFilter(shf))
			mySpi.toSpiderQuiet("SD E",spyder.fileFilter(shf))
			mySpi.close()

			# create class average images
			alignment.createClassAverages(
				shiftedStack,
				projs,
				apmqfile,
				numprojs,
				self.stack['boxsize'],
				shifted=True,
			)
			# rename class averages & variacnes for iteration
			cmd="mv classes.hed classes.%d.hed;" % iter
			cmd+="mv classes.img classes.%d.img;" % iter
			cmd+="mv variances.hed variances.%d.hed;" % iter
			cmd+="mv variances.img variances.%d.img;" % iter
			proc = subprocess.Popen(cmd, shell=True)
			proc.wait()

			# calculate the stddev for the apmq cc's for throwing out particles
			avgccrot/=self.params['numpart']
			stdccrot = 0
			for p in range(0,self.params['numpart']):
				stdccrot+=abs(float(apmqlist[p][3])-avgccrot)
			stdccrot/=self.params['numpart']
			cccutoff=avgccrot+(stdccrot*self.params['keepsig'])

			apDisplay.printMsg("average cc: %f" %avgccrot)
			apDisplay.printMsg("setting cutoff to: %f" %cccutoff)
			# create new selection file that only has particles with good cc's
			selectfile="select%03d.spi" % iter
			alignment.checkFile(selectfile)
			mySpi = spyder.SpiderSession(nproc=self.params['proc'],dataext=".spi", logo=False, log=False)
			i=1
			for p in range(0,self.params['numpart']):
				ccrot=float(apmqlist[p][3])
				if ccrot>=cccutoff:
					mySpi.toSpiderQuiet("x11=%d" % (p+1))
					mySpi.toSpiderQuiet("SD %d,x11" % i,spyder.fileFilter(selectfile))
					i+=1
			mySpi.close()

			# calculate the new 3d structure using centered projections
			# and the corrected angles from the angular doc file
			apDisplay.printMsg("creating 3d volume")
			out_rawvol="vol_raw%03d.spi" % iter
			if self.params['voliter'] is not None:
				alignment.iterativeBackProjection(
					shiftedStack,
					selectfile,
					rad=self.params['rad'],
					ang=outang,
					out=out_rawvol,
					lam=self.params['lambda'],
					iterlimit=self.params['voliter'],
					mode=self.params['bpmode'],
					smoothfac=self.params['smoothfac'],
					sym=sydoc,
					nproc=self.params['proc'],
				)
			else:
				alignment.backProjection(
					shiftedStack,
					selectfile,
					ang=outang,
					out=out_rawvol,
					sym=sydoc,
					nproc=self.params['proc']
				)

			# create even & odd select files
			apDisplay.printMsg("creating even/odd volumes")
			oddfile="selectodd%03d.spi" % iter
			evenfile="selecteven%03d.spi" % iter
			alignment.docSplit(selectfile,oddfile,evenfile)

			# get the even & odd volumesa
			oddvol="vol1%03d.spi" % iter
			evenvol="vol2%03d.spi" % iter
			if self.params['voliter'] is not None:
				alignment.iterativeBackProjection(
					shiftedStack,
					oddfile,
					rad=self.params['rad'],
					ang=outang,
					out=oddvol,
					lam=self.params['lambda'],
					iterlimit=self.params['voliter'],
					mode=self.params['eobpmode'],
					smoothfac=self.params['smoothfac'],
					sym=sydoc,
					nproc=self.params['proc']
				)
				alignment.iterativeBackProjection(
					shiftedStack,
					evenfile,
					rad=self.params['rad'],
					ang=outang,
					out=evenvol,
					lam=self.params['lambda'],
					iterlimit=self.params['voliter'],
					mode=self.params['eobpmode'],
					smoothfac=self.params['smoothfac'],
					sym=sydoc,
					nproc=self.params['proc']
				)
			else:
				alignment.backProjection(
					shiftedStack,
					oddfile,
					ang=outang,
					out=oddvol,
					sym=sydoc,
					nproc=self.params['proc'],
				)
				alignment.backProjection(
					shiftedStack,
					evenfile,
					ang=outang,
					out=evenvol,
					sym=sydoc,
					nproc=self.params['proc'],
				)

			# calculate the FSC
			apDisplay.printMsg("calculating FSC")
			fscfile="fsc%03d.spi" % iter
			emanfsc="fsc.eotest.%d" % iter
			alignment.calcFSC(oddvol,evenvol,fscfile)
			# convert to eman-style fscfile
			alignment.spiderFSCtoEMAN(fscfile,emanfsc)

			# calculate the resolution at 0.5 FSC & write to file
			res=apRecon.calcRes(emanfsc,self.stack['boxsize'],self.stack['apix'])
			restxt="resolution.txt"
			if iter==1 and os.path.isfile(restxt):
				os.remove(restxt)
			resfile=open(restxt,"a")
			resfile.write("iter %d:\t%.3f\n" % (iter,res))
			resfile.close()

			# filter & normalize the volume to be used as a reference in the next round
			outvol="vol%03d.spi" % iter
			emancmd="proc3d %s %s apix=%.3f lp=%.3f mask=%d norm spidersingle" % (out_rawvol,outvol,self.stack['apix'],res,self.params['rad'])
			if self.params['imask'] is not None:
				emancmd+=" imask=%d" % self.params['imask']
			apEMAN.executeEmanCmd(emancmd, verbose=True)

			# create mrc files of volumes
			emancmd="proc3d %s %s apix=%.3f mask=%d norm" % (out_rawvol,"threed.%da.mrc" % iter, self.stack['apix'],self.params['rad'])
			if self.params['imask'] is not None:
				emancmd+=" imask=%d" % self.params['imask']
			apEMAN.executeEmanCmd(emancmd, verbose=True)
			emancmd="proc3d %s %s apix=%.3f lp=%.3f mask=%d norm" % (out_rawvol,"threed.%da.lp.mrc" % iter, self.stack['apix'],res, self.params['rad'])
			if self.params['imask'] is not None:
				emancmd+=" imask=%d" % self.param['imask']
			apEMAN.executeEmanCmd(emancmd, verbose=True)

			# set this model as start for next iteration, remove previous
			os.remove(self.params['itervol'])
			os.remove(out_rawvol)
			self.params['itervol']=outvol

			# clean up directory
			apDisplay.printMsg("cleaning up directory")
			if os.path.isfile(oddvol):
				os.remove(oddvol)
			if os.path.isfile(evenvol):
				os.remove(evenvol)
			if os.path.isfile(ang):
				os.remove(ang)
			if os.path.isfile(sel):
				os.remove(sel)
			if os.path.isfile(projs):
				os.remove(projs)
			if os.path.isfile(oddfile):
				os.remove(oddfile)
			if os.path.isfile(evenfile):
				os.remove(evenfile)
			if os.path.isfile(emanfsc) and os.path.isfile(fscfile):
				os.remove(fscfile)
			if os.path.isfile(shiftedStack):
				os.remove(shiftedStack)
		os.remove(self.params['itervol'])

#=====================
if __name__ == "__main__":
	refine3d = apmqRefineScript()
	refine3d.start()
	refine3d.close()


