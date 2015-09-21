FROM centos:6
MAINTAINER Neil Voss <vossman77@yahoo.com>


### install epel
RUN yum -y update && yum -y install wget epel-release sudo passwd
#RUN wget 'https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm'
#RUN yum -y localinstall epel-release-latest-6.noarch.rpm
### install software
RUN yum -y update && yum -y install \
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
 libssh2-devel mlocate nano elinks
### Trying to do VNC
RUN yum -y update && yum -y install tigervnc-server xterm xsetroot fluxbox fbpanel
RUN yum -y update && yum -y install mozilla-adblockplus firefox dbus
RUN dbus-uuidgen > /var/lib/dbus/machine-id
RUN easy_install joblib

RUN yum -y clean all
RUN updatedb

VOLUME /emg/sw
RUN mkdir -p /emg/data
RUN mkdir -p /emg/sw
RUN chmod 777 -R /emg

### MySQL setup
RUN cp -fv /usr/share/mysql/my-huge.cnf /etc/my.cnf
#RUN svn co http://emg.nysbc.org/svn/myami/branches/myami-3.1/ /emg/sw/myami-3.1/
RUN svn co http://emg.nysbc.org/svn/myami/branches/myami-3.1/install/ /emg/sw/appion_install/
EXPOSE 80

### Change to local user
#RUN mkdir -p /home/appionuser
RUN useradd -d /home/appionuser -g 100 -p 'Phys-554' -s /bin/bash appionuser && echo 'appionuser' && usermod -aG wheel appionuser
RUN chmod 777 /home/appionuser
RUN chown -R appionuser:users /home/appionuser
#USER appionuser
env HOME /home/appionuser
#env HOME /
WORKDIR /home/appionuser
RUN mkdir -p .vnc
RUN chmod 777 .vnc
RUN echo AppionRules | vncpasswd -f > .vnc/passwd
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

#ENV DISPLAY localhost:0
#RUN vncserver -kill :1
CMD vncserver :1 -name vnc -geometry 1200x800 && tail -f .vnc/*:1.log
#CMD ["vncserver", ":1", "-geometry 1200x800",  "-fg" ]
