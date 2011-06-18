#!/usr/bin/env python

import sys
import os
import shutil
import math
import re
from appionlib import apPrepParallelRefine

class PrepParallelFrealign(apPrepParallelRefine.PrepParallelRefinement):
	def setupRefineScript(self):
		recondir = self.params['recondir']
		ppn = self.params['ppn']
		nproc = self.params['nproc']
		items = os.listdir(recondir)
		iter_dirs = []
		for item in items:
			if 'iter' == item[:4] and os.path.isdir(os.path.join(recondir,item)):
				iter_dirs.append(item)
		for iter_dir in iter_dirs:
			self.createProcShFiles(nproc,recondir,iter_dir)
			self.remakeCombineShFile(ppn,recondir,iter_dir)
			self.remakeRunShFile(nproc,recondir,iter_dir)

	def remakeRunShFile(self,nproc,recondir,iter_dir):
		sh = os.path.join(recondir,iter_dir,'frealign.%s.run.sh' % iter_dir)
		print 'Modifying %s' % os.path.basename(sh)
		file = open(sh,'w')
		lines = map((lambda x: '-np 1 %s/frealign.%s.proc%03d.sh\n' % (iter_dir,iter_dir,x)),range(1,nproc+1))
		file.writelines(lines)
		file.close()

	def remakeCombineShFile(self,ppn,recondir,iter_dir):
		sh = os.path.join(recondir,iter_dir,'frealign.%s.combine.sh' % iter_dir)
		print 'Modifying %s' % os.path.basename(sh)
		file = open(sh,'r')
		lines = file.readlines()
		file.close()
		for i,line in enumerate(lines):
			if 'NCPUS' in line:
				lines[i] = line.replace('1','%d' % ppn)
				break
		out = open(sh,'w')
		out.writelines(lines)
		out.close()

	def createProcShFiles(self,nproc,recondir,iter_dir):			
		original = os.path.join(recondir,iter_dir,'frealign.%s.proc001.sh' % iter_dir)
		if os.path.isfile(original):
			print 'Writing %d files based on %s' % (nproc,os.path.basename(original))
			# Determine particles per process from prepRefine template sh file
			templatefile = open(original)
			lines = templatefile.readlines()
			for i,line in enumerate(lines):
				if 'Job #' in line:
					job_comment_line = i
				if 'PARTICLES' in line:
					particle_comment_line = i
				if 'frealign.exe' in line:
					exe_line_number = i
					particle_range_line = i+4
					break
			templatefile.close()
			last_particle = int(lines[particle_range_line].split(',')[-1][:-1])
			# This is integer division and will return integer
			stepsize = int(math.ceil(float(last_particle) / nproc))
			for proc in range(nproc):
				newlines = list(lines)
				proc_start_particle = stepsize * proc + 1
				proc_end_particle = min(stepsize * (proc+1), last_particle)
				re1 = re.compile(r'proc001')
				newlines = map((lambda x:re1.sub('proc%03d' % (proc+1,),x)),newlines)
				newlines[job_comment_line] = '###Job #%03d, Particles %6d - %6d\n' % (proc+1, proc_start_particle, proc_end_particle)	
				newlines[particle_comment_line] = '#PARTICLES %d THRU %d\n' % (proc_start_particle, proc_end_particle)	
				newlines[particle_range_line] = '%d, %d\n' % (proc_start_particle, proc_end_particle)	
				# Write new file
				proc_path = os.path.join(recondir,iter_dir,'frealign.%s.proc%03d.sh' % (iter_dir,proc+1))
				proc_file = open(proc_path,'w')
				proc_file.writelines(newlines)
				proc_file.close()
		else:
			sys.exit('Failed: Could not find template file %s' % original)

if __name__ == '__main__':
	app = PrepParallelFrealign()
	app.run()

