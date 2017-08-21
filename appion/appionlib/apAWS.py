#!/usr/bin/env python
import glob
import time
import stat
import math
import linecache
import os
import sys
import subprocess
from fabric.operations import run, put
from fabric.api import env,run,hide,settings
from fabric.context_managers import shell_env
from fabric.operations import put
import shutil
import datetime

#==========================
def s3_to_ebs(IP,keypair,bucketname,dironebs,rclonepath,keyid,secretid,region,numfilesAtATime):
	#Copy rclone onto instance
	cmd='scp -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s %s ubuntu@%s:~/'%(keypair,rclonepath,IP)
	subprocess.Popen(cmd,shell=True).wait()

	#Write rclone config file
	homedir='/home/ubuntu/'
	rclonename='ebss3'
	if os.path.exists('.rclone.conf'):
		os.remove('.rclone.conf')
	r1=open('.rclone.conf','w')
        r1.write('[rclonename]\n')
        r1.write('type = s3\n')
        r1.write('env_auth = false\n')
        r1.write('access_key_id = %s\n' %(keyid))
        r1.write('secret_access_key = %s\n' %(secretid))
        r1.write('region = %s\n' %(region))
        r1.write('endpoint = \n')

	if region == 'us-east-1':
	
        	r1.write('location_constraint = \n')
	else:
        	r1.write('location_constraint = %s\n' %(region))
        r1.write('acl = authenticated-read\n')
        r1.write('server_side_encryption = \n')
        r1.write('storage_class = STANDARD\n')
        r1.close()

	cmd='scp -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s .rclone.conf ubuntu@%s:~/.rclone.conf' %(keypair,IP)
	subprocess.Popen(cmd,shell=True).wait()

	#Copy data down
	env.host_string='ubuntu@%s' %(IP)
        env.key_filename = '%s' %(keypair)
	rcloneexe='rclone'
	exec_remote_cmd('%s/%s copy rclonename:%s %s --max-size 1G --quiet --transfers %i' %(homedir,rcloneexe,bucketname.split('s3://')[-1],dironebs,numfilesAtATime))

	fileonly=dironebs.split('/')[-1]
	if dironebs.split('.')[-1] == 'mrcs' or dironebs.split('.')[-1] == 'spi':
		exec_remote_cmd('mv %s/%s tmp.mrcs' %(dironebs,fileonly))
		exec_remote_cmd('rm -rf /%s/' %(dironebs))
		#exec_remote_cmd('mv tmp.mrcs /data/%s' %(fileonly))
		exec_remote_cmd('mv tmp.mrcs /%s' %(fileonly))

#=========================
def rclone_to_s3(indir,numfiles,region,keyid,secretid,rclonename,bucketname,awspath,project,rclonelist,outdir):
	if subprocess.Popen('uname',shell=True, stdout=subprocess.PIPE).stdout.read().strip() == 'Linux':
		rclonepath='%s/rclone' %(awspath)
	if subprocess.Popen('uname',shell=True, stdout=subprocess.PIPE).stdout.read().strip() == 'Darwin':
		rclonepath='%s/rclone_mac'%(awspath)
	#Write .rclone.conf
	if os.path.exists('%s/.rclone.conf' %(outdir)):
		os.remove('%s/.rclone.conf' %(outdir))
        print ('Region = %s\n'%(region))
        print ('[rclonename]\n')
        print ('type = s3\n')
        print ('env_auth = false\n')
        print ('access_key_id = %s\n' %(keyid))
	print ('secret_access_key = %s\n' %(secretid[:5]+'****************************************'))
        print ('region = %s\n' %(region))

	r1=open('%s/.rclone.conf' %(outdir),'w')
	r1.write('[rclonename]\n')
	r1.write('type = s3\n')
	r1.write('env_auth = false\n')
	r1.write('access_key_id = %s\n' %(keyid))
	r1.write('secret_access_key = %s\n' %(secretid))
	r1.write('region = %s\n' %(region))

	if region == 'us-east-1':
		#r1.write('endpoint = s3.amazonaws.com\n')
		r1.write('endpoint = \n')
	else:
		r1.write('endpoint = \n')

	if region == 'us-east-1' or region == 'us-east-1a' or region == 'us-east-1b':
		r1.write('location_constraint = \n')
		print('location_constraint = \n')
	else:
		r1.write('location_constraint = %s\n' %(region))
		print('location_constraint = %s\n' %(region))
	r1.write('acl = authenticated-read\n')
	r1.write('server_side_encryption = \n')
	r1.write('storage_class = STANDARD\n')
	r1.close()

	#Create bucket on aws:
	#if len(project) == 0:
	#	cmd='aws s3 mb s3://%s --region %s > s3.log' %(bucketname,region)
	#	subprocess.Popen(cmd,shell=True).wait()
	#	os.remove('s3.log')
	if len(rclonelist) == 0:
		cmd='%s copy %s rclonename:%s --quiet  --config %s/.rclone.conf --transfers %i > rclone.log' %(rclonepath,indir,bucketname,outdir,math.ceil(numfiles))
		subprocess.Popen(cmd,shell=True).wait()
	if len(rclonelist) > 0:
		cmd='%s copy %s rclonename:%s --quiet --config %s/.rclone.conf --transfers %i --include-from %s > rclone.log' %(rclonepath,indir,bucketname,outdir,math.ceil(numfiles),rclonelist)
		subprocess.Popen(cmd,shell=True).wait()
	os.remove('rclone.log')
	return 's3://%s' %(bucketname)

