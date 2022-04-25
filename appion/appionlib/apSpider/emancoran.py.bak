
## python
import os
import subprocess
from appionlib import apEMAN
from appionlib import spyder

"""
A large collection of SPIDER functions for EMAN CORAN purposes only

I try to keep the trend
image file:
	*****img.spi
image stack file:
	*****stack.spi
doc/keep/reject file:
	*****doc.spi
file with some data:
	*****data.spi

that way its easy to tell what type of file it is
"""

#===============================
def runCoranClass(params,cls):
	print "processing class",cls

	#set up cls dir
	clsdir=cls.split('.')[0]+'.dir'
	os.mkdir(clsdir)

	clscmd='clstoaligned.py -c ' + cls
	## if multiprocessor, don't run clstoaligned yet
	if params['proc'] == 1:
		#make aligned stack
		proc = subprocess.Popen(clscmd, shell=True)
		proc.wait()

	corancmd=clscmd+'\n'

	coranbatch='coranfor'+cls.split('.')[0]+'.bat'

	#make spider batch
	params['nptcls'] = apEMAN.getNPtcls(cls)

	# if no particles, create an empty class average
	if params['nptcls'] == 0:
		# don't run clscmd, just make directory and empty average
		apEMAN.writeBlankImage(os.path.join(clsdir,'classes_avg.spi'),params['boxsize'],0,'spider')
		print "WARNING!! no particles in class"
		return

	# if only 3 particles or less, turn particles into the class averages
	elif params['nptcls'] < 4:
		#this is an ugly hack, just average the particles together, no ref-free
		# don't use mpi, just make directory with clscmd and average particles
		proc = subprocess.Popen(clscmd, shell=True)
		proc.wait()
		avgcmd=("proc2d %s %s average" % (os.path.join(clsdir,'aligned.spi'),os.path.join(clsdir,'classes_avg.spi')))
		proc = subprocess.Popen(avgcmd, shell=True)
		proc.wait()
		dummyclsdir=os.path.join(clsdir,'classes')
		os.mkdir(dummyclsdir)
		dummyfilename='clhc_cls0001.spi'
		dummyfile=open(os.path.join(dummyclsdir,dummyfilename),'w')
		dummyfile.write(';bat/spi\n')
		for ptcl in range(0,params['nptcls']):
			dummyfile.write('%d 1 %d\n' % (ptcl,ptcl+1))
		dummyfile.close()
		print "WARNING!! not enough particles in class for subclassification"
		return

	# otherwise, run coran
	else:
		makeSpiderCoranBatch(params,coranbatch,clsdir)
		### this is how we should do this
		#mySpider = spyder.SpiderSession(logo=False, nproc=1)
		#mySpider.toSpiderQuiet("@%s\n" % coranbatch.split('.')[0])
		spidercmd = ("cd %s\n" % clsdir)
		
		if params['hp'] is not None:
			spidercmd+=("proc2d aligned.spi alignedhp.spi spiderswap apix=%s hp=%s\n" % (params['apix'],params['hp']))
		spidercmd+= ("spider bat/spi @%s\n" % coranbatch.split('.')[0])
		## if multiprocessor, don't run spider yet
		if params['proc'] == 1:
			proc = subprocess.Popen(spidercmd, shell=True)
			proc.wait()
		corancmd+=spidercmd
		return corancmd

