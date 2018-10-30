FROM centos:7
MAINTAINER Neil Voss <vossman77@yahoo.com>

#No package grace available.
#No package compat-gcc-34-g77 available.
#No package re2c available.
#No package compat-libgfortran available.

### install epel
RUN yum -y install epel-release
RUN yum -y install dnf
RUN dnf -y upgrade && dnf -y install wget epel-release sudo passwd rsync && dnf -y clean all
#RUN wget 'https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm'
#RUN dnf -y localinstall epel-release-latest-6.noarch.rpm
### install software
RUN dnf -y upgrade && dnf -y install \
 python-tools python-devel python-matplotlib \
 subversion ImageMagick gnuplot \
 wxPython numpy scipy python-imaging \
 gcc-gfortran \
 gcc-objc fftw3-devel gsl-devel \
 mariadb mariadb-server MySQL-python \
 httpd php php-mysql phpMyAdmin mod_ssl php-pecl-ssh2 \
 gcc-c++ openmpi-devel libtiff-devel \
 php-devel gd-devel fftw3-devel php-gd \
 xorg-x11-server-Xvfb netpbm-progs \
 libssh2-devel mlocate nano elinks file \
 numactl && dnf -y clean all
### Trying to do VNC
#RUN dnf -y upgrade && dnf -y install tigervnc-server xterm xsetroot fluxbox fbpanel && dnf -y clean all
RUN dnf -y upgrade && dnf -y install tigervnc-server xterm xsetroot xfwm4 xfce4-session \
 && dnf -y clean all
#RUN dnf -y upgrade && dnf -y install mozilla-adblockplus firefox dbus && dnf -y clean all
RUN dbus-uuidgen > /var/lib/dbus/machine-id
RUN easy_install joblib pyfftw3 fs milk #FIXME check to see if in dnf

RUN updatedb

#VOLUME /emg/sw
RUN mkdir -p /emg/data  && echo 'mkdir /emg/data'
RUN mkdir -p /emg/sw && echo 'mkdir /emg/sw'
RUN chmod 777 -R /emg  && echo 'chmod 777'

### Apache setup
COPY php.ini /etc/php.ini
COPY httpd.conf /etc/httpd/conf/httpd.conf
COPY info.php /var/www/html/info.php
RUN chmod 444 /var/www/html/info.php && echo 'chmod info.php'
EXPOSE 80

### MariaDB setup
#RUN find /usr/share/mysql/ -type f
#RUN ls -d /usr/share/*/
#RUN cp -fv /usr/share/mysql/my-huge.cnf /etc/my.cnf
#RUN svn co http://emg.nysbc.org/svn/myami/branches/myami-3.2/ /emg/sw/myami/
RUN svn co http://emg.nysbc.org/svn/myami/trunk/ /emg/sw/myami/
RUN ln -sv /emg/sw/myami/myamiweb /var/www/html/ami
RUN ln -sv /emg/sw/myami/myamiweb /var/www/html/myamiweb
#EXPOSE 3306

### Myami setup
COPY sinedon.cfg /etc/myami/sinedon.cfg
COPY leginon.cfg /etc/myami/leginon.cfg
COPY appion.cfg /etc/myami/appion.cfg
COPY redux.cfg /etc/myami/redux.cfg
COPY config.php /emg/sw/myami/myamiweb/config.php
COPY docker.sql /emg/sw/docker.sql
RUN mkdir -p /var/cache/myami/redux/ && chmod 777 /var/cache/myami/redux/
RUN ln -sv /emg/sw/myami/appion/appionlib /usr/lib64/python2.7/site-packages/
WORKDIR /emg/sw/myami/
RUN ./pysetup.sh install
RUN mkdir /etc/fftw
RUN python /usr/lib/python2.7/site-packages/pyami/fft/fftwsetup.py 2 4096 4096 && mv -v  ~/fftw3-wisdom-* /etc/fftw/wisdom
RUN cp -v /emg/sw/myami/redux/init.d/reduxd /etc/init.d/reduxd

