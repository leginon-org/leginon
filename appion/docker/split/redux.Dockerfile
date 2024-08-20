FROM centos:7

RUN yum -y update && yum -y --nogpgcheck install epel-release

RUN yum -y update && yum -y install \
  wget \
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

RUN chmod +x /var/www/html/pysetup.sh
RUN cd /var/www/html && ./pysetup.sh install

RUN echo '#!/bin/bash' > /startRedux
RUN echo "/bin/cp -vf /var/www/html/redux/redux.cfg.template /usr/lib/python2.6/site-packages/redux/redux.cfg" >> /startRedux
RUN echo "sed -i -e 's/file: redux.log/file: \/var\/log\/redux.log/g' /usr/lib/python2.6/site-packages/redux/redux.cfg" >> /startRedux

RUN echo "sed -i -e 's/## redux config file//' /usr/lib/python2.6/site-packages/redux/redux.cfg" >> /startRedux
RUN echo "sed -i -e 's/\[server\]//g' /usr/lib/python2.6/site-packages/redux/redux.cfg" >> /startRedux
RUN echo "sed -i -e 's/host: localhost//g' /usr/lib/python2.6/site-packages/redux/redux.cfg" >> /startRedux

RUN echo "MYIP=\`ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'\` && export MYIP && echo -e \"[server]\nhost: \$MYIP\n\$(cat /usr/lib/python2.6/site-packages/redux/redux.cfg)\" > /usr/lib/python2.6/site-packages/redux/redux.cfg" >> /startRedux
RUN echo "/var/www/html/redux/bin/reduxd &> /var/log/redux_cmd.log" >> /startRedux
RUN chmod +x /startRedux


EXPOSE 55123

CMD ["/bin/sh","/startRedux"]
