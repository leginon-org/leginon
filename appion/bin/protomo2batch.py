#!/usr/bin/env python
# 
# This script provides the user access to the protomo command line interface,
# allowing for the initial coarse alignment and subsequent iterative alignments and
# reconstruction to be performed serially across a range of tiltseries. Three param files
# are required: One for coarse alignment, once for refinement, and one for reconstruction.
# 
# *To be used from Appion 'Batch Align Tilt Series'

import os
import sys
import math
import glob
import scipy
import subprocess
from multiprocessing import Pool
from appionlib import basicScript
from appionlib import apDisplay
from appionlib import apDatabase
from appionlib import apProTomo2Prep
from appionlib import apTomo
from appionlib import apProTomo
from appionlib import apParam
from pyami import mrc

try:
	import protomo
except:
	print "protomo did not get imported"

cwd=os.getcwd()
wd=''

#=====================
class ProTomo2Batch(basicScript.BasicScript):
	#=====================
	def setupParserOptions(self):
		self.parser.set_usage( "Usage: %prog --tiltseriesnumber=<#> --sessionname=<sessionname> [options]"
			+"\nFor batch alignment and reconstruction: %prog --tiltseriesnumber=<#> --sessionname=<sessionname>"
			+"--coarse_param_file=/path/to/coarse.param --refine_param_file=/path/to/refine.param"
			+"--recon_param_file=/path/to/recon.param --numtiltseries=50 [options]")
		
		self.parser.add_option("--sessionname", dest="sessionname", help="Session date, e.g. --sessionname=14aug02a")
		
		self.parser.add_option("--runname", dest="runname", help="Name of protmorun directory as made by Appion")
		
		self.parser.add_option('-R', '--rundir', dest='rundir', help="Path of run directory")
		
		self.parser.add_option("--tiltseries", dest="tiltseries", help="Name of Protomo series, e.g. --tiltseries=31")
		
		self.parser.add_option("--iters", dest="iters", default=1, type="int",
			help="Number of Refinement iterations, e.g. --iters=4", metavar="int")
		
		self.parser.add_option("--procs", dest="procs", default=1,
			help="Number of processors to use, 'all' defaults to use all processors on running machine e.g. --procs=4")
		
		self.parser.add_option("--coarse_param_file", dest="coarse_param_file",
			help="External Coarse Alignment param file. e.g. --coarse_param_file=/path/to/coarse.param", metavar="FILE")
		
		self.parser.add_option("--refine_param_file", dest="refine_param_file",
			help="External Refinement param file. e.g. --refine_param_file=/path/to/refine.param", metavar="FILE")
		
		self.parser.add_option("--recon_param_file", dest="recon_param_file",
			help="External Recnostruction param file. e.g. --recon_param_file=/path/to/recon.param", metavar="FILE")
	
		self.parser.add_option("--numtiltseries", dest="numtiltseries", type="int",
			help="Number of tilt series in session to batch process, e.g. --numtiltseries=4", metavar="int")
		
		self.parser.add_option("--tiltseriesranges", dest="tiltseriesranges",
			help="One or more ranges of tilt series to be processed. Only use numbers, commas, and hyphens., e.g. --tiltseriesranges=4,10-21,28-44,77", metavar="int")
		
		self.parser.add_option("--link_recons", dest="link_recons",
			help="Directory to hardlink completed reconstructions to, e.g. --link_recons=/path/to/batch_dir", metavar="int")
		
		self.parser.add_option("--jobtype", dest="jobtype", help="Appion jobtype")
		
		self.parser.add_option("--projectid", dest="projectid", help="Appion project ID")
		
		self.parser.add_option("--expid", dest="expid", help="Appion experiment ID")
		
		self.parser.add_option("--link", dest="link",  default=True,
			help="Link raw images if True, copy if False, e.g. --link=False")
		
	#=====================
	def checkConflicts(self):
		pass
		
		#check if files exist
		#check if necessary options exist
		
		return True

	#=====================
	def onInit(self):
		"""
		Advanced function that runs things before other things are initialized.
		For example, open a log file or connect to the database.
		"""
		return

	#=====================
	def onClose(self):
		"""
		Advanced function that runs things after all other things are finished.
		For example, close a log file.
		"""
		return
	
	
	#=====================
	#def alignAndReconstruct(n):
	#	print n
	
	#=====================
	def start(self):
		# PARALLEL PROCESSING!!! WORK DAMN YOU!
		#if self.params['procs'] == 'all':
		#	self.params['procs'] = None
		#elif self.params['procs'] > self.params['numtiltseries']:
		#	self.params['procs'] = self.params['numtiltseries']
		#pool = Pool(self.params['procs'])
		#tiltseriesrange = range(self.params['numtiltseries'])
		#chunksize = 1
		#pool.map(self.alignAndReconstruct, [0, 1, 2, 3, 4], 1)
		#pool.close()
		#pool.join()
		#print "\nDone Aligning and Reconstructing %s tiltseries in session %s\n" % (self.params['numtiltseries'],self.params['sessionname'])
		
		def hyphen_range(s):
			"""
			Takes a range in form of "a-b" and generate a list of numbers between a and b inclusive.
			also accepts comma separated ranges like "a-b,c-d,f" will build a list which will include
			numbers from a to b, a to d, and f.
			Taken from http://code.activestate.com/recipes/577279-generate-list-of-numbers-from-hyphenated-and-comma/
			"""
			s="".join(s.split())#removes white space
			r=set()
			for x in s.split(','):
			    t=x.split('-')
			    if len(t) not in [1,2]: raise SyntaxError("hash_range is given its arguement as "+s+" which seems not correctly formated.")
			    r.add(int(t[0])) if len(t)==1 else r.update(set(range(int(t[0]),int(t[1])+1)))
			l=list(r)
			l.sort()
			return l
		
		global wd
		wd=self.params['link_recons']
		self.params['rundir']=os.path.dirname(self.params['rundir']) #Need to be up one directory
		tiltseriesranges=hyphen_range(self.params['tiltseriesranges'])
		for tiltseriesnumber in tiltseriesranges:
			#=====================
			##PREP##
			#=====================
			apDisplay.printMsg("Beginning Processing of Tilt Series #%s from %s\n" % (tiltseriesnumber, self.params['sessionname']))
			tiltdirname="/tiltseries%04d" % (tiltseriesnumber)
			tiltdir=self.params['rundir']+tiltdirname
			seriesnumber = "%04d" % tiltseriesnumber
			seriesname = 'series'+str(seriesnumber)
			tiltfilename = seriesname+'.tlt'
			tiltfilename_full=tiltdir+'/'+tiltfilename
			raw_path = os.path.join(tiltdir,'raw')
			os.system("mkdir -p %s" % tiltdir)
			os.chdir(tiltdir)
			
			apDisplay.printMsg('Preparing raw images and initial tilt file')
			try:
				apProTomo2Prep.prepareTiltFile(self.params['sessionname'], seriesname, tiltfilename, tiltseriesnumber, raw_path, link=self.params['link'])
			except:
				apDisplay.printMsg("Failed to generate .tlt file. Skipping Tilt Series #%s...\n" % (tiltseriesnumber))
				continue
			
			
			#=====================
			##COARSE ALIGNMENT##
			#=====================
			name='coarse_'+seriesname
			cpparam="cp %s %s/%s.param" % (self.params['coarse_param_file'],tiltdir,name)
			os.system(cpparam)
			coarse_param_full=tiltdir+'/'+name+'.param'
			
			#Edit param file to replace pathlist, cachedir, and outdir
			newcachedir=tiltdir+'/cache'
			newoutdir=tiltdir+'/out'
			command1="grep -n 'pathlist' %s | awk '{print $1}' | sed 's/://'" % (coarse_param_full)
			proc=subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
			(pathlistline, err) = proc.communicate()
			pathlistline=int(pathlistline)
			command2="grep -n 'cachedir' %s | awk '{print $1}' | sed 's/://'" % (coarse_param_full)
			proc=subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
			(cachedirline, err) = proc.communicate()
			cachedirline=int(cachedirline)
			command3="grep -n 'outdir' %s | awk '{print $1}' | sed 's/://'" % (coarse_param_full)
			proc=subprocess.Popen(command3, stdout=subprocess.PIPE, shell=True)
			(outdirline, err) = proc.communicate()
			outdirline=int(outdirline)
			command11="sed -i \'%ss|.*| pathlist: \"%s\"  (* AP path to raw directory *)|\' %s" % (pathlistline, raw_path, coarse_param_full)
			os.system(command11)
			command22="sed -i \'%ss|.*| cachedir: \"%s\"  (* AP directory where cache files are stored *)|\' %s" % (cachedirline, newcachedir, coarse_param_full)
			os.system(command22)
			command33="sed -i \'%ss|.*| outdir: \"%s\"  (* AP directory where other output files are stored *)|\' %s" % (outdirline, newoutdir, coarse_param_full)
			os.system(command33)
			
			apDisplay.printMsg('Starting Protomo Coarse Alignment')
			coarse_seriesparam=protomo.param(coarse_param_full)
			coarse_seriesgeom=protomo.geom(tiltfilename_full)
			try:
				series=protomo.series(coarse_seriesparam,coarse_seriesgeom)
				series.align()
	
				corrfile=name+'.corr'
				series.corr(corrfile)
				
				#archive results
				tiltfile=name+'.tlt'
				series.geom(1).write(tiltfile)
				
				cleanup="mkdir coarse_out; ln coarse*.* coarse_out; rm %s.corr; ln %s.i3t %s.i3t" % (name, name, seriesname)
				os.system(cleanup)
				
				# Make correlation peak gif for depiction			
				os.system("mkdir -p %s/gifs/correlations" % tiltdir)
				try:
					img=name+'00_cor.img';
					mrcf=name+'00_cor.mrc';
					gif=name+'00_cor.gif';
					png='*.png';
					out_path=os.path.join(tiltdir,'out');
					img_full=out_path+'/'+img;
					mrc_full=out_path+'/'+mrcf;
					gif_path=os.path.join(tiltdir,'gifs','correlations');
					gif_full=gif_path+'/'+gif;
					png_full=gif_path+'/'+png;
					# Convert the corr peak *.img file to mrc for further processing
					os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
					
					volume = mrc.read(mrc_full);
					slices = len(volume) - 1;
					
					# Convert the *.mrc to a series of pngs
					print "\nCreating correlation peak gif..."
					for i in range(0, slices):
						slice = os.path.join(gif_path,"slice%04d.png" % (i));
						scipy.misc.imsave(slice, volume[i]);
					command = "convert -delay 10 -loop 0 -gravity South -background white -splice 0x18 -annotate 0 'Frame: %%[fx:t+1]' %s %s" % (png_full, gif_full);
					os.system(command);
					command2 = "rm %s" % (png_full);
					os.system(command2);
					print "Done!\n"
				except:
					print "\nAlignment Correlation Peak Images could not be generated. Make sure i3 and imagemagick are in your $PATH. Make sure that pyami and scipy are in your $PYTHONPATH.\n"
				
				apDisplay.printMsg("Coarse Alignment Finished!\n")
				
				
				#=====================
				##REFINEMENTS##
				#=====================
				name=seriesname
				cpparam="cp %s %s/%s.param" % (self.params['refine_param_file'],tiltdir,name)
				os.system(cpparam)
				refine_param_full=tiltdir+'/'+name+'.param'
				
				#Edit param file to replace pathlist, cachedir, and outdir
				command1="grep -n 'pathlist' %s | awk '{print $1}' | sed 's/://'" % (refine_param_full)
				proc=subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
				(pathlistline, err) = proc.communicate()
				pathlistline=int(pathlistline)
				command2="grep -n 'cachedir' %s | awk '{print $1}' | sed 's/://'" % (refine_param_full)
				proc=subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
				(cachedirline, err) = proc.communicate()
				cachedirline=int(cachedirline)
				command3="grep -n 'outdir' %s | awk '{print $1}' | sed 's/://'" % (refine_param_full)
				proc=subprocess.Popen(command3, stdout=subprocess.PIPE, shell=True)
				(outdirline, err) = proc.communicate()
				outdirline=int(outdirline)
				command11="sed -i \'%ss|.*| pathlist: \"%s\"  (* AP path to raw directory *)|\' %s" % (pathlistline, raw_path, refine_param_full)
				os.system(command11)
				command22="sed -i \'%ss|.*| cachedir: \"%s\"  (* AP directory where cache files are stored *)|\' %s" % (cachedirline, newcachedir, refine_param_full)
				os.system(command22)
				command33="sed -i \'%ss|.*| outdir: \"%s\"  (* AP directory where other output files are stored *)|\' %s" % (outdirline, newoutdir, refine_param_full)
				os.system(command33)
				
				apDisplay.printMsg('Starting Protomo Refinement')
				refine_seriesparam=protomo.param(refine_param_full)
				del series
				series=protomo.series(refine_seriesparam)
				for n in range(self.params['iters']):
					apDisplay.printMsg("Startng Refinement Iteration #%s for Tilt Series #%s from %s\n" % (n+1, tiltseriesnumber, self.params['sessionname']))
					series.align()
	
					it="%02d" % (n)
					itt="%02d" % (n+1)
					ite="_ite%02d" % (n)
					basename='%s%s' % (name,it)
					corrfile=basename+'.corr'
					series.corr(corrfile)
					series.fit()
					series.update()
	
					#archive results
					tiltfile=basename+'.tlt'
					series.geom(0).write(tiltfile)
					
					# Make correlation peak gifs for depiction			
					try:
						img=name+it+'_cor.img';
						mrcf=name+it+'_cor.mrc';
						gif=name+it+'_cor.gif';
						png='*.png';
						out_path=os.path.join(tiltdir,'out');
						img_full=out_path+'/'+img;
						mrc_full=out_path+'/'+mrcf;
						gif_path=os.path.join(tiltdir,'gifs','correlations');
						gif_full=gif_path+'/'+gif;
						png_full=gif_path+'/'+png;
						# Convert the corr peak *.img file to mrc for further processing
						os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
						
						volume = mrc.read(mrc_full);
						slices = len(volume) - 1;
						
						# Convert the *.mrc to a series of pngs
						print "\nCreating correlation peak gif for iteration #%s..." % (n+1)
						for i in range(0, slices):
							slice = os.path.join(gif_path,"slice%04d.png" % (i));
							scipy.misc.imsave(slice, volume[i]);
						command = "convert -delay 10 -loop 0 -gravity South -background white -splice 0x18 -annotate 0 'Frame: %%[fx:t+1]' %s %s" % (png_full, gif_full);
						os.system(command);
						command2 = "rm %s" % (png_full);
						os.system(command2);
						print "Done!\n"
					except:
						print "\nAlignment Correlation Peak Images could not be generated. Make sure i3 and imagemagick are in your $PATH. Make sure that pyami and scipy are in your $PYTHONPATH.\n"
					
					# Generate gif of reconstruction of the last iteration for depiction
					os.system("mkdir -p %s/gifs/reconstructions" % tiltdir)
					
					if n+1 == self.params['iters']:
						print "\nGenerating Refinement Reconstruction for Final Iteration (%s)\n" % (n+1)
						try:
							img=name+itt+'_bck.img';
							mrcf=name+itt+'_bck.mrc';
							gif=name+itt+'_bck.gif';
							img_full='out'+'/'+img;
							mrc_full='out'+'/'+mrcf;
							gif_path=os.path.join(tiltdir,'gifs','reconstructions');
							gif_full=gif_path+'/'+gif;
							png_full=gif_path+'/'+png;
							
							# Create intermediate reconstruction
							series.mapfile()
							
							# Convert the reconstruction *.img file to mrc for further processing
							os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
							
							volume = mrc.read(mrc_full);
							slices = len(volume) - 1;
							
							# Convert the *.mrc to a series of pngs
							print "\nCreating reconstruction gif for iteration #%s..." % (n+1)
							for i in range(0, slices):
								slice = os.path.join(gif_path,"slice%04d.png" % (i));
								scipy.misc.imsave(slice, volume[i]);
							# Determine if the resulting gif will be too large, if so resize it during conversion
							dim_x = len(volume[2]);
							if dim_x > 640:
								dim_x = 640;
								dim_y = int(round((640/dim_x) * dim_y));
								command = "convert -delay 10 -loop 0 -gravity South -background white -splice 0x18 -annotate 0 'Z-Slice: %%[fx:t+1] of ' -layers Optimize -resize %dx%d %s %s" % (dim_x, dim_y, png_full, gif_full);
								os.system(command);
								command2 = "rm %s" % (png_full);
								os.system(command2);
								command3 = "rm %s %s" % (img_full, mrc_full);
								os.system(command3);
							else:
								command = "convert -delay 10 -loop 0 -gravity South -background white -splice 0x18 -annotate 0 'Z-Slice: %%[fx:t+1]' -layers Optimize %s %s" % (png_full, gif_full);
								os.system(command);
								command2 = "rm %s" % (png_full);
								os.system(command2);
								command3 = "rm %s %s" % (img_full, mrc_full);
								os.system(command3);
							print "Done!\n"
							
						except:
							print "\nRefinement Images could not be generated. Make sure i3 and imagemagick are in your $PATH. Make sure that pyami and scipy are in your $PYTHONPATH.\n"
						
						apDisplay.printMsg("Refinement Finished!\n")
				
				
				#=====================
				##RECONSTRUCTION##
				#=====================
				name=seriesname
				cpparam="cp %s %s/%s.param" % (self.params['recon_param_file'],tiltdir,name)
				os.system(cpparam)
				recon_param_full=tiltdir+'/'+name+'.param'
				
				#Edit param file to replace pathlist, cachedir, and outdir
				command1="grep -n 'pathlist' %s | awk '{print $1}' | sed 's/://'" % (recon_param_full)
				proc=subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True)
				(pathlistline, err) = proc.communicate()
				pathlistline=int(pathlistline)
				command2="grep -n 'cachedir' %s | awk '{print $1}' | sed 's/://'" % (recon_param_full)
				proc=subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True)
				(cachedirline, err) = proc.communicate()
				cachedirline=int(cachedirline)
				command3="grep -n 'outdir' %s | awk '{print $1}' | sed 's/://'" % (recon_param_full)
				proc=subprocess.Popen(command3, stdout=subprocess.PIPE, shell=True)
				(outdirline, err) = proc.communicate()
				outdirline=int(outdirline)
				command11="sed -i \'%ss|.*| pathlist: \"%s\"  (* AP path to raw directory *)|\' %s" % (pathlistline, raw_path, recon_param_full)
				os.system(command11)
				command22="sed -i \'%ss|.*| cachedir: \"%s\"  (* AP directory where cache files are stored *)|\' %s" % (cachedirline, newcachedir, recon_param_full)
				os.system(command22)
				command33="sed -i \'%ss|.*| outdir: \"%s\"  (* AP directory where other output files are stored *)|\' %s" % (outdirline, newoutdir, recon_param_full)
				os.system(command33)
				
				apDisplay.printMsg('Starting Protomo Reconstructon')
				
				# Create reconstruction
				recon_seriesparam=protomo.param(recon_param_full)
				del series
				series=protomo.series(recon_seriesparam)
				series.mapfile()
				
				# Convert to mrc
				img=seriesname+itt+'_bck.img';
				mrcf=seriesname+itt+'_bck.mrc';
				img_full=tiltdir+'/out/'+img;
				mrc_full=tiltdir+'/out/'+mrcf;
				os.system("i3cut -fmt mrc %s %s" % (img_full, mrc_full))
				
				# Normalize
				err=0;
				try:
					command="e2proc3d.py --process=normalize %s %s" % (mrc_full, mrc_full)
					os.system(command)
				except:
					apDisplay.printMsg("e2proc3d not found. Trying proc3d...")
					err=1	# Error thrown. Try proc3d
				if err:
					try:
						command="proc3d %s %s norm" % (mrc_full, mrc_full)
						os.system(command)
					except:
						apDisplay.printMsg("proc3d not found. Skipping normalization.")
				
				apDisplay.printMsg('Reconstruction Complete!')
				apDisplay.printMsg("Tilt Series #%s from %s has Finished Processing\n" % (tiltseriesnumber, self.params['sessionname']))
				
			except:
				apDisplay.printMsg("Alignment failed. Skipping Tilt Series #%s...\n" % (tiltseriesnumber))
		
#=====================
#=====================
if __name__ == '__main__':
	protomo2batch = ProTomo2Batch()
	protomo2batch.start()
	protomo2batch.close()
	protomo2batch_log=cwd+'/'+'protomo2batch.log'
	cleanup="mv %s %s; mv %s %s; mv %s %s; mv %s %s;" % (protomo2batch_log, wd, self.params['coarse_param_file'], wd, self.params['refine_param_file'], wd, self.params['recon_param_file'], wd)
	os.system(cleanup)

