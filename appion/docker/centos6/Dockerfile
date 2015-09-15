FROM centos:6
MAINTAINER Neil Voss <vossman77@yahoo.com>

### install epel
RUN yum -y install wget
RUN wget 'https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm'
RUN yum -y localinstall epel-release-latest-6.noarch.rpm

### install software
RUN yum -y install \
 python-tools python-devel python-matplotlib \
 subversion ImageMagick grace gnuplot \
 wxPython numpy scipy python-imaging \
 gcc-gfortran compat-gcc-34-g77 \
 gcc-objc fftw3-devel gsl-devel \
 mysql mysql-server MySQL-python \
 httpd php php-mysql phpMyAdmin  \
 gcc-c++ openmpi-devel libtiff-devel \
 php-devel gd-devel re2c fftw3-devel php-gd \
 xorg-x11-server-Xvfb netpbm-progs \
 libssh2-devel mlocate nano elinks firefox

RUN yum -y clean all
RUN updatedb

### MySQL setup
#RUN cp -fv /usr/share/mysql/my-huge.cnf /etc/my.cnf
#RUN svn co http://emg.nysbc.org/svn/myami/branches/myami-3.1/ myami-3.1/
RUN svn co http://emg.nysbc.org/svn/myami/branches/myami-3.1/install/ appion_install/
EXPORT 80
