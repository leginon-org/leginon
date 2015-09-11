FROM centos:7
MAINTAINER Neil Voss <vossman77@yahoo.com>
RUN yum -y remove deltarpm
RUN yum -y update
RUN yum -y install wget
RUN wget 'https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm'
RUN yum -y localinstall epel-release-latest-7.noarch.rpm
RUN yum -y install bash-completion nano \
 subversion git screen ImageMagick \
 wxPython numpy scipy python-imaging \
 python-tools python-devel mysql \
 MySQL-python gcc-c++ libgomp \
 xorg-x11-server-Xvfb gsl \
 elinks libobjc \
 yum-plugin-fastestmirror yum-fastestmirror \
 python-matplotlib gnuplot fftw \
 openmpi libjpeg libtiff compat-libf2c-34 \
 fftw2 hdf5 colordiff netpbm-progs iotop \
 mpitests-openmpi fltk \
 yum-utils python-eyed3 
#opendyslexic-fonts grace python-joblib
RUN yum -y install fftw-devel gcc-gfortran gcc-objc gd-devel gsl-devel \
 httpd libssh2-devel libtiff-devel openmpi-devel php php-devel \
 php-gd php-mysql phpMyAdmin 
RUN yum-config-manager --enable cr
