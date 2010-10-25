#!/usr/bin/env python

import os
import re
import sys
import shutil
import subprocess
import platform
import webbrowser
import stat
import time

class CentosInstallation(object):

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

    def checkRoot(self):

        uid = os.getuid()
        if uid != 0:
            print "You must run this program as root. Exiting installation..."
            self.writeToLog("ERROR: root access checked deny ---")
            return False

        print "\"root\" access checked success..."
        self.writeToLog("root access checked success")


    def yumUpdate(self):
        print "Updating system files...."

        self.runCommand("rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/`uname -i`/epel-release-5-4.noarch.rpm")

        self.runCommand("yum -y update yum*")

        self.yumInstall(['yum-fastestmirror.noarch', 'yum-utils.noarch'])

        self.runCommand("yum -y update")

        #self.runCommand("updatedb")
        self.writeToLog("yum update finished..")

    def runCommand(self, cmd):
        
        self.writeToLog("#===================================================")
        self.writeToLog("Run the following Command:")
        self.writeToLog("%s"%(cmd,))
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
            
        self.runCommand("/sbin/iptables --insert RH-Firewall-1-INPUT --proto tcp --dport %d --jump ACCEPT"%(port))
        self.runCommand("/sbin/iptables-save > /etc/sysconfig/iptables")
        self.runCommand("/etc/init.d/iptables restart")
        self.writeToLog("firewall port %d opened"%(port))

    def setupWebServer(self):
        self.writeToLog("--- Start install Web Server")
        
        packagelist = ['fftw3-devel', 'gcc', 'httpd', 'libssh2-devel', 'php', 'php-mysql', 'phpMyAdmin.noarch', 'php-devel', 'php-gd',]
        self.yumInstall(packagelist)

        self.editPhpIni()
        self.editApacheConfig()
        
        self.installPhpMrc()
        self.installPhpSsh2()
        self.installMyamiWeb()
        self.editMyamiWebConfig()
        
        self.runCommand("/sbin/service httpd stop")
        self.runCommand("/sbin/service httpd start")
        self.runCommand("/sbin/chkconfig httpd on")
        self.openFirewallPort(80)
        return True

    def setupDBServer(self):
        self.writeToLog("--- Start install Database Server")

        self.mysqlYumInstall()
        # turn on auto mysql start

        self.runCommand("/sbin/chkconfig mysqld on")
        
        # start (restart) mysql server
        self.runCommand("/sbin/service mysqld restart")
        
        # run database setup script.
        cmd = os.path.join(self.svnMyamiDir, 'install/newDBsetup.php -L %s -P %s -H %s -U %s -E %s'%(self.leginonDB, self.projectDB, self.dbHost, self.dbUser, self.adminEmail))
        cmd = 'php ' + cmd

        self.runCommand(cmd)

        self.openFirewallPort(3306)
        return True

    def setupProcessServer(self):
        self.writeToLog("--- Start install Processing Server")

        self.processServerYumInstall()
        
        # install all the myami python packages except appion.
        os.chdir(self.svnMyamiDir)
        self.runCommand('./pysetup.sh install')

        # install the appion python packages
        os.chdir(self.svnMyamiDir + 'appion')
        self.runCommand('python setup.py install')
        
        # setup Leginon configure file
        self.writeToLog("setup Leginon configure file")
        leginonDir = self.runCommand('python -c "import leginon; print leginon.__path__[0]"')        
        leginonDir = leginonDir.strip()
        self.setupLeginonCfg(leginonDir + '/config')

        # setup Sinedon configure file
        self.writeToLog("setup Sinedon configure file")
        sinedonDir = self.runCommand('python -c "import sinedon; print sinedon.__path__[0]"')
        sinedonDir = sinedonDir.strip()
        self.setupSinedonCfg(sinedonDir)

        # setup instruments configuration
        pyscopeDir = self.runCommand('python -c "import pyscope; print pyscope.__path__[0]"')
        pyscopeDir = pyscopeDir.strip()

        self.setupPyscopeCfg(pyscopeDir)

        os.chdir(self.currentDir)        
        self.enableTorqueComputeNode()
        return True

    def setupJobServer(self):
        self.writeToLog("--- Start install Job Server")

        packagelist = ['torque-server', 'torque-scheduler',]
        self.yumInstall(packagelist)

        
        self.runCommand("/sbin/chkconfig pbs_server on")
        self.runCommand("/sbin/chkconfig pbs_sched on")

        f = open('/var/torque/server_priv/nodes', 'w')
        f.write("%s np=%d"%(self.hostname, self.nproc))
        f.close()

        f = open('/var/torque/server_name', 'w')
        f.write("%s"%(self.hostname))
        f.close()

        self.runCommand("/sbin/service pbs_server start")
        self.runCommand("/sbin/service pbs_sched start")
        # edit /var/hosts file
        self.editHosts()
        self.runCommand('qmgr -c "s s scheduling=true"')
        self.runCommand('qmgr -c "c q batch queue_type=execution"')
        self.runCommand('qmgr -c "s q batch started=true"')
        self.runCommand('qmgr -c "s q batch enabled=true"')
        self.runCommand('qmgr -c "s q batch resources_default.nodes=1"')
        self.runCommand('qmgr -c "s q batch resources_default.walltime=3600"')
        self.runCommand('qmgr -c "s s default_queue=batch"')
    
        self.runCommand("/sbin/service network restart")


        return True

    def processServerYumInstall(self):

        packagelist = ['ImageMagick', 'MySQL-python', 'compat-gcc-34-g77', 'fftw3-devel', 'gcc-c++', 'gcc-gfortran', 'gcc-objc', 'gnuplot', 'grace', 'gsl-devel', 'libtiff-devel', 'netpbm-progs', 'numpy', 'openmpi-devel', 'python-devel', 'python-imaging', 'python-matplotlib', 'python-tools', 'scipy', 'wxPython', 'xorg-x11-server-Xvfb',]
        self.yumInstall(packagelist)

    def enableTorqueComputeNode(self):
        packagelist = ['torque-mom', 'torque-client',]
        self.yumInstall(packagelist)
        self.runCommand("/sbin/chkconfig pbs_mom on")
        
        f = open('/var/torque/mom_priv/config', 'w')
        f.write("$pbsserver localhost # running pbs_server on this host")
        self.runCommand("/sbin/chkconfig pbs_mon on")
        self.runCommand("/sbin/service pbs_mom start")
        
        f.close()

    def mysqlYumInstall(self):
        packagelist = ['mysql-server', 'php', 'php-mysql',]
        self.yumInstall(packagelist)
    
    def setupLeginonCfg(self, leginonCfgDir):
        inf = open(leginonCfgDir + '/default.cfg', 'r')
        outf = open(leginonCfgDir + '/leginon.cfg', 'w')

        for line in inf:
            if line.startswith('path:'):
                outf.write('path: %s/leginon\n'%(self.imagesDir))
            else:
                outf.write(line)
        inf.close()
        outf.close()

    def setupPyscopeCfg(self, pyscopeCfgDir):
        shutil.copy(pyscopeCfgDir +'/instruments.cfg.template', pyscopeCfgDir +'/instruments.cfg')


    def setupSinedonCfg(self, sinedonDir):
        inf = open(self.svnMyamiDir + 'sinedon/examples/sinedon.cfg', 'r')
        outf = open(sinedonDir + '/sinedon.cfg', 'w')

        for line in inf:
            if line.startswith('user: usr_object'):
                outf.write('user: root\n')
            else:
                outf.write(line)
        inf.close()
        outf.close()        

    def editHosts(self):

        # make a back up file
        shutil.copy('/etc/hosts', '/etc/hosts-tmp')
        inf = open('/etc/hosts-tmp', 'r')
        outf = open('/etc/hosts', 'w')

        for line in inf:
            line = line.rstrip()
            if "127.0.0.1" in line:
                outf.write("127.0.0.1        %s localhost.localdomain localhost\n"%(self.hostname))
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
                outf.write("error_reporting = E_ALL & ~E_NOTICE\n")
            elif line.startswith('display_error'):
                outf.write("display_error = On\n")
            elif line.startswith('register_argc_argv'):
                outf.write("register_argc_argv = On\n")
            elif line.startswith('short_open_tag'):
                outf.write("short_open_tag = On\n")
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
        outf.write('max_input_time = 300     ; Maximum amout of time to spend parsing request data\n')
        outf.write('memory_limit = 1024M     ; Maximum amount of memory a script may consume\n')
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
                outf.write("DirectoryIndex index.html index.php\n")
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

        phpmrcdir = os.path.join(self.svnMyamiDir, "programs/php_mrc")
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

    def installPhpSsh2(self):
        if os.path.isfile("/etc/php.d/ssh2.ini"):
            return
        
        cwd = os.getcwd()
        self.runCommand("wget -c http://pecl.php.net/get/ssh2-0.11.0.tgz")
        self.runCommand("tar zxvf ssh2-0.11.0.tgz")
        sshdir = os.path.join(cwd, "ssh2-0.11.0")
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
        svnMyamiwebDir = os.path.join(self.svnMyamiDir, "myamiweb")
        centosWebDir = "/var/www/html"
        self.runCommand("cp -rf %s %s"%(svnMyamiwebDir, centosWebDir))

    def editMyamiWebConfig(self):
    
        configFile = os.path.join("/var/www/html/myamiweb/config.php")

        inf = open(configFile+".template", 'r')
        outf = open(configFile, 'w')

        for line in inf:
            line = line.rstrip()
            if line.startswith('// --- ') or len(line) == 0:
                outf.write(line + "\n")
            elif line.startswith("define('ENABLE_LOGIN'"):
                outf.write("define('ENABLE_LOGIN', %s);\n"%(self.enableLogin))
            elif line.startswith("define('DB_HOST'"):
                outf.write("define('DB_HOST', '%s');\n"%(self.dbHost))
            elif line.startswith("define('DB_USER'"):
                outf.write("define('DB_USER', '%s');\n"%(self.dbUser))
            elif line.startswith("define('DB_PASS'"):
                outf.write("define('DB_PASS', '%s');\n"%(self.dbPass))
            elif line.startswith("define('ADMIN_EMAIL'"):
                outf.write("define('ADMIN_EMAIL', '%s');\n"%(self.adminEmail))
            elif line.startswith("define('DB_LEGINON'"):
                outf.write("define('DB_LEGINON', '%s');\n"%(self.leginonDB))
            elif line.startswith("define('DB_PROJECT'"):
                outf.write("define('DB_PROJECT', '%s');\n"%(self.projectDB))
            elif line.startswith("define('MRC2ANY'"):
                outf.write("define('MRC2ANY', '%s');\n"%(self.mrc2any))
            elif "addplugin(\"processing\");" in line:
                outf.write("addplugin(\"processing\");\n")
            elif "// $PROCESSING_HOSTS[]" in line:
                outf.write("$PROCESSING_HOSTS[] = array('host' => '%s', 'nproc' => %d);\n"%(self.dbHost, self.nproc))
            elif "// $CLUSTER_CONFIGS[]" in line:
                outf.write("$CLUSTER_CONFIGS[] = 'default_cluster';\n")
            elif line.startswith("define('TEMP_IMAGES_DIR', "):
                outf.write("define('TEMP_IMAGES_DIR', '/tmp');\n")
            elif line.startswith("define('DEFAULTCS', "):
                outf.write("define('DEFAULTCS', '%.1f');\n"%(self.csValue))        
            else:
                outf.write(line + '\n')

        inf.close()
        outf.close()

    def writeToLog(self, message):
        logfile = open(self.currentDir + "/" + self.logFilename, 'a')
        logfile.write(message + '\n')
        logfile.close()
            
    def getMyami(self):
        # need to change to branch when release
        #cmd = "svn co http://ami.scripps.edu/svn/myami/branches/myami-2.0 /tmp/myami-2.0/"
        
        cmd = "svn co http://ami.scripps.edu/svn/myami/trunk " + self.svnMyamiDir

        self.runCommand(cmd)

    def getDefaultValues(self):

        print "===================================="
        print "Installing job submission server"
        print "Installing processing server"
        print "Installing database server"
        print "Installing web server"
        print "===================================="
        print ""
        value = raw_input("Please enter an email address: ")
        value = value.strip()

        self.adminEmail = value

        print ""
        print "What is the spherical aberration (Cs) constant for the microsope (in millimeters)."
        print "Example : 2.0"
        print ""
        value = raw_input("Please enter the spherical aberration (Cs) value : ")
        value = float (value.strip())

        self.csValue = value
        
        print ""
        print "Auto installtion required your system root password."
        print ""        
        password = raw_input("Please enter the system root password : ")
        password = password.strip()
        self.serverRootPass = password
        
    def downloadSampleImages(self):
       
        getImageCmd = "wget -P/tmp/images http://ami.scripps.edu/redmine/attachments/download/112/06jul12a_00015gr_00028sq_00004hl_00002en.mrc http://ami.scripps.edu/redmine/attachments/download/113/06jul12a_00015gr_00028sq_00023hl_00002en.mrc http://ami.scripps.edu/redmine/attachments/download/114/06jul12a_00015gr_00028sq_00023hl_00004en.mrc http://ami.scripps.edu/redmine/attachments/download/115/06jul12a_00022gr_00013sq_00002hl_00004en.mrc http://ami.scripps.edu/redmine/attachments/download/116/06jul12a_00022gr_00013sq_00003hl_00005en.mrc http://ami.scripps.edu/redmine/attachments/download/109/06jul12a_00022gr_00037sq_00025hl_00004en.mrc http://ami.scripps.edu/redmine/attachments/download/110/06jul12a_00022gr_00037sq_00025hl_00005en.mrc http://ami.scripps.edu/redmine/attachments/download/111/06jul12a_00035gr_00063sq_00012hl_00004en.mrc"

        print getImageCmd
        proc = subprocess.Popen(getImageCmd, shell=True)
        proc.wait()
        
    def run(self):

        self.currentDir = os.getcwd()
        self.logFilename = 'installation.log'
        self.svnMyamiDir = '/tmp/myami/'
        self.enableLogin = 'false'
        self.dbHost = 'localhost'
        self.dbUser = 'root'
        self.dbPass = ''
        self.serverRootPass = ''
        self.leginonDB = 'leginondb'
        self.projectDB = 'projectdb'
        self.adminEmail = ''
        self.csValue = ''
        self.mrc2any = '/usr/bin/mrc2any'
        self.imagesDir = '/myamiImages'

        self.hostname = self.getServerName()
        self.nproc = self.getNumProcessors()
        
        if os.path.isfile(self.logFilename):
            self.writeToLog("remove old log file")
            os.remove(self.logFilename)
        
        if not os.path.exists(self.imagesDir):
            self.writeToLog("create images folder - /myamiImages")
            os.makedirs(self.imagesDir, 0744)
        else:
            os.chmod(self.imagesDir, 0744)

        if not os.path.exists(os.path.join(self.imagesDir, "Leginon")):
            os.makedirs(os.path.join(self.imagesDir, "Leginon"), 0777)
        else:
            os.chmod(os.path.join(self.imagesDir, "Leginon"), 0777)
                
        if not os.path.exists(os.path.join(self.imagesDir, "Appion")):
            os.makedirs(os.path.join(self.imagesDir, "Appion"), 0777)
        else:
            os.chmod(os.path.join(self.imagesDir, "Appion"), 0777)

        result = self.checkDistro()
        if result is False:
            sys.exit(1)
        
        result = self.checkRoot()
        if result is False:
            sys.exit(1)

        result = self.getDefaultValues()
        if result is False:
            sys.exit(1)

        self.yumUpdate()
        self.yumInstall(['subversion'])
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
            
        self.downloadSampleImages()

        self.writeToLog("Installation Finish.")

        print("========================")
        print("Installation Finish.")
        print("========================")
        
        setupURL = "http://localhost/myamiweb/setup/autoInstallSetup.php?password=" + self.serverRootPass
        webbrowser.open_new(setupURL)
        self.writeToLog("Myamiweb Started.")
        
        subprocess.Popen("start-leginon.py")
        self.writeToLog("Leginon Started")
        
if __name__ == "__main__":
    a = CentosInstallation()
    a.run()