#====================
def exec_remote_cmd(cmd):
    from fabric.operations import run, put
    from fabric.api import hide,settings
    with hide('output','running','warnings'):
	    with settings(warn_only=True):
    		return run(cmd)

#==============================
def writeToLog(msg,outfile):
	cmd='echo '' >> %s' %(outfile)
	subprocess.Popen(cmd,shell=True).wait()

	cmd='echo "%s"  >> %s' %(msg,outfile)
        subprocess.Popen(cmd,shell=True).wait()

#==============================
def getCMDrefine(rlncmd):
	#o1=open(f1,'r')
	#for line in o1:
	#	if len(line.split('=')) > 0:
	#		if line.split('=')[0] == 'relioncmd':
	#			rlncmd=line.split('=')[1]
	#o1.close()

	#Get particle input directory and if there is a reference model
	outbasenanme=''
	continuecounter=-1
	indircounter=-1
	refcounter=-1
	outcounter=-1
	autoref=-1
	counter=1
	itercounter=0
	numiters=0
	mask=''
	maskcounter=-1
	ref='None'
	stack=False
	partstarname=''
	partdir=''
	contLocation=''
	particlediameter=-999
	partdiamcounter=-1
	for l in rlncmd.split():
		if l == '--i':
			indircounter=counter
		if l == '--ref':
			refcounter=counter
		if l == '--o':
			outcounter=counter
		if l == '--auto_refine':
			autoref=counter
		if l == '--iter':
			itercounter=counter
		if l == '--solvent_mask':
			maskcounter=counter
		if l == '--continue':
			continuecounter=counter
		if l == '--particle_diameter':
			partdiamcounter=counter
		counter=counter+1

	if indircounter > 0:
		partstarname=rlncmd.split()[indircounter].split('/')[-1]
		if '.star' not in partstarname:
			stack=True
		partdir=rlncmd.split()[indircounter].split('/')
		del partdir[-1]
		partdir='/'.join(partdir)
	if partdiamcounter > 0:
		diamlength=len(repr(rlncmd.split()[partdiamcounter].strip()))
		if diamlength>10: 
			particlediameter=float(repr(rlncmd.split()[partdiamcounter].strip())[1:-9])	
		if diamlength<=10:
			particlediameter=float(rlncmd.split()[partdiamcounter].strip())
		#Since appions command comes with this formatting: 234.0\xc2\xa0
	outbasename=rlncmd.split()[outcounter]
	outdir=rlncmd.split()[outcounter].split('/')
	del outdir[-1]
	outdir='/'.join(outdir)
	if itercounter > 0:
		numiterslength=len(repr(rlncmd.split()[itercounter].strip()))
		if numiterslength>8:
			numiters=int(repr(rlncmd.split()[itercounter].strip())[1:-9])
		if numiterslength<=8:
			numiters=int(rlncmd.split()[itercounter].strip())
	if refcounter > 0:
		ref=rlncmd.split()[refcounter]
	if maskcounter > 0:
		mask=rlncmd.split()[maskcounter]
	if continuecounter > 0:
		contLocation=rlncmd.split()[continuecounter]
	return rlncmd,partdir,ref,outdir,autoref,numiters,partstarname,mask,stack,contLocation,outbasename,particlediameter

#==============================
def checkPartLocation(instarfile,indir):

	otherPartDir=''
	otherPartRclone=[]
	error=''

	o44=open(instarfile,'r')
	for line in o44:
		if len(line) > 0:
			if 'data' not in line:
				if '_rln' in line:
					if line.split()[0] == '_rlnImageName':
						imagecolnum=int(line.split('#')[-1])
					if line.split()[0] == '_rlnMicrographName':
						microcolnum=int(line.split('#')[-1])
	o44.close()

	if microcolnum == 0:
		error='Could not find _rlnImageName in starfile %s' %(instarfile)
	if microcolnum != 0:
		o44=open(instarfile,'r')
		for line in o44:
			if len(line.split()) > 0:
				if 'data' not in line:
					if '_rln' not in line:
						if 'loop_' not in line:
							part=line.split()[imagecolnum-1].split('@')[-1]
							starfile=''
							if not os.path.exists(part):
								error='Error: particle stack %s does not exist.' %(part)
							if os.path.exists('%s_extract.star' %(part[:-5])):
								starfile='%s_extract.star' %(part[:-5])
							InIt=False
							if indir in part:
								InIt=True
							if InIt is False:
								if len(part.split('/')) == 5:
									otherPartDir=part.split('/')[0]+'/'+part.split('/')[1]+'/'
									tmpline=part.split('/')[2]+'/'+part.split('/')[3]+'/'+part.split('/')[4]
									tmpline=tmpline.replace('//','/')
									otherPartRclone.append(tmpline)
								if len(part.split('/')) == 4:
									otherPartDir=part.split('/')[0]+'/'+part.split('/')[1]+'/'
									otherPartRclone.append(part.split('/')[2]+'/'+part.split('/')[3])
								if len(part.split('/')) == 3:
									otherPartDir=part.split('/')[0]+'/'+part.split('/')[1]+'/'
                                                                        otherPartRclone.append(part.split('/')[2])
							'''
							checkdir=part.split(micro)[0]
							if checkdir[-1] == '/':
								checkdir=checkdir[:-1]
							if checkdir != indir:
								otherPartDir=checkdir
								if micro not in otherPartRclone:
									partfilename=part.split('/')[-1]
									micdironly=micro.split('/')
									del micdironly[-1]
									micdironly='/'.join(micdironly)
									otherPartRclone.append('%s/%s' %(micdironly,partfilename))
									if len(starfile) > 0:
										instarfile='%s/%s_extract.star' %(micdironly,partfilename[:-5])
										if instarfile not in otherPartRclone:
											otherPartRclone.append(instarfile)
							'''
		o44.close()
	return otherPartDir,otherPartRclone,error

