FROM centos:6
MAINTAINER Neil Voss <vossman77@yahoo.com>


### install epel
RUN yum -y update && yum -y install wget epel-release sudo passwd rsync && yum -y clean all
#RUN wget 'https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm'
#RUN yum -y localinstall epel-release-latest-6.noarch.rpm
### install software
RUN yum -y update && yum -y install \
 python-tools python-devel python-matplotlib \
 subversion ImageMagick grace gnuplot \
 wxPython numpy scipy python-imaging \
 gcc-gfortran compat-gcc-34-g77 \
 gcc-objc fftw3-devel gsl-devel \
 mysql mysql-server MySQL-python mod_python \
 httpd php php-mysql phpMyAdmin mod_ssl php-pecl-ssh2 \
 gcc-c++ openmpi-devel libtiff-devel \
 php-devel gd-devel re2c fftw3-devel php-gd \
 xorg-x11-server-Xvfb netpbm-progs \
 libssh2-devel mlocate nano elinks && yum -y clean all
### Trying to do VNC
RUN yum -y update && yum -y install tigervnc-server xterm xsetroot fluxbox fbpanel && yum -y clean all
RUN yum -y update && yum -y install mozilla-adblockplus firefox dbus && yum -y clean all
RUN dbus-uuidgen > /var/lib/dbus/machine-id
RUN easy_install joblib pyfftw3 fs

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

### MySQL setup
RUN cp -fv /usr/share/mysql/my-huge.cnf /etc/my.cnf
RUN svn co http://emg.nysbc.org/svn/myami/branches/myami-3.2/ /emg/sw/myami-3.2/
RUN svn co http://emg.nysbc.org/svn/myami/branches/myami-3.2/install/ /emg/sw/appion_install/ && echo 'appion_install'
RUN ln -sv /emg/sw/myami-3.2/myamiweb /var/www/html/ami
RUN ln -sv /emg/sw/myami-3.2/myamiweb /var/www/html/myamiweb
EXPOSE 3306

### Myami setup
COPY sinedon.cfg /etc/myami/sinedon.cfg
COPY leginon.cfg /etc/myami/leginon.cfg
COPY appion.cfg /etc/myami/appion.cfg
COPY redux.cfg /etc/myami/redux.cfg
COPY config.php /emg/sw/myami-3.2/myamiweb/config.php
COPY docker.sql /emg/sw/docker.sql
RUN mkdir -p /var/cache/myami/redux/ && chmod 777 /var/cache/myami/redux/
RUN ln -sv /emg/sw/myami-3.2/appion/appionlib /usr/lib64/python2.6/site-packages/
WORKDIR /emg/sw/myami-3.2/
RUN ./pysetup.sh install
RUN mkdir /etc/fftw
RUN python /usr/lib/python2.6/site-packages/pyami/fft/fftwsetup.py 2 4096 4096 && mv -v  ~/fftw3-wisdom-* /etc/fftw/wisdom
RUN cp -v /emg/sw/myami-3.2/redux/init.d/reduxd /etc/init.d/reduxd

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
env HOME /home/appionuser
#env HOME /
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

#ADD http://emg.nysbc.org/redmine/attachments/download/631/eman-linux-x86_64-cluster-1.9.tar.gz /emg/sw/eman1/
#ADD http://emg.nysbc.org/redmine/attachments/download/638/spidersmall.18.10.tar.gz /emg/sw/spider/

#ENV DISPLAY localhost:0
#RUN vncserver -kill :1

COPY bashrc /etc/bashrc
#RUN mkdir -p /home/appionuser/.mozilla/firefox/yvn3wpn8.default
#COPY profiles.ini  /home/appionuser/.mozilla/firefox/
COPY startup.sh /emg/startup.sh
CMD /emg/startup.sh

#CMD vncserver -autokill :1 -name vnc -geometry 1200x800 && /usr/sbin/httpd && /etc/init.d/mysqld start && mysql -u root < /emg/sw/myami-3.2/docker.sql && tail -f .vnc/*:1.log

#CMD ["vncserver", ":1", "-geometry 1200x800",  "-fg" ]
