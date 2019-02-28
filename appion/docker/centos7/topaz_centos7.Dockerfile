FROM centos:7
MAINTAINER Neil Voss <vossman77@gmail.com>

### install epel
RUN yum -y install epel-release
RUN yum -y upgrade \
  && yum -y install wget epel-release sudo passwd rsync tar openssh-clients && yum -y clean all

### install software
RUN yum -y upgrade && yum -y install \
 python-tools python-devel python-matplotlib \
 ImageMagick grace gnuplot bash-completion colordiff \
 wxPython python2-pip  \
 gcc-gfortran opencv-python \
 gcc-objc fftw3-devel gsl-devel boost148-python PyQt4 \
 mariadb mariadb-server MySQL-python ftgl \
 httpd php php-mysql mod_ssl php-pecl-ssh2 \
 gcc-c++ libtiff-devel PyOpenGL python-argparse \
 php-devel gd-devel fftw3-devel php-gd \
 xorg-x11-server-Xvfb netpbm-progs python-requests \
 libssh2-devel mlocate nano elinks file \
 python-configparser h5py git pyflakes \
 gtkglext-libs pangox-compat `#protomo specific pkgs` \
 numactl && yum -y clean all

RUN sed -i.bak 's/max_allowed_packet = [0-9]*M/max_allowed_packet = 24M/' /etc/nanorc

## Appion specific installs
#RUN yum -y upgrade && yum -y install mozilla-adblockplus firefox dbus && yum -y clean all
RUN dbus-uuidgen > /var/lib/dbus/machine-id
RUN pip install --upgrade pip
RUN yum -y remove numpy
RUN pip install joblib pyfftw3 fs==0.5.4 \
  torch==0.3.1 torchvision==0.1.9 numpy==1.11 scipy==0.19.1 pandas==0.20.3 scikit-learn==0.19.0
RUN python -c 'from sklearn import svm' # test for function

RUN updatedb

#VOLUME /emg/sw
RUN mkdir -p /emg/data  && echo 'mkdir /emg/data'
RUN mkdir -p /emg/sw && echo 'mkdir /emg/sw'
RUN chmod 777 -R /emg  && echo 'chmod 777'

### Apache setup
COPY php.ini /etc/php.ini
#COPY httpd.conf /etc/httpd/conf/httpd.conf
COPY info.php /var/www/html/info.php
RUN chmod 444 /var/www/html/info.php && echo 'chmod info.php'
EXPOSE 80

### MariaDB setup
#RUN cp -fv /usr/share/mysql/my-huge.cnf /etc/my.cnf
RUN sed -i.bak 's/max_allowed_packet = [0-9]*M/max_allowed_packet = 24M/' /etc/my.cnf
RUN mysql_install_db --user=mysql --ldata=/var/lib/mysql/
#EXPOSE 3306

### Myami setup
RUN git clone -b myami-3.3 http://emg.nysbc.org/git/myami.git /emg/sw/myami/
RUN git clone https://github.com/tbepler/topaz /emg/sw/topaz/
RUN pip install /emg/sw/topaz/
RUN ln -sv /emg/sw/myami/myamiweb /var/www/html/ami
RUN ln -sv /emg/sw/myami/myamiweb /var/www/html/myamiweb

COPY sinedon.cfg /etc/myami/sinedon.cfg
COPY leginon.cfg /etc/myami/leginon.cfg
COPY instruments.cfg /etc/myami/instruments.cfg
COPY appion.cfg /etc/myami/appion.cfg
COPY redux.cfg /etc/myami/redux.cfg
COPY config.php /emg/sw/myami/myamiweb/config.php
COPY docker-innodb.sql /emg/sw/docker.sql
COPY particledata.dat /emg/sw/particledata.dat
RUN mkdir -p /var/cache/myami/redux/ && chmod 777 /var/cache/myami/redux/
RUN ln -sv /emg/sw/myami/appion/appionlib /usr/lib64/python2.7/site-packages/
RUN ln -sv /emg/sw/myami/redux/bin/reduxd /usr/bin/ && chmod 755 /usr/bin/reduxd
RUN for i in pyami imageviewer leginon pyscope sinedon redux; \
	do ln -sv /emg/sw/myami/$i /usr/lib64/python2.7/site-packages/; done

### Compile radermacher, libcv, numextension, and redux
WORKDIR /emg/sw/myami/modules/radermacher
RUN python ./setup.py install
WORKDIR /emg/sw/myami/modules/libcv
RUN python ./setup.py install
WORKDIR /emg/sw/myami/modules/numextension
RUN python ./setup.py install
WORKDIR /emg/sw/myami/redux
RUN python ./setup.py install

RUN mkdir /etc/fftw
RUN python /emg/sw/myami/pyami/fft/fftwsetup.py 2 4096 4096 && mv -v ~/fftw3-wisdom-* /etc/fftw/wisdom
RUN cp -v /emg/sw/myami/redux/init.d/reduxd /etc/init.d/reduxd
COPY findem-docker-centos7/findem64.exe /emg/sw/myami/appion/bin/
WORKDIR /emg/sw/myami/

### EMAN 1
ADD TGZ/eman-linux-x86_64-cluster-1.9.tar.gz /emg/sw
RUN mv -v /emg/sw/EMAN /emg/sw/eman1
RUN ln -sv /emg/sw/eman1/lib/libpyEM.so.ucs4.py2.6 /emg/sw/eman1/lib/libpyEM.so #FIX ME

### RELION
ADD TGZ/relion-1.4.tgz /emg/sw/

### Trying to do VNC
#RUN yum -y upgrade && yum -y install  \
# ftp://ftp.pbone.net/mirror/ftp.scientificlinux.org/linux/scientific/6.5/x86_64/os/Packages/xorg-x11-twm-1.0.3-5.1.el6.x86_64.rpm \
# && yum -y clean all
RUN yum -y upgrade && yum -y install \
 tigervnc-server xterm xsetroot fluxbox \
 xorg-x11-xinit xorg-x11-font-utils xorg-x11-fonts-Type1 xorg-x11-xauth  \
 libX11-common libX11 dbus-x11 xorg-x11-server-utils xorg-x11-xkb-utils \
 xorg-x11-fonts-75dpi xorg-x11-fonts-100dpi xorg-x11-fonts-misc \
 && yum -y clean all

### Change to local user
#RUN mkdir -p /home/appionuser
RUN useradd -d /home/appionuser -g 100 -p 'Phys-554' -s /bin/bash appionuser && echo 'appionuser' && usermod -aG wheel appionuser
RUN chmod 777 /home/appionuser
RUN chown -R appionuser:users /home/appionuser
#USER appionuser
ENV HOME /home/appionuser
WORKDIR /home/appionuser
RUN mkdir -p .vnc
RUN touch .Xauthority
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

### copy the image data
COPY findem-docker-centos7/groel_template1.mrc /emg/data/leginon/06jul12a/templates/
COPY findem-docker-centos7/groel_template2.mrc /emg/data/leginon/06jul12a/templates/
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
RUN chown -R appionuser:users /emg/data

### just double check that this directory is missing
RUN rm -fvr /emg/data/appion

RUN updatedb

CMD /emg/sw/startup.sh