#ADD Xmipp-2.4-src.tar.gz /emg/sw
#RUN mv -v /emg/sw/Xmipp-2.4-src /emg/sw/xmipp 
#WORKDIR /emg/sw/xmipp
#ENV MPIPATH /usr/lib64/openmpi
#ENV PATH /bin:/usr/bin:/sbin:/usr/sbin:/usr/lib64/openmpi/bin
#RUN ./scons.configure MPI_LIBDIR=/usr/lib64/openmpi/lib  MPI_LIB=mpi  MPI_INCLUDE=/usr/include/openmpi-x86_64
#RUN ./scons.compile
#FIXME: mpirun does not run as root

ADD eman-linux-x86_64-cluster-1.9.tar.gz /emg/sw
RUN mv -v /emg/sw/EMAN /emg/sw/eman1
RUN ls /emg/sw/eman1/lib/
RUN ln -sv /emg/sw/eman1/lib/libpyEM.so.ucs4.py2.6 /emg/sw/eman1/lib/libpyEM.so #FIXME

ADD spidersmall.13.00.tgz /emg/sw
#RUN ln -sv /emg/sw/spider/bin/spider_linux_mp_opt64 /emg/sw/spider/bin/spider

RUN mkdir -p /emg/sw/grigorieff/bin
ADD ctf_140609.tar.gz /emg/sw/grigorieff/
ADD ctffind-4.0.16-linux64.tar.gz /emg/sw/grigorieff/
RUN mv -v /emg/sw/grigorieff/ctf /emg/sw/grigorieff/ctffind3
RUN mv -v /emg/sw/grigorieff/ctffind /emg/sw/grigorieff/bin/ctffind4
RUN ln -sv /emg/sw/grigorieff/ctffind3/ctffind3_mp.exe /emg/sw/grigorieff/bin/ctffind64.exe
RUN chmod 777 /emg/sw/grigorieff/ctffind3/ctffind3_mp.exe 
RUN chmod 777 /emg/sw/grigorieff/bin/ctffind4

### software
COPY 06jul12a_00015gr_00028sq_00004hl_00002en.mrc /emg/data/leginon/06jul12a/rawdata/
COPY 06jul12a_00015gr_00028sq_00023hl_00002en.mrc /emg/data/leginon/06jul12a/rawdata/
COPY 06jul12a_00015gr_00028sq_00023hl_00004en.mrc /emg/data/leginon/06jul12a/rawdata/
COPY 06jul12a_00022gr_00013sq_00002hl_00004en.mrc /emg/data/leginon/06jul12a/rawdata/
COPY 06jul12a_00022gr_00013sq_00003hl_00005en.mrc /emg/data/leginon/06jul12a/rawdata/
COPY 06jul12a_00022gr_00037sq_00025hl_00004en.mrc /emg/data/leginon/06jul12a/rawdata/
COPY 06jul12a_00022gr_00037sq_00025hl_00005en.mrc /emg/data/leginon/06jul12a/rawdata/
COPY 06jul12a_00035gr_00063sq_00012hl_00004en.mrc /emg/data/leginon/06jul12a/rawdata/

### Change to local user
#RUN mkdir -p /home/appionuser
RUN useradd -d /home/appionuser -g 100 -p 'Phys-554' -s /bin/bash appionuser && echo 'appionuser' && usermod -aG wheel appionuser
RUN chmod 777 /home/appionuser
RUN chown -R appionuser:users /home/appionuser
#USER appionuser
ENV HOME /home/appionuser
WORKDIR /home/appionuser
RUN mkdir -p .vnc
RUN chmod 777 .vnc
RUN echo Phys-554 | vncpasswd -f > .vnc/passwd
RUN chmod 600 .vnc/passwd
RUN ls .vnc/
COPY xstartup .vnc/xstartup
RUN mkdir -p .config/fbpanel
COPY fbpanel-default .config/fbpanel/default
RUN ls .vnc/
USER root
RUN chown -R appionuser:users /home/appionuser
#USER appionuser
RUN chmod 700 .vnc/xstartup
EXPOSE 5901

#ADD mysql.tgz /var/lib/mysql/
COPY bashrc /etc/bashrc
#RUN mkdir -p /home/appionuser/.mozilla/firefox/yvn3wpn8.default
#COPY profiles.ini  /home/appionuser/.mozilla/firefox/
COPY startup.sh /emg/sw/startup.sh
RUN updatedb

CMD /emg/sw/startup.sh



