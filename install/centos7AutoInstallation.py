
import os
import re
import sys
import shutil
import subprocess
import platform
import webbrowser
import stat
import time
import hashlib


class CentosInstallation(object):

	def setReleaseDependantValues(self):
		# need to change to branch when release
		self.gitCmd = "git clone http://emg.nysbc.org/git/myami " + self.gitMyamiDir
		# redhat release related values
		self.torqueLibPath = '/var/lib/torque/'

 		self.redhatMajorRelease = '7'
		# SHA-1 digest of a registration key provided by AMI. When we change the key that we give to
		# registered users, we need to update this value.
		self.regKeyHash = '4\xa3T\xf2KB\x0e\xd7\x1fk1\xfdb\xcd\x04\xdcH>\xcc\x8e'

	def checkDistro(self):

		flavfile = "/etc/redhat-release"
		if not os.path.exists(flavfile):		
			print "This is not CentOS. Exiting installation..."
			self.writeToLog("ERROR: not CentOS ---")
			return False

		f = open(flavfile, "r")
		flavor = f.readline().strip()
		f.close()

		if not flavor.startswith("CentOS"):
			print "This is not CentOS. Exiting installation..."
			self.writeToLog("ERROR: not CentOS ---")
			return False

		print "Current OS Information: " + flavor
		self.writeToLog("CentOS info: " + flavor)

		
	def  determineNumberOfCPUs(self):
		""" Number of virtual or physical CPUs on this system """

		# Python 2.6+
		try:
			import multiprocessing
			return multiprocessing.cpu_count()
		except (ImportError, NotImplementedError):
			pass

		# POSIX
		try:
			res = int(os.sysconf('SC_NPROCESSORS_ONLN'))

			if res > 0:
				return res
		except (AttributeError, ValueError):
			pass

	def checkRoot(self):

		uid = os.getuid()
		if uid != 0:
			print "You must run this program as root. Exiting installation..."
			self.writeToLog("ERROR: root access checked deny ---")
			return False

		print "\"root\" access checked success..."
		self.writeToLog("root access checked success")

	def removeLogFile(self):
		if os.path.isfile(self.logFilename):
			self.writeToLog("remove old log file")
			os.remove(self.logFilename)

	def disableSeLinux(self):
		self.runCommand("/usr/sbin/setenforce 0")
		seLinuxConfig = "/etc/selinux/config"
		seLinuxConfigBackup = "/etc/selinux/config.bck"

		if not os.path.exists(seLinuxConfig):
			print "SeLinux configure file does not exist..."
			self.writeToLog("ERROR: No SeLinux configure file ---")
		return False 

		# make a back up from original config file
		shutil.move(seLinuxConfig, seLinuxConfigBackup)

		inf = open(seLinuxConfigBackup, 'r')
		outf = open(seLinuxConfig, 'w')

		for line in inf:
			line = line.rstrip()
			if line.startswith('SELINUX=enforcing'):
				outf.write("SELINUX=disabled\n")
			elif line.startswith('SELINUX=permissive'):
				outf.write("SELINUX=disabled\n")
			else:
				outf.write(line + '\n')

		inf.close()
		outf.close()
		return True
	
	# if SeLinus is not disable, return false, otherwise good to go.
	def checkSeLinux(self):
		selinuxenabled = "/usr/sbin/selinuxenabled"
		if not os.path.exists(selinuxenabled): return True
		proc = subprocess.Popen(selinuxenabled)
		returnValue = proc.wait()

		
		if not returnValue:
			print("========================")
			print("ERROR: Please disable SELinux before running this auto installation. Visit http://emg.nysbc.org/redmine/projects/appion/wiki/Install_Appion_and_Leginon_using_the_auto-installation_tool .")
			print("Exiting installation...")
			print("========================")
			return False
		return True

	def setupFilePermission(self):
		# Set umask to 0 so that we can set mode to 0777 later
		originalUmask = os.umask(0)
		
		if not os.path.exists(self.imagesDir):
			self.writeToLog("create images folder - /myamiImages")
			os.makedirs(self.imagesDir, 0777)
		else:
			os.chmod(self.imagesDir, 0777)

		if not os.path.exists(os.path.join(self.imagesDir, "leginon")):
			os.makedirs(os.path.join(self.imagesDir, "leginon"), 0777)
		else:
			os.chmod(os.path.join(self.imagesDir, "leginon"), 0777)
				
		if not os.path.exists(os.path.join(self.imagesDir, "appion")):
			os.makedirs(os.path.join(self.imagesDir, "appion"), 0777)
		else:
			os.chmod(os.path.join(self.imagesDir, "appion"), 0777)
			
		umask = os.umask(originalUmask)


	def yumUpdate(self):
		print "Updating system files...."
		self.runCommand("rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-%s.noarch.rpm" % (self.redhatMajorRelease))

		self.runCommand("yum -y update yum*")

		self.yumInstall(['yum-fastestmirror.noarch', 'yum-utils.noarch'])

		self.runCommand("yum -y update")

		#self.runCommand("updatedb")
		self.writeToLog("yum update finished..")

	def runCommand(self, cmd):
		
		self.writeToLog("#===================================================")
		self.writeToLog("Run the following Command:")
		self.writeToLog("%s" % (cmd,))
		print cmd + '\n'
		print 'Please wait......(This may take a few minutes.)\n'

		proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdoutResult = proc.stdout.read()
		stderrResult = proc.stderr.read()
		print stdoutResult
		sys.stderr.write(stderrResult)
		returncode = proc.wait()
		if (stderrResult != ""):
			self.writeToLog("--- Run Command Error ---")
			self.writeToLog(stderrResult)
		self.writeToLog("#===================================================\n")
		return stdoutResult

	def yumInstall(self, packagelist):
		
		if not packagelist:
			return
	
		packagestr = ""
		for package in packagelist:
			packagestr += " " + package

		cmd = "yum -y install" + packagestr
		self.runCommand(cmd)
		#self.runCommand("updatedb")

	def openFirewallPort(self, port):
		
		# The following command does not seem to be working	
		#self.runCommand("/sbin/iptables --insert RH-Firewall-1-INPUT --proto tcp --dport %d --jump ACCEPT" % (port))
		# replacing with:
		self.runCommand("/sbin/iptables -I INPUT -p tcp --dport %d -j ACCEPT" % (port))		
		self.runCommand("/sbin/iptables-save > /etc/sysconfig/iptables")
		self.runCommand("service iptables restart")
		self.writeToLog("firewall port %d opened" % (port))

	def installPythonPackage(self, targzFileName, fileLocation, unpackDirName):
		os.chdir(self.currentDir)
		# download the tar file and unzip it
		command = "wget -c " + os.path.join(fileLocation, targzFileName)
		self.runCommand(command)

		if not os.path.exists( targzFileName ):
			command = "wget -c " + fileLocation
			self.runCommand(command)

		command = "tar -zxvf " + targzFileName
		self.runCommand(command)
		
		# install with python installer
		os.chdir(unpackDirName)
		command = "python setup.py install"
		self.runCommand(command)
		os.chdir(self.currentDir)

	def linkMpiRun(self):
		# mpirun is not automatically available for use
		filename = 'mpirun'
		command = 'which %s' % (filename)
		resultstring = self.runCommand(command)
		if filename in resultstring:
			self.writeToLog("mpirun already in path, nothing to do")
			return True
		# find the source in some bin directory and link it	
		command = 'locate '+filename
		resultstring = self.runCommand(command)
		if ( filename not in resultstring ):
			self.writeToLog("Failed to enable mpirun: link source not found")
			return False
		else:
			lines = resultstring.split('\n')
			binMpiPath = None
			for source in lines:
				if source.split(filename) <2:
					continue
				binMpiPath = source.split(filename)[0]
				if len(binMpiPath.split('bin')) > 1:
					break
			if binMpiPath:
				destination = '/usr/local/bin/%s' % filename
				if os.path.isfile(destination):
					self.writeToLog("Error in Linking: Existing mpirun in /usr/local/bin is a file")
					return False
				if os.path.islink(destination):
					os.remove(destination)
				command = 'ln -s %s %s' % (source,destination)
				self.runCommand(command)
				self.writeToLog("%s is linked to %s"%(destination,source))
				return True

	def processServerPackageEnable(self):
		self.linkMpiRun()

	def processServerExtraPythonPackageInstall(self):
		self.runCommand("yum install -y python-pip")
		self.runCommand("pip install joblib==0.10.3")		

	def setupWebServer(self):
		self.writeToLog("--- Start install Web Server")
		#myamiweb yum packages
		packagelist = ['php-pecl-ssh2','mod_ssl', 'fftw3-devel','git','python-imaging','python-devel','mod_python','scipy','httpd', 'libssh2-devel', 'php', 'php-mysql', 'phpMyAdmin.noarch', 'php-devel', 'php-gd', ]
		self.yumInstall(packagelist)
		self.runCommand("easy_install fs PyFFTW3")

		# Redux Server is on Web server for now.
		self.installReduxServer()

		self.editPhpIni()
		self.editApacheConfig()
		
		# PHP ssh2 is now available as a yum package and does not need to be compiled.
		#self.installPhpSsh2()
		self.installMyamiWeb()
		self.editMyamiWebConfig()
		
		self.runCommand("systemctl restart httpd")
		self.runCommand("systemctl enable httpd")
		self.openFirewallPort(80)
		return True

	def setupDBServer(self):
		self.writeToLog("--- Start install Database Server")
		self.mysqlYumInstall()
		# turn on auto mysql start
		
		# stop mysql server (if it's running)
		self.runCommand("systemctl enable mysqld")
		# start mysql server
		
		#https://stackoverflow.com/questions/33510184/change-mysql-root-password-on-centos7
		os.system('systemctl set-environment MYSQLD_OPTS="--skip-grant-tables"')
		os.system("systemctl start mysqld")
		mysql_is_active = False
                while not mysql_is_active:
                        mysql_is_active = os.system("mysqladmin -umysql ping") == 0
                        time.sleep(1.0)

		# run database setup script.
		cmd = os.path.join(self.gitMyamiDir, 'install/newDBsetup.php -L %s -P %s -H %s -U %s -E %s' % (self.leginonDB, self.projectDB, self.dbHost, self.dbUser, self.adminEmail))
		cmd = 'php ' + cmd

		self.runCommand(cmd)
		self.openFirewallPort(3306)
		return True

	def setupProcessServer(self):
		self.writeToLog("--- Start install Processing Server")
		self.processServerYumInstall()

		# make certain yum package binary available
		self.processServerPackageEnable()

		# install non-Yum packages
		self.processServerExtraPythonPackageInstall()
 
		# install all the myami python packages except appion.
		os.chdir(self.gitMyamiDir)
		self.runCommand('./pysetup.sh install')

		# install the appion python packages
		# For the bin scripts, we add an extra directory level below
		# the default location to keep all appion scripts in their
		# own place, rather than cluttering up /usr/bin or whatever.
		pyprefix = self.runCommand('python -c "import sys;print sys.prefix"')
		pyprefix = pyprefix.strip()
		apbin = os.path.join(pyprefix, 'bin', 'appion')
		os.chdir(self.gitMyamiDir + 'appion')
		self.runCommand('python setup.py install --install-scripts=%s' % (apbin,))
		
		# add a custom search path to appion.sh and appion.csh in profile.d
		for ext,cmd,eq in (('sh','export','='),('csh','setenv',' ')):
			fname = '/etc/profile.d/appion.%s' % (ext,)
			f = open(fname, 'w')
			setcmd = '%s PATH%s${PATH}:%s' % (cmd, eq, apbin,)
			f.write(setcmd)
			f.close()
			os.chmod(fname, 0755)


		# setup Leginon configuration file
		self.writeToLog("setup Leginon configuration file")
		self.setupLeginonCfg()

		# setup Sinedon configuration file
		self.writeToLog("setup Sinedon configuration file")
		sinedonDir = self.runCommand('python -c "import sinedon; print sinedon.__path__[0]"')
		sinedonDir = sinedonDir.strip()
		self.setupSinedonCfg(sinedonDir)

		# setup .appion.cfg configuration file
		self.writeToLog("setup .appion.cfg configuration file")
		self.setupAppionCfg("/usr/bin")

		# setup instruments configuration
		pyscopeDir = self.runCommand('python -c "import pyscope; print pyscope.__path__[0]"')
		pyscopeDir = pyscopeDir.strip()
		self.setupPyscopeCfg(pyscopeDir)

		os.chdir(self.currentDir)		
		self.enableTorqueComputeNode()
		return True

	def setupJobServer(self):
		self.writeToLog("--- Start install Job Server")

		packagelist = ['torque-server', 'torque-scheduler', ]
		self.yumInstall(packagelist)

		nodes_file = self.torqueLibPath + 'server_priv/nodes'
		if not os.path.exists(nodes_file):
			message = "\nWarning: "+nodes_file+" not found.\n"
			print message 
			self.writeToLog(message)
			return True

		self.runCommand("systemctl start pbs_server")
		self.runCommand("systemctl start pbs_sched")
		
		f = open(nodes_file, 'w')
		f.write("%s np=%d" % (self.hostname, self.nproc))
		f.close()

		f = open(self.torqueLibPath + 'server_name', 'w')
		f.write("%s" % (self.hostname))
		f.close()

		# edit /var/hosts file
		self.editHosts()

		# start the Torque server, keep this after any config file editing.
		self.runCommand("systemctl enable pbs_server")
		self.runCommand("systemctl enable pbs_sched")
		
		self.runCommand("/sbin/service network restart")
		return True

	def installExternalPackages(self):
		self.writeToLog("--- Start install External Packages")
		self.installEman()
		self.installSpider()
		self.installXmipp()
		self.installProtomo()
		self.installFFmpeg()
		return True

	def installEman(self):
		self.writeToLog("--- Start install Eman1")
		cwd = os.getcwd()
		
		# select 32 or 64 bit file to download
		if self.machine == "i686" or self.machine == "i386" :
			fileLocation = "http://emg.nysbc.org/redmine/attachments/download/632/eman-linux-x86-cluster-1.9.tar.gz"
			fileName = "eman-linux-x86-cluster-1.9.tar.gz"
		else :
			fileLocation = "http://emg.nysbc.org/redmine/attachments/download/631/eman-linux-x86_64-cluster-1.9.tar.gz"
			fileName = "eman-linux-x86_64-cluster-1.9.tar.gz"

		# download the tar file and unzip it
		command = "wget -c " + fileLocation
		self.runCommand(command)
		command = "tar -zxvf " + fileName
		self.runCommand(command)
		
		# move the unzipped folder to a global location
		self.runCommand("mv -v EMAN /usr/local/")

		# Run the EMAN installer, it sets up the EMAN python module (must be run from the EMAN directory)
		emandir = "/usr/local/EMAN"
		os.chdir(emandir)
		self.runCommand("./eman-installer")

		# set environment variables
		# For BASH, create an eman.sh
		f = open('eman.sh', 'w')
		f.write('''export EMANDIR=/usr/local/EMAN\n
			export PATH=${EMANDIR}/bin:${PATH}\n
			export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${EMANDIR}/lib\n
			export PYTHONPATH=${EMANDIR}/lib''')
		f.close()

		# For C shell, create an eman.csh
		f = open('eman.csh', 'w')
		f.write('''setenv EMANDIR /usr/local/EMAN\n
			setenv PATH ${EMANDIR}/bin:${PATH}\n
			setenv LD_LIBRARY_PATH ${EMANDIR}/lib\n
			setenv PYTHONPATH ${EMANDIR}/lib''')
		f.close()
		
		# add them to the global /etc/profile.d/ folder
		shutil.copy("eman.sh", "/etc/profile.d/eman.sh")
		shutil.copy("eman.csh", "/etc/profile.d/eman.csh")
		os.chmod("/etc/profile.d/eman.sh", 0755)
		os.chmod("/etc/profile.d/eman.csh", 0755)
		
		os.chdir(self.currentDir)
				
		return True

	def installSpider(self):
		self.writeToLog("--- Start install Spider")
		
		fileLocation = "http://emg.nysbc.org/redmine/attachments/download/638/spidersmall.18.10.tar.gz"
		fileName = "spidersmall.18.10.tar.gz"

		# download the tar file and unzip it
		command = "wget -c " + fileLocation
		self.runCommand(command)
		print "-------------done with wget.------------"
		command = "tar -zxvf " + fileName
		self.runCommand(command)
		
		# move the unzipped folder to a global location
		try:
			shutil.move("spider", "/usr/local/spider")
		except:
			self.writeToLog("--- Spider installation failed: could not copy spider directory tp /usr/local/spider")
			return False
		#self.runCommand("mv -v spider /usr/local/")

		# select 32 or 64 bit file to install
		if self.machine == "i686" or self.machine == "i386" :
			if self.nproc == 1:
				fileName = "spider_linux"
			else:
				fileName = "spider_linux_mp_intel"
		else :
			fileName = "spider_linux_mp_opt64"

		# create a link to the selected file in /usr/local/bin
		command = "ln -sv /usr/local/spider/bin/" + fileName + " /usr/local/bin/spider"
		self.runCommand(command)

		# set environment variables
		# For BASH, create an spider.sh
		f = open('spider.sh', 'w')
		f.write('''export SPIDERDIR=/usr/local/spider
export SPBIN_DIR=${SPIDERDIR}/bin/
export SPPROC_DIR=${SPIDERDIR}/proc/
export SPMAN_DIR=${SPIDERDIR}/man/
''')
		f.close()

		# For C shell, create an spider.csh
		f = open('spider.csh', 'w')
		f.write('''setenv SPIDERDIR /usr/local/spider
setenv SPMAN_DIR ${SPIDERDIR}/man/
setenv SPPROC_DIR ${SPIDERDIR}/proc/
setenv SPBIN_DIR ${SPIDERDIR}/bin/''')
		f.close()
		
		# add them to the global /etc/profile.d/ folder
		shutil.copy("spider.sh", "/etc/profile.d/spider.sh")
		shutil.copy("spider.csh", "/etc/profile.d/spider.csh")
		os.chmod("/etc/profile.d/spider.sh", 0755)
		os.chmod("/etc/profile.d/spider.csh", 0755)


	def installXmipp(self):
		self.writeToLog("--- Start install Xmipp")

		cwd = os.getcwd()
		
		dirName = "Xmipp-2.4-src"
		tarFileName = dirName + ".tar.gz"
		tarFileLocation = "http://emg.nysbc.org/redmine/attachments/download/636/" + tarFileName

		# download the source code tar file and unzip it
		command = "wget -c " + tarFileLocation
		self.runCommand(command)
		command = "tar -zxvf " + tarFileName
		self.runCommand(command)

		# change directories to the unzipped xmipp dir
		os.chdir(dirName)

		#
		# prepare Xmipp make files
		# 
		
		# locate the mpi library
		mpifile = "libmpi.so"
		command = "locate " + mpifile
		libMpiPath = self.runCommand(command)

		# format mpi include and lib paths
		if (mpifile in libMpiPath):
			matchPattern = "lib/" + mpifile
			libMpiPath = libMpiPath.split(matchPattern)
			MpiBasePath = libMpiPath[0]
		else:
			self.writeToLog("--- Error installing Xmipp. Could not locate libmpi.so.")
			return False

		includeMpiDir = MpiBasePath + "include/"
		MpiLibDir = MpiBasePath + "lib/"

		MpiBinDir = MpiBasePath + "bin/"
		os.environ["PATH"] = MpiBinDir + ':' + os.environ["PATH"]

		command = "./scons.configure MPI_LIBDIR="+MpiLibDir+"  MPI_LIB=mpi  MPI_INCLUDE="+includeMpiDir
		output = self.runCommand(command)
		if ("Checking for MPI ... yes" not in output):
			self.writeToLog("--- Error installing Xmipp. Could not find MPI during configuration.")
			return False

		# compile
		self.runCommand("./scons.compile")

		# change directories to original working dir
		os.chdir(cwd)

		# move the main source code directory to global location, like /usr/local
		self.writeToLog("--- Moving the Xmipp directory to /usr/local/Xmipp.")
		xmipp_dest = "/usr/local/Xmipp"
		if not os.path.exists(xmipp_dest):
			shutil.move(dirName, xmipp_dest)

		#
		# set environment variables
		#

		bashFile = "xmipp.sh"
		cShellFile = "xmipp.csh"
		profileDir = "/etc/profile.d/"

		# For BASH, create an xmipp.sh
		f = open(bashFile, 'w')
		f.write('''export XMIPPDIR=/usr/local/Xmipp
export PATH=${XMIPPDIR}/bin:${PATH}
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${XMIPPDIR}/lib:%s''' % (MpiLibDir))
		f.close()

		# For C shell, create an xmipp.csh
		f = open(cShellFile, 'w')
		f.write('''setenv XMIPPDIR /usr/local/Xmipp
setenv PATH ${XMIPPDIR}/bin:${PATH}
setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:${XMIPPDIR}/lib:%s''' % (MpiLibDir))
		f.close()
		
		# add them to the global /etc/profile.d/ folder
		self.writeToLog("--- Adding xmipp.sh and xmipp.csh to /etc/profile.d/.")
		shutil.copy(bashFile, profileDir + bashFile)
		shutil.copy(cShellFile, profileDir + cShellFile)
		os.chmod(profileDir + bashFile, 0755)
		os.chmod(profileDir + cShellFile, 0755)



        def installFFmpeg(self):

                print "Installing FFmpeg"
                self.writeToLog("--- Start install FFmpeg")
                use_local = "/usr/local"
                cwd = cwd = os.getcwd()

                ffmpegName = "ffmpeg-git-32bit-static"
                ffmpegtarFileName = ffmpegName + ".tar.xz"
                ffmpegtarFileLocation = "http://emg.nysbc.org/redmine/attachments/download/4674/ffmpeg-git-32bit-static.tar.xz"

                command = "wget -c " + ffmpegtarFileLocation
                self.runCommand(command)
                command = "tar -xvf " + ffmpegtarFileName
                self.runCommand(command)
                print "-------------Done downloading ffmpeg with wget.------------"

              

                #ffmpeg tar is compilied daily at http://johnvansickle.com/ffmpeg/. The git static version compiled on 11/11/2015 was used for this ffmpeg installation. The extracted folder name contains the datestamp; make sure to change the datestamp in the extracted folder name if using a newer version of ffmpeg from the johnvansickle site.

                self.runCommand("mv ffmpeg-git-20151111-32bit-static ffmpeg")
                newDir = os.path.join(use_local,"ffmpeg")
                command = "mv ffmpeg "+newDir
                self.runCommand(command)
                os.chdir(newDir)             
                command = "./ffmpeg"
                self.runCommand("./ffmpeg")

                #
                #set environment variables
                #
                bashFile = "ffmpeg.sh"
                cShellFile = "ffmpeg.csh"
                profileDir = "/etc/profile.d/"

                print "---------------Create bash and csh scripts---------"
                #For BASH, create an ffmpeg.sh
                f = open(bashFile, 'w')
                f.write('''export FFMPEGDIR="/usr/local/ffmpeg"
export PATH=${PATH}:${FFMPEGDIR}''')

                f.close()

                # For C shell, create an ffmpeg.sh

                f=open(cShellFile,'w')

                f.write('''setenv FFMPEGDIR="/usr/local/ffmpeg"
setenv PATH ${FFMPEGDIR}:${PATH}
if ($?LD_LIBRARY_PATH) then
        setenv LD_LIBRARY_PATH "${LD_LIBRARY_PATH}:${FFMPEGDIR}"
else
        setenv LD_LIBRARY_PATH "${FFMPEGDIR}"
endif''')

                f.close()
                #add them to the global /etc/profile.d/ folder
                self.writeToLog("--- Adding ffmpeg.sh and ffmpeg.csh to /etc/profile.d/.")
                shutil.copy(bashFile, profileDir + bashFile)
                shutil.copy(cShellFile, profileDir + cShellFile)
                os.chmod(profileDir + bashFile, 0755)
                os.chmod(profileDir + cShellFile,0755)




	def installProtomo(self):
		self.writeToLog("--- Start install Protomo")
		
		cwd = os.getcwd()
		protomoVer = "protomo-2.4.1"
		zipFileName = protomoVer + ".zip"
		zipFileLocation = "http://emg.nysbc.org/redmine/attachments/download/4147/" + zipFileName
		
		# download the source code tar file and unzip it
		command = "wget -c " + zipFileLocation
		self.runCommand(command)
		command = "unzip -o " + zipFileName
		self.runCommand(command)
		
		use_local = "/usr/local"
		# move the unzipped folder to a global location
		self.runCommand("tar -vxjf " + protomoVer + ".tar.bz2 --directory=" + use_local)
		protomoDir = os.path.join(use_local, protomoVer)
		deplibs = os.path.join(protomoDir, 'deplibs')
		if not os.path.isdir(deplibs):
			os.mkdir(deplibs)		
		self.runCommand("tar -vxjf deplibs.tar.bz2 --directory=" + deplibs)
		self.runCommand("tar -vxjf i3-0.9.6.tar.bz2 --directory=" + use_local)
		
			# set environment variables
		   # For BASH, create an protom.sh
		f = open('protomo.sh', 'w')
		f.write('''export I3ROOT=%s
export I3LIB=${I3ROOT}/lib/linux/x86-64
export PATH=${PATH}:${I3ROOT}/bin/linux/x86-64
export I3LEGACY="/usr/local/i3-0.9.6"
export PATH=${PATH}:/usr/local/i3-0.9.6/bin/linux/x86-64
export PATH=${PATH}:${I3ROOT}/lib/linux/x86-64

if [ $LD_LIBRARY_PATH ];
then
   export LD_LIBRARY_PATH="${LD_LIBRARY_PATH}:${I3LIB}:%s/lib/linux/x86-64"
else
   export LD_LIBRARY_PATH="${I3LIB}:%s/lib/linux/x86-64"
fi
if [ $PYTHONPATH ];
then
   export PYTHONPATH=${I3LIB}:${PYTHONPATH}
else
   export  PYTHONPATH=${I3LIB}
fi
''' % (protomoDir, deplibs, deplibs))
		f.close()

		# For C shell, create an eman.csh
		f = open('protomo.csh', 'w')
		f.write('''setenv I3ROOT %s
setenv I3LIB ${I3ROOT}/lib/linux/x86-64
setenv PATH ${PATH}:${I3ROOT}/bin/linux/x86-64
setenv I3LEGACY "/usr/local/i3-0.9.6"
setenv PATH ${PATH}:/usr/local/i3-0.9.6/bin/linux/x86-64
setenv PATH ${PATH}:${I3ROOT}/lib/linux/x86-64

if ($?LD_LIBRARY_PATH) then
	setenv LD_LIBRARY_PATH "${LD_LIBRARY_PATH}:${I3LIB}:%s/lib/linux/x86-64"
else
	setenv LD_LIBRARY_PATH "${I3LIB}:%s/lib/linux/x86-64"
endif
if ( $?PYTHONPATH) then
    setenv PYTHONPATH ${I3LIB}:${PYTHONPATH}
else
    setenv PYTHONPATH ${I3LIB}
endif
''' % (protomoDir, deplibs, deplibs))
		f.close()
		
		# add them to the global /etc/profile.d/ folder
		shutil.copy("protomo.sh", "/etc/profile.d/protomo.sh")
		shutil.copy("protomo.csh", "/etc/profile.d/protomo.csh")
		os.chmod("/etc/profile.d/protomo.sh", 0755)
		os.chmod("/etc/profile.d/protomo.csh", 0755)
		self.yumInstall(['http://pkgs.repoforge.org/rpmforge-release/rpmforge-release-0.5.3-1.el6.rf.x86_64.rpm'])



	def installFrealign(self):
		self.writeToLog("--- Start install Frealign")
		
		fileLocation = "http://emg.nysbc.org/redmine/attachments/download/740/frealign_v8.09_110505.tar.gz"
		fileName = "frealign_v8.09_110505.tar.gz"

		# download the tar file and unzip it
		command = "wget -c " + fileLocation
		self.runCommand(command)
		print "-------------done with wget.------------"
		command = "tar -zxvf " + fileName
		self.runCommand(command)
		
		# move the unzipped folder to a global location
		shutil.move("frealign_v8.09", "/usr/local/")
		#self.runCommand("mv -v spider /usr/local/")

		# select 32 or 64 bit file to install
		if self.machine == "i686" or self.machine == "i386" :
			if self.nproc == 1:
				fileName = "frealign_v8.exe"
			else:
				fileName = "frealign_v8_mp.exe"
		else :
			fileName = "frealign_v8.exe"

		# create a link to the selected file in /usr/local/bin
		command = "ln -sv /usr/local/frealign_v8.09/bin/" + fileName + " /usr/local/bin/frealign"
		# appion actually calls the mp version only:  Need to decide what to do
		command = "ln -sv /usr/local/frealign_v8.09/bin/" + fileName + " /usr/local/bin/frealign_mp"
		self.runCommand(command)

		# set environment variables
		# Nothing to set.


	def processServerYumInstall(self):

		packagelist = ['ImageMagick', 'MySQL-python', 'compat-gcc-34-g77', 'fftw3-devel', 'gcc-c++', 'gcc-gfortran', 'gcc-objc', 'gnuplot', 'grace', 'gsl-devel', 'libtiff-devel', 'netpbm-progs', 'numpy', 'openmpi-devel', 'opencv-python', 'python-devel', 'python-imaging', 'python-matplotlib', 'python-tools', 'scipy', 'wxPython', 'xorg-x11-server-Xvfb', 'libjpeg-devel', 'zlib-devel', ]
		self.yumInstall(packagelist)

	def enableTorqueComputeNode(self):
		packagelist = ['torque-mom', 'torque-client', ]
		self.yumInstall(packagelist)
		self.runCommand("systemctl enable pbs_mom")

		torqueConfig_file = self.torqueLibPath + 'mom_priv/config'
		if not os.path.exists(torqueConfig_file):
			message = "\nWarning: "+torqueConfig_file+" not found.\n"
			print message 
			self.writeToLog(message)
			return
		
		f = open(self.torqueLibPath + 'mom_priv/config', 'w')
		f.write("$pbsserver localhost # running pbs_server on this host")

		# Need munge key
		#self.runCommand("/usr/sbin/munged")
		#self.runCommand("/usr/sbin/create-munge-key")
		#self.runCommand("chkconfig munge on")
		
		self.runCommand('qmgr -c "s s scheduling=true"')
		self.runCommand('qmgr -c "c q batch queue_type=execution"')
		self.runCommand('qmgr -c "s q batch started=true"')
		self.runCommand('qmgr -c "s q batch enabled=true"')
		self.runCommand('qmgr -c "s q batch resources_default.nodes=1"')
		self.runCommand('qmgr -c "s q batch resources_default.walltime=3600"')
		self.runCommand('qmgr -c "s s default_queue=batch"')		
		
		self.runCommand("systemctl start pbs_mom")
		
		f.close()

	def mysqlYumInstall(self):
		self.runCommand("rpm -Uvh http://repo.mysql.com/mysql57-community-release-el%s.rpm" % (self.redhatMajorRelease))
		packagelist = ['mysql-server', 'php', 'php-mysql', ]
		self.yumInstall(packagelist)
	
	def setupLeginonCfg(self):
		# The template config file is in the git download location. The last place the leginon.cfg
		# file is looked for is /etc/myami, which makes it the most global config file location.
		configTemplateFile	= os.path.join(self.gitMyamiDir, "leginon", "leginon.cfg.template")
		configOutFile 		= "leginon.cfg"
		configDest 		= "/etc/myami"
		
		# make and go to the destination dir
		if not os.path.exists( configDest ):
			self.writeToLog("create leginon configuration folder - /etc/myami")
			os.makedirs( configDest )
		os.chdir( configDest )

		inf  = open( configTemplateFile, 'r' )
		outf = open( configOutFile, 'w' )

		for line in inf:
			if line.startswith('path:'):
				outf.write('path: %s/leginon\n' % (self.imagesDir))
			else:
				outf.write(line)
		inf.close()
		outf.close()
		os.chdir(self.currentDir)

	def setupPyscopeCfg(self, pyscopeCfgDir):
		shutil.copy(pyscopeCfgDir + '/instruments.cfg.template', pyscopeCfgDir + '/instruments.cfg')


	def setupSinedonCfg(self, sinedonDir):
		inf = open(self.gitMyamiDir + 'sinedon/examples/sinedon.cfg', 'r')
		outf = open('/etc/myami/sinedon.cfg', 'w')

		for line in inf:
			if line.startswith('user: usr_object'):
				outf.write('user: root\n')
			else:
				outf.write(line)
		inf.close()
		outf.close()		

	def setupAppionCfg(self, appionCfgDir):
		outf = open(appionCfgDir + '/.appion.cfg', 'w')
		
		outf.write("ProcessingHostType=Torque\n")
		outf.write("Shell=/bin/csh\n")
		outf.write("ScriptPrefix=\n")
		outf.write("ExecCommand=/usr/bin/qsub\n")
		outf.write("StatusCommand=/usr/bin/qstat\n")
		outf.write("AdditionalHeaders= -m e, -j oe\n")
		outf.write("PreExecuteLines=\n")

		outf.close()		

	def editHosts(self):

		# make a back up file
		shutil.copy('/etc/hosts', '/etc/hosts-tmp')
		inf = open('/etc/hosts-tmp', 'r')
		outf = open('/etc/hosts', 'w')

		for line in inf:
			line = line.rstrip()
			if "127.0.0.1" in line:
				outf.write("127.0.0.1		%s localhost.localdomain localhost\n" % (self.hostname))
			else:
				outf.write(line + '\n')
		
		inf.close()
		outf.close()
		os.remove('/etc/hosts-tmp')
			

	def editPhpIni(self):

		# make a back up file
		shutil.copy('/etc/php.ini', '/etc/php.ini-backup')		
		shutil.move('/etc/php.ini', '/etc/php.ini-tmp')
		inf = open('/etc/php.ini-tmp', 'r')
		outf = open('/etc/php.ini', 'w')

		for line in inf:
			line = line.rstrip()
			if line.startswith(';'):
				outf.write(line + "\n")
			elif line.startswith('error_reporting'):
				outf.write("error_reporting = E_ALL & ~E_NOTICE & ~E_WARNING & ~E_DEPRECATED\n")
			elif line.startswith('display_error'):
				outf.write("display_error = On\n")
			elif line.startswith('register_argc_argv'):
				outf.write("register_argc_argv = On\n")
			elif line.startswith('short_open_tag'):
				outf.write("short_open_tag = On\n")
			elif line.startswith(';date.timezone'):
				timestring = "date.timezone = '" + self.timezone + "'\n"
				outf.write(timestring)
			elif line.startswith('max_execution_time'):
				pass
			elif line.startswith('max_input_time'):
				pass
			elif line.startswith('memory_limit'):
				pass
			else:
				outf.write(line + '\n')

		inf.close()
		os.remove('/etc/php.ini-tmp')
		
		outf.write('; custom parameters from CentOS Auto Install script\n')
		outf.write('max_execution_time = 300 ; Maximum execution time of each script, in seconds\n')
		outf.write('max_input_time = 300	 ; Maximum amount of time to spend parsing request data\n')
		outf.write('memory_limit = 1024M	 ; Maximum amount of memory a script may consume\n')
		outf.write('\n')

		outf.close()			
			
	def editApacheConfig(self):
	
		shutil.copy('/etc/httpd/conf/httpd.conf', '/etc/httpd/conf/httpd.conf-backup')
		shutil.move('/etc/httpd/conf/httpd.conf', '/etc/httpd/conf/httpd.conf-tmp')
		inf = open('/etc/httpd/conf/httpd.conf-backup', 'r')
		outf = open('/etc/httpd/conf/httpd.conf', 'w')

		for line in inf:
			line = line.rstrip()
			if line.startswith('#'):
				outf.write(line + "\n")
			elif line.startswith('DirectoryIndex'):
				outf.write("DirectoryIndex index.html index.html.var index.php\n")
			elif line.startswith('HostnameLookups'):
				outf.write("HostnameLookups On\n")
			elif line.startswith('UseCanonicalName'):
				outf.write("UseCanonicalName On\n")
			else:
				outf.write(line + '\n')

		inf.close()
		outf.close()
		os.remove('/etc/httpd/conf/httpd.conf-tmp')

	def installPhpMrc(self):
		
		if os.path.isfile('/etc/php.d/mrc.ini'):
			return

		phpmrcdir = os.path.join(self.gitMyamiDir, "programs/php_mrc")
		os.chdir(phpmrcdir)
		self.runCommand("phpize")
		self.runCommand("./configure")
		self.runCommand("make")
		module = os.path.join(phpmrcdir, "modules/mrc.so")

		if not os.path.isfile(module):
			self.writeToLog("ERROR: mrc.so failed")
			sys.exit(1)

		self.runCommand("make install")
		f = open("/etc/php.d/mrc.ini", "w")
		f.write("; Enable mrc extension module\n")
		f.write("extension=mrc.so\n")
		f.close()
		os.chdir(self.currentDir)

	def installReduxServer(self):
		# Redux prerequisits: python, numpy, scipy, pil, pyfilesystem, fftw3, pyfftw, pyami, numextension
		#redux yum packages
		packagelist = [ 'fftw-devel', 'numpy', 'python-devel', 'python-imaging', 'scipy', ]
		self.yumInstall(packagelist)
		# Most are installed as on processingServer
		packagelist = [
			{
				# Python fs
				'targzFileName':'fs-0.4.0.tar.gz',
				'fileLocation':'https://pypi.python.org/packages/08/c3/9a6e3c7bd2755e3383c84388c1e01113bddafa8008a0aa4af64996ab4470/',
				'unpackDirName':'fs-0.4.0',
			}
		]

		for p in packagelist:
			self.installPythonPackage(p['targzFileName'], p['fileLocation'], p['unpackDirName'])

		# Setup the redux config file.
		self.editReduxConfig()

		# Can't start the redux server from within this script, so we prompt the user to start it 
		# at the end of this script.
		# self.runCommand("/sbin/service reduxd start")

	def editReduxConfig(self):
		
		# The redux log should go to /var/log
		copyFrom  = self.gitMyamiDir + "redux/redux.cfg.template"
		copyTo    = "/etc/myami/redux.cfg"
		inf       = open(copyFrom, 'r')
		outf      = open(copyTo, 'w')

		for line in inf:
			line = line.rstrip()
			if line.startswith('#'):
				outf.write(line + "\n")
			elif line.startswith('file:'):
				outf.write("file: /var/log/redux.log\n")
			else:
				outf.write(line + '\n')

		inf.close()
		outf.close()
		
	def installPhpSsh2(self):
		if os.path.isfile("/etc/php.d/ssh2.ini"):
			return
		
		cwd = os.getcwd()
		self.runCommand("wget -c http://pecl.php.net/get/ssh2-0.11.3.tgz")
		self.runCommand("tar zxvf ssh2-0.11.3.tgz")
		sshdir = os.path.join(cwd, "ssh2-0.11.3")
		os.chdir(sshdir)
		self.runCommand("phpize")
		self.runCommand("./configure")
		self.runCommand("make")

		module = "modules/ssh2.so"
		if not os.path.isfile(module):
			self.writeToLog("ERROR ssh2.so failed")
			sys.exit(1)

		self.runCommand("make install")

		f = open('/etc/php.d/ssh2.ini', 'w')
		f.write('; Enable ssh2 extension module\n')
		f.write('extension=ssh2.so\n')
		f.close()
		os.chdir(self.currentDir)

	def getServerName(self):
		return platform.node()

	def getNumProcessors(self):
		if not os.path.exists('/proc/cpuinfo'):
			return None
		f = open('/proc/cpuinfo', 'r')
		nproc = 0
		for line in f:
			if line.startswith('processor'):
				nproc += 1
		f.close()
		return nproc
		
	def installMyamiWeb(self):
		gitMyamiwebDir = os.path.join(self.gitMyamiDir, "myamiweb")
		centosWebDir = "/var/www/html"
		self.runCommand("cp -rf %s %s" % (gitMyamiwebDir, centosWebDir))

	def editMyamiWebConfig(self):
	
		configFile = os.path.join("/var/www/html/myamiweb/config.php")

		inf = open(configFile + ".template", 'r')
		outf = open(configFile, 'w')

		for line in inf:
			line = line.rstrip()
			if line.startswith('// --- ') or len(line) == 0:
				outf.write(line + "\n")
			elif line.startswith("define('ENABLE_LOGIN'"):
				outf.write("define('ENABLE_LOGIN', %s);\n" % (self.enableLogin))
			elif line.startswith("define('DB_HOST'"):
				outf.write("define('DB_HOST', '%s');\n" % (self.dbHost))
			elif line.startswith("define('DB_USER'"):
				outf.write("define('DB_USER', '%s');\n" % (self.dbUser))
			elif line.startswith("define('DB_PASS'"):
				outf.write("define('DB_PASS', '%s');\n" % (self.dbPass))
			elif line.startswith("define('ADMIN_EMAIL'"):
				outf.write("define('ADMIN_EMAIL', '%s');\n" % (self.adminEmail))
			elif line.startswith("define('DB_LEGINON'"):
				outf.write("define('DB_LEGINON', '%s');\n" % (self.leginonDB))
			elif line.startswith("define('DB_PROJECT'"):
				outf.write("define('DB_PROJECT', '%s');\n" % (self.projectDB))
			elif "addplugin(\"processing\");" in line:
				outf.write("addplugin(\"processing\");\n")
			elif "// $PROCESSING_HOSTS[]" in line:
				outf.write("$PROCESSING_HOSTS[] = array('host' => '%s', 'nproc' => %d,'nodesmax' => '1','ppndef' => '1','ppnmax' => '1','reconpn' => '1','walltimedef' => '48','walltimemax' => '240','cputimedef' => '1000','cputimemax' => '10000','memorymax' => '','appionbin' => '/usr/','appionlibdir' => '/usr/lib/python2.4/site-packages/','baseoutdir' => '/appion','localhelperhost' => 'localhost','dirsep' => '/','wrapperpath' => '','loginmethod' => 'USERPASSWORD','loginusername' => '','passphrase' => '','publickey' => '','privatekey' => ''	);\n"%(self.dbHost, self.nproc))
			elif "// $CLUSTER_CONFIGS[]" in line:
				outf.write("$CLUSTER_CONFIGS[] = 'default_cluster';\n")
			elif line.startswith("define('TEMP_IMAGES_DIR', "):
				outf.write("define('TEMP_IMAGES_DIR', '/tmp');\n")
			elif line.startswith("define('DEFAULTCS', "):
				outf.write("define('DEFAULTCS', '%.1f');\n" % (self.csValue))
			elif line.startswith("define('SERVER_HOST'"):
				outf.write("define('SERVER_HOST', 'localhost');\n")		
			else:
				outf.write(line + '\n')

		inf.close()
		outf.close()

	def writeToLog(self, message):
		logfile = open(self.currentDir + "/" + self.logFilename, 'a')
		logfile.write(message + '\n')
		logfile.close()
			
	def getMyami(self):
		#TODO: handle "git: is already a working copy for a different URL" case


                if os.path.exists('/tmp/myami/'):

                        shutil.rmtree('/tmp/myami/')

		self.runCommand(self.gitCmd)

	def getDefaultValues(self):

		print "===================================="
		print "Installing job submission server"
		print "Installing processing server"
		print "Installing database server"
		print "Installing web server"
		print "===================================="
		print ""
		
		value = raw_input("Please enter the registration key. You must be registered at http://emg.nysbc.org/redmine to recieve a registration key: ")
		value = value.strip()

		self.regKey = value
		# Note to user: We try to collect a small amount of information about who installs our software
		# so that we may recieve funding for its continued support and development. We also pass this information
		# on to the providers of EMAN, XMIPP, and SPIDER, which we install with this script, 
		# to ensure their continued development as well. If you remove this check for the reg key, please
		# remember to appropriatly cite any software that you find useful while processing your data.
		result = self.checkRegistrationKey()
		if result is False:
			return False

		# Set the admin email address
		value             = raw_input("Please enter an email address: ")
		value             = value.strip()
		self.adminEmail   = value
		
		# Set the root password		
		password              = raw_input("Please enter the system root password: ")
		password              = password.strip()
		self.serverRootPass   = password
		
		# Set the local timezone for use in the php.ini file
		timezone      = raw_input("Please enter your timezone based on the available options listed at http://www.php.net/manual/en/timezones.php : ")
		timezone      = timezone.strip()
		if ( timezone == "" ):
			# provide a default timezone if it is empty
			timezone = "America/Los_Angeles" 
		self.timezone = timezone

		questionText = "Would you like to download demo GroEL images and upload them to this installation?"
		self.doDownloadSampleImages = self.getBooleanInput(questionText)
		
		questionText = "Would you like to install EMAN, Xmipp, Spider, and Protomo at this time?"
		self.doInstallExternalPackages = self.getBooleanInput(questionText)
		
	def getBooleanInput(self, questionText = ''):
		'''
		Return boolean True/False depending on Y/N input from user.
		'''
		value = ""
		while (value != "Y" and value != "y" and value != "N" and value != "n"): 
			value = raw_input("%s(Y/N): " % questionText)
			value = value.strip()

		if (value == "Y" or value == "y"):
			return True
		else:
			return False
		
	
	def downloadSampleImages(self):
	   
		getImageCmd = "wget -P/tmp/images http://emg.nysbc.org/redmine/attachments/download/112/06jul12a_00015gr_00028sq_00004hl_00002en.mrc http://emg.nysbc.org/redmine/attachments/download/113/06jul12a_00015gr_00028sq_00023hl_00002en.mrc http://emg.nysbc.org/redmine/attachments/download/114/06jul12a_00015gr_00028sq_00023hl_00004en.mrc http://emg.nysbc.org/redmine/attachments/download/115/06jul12a_00022gr_00013sq_00002hl_00004en.mrc http://emg.nysbc.org/redmine/attachments/download/116/06jul12a_00022gr_00013sq_00003hl_00005en.mrc http://emg.nysbc.org/redmine/attachments/download/109/06jul12a_00022gr_00037sq_00025hl_00004en.mrc http://emg.nysbc.org/redmine/attachments/download/110/06jul12a_00022gr_00037sq_00025hl_00005en.mrc http://emg.nysbc.org/redmine/attachments/download/111/06jul12a_00035gr_00063sq_00012hl_00004en.mrc"

		print getImageCmd
		proc = subprocess.Popen(getImageCmd, shell=True)
		proc.wait()

	def checkRegistrationKey(self):
		# used sha-1. This has been deprecated as of python 2.5.
		# we now use the hashlib instead: http://docs.python.org/library/hashlib.html#module-hashlib
		if (hashlib.sha1(self.regKey).digest() != self.regKeyHash):
			print "The registration key provided is incorrect. Exiting installation..."
			self.writeToLog("ERROR: registration key (%s) is incorrect ---" % (self.regKey,))
			return False

		print "Registration Key confirmed."
		self.writeToLog("Registration Key confirmed.")
		return True

	def run(self):
		self.currentDir = os.getcwd()
		self.logFilename = 'installation.log'
		self.gitMyamiDir = '/tmp/myami/'
		self.enableLogin = 'false'
		self.dbHost = 'localhost'
		self.dbUser = 'root'
		self.dbPass = ''
		self.serverRootPass = ''
		self.leginonDB = 'leginondb'
		self.projectDB = 'projectdb'
		self.adminEmail = ''
		self.csValue = 2.0
		self.imagesDir = '/myamiImages'

		self.setReleaseDependantValues()

		self.hostname = self.getServerName()
		self.nproc = self.getNumProcessors()
		# Don't think we need this anymore
		#self.numCPUs = self.determineNumberOfCPUs()
		self.machine = platform.machine()

		result = self.checkDistro()
		if result is False:
			sys.exit(1)
		
		result = self.checkRoot()
		if result is False:
			sys.exit(1)

		self.removeLogFile()
		self.setupFilePermission()
			
		result = self.checkSeLinux()
		if result is False:
			sys.exit(1)

		result = self.getDefaultValues()
		if result is False:
			sys.exit(1)
		

		self.yumUpdate()
		self.yumInstall(['git'])
		self.getMyami()
		
		result = self.setupJobServer()
		if result is False:
			sys.exit(1)
		
		result = self.setupProcessServer()
		if result is False:
			sys.exit(1)

		result = self.setupDBServer()
		if result is False:
			sys.exit(1)

		result = self.setupWebServer()
		if result is False:
			sys.exit(1)

		if (self.doDownloadSampleImages):
			self.downloadSampleImages()

		if (self.doInstallExternalPackages):
			self.installExternalPackages()
					

		self.writeToLog("Installation Complete.")

		print("========================")
		print("Installation Complete.")
		print("Appion will launch in your web browser momentarily.")
		print("You may launch Leginon with the following command: start-leginon.py")
		print("IMPORTANT: To view images in the web browser, you must first start the Redux server.")
		print("Start the Redux Server with the following command: /sbin/service reduxd start")
		print("========================")

		# Start the Torque server
		self.runCommand("systemctl start pbs_server")
				
		setupURL = "http://localhost/myamiweb/setup/autoInstallSetup.php?password=" + self.serverRootPass + "&myamidir=" + self.gitMyamiDir + "&uploadsample=" + "%d" % int(self.doDownloadSampleImages)
		setupOpened = None
		try:
			setupOpened = webbrowser.open_new(setupURL)
		except:
			print("ERROR: Failed to run Myamiweb setup script.")
			print("You may try running " + setupURL + " in your web browser. ")
			print(sys.exc_info()[0])
			self.writeToLog("ERROR: Failed to run Myamiweb setup script (autoInstallSetup.php). ")
		else:
			if ( setupOpened ):
				self.writeToLog("Myamiweb Started.")
			else:
				print("ERROR: Failed to run Myamiweb setup script.")
				print("You may try running " + setupURL + " in your web browser. ")
				self.writeToLog("ERROR: Failed to run Myamiweb setup script (autoInstallSetup.php). ")
		
		subprocess.Popen("start-leginon.py")
		self.writeToLog("Leginon Started")
		
if __name__ == "__main__":
	a = CentosInstallation()
	a.run()
