FROM centos:7
MAINTAINER Neil Voss <vossman77@gmail.com>

### install epel
RUN yum -y --nogpgcheck install epel-release
RUN yum -y upgrade \
  && yum -y install wget sudo passwd rsync tar openssh-clients && yum -y clean all

RUN yum clean all

### install software
RUN yum -y upgrade && yum -y install \
 python-tools python-devel python-matplotlib \
 ImageMagick grace gnuplot bash-completion colordiff \
 wxPython numpy scipy python-imaging  \
 gcc-gfortran opencv-python \
 gcc-objc fftw3-devel gsl-devel boost148-python PyQt4 \
 MySQL-python ftgl \
 gcc-c++ libtiff-devel PyOpenGL python-argparse \
 fftw3-devel \
 xorg-x11-server-Xvfb netpbm-progs python-requests \
 mlocate nano elinks file which telnet \
 python-configparser h5py git pyflakes \
 numactl && yum -y clean all

## Appion specific installs
#RUN yum -y upgrade && yum -y install mozilla-adblockplus firefox dbus && yum -y clean all
RUN yum install -y python2-pip
RUN dbus-uuidgen > /var/lib/dbus/machine-id
RUN pip install --upgrade pip
RUN pip install joblib pyfftw3 fs==0.5.4 scikit-learn==0.18.2
RUN python -c 'from sklearn import svm' # test for function

#VOLUME /emg/sw
RUN mkdir -p /emg/data  && echo 'mkdir /emg/data'
RUN mkdir -p /emg/sw && echo 'mkdir /emg/sw'
RUN chmod 777 -R /emg  && echo 'chmod 777'

### Myami setup
RUN git clone -b myami-3.3 https://github.com/leginon-org/leginon.git /emg/sw/myami/

#COPY sinedon.cfg /etc/myami/sinedon.cfg
#COPY leginon.cfg /etc/myami/leginon.cfg
#COPY instruments.cfg /etc/myami/instruments.cfg
#COPY appion.cfg /etc/myami/appion.cfg
RUN ln -sv /emg/sw/myami/appion/appionlib /usr/lib64/python2.7/site-packages/
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

### see procnode.build.sh to obtain files

RUN mkdir /etc/fftw
RUN python /emg/sw/myami/pyami/fft/fftwsetup.py 2 4096 4096 && mv -v ~/fftw3-wisdom-* /etc/fftw/wisdom
ADD TGZ/findem-docker-centos7.tgz /emg/sw/
#COPY /emg/sw/findem-docker-centos7/findem64.exe /emg/sw/myami/appion/bin/
WORKDIR /emg/sw/myami/

### Xmipp
ADD TGZ/xmipp_centos6_docker.tgz /emg/sw

### EMAN 1
ADD TGZ/eman-linux-x86_64-cluster-1.9.tar.gz /emg/sw
RUN mv -v /emg/sw/EMAN /emg/sw/eman1
RUN ln -sv /emg/sw/eman1/lib/libpyEM.so.ucs4.py2.6 /emg/sw/eman1/lib/libpyEM.so #FIX ME

### EMAN 2
ADD TGZ/eman2_centos6_docker.tgz /emg/sw/

### RELION
ADD TGZ/relion-1.4.tgz /emg/sw/

### SPIDER
ADD TGZ/spidersmall.13.00.tgz /emg/sw

### Grigorieff lab
RUN mkdir -p /emg/sw/grigorieff/bin
ADD TGZ/ctf_140609.tar.gz /emg/sw/grigorieff/
ADD TGZ/ctffind-4.1.5.tgz /emg/sw/grigorieff/
RUN mv -v /emg/sw/grigorieff/ctf /emg/sw/grigorieff/ctffind3
RUN chmod 777 /emg/sw/grigorieff/ctffind3/ctffind3_mp.exe 
RUN chmod 777 /emg/sw/grigorieff/ctffind4/ctffind-4.1.5
RUN ln -sv /emg/sw/grigorieff/ctffind4/ctffind-4.1.5 /emg/sw/grigorieff/bin/ctffind4
RUN ln -sv /emg/sw/grigorieff/ctffind3/ctffind3_mp.exe /emg/sw/grigorieff/bin/ctffind64.exe

### Environmental variables
COPY procnode.bashrc /etc/bashrc

### just double check that this directory is missing
RUN rm -fvr /emg/data/appion

RUN updatedb
