FROM centos:centos6.7

RUN yum -y update
RUN yum -y install wget
RUN wget 'http://mirrors.cat.pdx.edu/epel/6/i386/epel-release-6-8.noarch.rpm'
RUN yum -y --nogpgcheck localinstall epel-release-6-8.noarch.rpm

RUN yum clean all

RUN yum -y install \
  nano \
  telnet \
  php-gd \
  gcc \
  phpMyAdmin \
  libssh2-devel \
  php-pecl-ssh2 \
  mod_ssl \
  httpd \
  php-mysql \
  php-devel \
  php \
  fftw3-devel \
  svn \
  python-imaging \
  python-devel \
  mod_python \
  scipy

RUN yum install -y python-pip
RUN pip install fs
RUN pip install PyFFTW3

RUN sed -i -e 's/short_open_tag = Off/short_open_tag = On/g' /etc/php.ini

RUN sed -i -e 's/HostnameLookups Off/HostnameLookups On/g' /etc/httpd/conf/httpd.conf
RUN sed -i -e 's/DirectoryIndex index.html index.html.var/DirectoryIndex index.html index.html.var index.php/g' /etc/httpd/conf/httpd.conf

RUN sed -i -e 's/UseCanonicalName Off/UseCanonicalName On/g' /etc/httpd/conf/httpd.conf

RUN sed -i -e 's/#ServerName www.example.com:80/ServerName krios.rcc.fsu.edu/g' /etc/httpd/conf/httpd.conf

RUN yum -y install \
   php-pecl-ssh2 \
   php-devel \
   libssh2-devel

RUN yum -y install git

RUN git clone -b trunk https://github.com/leginon-org/leginon.git /var/www/html/

RUN chown -R apache.apache /var/www/html/myamiweb/

RUN echo "<?php phpinfo(); ?>" > /var/www/html/info.php
RUN chmod 755 /var/www/html/info.php



EXPOSE 80

CMD /usr/sbin/apachectl -D FOREGROUND
