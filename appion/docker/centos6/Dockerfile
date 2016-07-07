FROM centos:6
MAINTAINER Neil Voss <vossman77@yahoo.com>
#FIXME: CentOS 6.7 broken

### TODO install phpMyAdmin, submit jobs from the web

### install epel
RUN yum -y update && \
  yum -y install wget epel-release sudo passwd rsync tar openssh-clients && yum -y clean all
#RUN wget 'https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm'
#RUN yum -y localinstall epel-release-latest-6.noarch.rpm
### install software
RUN yum -y update && yum -y install \
 python-tools python-devel python-matplotlib \
 subversion ImageMagick grace gnuplot \
 wxPython numpy scipy python-imaging python-pip \
 gcc-gfortran compat-gcc-34-g77 libgfortran.x86_64 \
 gcc-objc fftw3-devel gsl-devel boost148-python PyQt4 \
 mysql mysql-server MySQL-python mod_python ftgl \
 httpd php php-mysql phpMyAdmin mod_ssl php-pecl-ssh2 \
 gcc-c++ libtiff-devel PyOpenGL python-argparse \
 php-devel gd-devel re2c fftw3-devel php-gd \
 xorg-x11-server-Xvfb netpbm-progs qiv python-requests \
 libssh2-devel mlocate nano elinks file \
 python-configparser \
 numactl compat-libgfortran && yum -y clean all
### Trying to do VNC
RUN yum -y update && yum -y install tigervnc-server xterm xsetroot fluxbox fbpanel && yum -y clean all
### Firefox
#RUN yum -y update && yum -y install mozilla-adblockplus firefox dbus && yum -y clean all
#RUN dbus-uuidgen > /var/lib/dbus/machine-id
RUN pip install --upgrade pip
RUN pip install joblib pyfftw3 fs scikit-learn==0.14
RUN python -c 'from sklearn import svm'

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
RUN sed -i.bak 's/max_allowed_packet = [0-9]*M/max_allowed_packet = 24M/' /etc/my.cnf
#RUN svn checkout http://emg.nysbc.org/svn/myami/branches/myami-3.2/ /emg/sw/myami/
RUN svn checkout http://emg.nysbc.org/svn/myami/trunk/ /emg/sw/myami/
#RUN svn checkout -r 19651 http://emg.nysbc.org/svn/myami/trunk/ /emg/sw/myami/
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
COPY particledata.dat /emg/sw/particledata.dat
RUN mkdir -p /var/cache/myami/redux/ && chmod 777 /var/cache/myami/redux/
RUN ln -sv /emg/sw/myami/appion/appionlib /usr/lib64/python2.6/site-packages/
RUN ln -sv /emg/sw/myami/redux/bin/reduxd /usr/bin/ && chmod 755 /usr/bin/reduxd
RUN for i in pyami imageviewer leginon pyscope sinedon redux; do ln -sv /emg/sw/myami/$i /usr/lib64/python2.6/site-packages/; done
#TODO compile radermacher libcv and numextension
WORKDIR /emg/sw/myami/modules/radermacher
RUN python ./setup.py install
WORKDIR /emg/sw/myami/modules/libcv
RUN python ./setup.py install
WORKDIR /emg/sw/myami/modules/numextension
RUN python ./setup.py install
WORKDIR /emg/sw/myami/redux
RUN python ./setup.py install
#RUN ./pysetup.sh install #disabled, because does not allow overriding via docker run
RUN mkdir /etc/fftw
RUN python /emg/sw/myami/pyami/fft/fftwsetup.py 2 4096 4096 && mv -v ~/fftw3-wisdom-* /etc/fftw/wisdom
RUN cp -v /emg/sw/myami/redux/init.d/reduxd /etc/init.d/reduxd
COPY findem64.exe /emg/sw/myami/appion/bin/
WORKDIR /emg/sw/myami/

#FIXME: mpirun does not run as root
ADD TGZ/xmipp_centos6_docker.tgz /emg/sw

### EMAN 1
ADD TGZ/eman-linux-x86_64-cluster-1.9.tar.gz /emg/sw
RUN mv -v /emg/sw/EMAN /emg/sw/eman1
RUN ln -sv /emg/sw/eman1/lib/libpyEM.so.ucs4.py2.6 /emg/sw/eman1/lib/libpyEM.so #FIX ME

### EMAN 2
### http://emg.nysbc.org/redmine/projects/appion/wiki/Install_EMAN2
ADD TGZ/eman2_centos6_docker.tgz /emg/sw/