#===============================
def makeSpiderCoranBatch(params,filename,clsdir):
	nfacts=20
	if params['nptcls'] < 21:
		nfacts=params['nptcls']-1
	f=open(os.path.join(clsdir,filename),'w')
	f.write('MD ; verbose off in spider log file\n')
	f.write('VB OFF\n')
	f.write('\n')
	f.write('x99=%d  ; number of particles in stack\n' % params['nptcls'])
	f.write('x98=%d   ; box size\n' % params['boxsize'])
	f.write('x94=%d    ; mask radius\n' % params['coranmask'])
	haccut = params['haccut']
	sp = spyder.SpiderSession()
	if sp.version() >= 18.03:
		haccut*=100
	sp.close()
	f.write('x93=%f  ; cutoff for hierarchical clustering\n' % haccut)
	f.write('x92=20    ; additive constant for hierarchical clustering\n')
	f.write('\n')
	alignstack='aligned'
	if params['hp'] is not None:
		f.write('FR G ; aligned hp stack file\n')
		f.write('[alignedhp]alignedhp\n')
		alignstack='alignedhp'
	f.write('FR G ; aligned stack file\n')
	f.write('[aligned]aligned\n')
	f.write('\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write('\n')
	f.write('FR G ; where to write class lists\n')
	f.write('[clhc_cls]classes/clhc_cls\n')
	f.write('\n')
	f.write('FR G ; where to write alignment data\n')
	f.write('[ali]alignment/\n')
	f.write('\n')
	f.write('VM\n')
	f.write('mkdir alignment\n')
	f.write('\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write(';; create the sequential file and then use that file and do a hierarchical ;;\n')
	f.write(';; clustering. Run clhd and clhe to classify the particles into different  ;;\n')
	f.write(';; groups.                                                                 ;;\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write('\n')
	f.write('VM\n')
	f.write('echo Performing multivariate statistical analysis\n')
	f.write('VM\n')
	f.write('echo "  making template file"\n')
	f.write('\n')
	f.write('MO      ; make mask template\n')
	f.write('_9      ; save template in memory\n')
	f.write('x98,x98 ; box size\n')
	f.write('c       ; circle\n')
	f.write('x94     ; radius of mask\n')
	f.write('\n')
	f.write('VM\n')
	f.write('echo "  doing correspondence analysis"\n')
	f.write('\n')
	f.write('CA S           ; do correspondence analysis\n')
	f.write('[%s]@***** ; aligned stack\n' % alignstack)
	f.write('1-x99          ; particles to use\n')
	f.write('_9             ; mask file\n')
	f.write('%d             ; number of factors to be used\n' % nfacts)
	f.write('C              ; Coran analysis\n')
	f.write('x92            ; additive constant (since coran cannot have negative values)\n')
	f.write('[ali]coran     ; output file prefix\n')
	f.write('\n')
	f.write('\n')
	f.write('DO LB14 x11=1,%d\n' % nfacts)
	f.write('CA SRE\n')
	f.write('[ali]coran\n')
	f.write('x11\n')
	f.write('[ali]sre@{***x11}\n')
	f.write('LB14\n')
	f.write('\n')
	#f.write('VM\n')
	#f.write('eigendoc.py alignment/coran_EIG.spi alignment/eigendoc.out 30\n')
	#f.write('\n')
	f.write('VM\n')
	f.write('echo "  clustering..."\n')
	f.write('\n')
	f.write('CL HC          ; do hierarchical clustering\n')
	f.write('[ali]coran_IMC ; coran image factor coordinate file\n')
	f.write('1-3\n')
	f.write('1.00           ; factor numbers to be included in clustering algorithm\n')
	f.write('1.00           ; factor weights\n')
	f.write('1.00           ; for each factor number\n')
	f.write('5              ; use Wards method\n')
	f.write('Y              ; make a postscript of dendogram\n')
	f.write('[ali]clhc.ps   ; dendogram image file\n')
	f.write('Y              ; save dendogram doc file\n')
	f.write('[ali]clhc_doc  ; dendogram doc file\n')
	f.write('\n')
	f.write('\n')
	f.write(';;;determine number of classes for given threshold\n')
	f.write('CL HD\n')
	f.write('x93\n')
	f.write('[ali]clhc_doc\n')
	f.write('clhc_classes\n')
	f.write('\n')
	f.write('UD N,x12\n')
	f.write('clhc_classes\n')
	f.write('\n')
	f.write('VM\n')
	f.write('mkdir classes\n')
	f.write('\n')
	f.write('VM\n')
	f.write('echo "Creating {%F5.1%x12} classes using a threshold of {%F7.5%x93}"\n')
	f.write('CL HE         ; generate doc files containing particle numbers for classes\n')
	f.write('x93         ; threshold (closer to 0=more classes)\n')
	f.write('[ali]clhc_doc      ; dendogram doc file\n')
	f.write('[clhc_cls]****  ; selection doc file that will contain # of objects for classes\n')
	f.write('\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write(';; average aligned particles together ;;\n')
	f.write(';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;\n')
	f.write('\n')
	f.write('VM\n')
	f.write('echo Averaging particles into classes\n')
	f.write('\n')
	f.write('DO LB20 x81=1,x12\n')
	f.write('AS R\n')
	f.write('[aligned]@*****\n')
	f.write('[clhc_cls]{****x81}\n')
	f.write('A\n')
	f.write('classes_avg@{****x81}\n')
	f.write('classes_var@{****x81}\n')
	f.write('LB20\n')
	f.write('\n')
	f.write('EN D\n')
