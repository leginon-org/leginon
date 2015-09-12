FROM centos:7
MAINTAINER Neil Voss <vossman77@yahoo.com>

### install epel
RUN yum -y install wget yum-utils yum-plugin-fastestmirror
RUN wget 'https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm'
RUN yum -y localinstall epel-release-latest-7.noarch.rpm

### not best practice to update images
#RUN yum-config-manager --enable cr
#RUN yum -y update

### install needed software
RUN yum -y install bash-completion nano \
 subversion git screen ImageMagick \
 wxPython numpy scipy python-imaging \
 python-tools python-devel mysql \
 MySQL-python gcc-c++ libgomp \
 xorg-x11-server-Xvfb gsl \
 elinks libobjc \
 python-matplotlib gnuplot fftw \
 openmpi libjpeg libtiff \
 hdf5 colordiff netpbm-progs iotop \
 mpitests-openmpi fltk python-eyed3 \
 fftw-devel gcc-gfortran gcc-objc gd-devel gsl-devel \
 httpd libssh2-devel libtiff-devel openmpi-devel php php-devel \
 php-gd php-mysql phpMyAdmin 

RUN easy_install joblib
EXPOSE 80