### RELION
ADD TGZ/relion-1.4.tgz /emg/sw/

ADD TGZ/spidersmall.13.00.tgz /emg/sw
#RUN ln -sv /emg/sw/spider/bin/spider_linux_mp_opt64 /emg/sw/spider/bin/spider

RUN mkdir -p /emg/sw/grigorieff/bin
ADD TGZ/ctf_140609.tar.gz /emg/sw/grigorieff/
ADD TGZ/ctffind-4.0.16-linux64.tar.gz /emg/sw/grigorieff/
RUN mv -v /emg/sw/grigorieff/ctf /emg/sw/grigorieff/ctffind3
RUN mv -v /emg/sw/grigorieff/ctffind /emg/sw/grigorieff/bin/ctffind4
RUN ln -sv /emg/sw/grigorieff/ctffind3/ctffind3_mp.exe /emg/sw/grigorieff/bin/ctffind64.exe
RUN chmod 777 /emg/sw/grigorieff/ctffind3/ctffind3_mp.exe 
RUN chmod 777 /emg/sw/grigorieff/bin/ctffind4

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

COPY bashrc /etc/bashrc
#RUN mkdir -p /home/appionuser/.mozilla/firefox/yvn3wpn8.default
#COPY profiles.ini  /home/appionuser/.mozilla/firefox/
COPY startup.sh /emg/sw/startup.sh

#RUN yum -y update && yum -y install \
# fftw-devel gsl-devel hdf5-devel python-devel numpy \
# boost-devel freeglut ftgl-devel \
# mesa-libGLU-devel freetype-devel sip-devel\
# libjpeg-devel PyQt4-devel cmake ipython \
# libtiff-devel libpng-devel \
# PyOpenGL db4-devel python-argparse python-pip \
# && yum -y clean all
#RUN ln -sv /usr/lib64/libboost_python.so.5 /usr/lib64/libboost_python.so.1.52.0
#RUN ln -sv /usr/lib64/libtiff.so.3 /usr/lib64/libtiff.so.5
#RUN ln -sv /usr/lib64/libjpeg.so.62 /usr/lib64/libjpeg.so.8
#RUN ln -sv /usr/lib64/libhdf5.so.6 /usr/lib64/libhdf5.so.7
#RUN ln -sv /usr/lib64/libpng.so.3 /usr/lib64/libpng16.so.16
#RUN pip install bsddb3 ipython PyOpenGL

### copy the image data
COPY MRC/06jul12a/groel_template1.mrc /emg/data/leginon/06jul12a/templates/
COPY MRC/06jul12a/groel_template2.mrc /emg/data/leginon/06jul12a/templates/
COPY MRC/06jul12a/06jul12a_15gr_28sq_04hl_02em.mrc /emg/data/leginon/06jul12a/rawdata/
COPY MRC/06jul12a/06jul12a_15gr_28sq_11hl_03em.mrc /emg/data/leginon/06jul12a/rawdata/
COPY MRC/06jul12a/06jul12a_15gr_28sq_23hl_02em.mrc /emg/data/leginon/06jul12a/rawdata/
COPY MRC/06jul12a/06jul12a_15gr_28sq_23hl_04em.mrc /emg/data/leginon/06jul12a/rawdata/
COPY MRC/06jul12a/06jul12a_22gr_13sq_02hl_04em.mrc /emg/data/leginon/06jul12a/rawdata/
COPY MRC/06jul12a/06jul12a_22gr_13sq_03hl_05em.mrc /emg/data/leginon/06jul12a/rawdata/
COPY MRC/06jul12a/06jul12a_22gr_37sq_05hl_02em.mrc /emg/data/leginon/06jul12a/rawdata/
COPY MRC/06jul12a/06jul12a_22gr_37sq_05hl_05em.mrc /emg/data/leginon/06jul12a/rawdata/
COPY MRC/06jul12a/06jul12a_22gr_37sq_25hl_04em.mrc /emg/data/leginon/06jul12a/rawdata/
COPY MRC/06jul12a/06jul12a_22gr_37sq_25hl_05em.mrc /emg/data/leginon/06jul12a/rawdata/
COPY MRC/06jul12a/06jul12a_27gr_65sq_09hl_05em.mrc /emg/data/leginon/06jul12a/rawdata/
COPY MRC/06jul12a/06jul12a_35gr_63sq_12hl_04em.mrc /emg/data/leginon/06jul12a/rawdata/

### just double check that this directory is missing
RUN rm -fvr /emg/data/appion

RUN updatedb

CMD /emg/sw/startup.sh



