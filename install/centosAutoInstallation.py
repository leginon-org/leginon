#!/usr/bin/env python

import os
import re
import sys
import shutil
import subprocess
import platform
import webbrowser

class CentosInstallation(object):

    def checkDistro(self):

        flavfile = "/etc/redhat-release"
        if not os.path.exists(flavfile):        
            print "This is not CentOS. Exiting installation..."
            return False

        f = open(flavfile, "r")
        flavor = f.readline().strip()
        f.close()

        if not flavor.startswith("CentOS"):
            print "This is not CentOS. Exiting installation..."
            return False

        print "Current OS Information: " + flavor

    def checkRoot(self):

        uid = os.getuid()
        if uid != 0:
            print "You must run this program as root. Exiting installation..."
            return False

        print "\"root\" access checked success..."


    def yumUpdate(self):
        print "Updating system files...."

        self.runCommand("rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/`uname -i`/epel-release-5-4.noarch.rpm")

        self.runCommand("yum -y update yum*")

        self.yumInstall(['yum-fastestmirror.noarch', 'yum-utils.noarch'])

        self.runCommand("yum -y update")

        self.runCommand("updatedb")

    def runCommand(self, cmd):
        print "#==================================================="
        print cmd
        print "#==================================================="

        proc = subprocess.Popen(cmd, shell=True)
        proc.wait()

    def yumInstall(self, packagelist):
        
        #arch = self.getMachineArch()
        if not packagelist:
            return
    
        packagestr = ""
        for package in packagelist:
            packagestr += " " + package

        cmd = "yum -y install" + packagestr
        self.runCommand(cmd)
        self.runCommand("updatedb")

    def openFirewallPort(self, port):
            
        self.runCommand("/sbin/iptables --insert RH-Firewall-1-INPUT --proto tcp --dport %d --jump ACCEPT"%(port))
        self.runCommand("/sbin/iptables-save > /etc/sysconfig/iptables")
        self.runCommand("/etc/init.d/iptables restart")

    def setupWebServer(self):
        
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
        sleep(1)

    def setupDBServer(self):
        self.mysqlYumInstall()

        # turn on auto mysql start
        self.runCommand("/sbin/chkconfig mysqld on")
        # start (restart) mysql server
        self.runCommand("/sbin/service mysqld restart")

        self.openFirewallPort(3306)
        
        # run database setup script.
        cmd = os.path.join(self.svnMyamiDir, 'install/newDBsetup.php -L %s -P %s -H %s -U %s -E %s'%(self.leginonDB, self.projectDB, self.dbHost, self.dbUser, self.adminEmail))
        cmd = 'php ' + cmd
        self.runCommand(cmd)
        sleep(1)
        return

    def setupProcessServer(self):

        self.processServerYumInstall()
        #TODO: missing the appion installation and setup.
        #TODO: Leginon config & sinedon config
        self.enableTorqueComputeNode()
        sleep(1)
        return

    def processServerYumInstall(self):

        packagelist = ['ImageMagick', 'MySQL-python', 'compat-gcc-34-g77', 'fftw3-devel', 'gcc-c++', 'gcc-gfortran', 'gcc-objc', 'gnuplot', 'grace', 'gsl-devel', 'libtiff-devel', 'netpbm-progs', 'numpy', 'openmpi-devel', 'python-devel', 'python-imaging', 'python-matplotlib', 'python-tools', 'scipy', 'wxPython', 'xorg-x11-server-Xvfb',]
        self.yumInstall(packagelist)

    def enableTorqueComputeNode(self):
        packagelist = ['torque-mom', 'torque-client',]
        self.yumInstall(packagelist)
        self.runCommand("/sbin/chkconfig pbs_mom on")
        
        f = open('/var/torque/mom_priv/config', 'w')
        f.write("$pbsserver localhost # running pbs_server on this host")
        f.close()

    def setupJobServer(self):
        
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

        # edit /var/hosts file
        self.editHosts()
        self.runCommand("/usr/share/doc/torque-2.3.10/torque.setup root")
    
        self.runCommand("/sbin/service network restart")
        self.runCommand("/sbin/service pbs_server start")
        self.runCommand("/sbin/service pbs_sched start")
        sleep(1)
        return

    def mysqlYumInstall(self):
        packagelist = ['mysql-server',]
        self.yumInstall(packagelist)
    
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

        cwd = os.getcwd()
        phpmrcdir = os.path.join(self.svnMyamiDir, "programs/php_mrc")
        os.chdir(phpmrcdir)
        self.runCommand("phpize")
        self.runCommand("./configure")
        self.runCommand("make")
        module = os.path.join(phpmrcdir, "modules/mrc.so")

        if not os.path.isfile(module):
            print"ERROR: mrc.so failed"
            sys.exit(1)

        self.runCommand("make install")
        f = open("/etc/php.d/mrc.ini", "w")
        f.write("; Enable mrc extension module\n")
        f.write("extension=mrc.so\n")
        f.close()
        os.chdir(cwd)

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
            print "ERROR ssh2.so failed"
            sys.exit(1)

        self.runCommand("make install")

        f = open('/etc/php.d/ssh2.ini', 'w')
        f.write('; Enable ssh2 extension module\n')
        f.write('extension=ssh2.so\n')
        f.close()
        os.chdir(cwd)

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

    def getMyami(self):
        # need to change to branch when release
        #cmd = "svn co http://ami.scripps.edu/svn/myami/branches/myami-2.0 /tmp/myami-2.0/"
        
        cmd = "svn co http://ami.scripps.edu/svn/myami/trunk " + self.svnMyamiDir

        self.runCommand(cmd)

    def selectInstallType(self):

        self.webServer = True
        self.databaseServer = True
        self.processingServer = True
        self.jobServer = True
        self.svnMyamiDir = '/tmp/myami/'
        self.enableLogin = 'false'
        self.dbHost = 'localhost'
        self.dbUser = 'root'
        self.dbPass = ''
        self.leginonDB = 'leginondb'
        self.projectDB = 'projectdb'
        self.adminEmail = ''
        self.csValue = ''
        self.mrc2any = '/usr/bin/mrc2any' # TODO: need to find this path..... 

        self.hostname = self.getServerName()
        self.nproc = self.getNumProcessors()

        print "===================================="
        print "1. Installing job submission server"
        print "2. Installing processing server"
        print "3. Installing database server"
        print "4. Installing web server"
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
    
    def run(self):

        result = self.checkDistro()
        if result is False:
            sys.exit(1)

        result = self.checkRoot()
        if result is False:
            sys.exit(1)

        result = self.selectInstallType()
        if result is False:
            sys.exit(1)

        self.yumUpdate()
        self.yumInstall(['subversion'])
        self.getMyami()
        
        if self.jobServer is True:
            self.setupJobServer()

        if self.processingServer is True:
            self.setupProcessServer()

        if self.databaseServer is True:
            self.setupDBServer()

        if self.webServer is True:
            self.setupWebServer()
        
        print ""
        print "Installation Successful."
        print ""
        
        webbrowser.open_new("http://localhost/myamiweb")

if __name__ == "__main__":
    a = CentosInstallation()
    a.run()
