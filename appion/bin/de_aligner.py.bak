#!/usr/bin/env python

"""
wrapper for de alignment python script
"""

import os
from appionlib import appionScript
from appionlib import apDisplay
from appionlib import apStack
from appionlib import apBoxer
from appionlib import apDDprocess
from pyami import mrc, numpil
import deProcessFrames
import subprocess
import glob
import sys
import shutil

#=====================
#=====================
###Appion part
class ExampleScript(appionScript.AppionScript):
	#=====================
	def setupParserOptions(self):
		configuration_options = deProcessFrames.ConfigurationOptions( )
		options_list = configuration_options.get_options_list( )
		sections = options_list.keys( )
		for section in sections :
			for option in options_list[ section ] :
				if section == 'gainreference' or section == 'darkreference':
					if option['name'] in ['filename', 'framecount']:
						continue
				if section == 'boxes':
					if option['name'] in ['fromlist','fromonefile','fromfiles','boxsize','minimum']:
						continue
				if section == 'input' and option['name']=='framecount':
					continue
				if section == 'radiationdamage':
#					if option['name'] in ['apix', 'voltage']:
					if option['name'] in ['voltage']:
						continue
#				if section == 'alignment' and option['name']=='correct':
#					continue
				if option[ 'type' ] == str :
					metavar = "STR"
				elif option[ 'type' ] == int :
					metavar = "INT"
				elif option[ 'type' ] == float :
					metavar = "FLOAT"
				self.parser.add_option( "--%s_%s" % ( section, option[ 'name' ] ), type = option[ 'type' ], metavar = metavar, help = option[ 'help' ], default=option['default'] )

		self.parser.add_option("--stackid", dest="stackid", type="int", help="Stack on which to do frame alignment. ", metavar="INT")
		self.parser.add_option('--dryrun', dest='dryrun', action='store_true', default=False, help="Just show the command, but do not execute")
		self.parser.add_option("--output_rotation", dest="output_rotation", type='int', default=0, help="Rotate output particles by the specified angle", metavar="INT")
		self.parser.add_option("--override_camera", dest="override_camera", default=None, help="Specify camera type")
		self.parser.add_option("--show_DE_command", dest="show_DE_command", action='store_true',default=False, help="Show the command line options for the DE script")

	#=====================
	def checkConflicts(self):
	
		pass


	#=====================
	def setRunDir(self):
		pass
		
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
	def start(self):
		self.params['output_fileformat'] = 'mrc'
		newstackname='framealigned.hed'
		stackdata=apStack.getStackParticlesFromId(self.params['stackid'])
		stackrundata=apStack.getOnlyStackData(self.params['stackid'])
		apix=stackrundata['pixelsize']*1e10
		kev=stackdata[0]['particle']['image']['scope']['high tension']/1000
		origstackpath=os.path.join(stackrundata['path']['path'],stackrundata['name'])
		boxsize=stackdata[0]['stackRun']['stackParams']['boxSize']
		binning=stackdata[0]['stackRun']['stackParams']['bin']	
		
		#determine camera type
		cameratype=stackdata[0]['particle']['image']['camera']['ccdcamera']['name']
		if self.params['override_camera'] is not None:
			cameratype=self.params['override_camera']
		
		#create sorted boxfiles
		imagedict={}
		masterlist=[]
		for particle in stackdata:
			parentimage=particle['particle']['image']['filename']
			if parentimage in imagedict.keys():
				imagedict[parentimage].append(particle['particle'])
			else:
				imagedict[parentimage]=[]
				imagedict[parentimage].append(particle['particle'])
			index=len(imagedict[parentimage])-1
			masterlist.append({'particle':particle,'key':parentimage,'index':index})
		#print masterlist
		
		for key in imagedict:
			particlelst=imagedict[key]
			parentimage=key
			framespath=particlelst[0]['image']['session']['frame path']
			
			print cameratype
			if 'Gatan' in cameratype:
				#prepare frames
				print framespath
				
				#prepare frame directory
				framespathname=os.path.join(self.params['rundir'],parentimage+'.frames')
				if os.path.exists(framespathname):
					pass
				else:
					os.mkdir(framespathname)
				print framespathname
				
				mrcframestackname=parentimage+'.frames.mrc'
				
				print mrcframestackname
				
				nframes=particlelst[0]['image']['camera']['nframes']
				
				print "Extracting frames for", mrcframestackname
				for n in range(nframes):
					a=mrc.read(os.path.join(framespath,mrcframestackname),n)
					numpil.write(a,imfile=os.path.join(framespathname,'RawImage_%d.tif' % (n)), format='tiff')
				
			elif 'DE' in cameratype:
				framespathname=os.path.join(framespath,parentimage+'.frames')
			
			print os.getcwd()
			print framespathname
			#generate DE script call
			if os.path.exists(framespathname):
				print "found frames for", parentimage

				nframes=particlelst[0]['image']['camera']['nframes']
				boxname=parentimage + '.box'
				boxpath=os.path.join(framespathname,boxname)
				shiftdata={'scale':1,'shiftx':0,'shifty':0}

				#flatfield references
				brightrefpath=particlelst[0]['image']['bright']['session']['image path']
				brightrefname=particlelst[0]['image']['bright']['filename']
				brightnframes=particlelst[0]['image']['bright']['camera']['nframes']
				darkrefpath=particlelst[0]['image']['dark']['session']['image path']
				darkrefname=particlelst[0]['image']['dark']['filename']
				darknframes=particlelst[0]['image']['dark']['camera']['nframes']
				brightref=os.path.join(brightrefpath,brightrefname+'.mrc')
				darkref=os.path.join(darkrefpath,darkrefname+'.mrc')
				print brightref
				print darkref			
				apBoxer.processParticleData(particle['particle']['image'],boxsize,particlelst,shiftdata,boxpath)
				print framespathname			

				#set appion specific options
				self.params['gainreference_filename']=brightref
				self.params['gainreference_framecount']=brightnframes
				self.params['darkreference_filename']=darkref
				self.params['darkreference_framecount']=darknframes
				self.params['input_framecount']=nframes
				self.params['boxes_fromfiles']=1
				#self.params['run_verbosity']=3
				self.params['output_invert']=0
				#self.params['radiationdamage_apix=']=apix
				self.params['radiationdamage_voltage']=kev
				#self.params['boxes_boxsize']=boxsize

				outpath=os.path.join(self.params['rundir'],key)
				if os.path.exists(outpath):
					shutil.rmtree(outpath)
				os.mkdir(outpath)
				
				command=['deProcessFrames.py']
				keys=self.params.keys()
				keys.sort()
				for key in keys:
					param=self.params[key]
					#print key, param, type(param)
					if param == None or param=='':
						pass
					else:
						option='--%s=%s' % (key,param)
						command.append(option)
				command.append(outpath)
				command.append(framespathname)
				print command
				if self.params['dryrun'] is False:
					subprocess.call(command)
					
		
		#recreate particle stack
		for n,particledict in enumerate(masterlist):
			parentimage=particledict['key']
			correctedpath=os.path.join(self.params['rundir'],parentimage)
			print correctedpath
			if os.path.exists(correctedpath):
			
				correctedparticle=glob.glob(os.path.join(correctedpath,('%s.*.region_%03d.*' % (parentimage,particledict['index']))))
				print os.path.join(correctedpath,('%s.*.region_%03d.*' % (parentimage,particledict['index'])))
				print correctedparticle
				#sys.exit()
				command=['proc2d',correctedparticle[0], newstackname]
				if self.params['output_rotation'] !=0:
					command.append('rot=%d' % self.params['output_rotation'])
				
				if self.params['show_DE_command'] is True:
					print command
				subprocess.call(command)
			else:
				print "did not find frames for ", parentimage
				command=['proc2d', origstackpath, newstackname,('first=%d' % n), ('last=%d' % n)]
				print command
				if self.params['dryrun'] is False:
					subprocess.call(command)
				
		#upload stack
		
		#make keep file
		self.params['keepfile']='keepfile.txt'
		f=open(self.params['keepfile'],'w')
		for n in range(len(masterlist)):
			f.write('%d\n' % (n))
		f.close()
		
		apStack.commitSubStack(self.params, newname=newstackname)
		apStack.averageStack(stack=newstackname)
		
		print "Done!!!!"
				
		
			
		



#=====================
#=====================
if __name__ == '__main__':
	examplescript = ExampleScript()
	examplescript.start()
	examplescript.close()

