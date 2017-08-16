FROM centos:centos6.7

RUN yum -y --nogpgcheck install epel-release
RUN yum -y update

RUN yum -y --nogpgcheck install \
  nano \
  telnet \
  gcc \
  phpMyAdmin \
  libssh2-devel \
  php-mysql \
  php-devel \
  php \
  svn \
  python-devel \
  mod_python \
  mysql \
  mysql-server \
  git

RUN /bin/cp -vf /usr/share/mysql/my-huge.cnf /etc/my.cnf

# These were not in the config file by default
#query_cache_type = 1 / query_cache_size = 100M / default-storage-engine=MyISAM

# added time zone... Set to US Eastern
RUN sed -i -e "s/query_cache_size = 32M/default-time-zone = 'America\/New_York'\nquery_cache_size = 100M\nquery_cache_type = 1\nquery_cache_size = 100M\ndefault-storage-engine=MyISAM/g" /etc/my.cnf

# This is only needed for a blank database
RUN if [ -f /var/lib/mysql/mysql* ] ; mysql_install_db --user=mysql --basedir=/usr/ --ldata=/var/lib/mysql/; fi  



EXPOSE 3306

CMD /usr/bin/mysqld_safe
