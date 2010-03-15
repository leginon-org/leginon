#!/usr/bin/env python
# this should be passed a list of cls files as arguments. It will take each raw
# particle, apply the predetermined 2D alignment to it and write it to a common
# output file using the Eulers take from the reference projection

import EMAN
import os,sys
import optparse
import tarfile
import shutil

def setupParserOptions():
	parser=optparse.OptionParser()
	parser.set_description("this should be passed a cls file. It will take each raw particle, apply the predetermined 2D alignment to it and write it to a common output file using the Eulers take from the reference projection")
	parser.set_usage("%prog -c FILE [options]")
	parser.add_option("-c", "--cls", dest="cls", type="string", metavar="FILE",
		help="cls####.lst file")
	parser.add_option("--format", dest="format", type="string", default="spider", metavar="FORMAT",
		help="file format of aligned output (default=SPIDER)")
	parser.add_option("--clean", dest="clean", default=False, action="store_true",
		help="only use particles that passed correspondence analysis previously")
	parser.add_option("--prealigned", dest="prealigned", default=False, action="store_true",
		help="do not perform an alignment of the input particles")
	parser.add_option("-s", "--stack", dest="stack", type="string", metavar="FILE",
		help="specify stack to override the one in the lst file")
	parser.add_option("--noproj", dest="noproj", default=False, action="store_true",
		help="use if the first particle in the stack is not an average or projection")
	options,args = parser.parse_args()
	if len(args) > 0:
		parser.error("Unknown commandline options: " +str(args))
	if len(sys.argv) < 2:
		parser.print_help()
		parser.error("no options defined")
	params = {}
	for i in parser.option_list:
		if isinstance(i.dest, str):
			params[i.dest] = getattr(options, i.dest)
	return params

	
if __name__ == "__main__":
	params=setupParserOptions()

	fsp=params['cls']
	format=params['format'].lower()

	if not os.path.exists(fsp):
		print "file '%s' does not exist"%fsp
		sys.exit()

	if fsp[-4:] == ".tar":
		# expand cls.#.tar into tmp dir
		tmpdir = "cls2alignextracttmpdir"
		if os.path.exists(tmpdir):
			shutil.rmtree(tmpdir)
		os.mkdir(tmpdir)

		print "reading",fsp
		clstar=tarfile.open(fsp)
		clslist=clstar.getmembers()
		clsnames=clstar.getnames()
		print "extracting",fsp,"into temp directory"
		for clsfile in clslist:
			clstar.extract(clsfile,tmpdir)
		clstar.close() 

		# combine all cls files into 1
		print "creating combined LST file"
		particles = {} 
		outcls = "cls.combined.lst"
		outf = open(outcls,'w')
		outf.write("#LST\n")
		params['noproj'] = True
		for i in range(len(clsnames)):
			f = open(os.path.join(tmpdir,clsnames[i]))
			for line in f:
				d = line.strip().split()
				if len(d)<4:
					continue
				particles[int(d[0])]=line
		parts = particles.keys()
		parts.sort()
		for p in parts:
			outf.write(particles[p])
		outf.close()

		shutil.rmtree(tmpdir)
		fsp = outcls

	# if using different particle stack
	if params['stack']:
		if not os.path.exists(params['stack']):
			print "Error: stack '%s' does not exist\n"%params['stack']
			sys.exit()
		print "using stack: %s"%params['stack']
		f=open(fsp,'r')
		lines=f.readlines()
		f.close()
		fsp=fsp.split('.')[0]+'.2.lst'
		f=open(fsp,'w')
		for l in lines:
			d=l.strip().split()
			if len(d) < 3:
				f.write(l)
				continue
			f.write("%s\t%s\t%s\t%s\n"%(d[0],os.path.abspath(params['stack']),d[2],d[3]))
		f.close()

	# if only want particles that passed coran,
	# create new list file with only good particles
	if params['clean'] is True:
		f=open(fsp,'r')
		lines=f.readlines()
		f.close()
		fsp=fsp.split('.')[0]+'.good.lst'
		f=open(fsp,'w')
		for l in lines:
			d=l.strip().split()
			if len(d) < 3:
				f.write(l)
				continue
			if d[3][-1]=='1':
				f.write(l)
		f.close()
	n=EMAN.fileCount(fsp)[0]
	
	classnamepath = fsp.split('.')[0]+'.dir'
	if not os.path.exists(classnamepath):
		os.mkdir(classnamepath)
	b=EMAN.EMData()
	b.readImage(fsp,0)
	e=b.getEuler()

	a=EMAN.EMData()
	if format == "eman" or format=="imagic":
		outname="aligned.hed"
	else:
		outname="aligned.spi"

	startn = 1
	if params['noproj'] is True:
		startn=0
	print "creating aligned stack"
	for i in range(startn,n):
		a.readImage(fsp,i)
		a.edgeNormalize()
		if params['prealigned'] is False:
			a.rotateAndTranslate()
			a.setRAlign(e)
			if a.isFlipped():
				a.hFlip()
		output = os.path.join(classnamepath,outname)
		a.writeImage(output,-1)