#==============================
def parseCMDrefine(relioncmd):

	l=relioncmd.split()
	newcmd=[]
	tot=len(l)
	counter=0
	selectflag=''
	while counter < tot:
		if 'mpirun' in l[counter]: 
			counter=counter+1
			continue
		if l[counter] == '-np': 
			counter=counter+2
			continue
		if l[counter] == '--preread_images':
			counter=counter+1
			continue
		if l[counter] == '--pool':
			counter=counter+2
			continue
		if l[counter] == '`which':
			counter=counter+1
			continue
		if l[counter] == 'relion_refine_mpi`':
			counter=counter+1
			continue
		if l[counter] == 'relion_refine`':
                        counter=counter+1
                        continue
		if l[counter] == 'relion_refine':
			counter=counter+1
			continue
		if l[counter] == 'relion_refine_mpi': 
			counter=counter+1
			continue
		if l[counter] == '--gpu':
			if counter+1 < tot:
				if l[counter+1][0] == '-':
					counter=counter+1
				else:
					counter=counter+2
			else:
				counter=counter+1
			continue
		if l[counter] == '--j':
			counter=counter+2
			continue
		if l[counter] == '--i':
			if l[counter+1].split('/')[0] == 'Select':
				selectflag=l[counter+1]
		newcmd.append(l[counter])
 		counter=counter+1
	return ' '.join(newcmd),selectflag

#==============================
def getSelectParticleDir(selectdir):

	r1=open(selectdir,'r')
	imagenumcol=3
	for line in r1:
		if len(line) < 40:
			if len(line.split()) > 0:
				if line.split()[0] == '_rlnImageName':
					imagenumcol=int(line.split()[1].split('#')[-1])-1
	r1.close()
	r1=open(selectdir,'r')
	skip=0
	for line in r1:
		if len(line) < 40:
			continue
		if len(line.split()) > 3:
			if skip == 0:
				micname=line.split()[imagenumcol]
				skype=1
	r1.close()
	jobname=micname.split('@')[-1].split('/')[1]

	return 'Extract/%s' %(jobname)

#==============================
def relion_refine_mpi(in_cmd,numParticles,partxdim,instancetype=''):

	assert type(instancetype) == str
	assert type(numParticles) == int
	assert type(partxdim) == int

	print("Instance type is: ",instancetype)
	#Set entry
	otherPartDir=''
	otherPartRclone=''
	error=''

	#Get relion command and input options
	relioncmd,particledir,initmodel,outdir,autoref,numiters,partstarname,mask,stack,continueRun,outbasename,diameter=getCMDrefine(in_cmd)

	#Make output directory
	if not os.path.exists(outdir):
		os.makedirs(outdir)
	cmd='touch %s/note.txt' %(outdir)
	subprocess.Popen(cmd,shell=True).wait()

	if os.path.exists('%s/run.err' %(outdir)):
		os.remove('%s/run.err' %(outdir))
		cmd='touch %s/run.err' %(outdir)
		subprocess.Popen(cmd,shell=True).wait()

	if len(continueRun) > 0:
		particledir=continueRun.split('/')
		del particledir[-1]
		particledir='/'.join(particledir)
		partstarname='%s_data.star' %(continueRun.split('/')[-1][:-15])
		for line in open(continueRun,'r'):
			if len(line) > 4:
				if line.split()[0] == '_rlnCurrentIteration':
					iterationNumOpt=int(line.split()[1].strip())
			writeToLog('Error: Number of iterations requested %i is less than / equal to current iteration of data (%i). Exiting' %(numiters,iterationNumOpt),'%s/run.err' %(outdir))
			sys.exit()

	if len(particledir) == 0:
		particledir=partstarname

	#Get number of particles to decide how big of a machine to spin up
	if stack is False:
		if len(particledir) == 0:
			starfilename=particledir
			numParticles=len(open(particledir,'r').readlines())
		if len(particledir) > 0:
			starfilename='%s/%s' %(particledir,partstarname)
			numParticles=len(open('%s/%s' %(particledir,partstarname),'r').readlines())
		magcheck=False
		pixcheck=False
		ctfcheck=False
		partcolnum=-1
		detectorcolnum=-1
		magcolnum=-1
		exampleline=''
		for line in open(starfilename,'r'):
			if len(line.split()) > 0:
				if line.split()[0] == '_rlnMagnification':
					magcheck=True
					magcolnum=int(line.split()[1].split('#')[-1])
				if line.split()[0] == '_rlnDetectorPixelSize':
					pixcheck=True
					detectorcolnum=int(line.split()[1].split('#')[-1])
				if line.split()[0] == '_rlnDefocusU':
					ctfcheck=True
				if line.split()[0] == '_rlnImageName':
					partcolnum=int(line.split()[1].split('#')[-1])
				exampleline=line
		ctfin=False
		apixin=False
		rlncounter=1
		while rlncounter <= len(relioncmd.split()):
			if relioncmd.split()[rlncounter-1] == '--ctf':
				ctfin=True
			if relioncmd.split()[rlncounter-1] == '--angpix':
				apixin=True
				apixVal=float(relioncmd.split()[rlncounter])
			rlncounter=rlncounter+1
		if partcolnum < 0:
			writeToLog('Error: could not find _rlnImageName in .star file. Exiting','%s/run.err' %(outdir))
			sys.exit()
		if apixin is False:
			if magcheck is False:
				writeToLog('Error: No magnification information found in .star file. Exiting', '%s/run.err' %(outdir))
				sys.exit()
		if apixin is False:
                        if pixcheck is False:
                                writeToLog('Error: No detector pixel size information found in .star file. Exiting', '%s/run.err' %(outdir))
                                sys.exit()
		if ctfin is True:
			if ctfcheck is False:
				writeToLog('Error: no defocus information found in .star file. Exiting', '%s/run.err' %(outdir))
				sys.exit()

		#Get xdims
		if len(exampleline) == 0:
			writeToLog('Error: no inputline found','%s/run.err' %(outdir))
			sys.exit()
		examplePart=exampleline.split()[partcolnum-1]
		if os.path.exists('%s/handler.txt' %(outdir)):
                        os.remove('%s/handler.txt' %(outdir))
                cmd='relion_image_handler --i %s --stats > %s/handler.txt' %(examplePart,outdir)
		subprocess.Popen(cmd,shell=True).wait()
		partxdim=int(linecache.getline('%s/handler.txt' %(outdir),1).split('=')[1].split('x')[0].strip())

		if apixin is False:
			if len(exampleline.split()) < detectorcolnum-1:
				writeToLog('Error: particle line is missing columns: %s' %(exampleline), '%s/run.err' %(outdir))
				sys.exit()
			example_detector=float(exampleline.split()[detectorcolnum-1])
			example_mag=float(exampleline.split()[magcolnum-1])
			apixVal=(example_detector/example_mag)*10000
	if stack is True:
		# Appion uses .hed files, not mrcs
		#if partstarname.split('.')[-1] != 'mrcs':
		#	writeToLog('Error: input stack must have .mrcs extension. Exiting','%s/run.err' %(outdir))
		#	sys.exit()
		#if os.path.exists('%s/handler.txt' %(outdir)):
		#	os.remove('%s/handler.txt' %(outdir))
		#cmd='relion_image_handler --i %s --stats > %s/handler.txt' %(partstarname,outdir)
		#subprocess.Popen(cmd,shell=True).wait()
		#numParticles=int(linecache.getline('%s/handler.txt' %(outdir),1).split('=')[1].split('x')[3].split(';')[0])
		#partxdim=int(linecache.getline('%s/handler.txt' %(outdir),1).split('=')[1].split('x')[0].strip())
		
		print("numParticles is",numParticles)
		print("partxdim calculated is",partxdim)
		ctf=False
		angpix=False
		rlncounter=1
                while rlncounter <= len(relioncmd.split()):
                        if relioncmd.split()[rlncounter-1] == '--ctf':
                                ctf=True
                        if relioncmd.split()[rlncounter-1] == '--angpix':
                                angpix=True
                                apixVal=float(relioncmd.split()[rlncounter])
                        rlncounter=rlncounter+1
		if ctf is True:
			writeToLog('Error: CTF correction was selected for a particle stack without a star file (which means that Relion cannot do CTF correction). Exiting','%s/run.err' %(outdir))
			sys.exit()
		if angpix is False:
			writeToLog('Error: Pixel size required. Please include --angpix into "Additional arguments" and resubmit','%s/run.err' %(outdir))
			sys.exit()
	if initmodel != 'None':
		if os.path.exists('handler2.txt'):
			os.remove('handler2.txt')
		time.sleep(2)
		cmd='relion_image_handler --i %s --stats > handler2.txt' %(initmodel)
		subprocess.Popen(cmd,shell=True).wait()
		time.sleep(2)
		modxdim=int(linecache.getline('handler2.txt',1).split('=')[1].split('x')[0].strip())
		os.remove('handler2.txt')
		if modxdim != partxdim:
			writeToLog('Error: 3D model and particles do not have the same dimensions. Exiting','%s/run.err' %(outdir))
			sys.exit()

	#Check that diameter specified fits within box
	if float(diameter) >= float(apixVal)*float(partxdim)-1:
		writeToLog('Error: Diameter specified (%.0f Angstroms) is greater than box size (%.0f Angstroms). Exiting' %(diameter,apixVal*partxdim),'%s/run.err' %(outdir))
		writeToLog('Error: Diameter specified (%.0f Angstroms) is greater than box size (%.0f Angstroms). Exiting' %(diameter,apixVal*partxdim),'%s/run.out' %(outdir))
		sys.exit()

	#Parse relion command to only include input options, removing any mention of 'gpu' or j threads in command
	relioncmd,select=parseCMDrefine(relioncmd)
	#Check where input particles are located
	if stack is False:
		otherPartDir,otherPartRclone,error=checkPartLocation(starfilename,particledir)
	if len(error) > 0:
		writeToLog(error,'%s/run.err' %(outdir))
                sys.exit()
	if len(otherPartRclone) > 0:
		if os.path.exists('rclonetmplist1298.txt'):
			os.remove('rclonetmplist1298.txt')
		o89=open('rclonetmplist1298.txt','w')
		for entry in otherPartRclone:
			o89.write('%s\n' %(entry.strip()))
		o89.close()
		otherPartRclone='rclonetmplist1298.txt'
	#Choose instance type
	print("Selecting instance type...")
	if instancetype == '':
		print("No instance type specified. Selecting instance based on number of particles")
		if initmodel == 'None': #2D classification
			if numParticles < 20000:
				instance='p2.xlarge'
			if numParticles >= 20000 and numParticles <= 100000:
				instance='p2.8xlarge'
			if numParticles > 100000:
				instance='p2.16xlarge'
		if initmodel != 'None': #3D classification or refinement
			if autoref == -1: #3D classification
				if numParticles <25000:
					instance='p2.xlarge'
				if numParticles >=25000:
					instance='p2.8xlarge'
			if autoref != -1: #3D refinement
				instance='p2.8xlarge'
			instance='p2.xlarge'
	else:
		instance = instancetype
	print("Using %s instance type."%instancetype)

	#Get AWS region from aws_init.sh environment variable
	awsregion=subprocess.Popen('echo $AWS_DEFAULT_REGION', shell=True, stdout=subprocess.PIPE).stdout.read().split()[0]
	if len(awsregion) == 0:
                writeToLog('Error: Could not find default region specified as $AWS_DEFAULT_REGION. Please set this environmental variable and try again.','%s/run.err' %(outdir))
                sys.exit()

	writeToLog('Booting up virtual machine %s on AWS in availability zone %sa' %(instance,awsregion), '%s/run.out' %(outdir))

	#Get AWS ID
	AWS_ID=subprocess.Popen('echo $AWS_ACCOUNT_ID',shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	key_ID=subprocess.Popen('echo $AWS_ACCESS_KEY_ID',shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	secret_ID=subprocess.Popen('echo $AWS_SECRET_ACCESS_KEY',shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	teamname=subprocess.Popen('echo $RESEARCH_GROUP_NAME',shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	keypair=subprocess.Popen('echo $KEYPAIR_PATH',shell=True, stdout=subprocess.PIPE).stdout.read().strip()

	#Get AWS CLI directory location
	awsdir=subprocess.Popen('echo $AWS_CLI_DIR', shell=True, stdout=subprocess.PIPE).stdout.read().split()[0]
	if len(awsdir) == 0:
		print 'Error: Could not find AWS scripts directory specified as $AWS_CLI_DIR. Please set this environmental variable and try again.'
		sys.exit()

	#.aws_relion will Have: [particledir] [s3 bucket name] [ebs volume]
	ebs_exist=False
	s3_exist=False
	bucketname=''
	if os.path.exists('.aws_relion'):
                for line in open('.aws_relion','r'):
                        if line.split()[0] == particledir:
				bucketname=line.split()[1]
				ebsvolname=''
				#Check if it exists:
				if os.path.exists('%s/ebsout.log' %(outdir)):
					os.remove('%s/ebsout.log' %(outdir))
				cmd='aws ec2 describe-volumes | grep VolumeId > %s/ebsout.log' %(outdir)
 				subprocess.Popen(cmd,shell=True).wait()
				for line in open('%s/ebsout.log' %(outdir),'r'):
					if line.strip().split()[-1].split('"')[1] == ebsvolname:
						ebs_exist=True
						volID=ebsvolname
				os.remove('%s/ebsout.log' %(outdir))
				if os.path.exists('%s/s3out.log' %(outdir)):
                                        os.remove('%s/s3out.log' %(outdir))
                                cmd='aws s3 ls %s > %s/s3out.log' %(bucketname.split('s3://')[-1],outdir)
                                subprocess.Popen(cmd,shell=True).wait()
                                if len(open('%s/s3out.log' %(outdir),'r').readlines()) > 0:
                                        s3_exist=True
	keyname=keypair.split('/')[-1].split('.pem')[0]
        keyname=keyname.split('_')
        keyname='-'.join(keyname)
        outdirname=outdir.split('/')
        if len(outdirname[-1]) == 0:
                del outdirname[-1]
        outdirname='-'.join(outdirname)
        outdirname=outdirname.lower().strip()
        keyname=keyname.lower().strip()
        project=''
	project=project.strip()
	if s3_exist is False:
		if ebs_exist is True:
			ebs_exist=False
			cmd='aws ec2 delete-volume --volume-id %s' %(ebsvolname)
			subprocess.Popen(cmd,shell=True).wait()
	if len(otherPartDir) == 0:
		inputfilesize=subprocess.Popen('du %s' %(particledir), shell=True, stdout=subprocess.PIPE).stdout.read().split()[-2]
	if len(otherPartDir) > 0:
		inputfilesize=subprocess.Popen('du %s' %(otherPartDir), shell=True, stdout=subprocess.PIPE).stdout.read().split()[-2]
	sizeneeded='%.0f' %(math.ceil((float(inputfilesize)*4)/1000000))
        actualsize='%.0f' %(math.ceil((float(inputfilesize)/1000000)))
	#Upload data to S3
	if s3_exist is False:
		writeToLog('Started uploading %sGB to AWS on %s' %(actualsize,time.asctime(time.localtime(time.time()))),'%s/run.out' %(outdir))
		if len(project) == 0:
			bucketname='rln-aws-tmp-%s/%s/%0.f' %(teamname,keyname,time.time())
		if len(project) > 0:
			bucketname='rln-aws-%s-%s/%s/%s' %(teamname,keyname,project,outdirname)
		if subprocess.Popen('uname',shell=True, stdout=subprocess.PIPE).stdout.read().strip() == 'Linux':
                	numCPUs=int(subprocess.Popen('grep -c ^processor /proc/cpuinfo',shell=True, stdout=subprocess.PIPE).stdout.read().strip())
		if subprocess.Popen('uname',shell=True, stdout=subprocess.PIPE).stdout.read().strip() == 'Darwin':
	                numCPUs=int(subprocess.Popen('sysctl -n hw.ncpu',shell=True, stdout=subprocess.PIPE).stdout.read().strip())
		if len(otherPartRclone) == 0:
			bucketname=rclone_to_s3(particledir,numCPUs*2.4,awsregion,key_ID,secret_ID,bucketname,bucketname,awsdir,project,otherPartRclone,outdir)
		if len(otherPartRclone) > 0:
			bucketname=rclone_to_s3(otherPartDir,numCPUs*2.4,awsregion,key_ID,secret_ID,bucketname,bucketname,awsdir,project,otherPartRclone,outdir)
		writeToLog('Finished at %s' %(time.asctime(time.localtime(time.time()))),'%s/run.out' %(outdir))
	if ebs_exist is False:
		writeToLog('Creating data storage drive ...','%s/run.out' %(outdir))
        	#Create EBS volume
        	if os.path.exists('%s/awsebs.log' %(outdir)) :
                	os.remove('%s/awsebs.log' %(outdir))
        	cmd='%s/create_volume.py %i %sa "rln-aws-tmp-%s-%s"'%(awsdir,int(sizeneeded),awsregion,teamname,particledir)+'> %s/awsebs.log' %(outdir)
        	subprocess.Popen(cmd,shell=True).wait()

        	#Get volID from logfile
        	volID=linecache.getline('%s/awsebs.log' %(outdir),5).split('ID: ')[-1].split()[0]

	#Restore volume, returning with it volID for later steps
	writeToLog('Launching virtual machine %s...' %(instance),'%s/run.out' %(outdir))
	now=datetime.datetime.now()
	startday=now.day
	starthr=now.hour
	startmin=now.minute

	#Launch instance
	if os.path.exists('%s/awslog.log' %(outdir)):
		os.remove('%s/awslog.log' %(outdir))
	cmd='%s/launch_AWS_instance.py --instance=%s --availZone=%sa --volume=%s > %s/awslog.log' %(awsdir,instance,awsregion,volID,outdir)
	subprocess.Popen(cmd,shell=True).wait()
	#Get instance ID, keypair, and username:IP
	instanceID=subprocess.Popen('cat %s/awslog.log | grep ID' %(outdir), shell=True, stdout=subprocess.PIPE).stdout.read().split('ID:')[-1].strip()
	keypair=subprocess.Popen('cat %s/awslog.log | grep ssh' %(outdir), shell=True, stdout=subprocess.PIPE).stdout.read().split()[3].strip()
	userIP=subprocess.Popen('cat %s/awslog.log | grep ssh' %(outdir), shell=True, stdout=subprocess.PIPE).stdout.read().split('@')[-1].strip()

	#Create directories on AWS
	if instance == 'p2.xlarge':
                gpu='--gpu '
                j='--j 2 '
                mpi=2
                numfiles=8
		cost=0.9
        if instance == 'p2.8xlarge':
                gpu='--gpu '
                j='--j 3 '
                mpi=9
                numfiles=50
		cost=7.20
        if instance == 'p2.16xlarge':
                gpu='--gpu '
                j='--j 3 '
                mpi=17
                numfiles=90
		cost=14.40
	if instance == 't2.xlarge':
		gpu=' '
		j='--j 2'
		mpi=5
		numfiles=8
		cost=0.188
	if instance == 't2.2xlarge':
		gpu=' '
		j='--j 2'
		mpi=9
		numfiles=8
		cost=0.188
	
	env.host_string='ubuntu@%s' %(userIP)
        env.key_filename = '%s' %(keypair)
	if ebs_exist is False:
		writeToLog('Started transferring %sGB at %s' %(actualsize,time.asctime(time.localtime(time.time()))),'%s/run.out' %(outdir))
		dirlocation='/data'
		#if stack is False:
		#	for entry in particledir.split('/'):
		#		if len(entry.split('.star')) == 1:
		#			exec_remote_cmd('mkdir /%s/%s' %(dirlocation,entry))
		#			dirlocation=dirlocation+'/'+entry
		if len(otherPartDir) == 0:
			if stack is False:
				#s3_to_ebs(userIP,keypair,bucketname,'/data/%s/' %(particledir),'%s/rclone' %(awsdir),key_ID,secret_ID,awsregion,numfiles)
				s3_to_ebs(userIP,keypair,bucketname,'/%s/' %(particledir),'%s/rclone' %(awsdir),key_ID,secret_ID,awsregion,numfiles)
			if stack is True:
				#s3_to_ebs(userIP,keypair,bucketname,'/data/%s' %(particledir),'%s/rclone' %(awsdir),key_ID,secret_ID,awsregion,numfiles)
				s3_to_ebs(userIP,keypair,bucketname,'/%s' %(particledir),'%s/rclone' %(awsdir),key_ID,secret_ID,awsregion,numfiles)
		if len(otherPartDir) > 0:
			#s3_to_ebs(userIP,keypair,bucketname,'/data/%s/' %(otherPartDir),'%s/rclone' %(awsdir),key_ID,secret_ID,awsregion,numfiles)
			s3_to_ebs(userIP,keypair,bucketname,'/%s/' %(otherPartDir),'%s/rclone' %(awsdir),key_ID,secret_ID,awsregion,numfiles)
		writeToLog('Finished transfer at %s' %(time.asctime( time.localtime(time.time()) )),'%s/run.out' %(outdir))

	#Make output directories
	dirlocation='/data'
	outdirlist=outdir.split('/')
	#exec_remote_cmd('mkdir %s'%particledir)
	#exec_remote_cmd('echo'+particledir+' > /home/ubuntu/check.log')
	del outdirlist[-1]
        for entry in outdirlist:
        	exec_remote_cmd('mkdir /%s/%s' %(dirlocation,entry))
                dirlocation=dirlocation+'/'+entry
	cmd='rsync -avzu --rsync-path="rsync" --log-file="%s/rsync.log" -e "ssh -q -o StrictHostKeyChecking=no -i %s" %s ubuntu@%s:%s/ > %s/rsync.log' %(outdir,keypair,outdir,userIP,dirlocation,outdir)
    	subprocess.Popen(cmd,shell=True).wait()
	if len(otherPartDir) > 0:
		dirlocation='/data/'
		partdirlist=particledir.split('/')
		del partdirlist[-1]
		for entry in partdirlist:
			exec_remote_cmd('mkdir /%s/%s' %(dirlocation,entry))
			dirlocation=dirlocation+'/'+entry
		cmd='rsync --rsync-path="rsync" --log-file="%s/rsync.log" -avzu -e "ssh -q -o StrictHostKeyChecking=no -i %s" %s ubuntu@%s:%s/ > %s/rsync.log' %(outdir,keypair,particledir,userIP,dirlocation,outdir)
		subprocess.Popen(cmd,shell=True).wait()
	if initmodel != 'None':
		#cmd='rsync --rsync-path="rsync" --log-file="%s/rsync.log" -avzu -R -e "ssh -q -o StrictHostKeyChecking=no -i %s" %s ubuntu@%s:/data/ > %s/rsync.log' %(outdir,keypair,initmodel,userIP,outdir)
		cmd='rsync --rsync-path="rsync" --log-file="%s/rsync.log" -avzu -R -e "ssh -q -o StrictHostKeyChecking=no -i %s" %s ubuntu@%s:/ > %s/rsync.log' %(outdir,keypair,initmodel,userIP,outdir)
        	subprocess.Popen(cmd,shell=True).wait()
	if len(mask) > 0:
		#cmd='rsync --rsync-path="rsync" --log-file="%s/rsync.log" -avzu -R -e "ssh -q -o StrictHostKeyChecking=no -i %s" %s ubuntu@%s:/data/ > %s/rsync.log' %(outdir,keypair,mask,userIP,outdir)
                cmd='rsync --rsync-path="rsync" --log-file="%s/rsync.log" -avzu -R -e "ssh -q -o StrictHostKeyChecking=no -i %s" %s ubuntu@%s:/ > %s/rsync.log' %(outdir,keypair,mask,userIP,outdir)
                subprocess.Popen(cmd,shell=True).wait()

	relion_remote_cmd='mpirun -np %i /home/EM_Packages/relion2.0/build/bin/relion_refine_mpi %s %s %s' %(mpi,relioncmd,j,gpu)

	o2=open('run_aws.job','w')
	o2.write('#!/bin/bash\n')
	#o2.write('cd /data\n')
	o2.write('cd /gpfs\n')
	o2.write('%s\n' %(relion_remote_cmd))
	o2.close()
	st = os.stat('run_aws.job')
	os.chmod('run_aws.job', st.st_mode | stat.S_IEXEC)
	cmd='rsync --rsync-path="rsync" --log-file="%s/rsync.log" -avzu -e "ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s" run_aws.job ubuntu@%s:~/ > %s/rsync.log' %(outdir,keypair,userIP,outdir)
	subprocess.Popen(cmd,shell=True).wait()
	#cmd='ssh -q -n -f -i %s ubuntu@%s "export LD_LIBRARY_PATH=/home/EM_Packages/relion2.0/build/lib:$LD_LIBRARY_PATH && nohup ./run_aws.job > /data/%s/run.out 2> /data/%s/run.err < /dev/null &"' %(keypair,userIP,outdir,outdir)
	cmd='ssh -q -n -f -i %s ubuntu@%s "export LD_LIBRARY_PATH=/home/EM_Packages/relion2.0/build/lib:$LD_LIBRARY_PATH && nohup ./run_aws.job > /%s/run.out 2> /%s/run.err < /dev/null &"' %(keypair,userIP,outdir,outdir)
	subprocess.Popen(cmd,shell=True)

	writeToLog('Job submitted to the cloud...','%s/run.out' %(outdir))
	#cmd='scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i %s %s/run.out ubuntu@%s:/data/%s/ > %s/rsync.log' %(keypair,outdir,userIP,outdir,outdir)
	cmd='scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i %s %s/run.out ubuntu@%s:/%s/ > %s/rsync.log' %(keypair,outdir,userIP,outdir,outdir)
	subprocess.Popen(cmd,shell=True)
	isdone=0

	while isdone == 0:
		#cmd='rsync --rsync-path="rsync" --log-file="%s/rsync.log" -avzu -e "ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s" ubuntu@%s:/data/%s/ %s/ > %s/rsync.log' %(outdir,keypair,userIP,outdir,outdir,outdir)
		cmd='mkdir -p %s/%s; rsync --rsync-path="rsync" --log-file="%s/rsync.log" -avzu -e "ssh -q -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s" ubuntu@%s:/%s/ %s/ > %s/rsync.log' %(outdir,outbasename,outdir,keypair,userIP,outdir,outdir,outdir)
		subprocess.Popen(cmd,shell=True).wait()
		time.sleep(2)
		if autoref == -1:
			if os.path.exists('%s_it%03i_data.star' %(outbasename,int(numiters))):
				isdone=1
		if autoref != -1:
			if os.path.exists('%s_class001.mrc' %(outbasename)):
				isdone=1
		#Check if job was specified to be killed
		if isdone ==0:
 			isdone=check_and_kill_job('%s/note.txt' %(outdir),userIP,keypair)

		#Check if there are any errors
		if isdone == 0:
			if os.path.exists('%s/run.err' %(outdir)):
				if float(subprocess.Popen('cat %s/run.err | wc -l' %(outdir),shell=True, stdout=subprocess.PIPE).stdout.read().strip()) > 0:
					writeToLog('\nError detected in run.err. Shutting down instance.','%s/run.out' %(outdir))
					isdone=1

		time.sleep(10)
	time.sleep(30)

	writeToLog('Job finished!','%s/run.out' %(outdir))
	writeToLog('Shutting everything down ...','%s/run.out' %(outdir))
	cmd=subprocess.Popen('aws ec2 terminate-instances --instance-ids %s > %s/tmp4949585940.txt' %(instanceID,outdir),shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	isdone=0
	time.sleep(10)
	while isdone == 0:
		status=subprocess.Popen('aws ec2 describe-instances --instance-ids %s --query "Reservations[*].Instances[*].{State:State}" | grep Name'%(instanceID),shell=True, stdout=subprocess.PIPE).stdout.read().strip()
		if 'terminated' in status: 
			isdone=1
		time.sleep(10)

	volID=subprocess.Popen('aws ec2 delete-volume --volume-id %s' %(volID),shell=True, stdout=subprocess.PIPE).stdout.read().strip()
	now=datetime.datetime.now()
        finday=now.day
        finhr=now.hour
        finmin=now.minute
        if finday != startday:
                finhr=finhr+24
        deltaHr=finhr-starthr
        if finmin > startmin:
        	deltaHr=deltaHr+1
        if not os.path.exists('aws_relion_costs.txt'):
		cmd="echo 'Input                   Output               Cost ($)' >> aws_relion_costs.txt"
		subprocess.Popen(cmd,shell=True).wait()
		cmd="echo '-----------------------------------------------------------' >> aws_relion_costs.txt"
                subprocess.Popen(cmd,shell=True).wait()
	cmd='echo "%s      %s      %.02f  " >> aws_relion_costs.txt' %(particledir,outdir,float(deltaHr)*float(cost))
        subprocess.Popen(cmd,shell=True).wait()

	#Update .aws_relion
	if os.path.exists('.aws_relion_tmp'):
		os.remove('.aws_relion_tmp')
	if os.path.exists('.aws_relion'):
		shutil.move('.aws_relion','.aws_relion_tmp')
		tmpout=open('.aws_relion','w')
		for line in open('.aws_relion_tmp','r'):
			if line.split()[0] == particledir:
				continue
			tmpout.write(line)
		tmpout.close()
	        os.remove('.aws_relion_tmp')

	cmd='echo "%s     %s      %s" >> .aws_relion' %(particledir,bucketname,'')
	subprocess.Popen(cmd,shell=True).wait()

	#Cleanup
	if os.path.exists('%s/awslog.log' %(outdir)):
		os.remove('%s/awslog.log' %(outdir))
	if os.path.exists('%s/awsebs.log' %(outdir)):
		os.remove('%s/awsebs.log' %(outdir))
	if os.path.exists('run_aws.job'):
		os.remove('run_aws.job')
	if os.path.exists('rclonetmplist1298.txt'):
		os.remove('rclonetmplist1298.txt')
	if os.path.exists('%s/.rclone.conf' %(outdir)):
		os.remove('%s/.rclone.conf' %(outdir))
	if os.path.exists('runningProcs.txt'):
		os.remove('runningProcs.txt')

#==============================
def check_and_kill_job(note,IP,keypair):
	
	o9=open(note,'r')
	kill=0
	for line in o9:
		if len(line.split()) > 0:
			if line.split()[0] == 'Kill':
				kill=1
			if line.split()[0] == 'kill':
        	                kill=1
	if kill == 1:
		kill_job(keypair,IP)
	o9.close()

	return kill

#====================
def kill_job(keypair,IP):

	env.host_string='ubuntu@%s' %(IP)
        env.key_filename = '%s' %(keypair)
	exec_remote_cmd('ps aux | grep mpi > runningProcs.txt')

	cmd='scp -q -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i %s ubuntu@%s:~/runningProcs.txt .' %(keypair,IP)
	subprocess.Popen(cmd,shell=True).wait()

	pidlist=[]

	for proc in open('runningProcs.txt','r'):
		if 'refine_mpi' in proc:
			pidlist.append(proc.split()[1])

	for pid in pidlist:
		exec_remote_cmd('kill -9 %s' %(pid))

#==============================
if __name__ == "__main__":

	#Read relion command from appion
	in_cmd=sys.argv[1]

	#checkConflicts()

	relion_refine_mpi(in_cmd)
