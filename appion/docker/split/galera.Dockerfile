FROM debian:9
MAINTAINER Neil Voss <vossman77@gmail.com>
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update && apt-get -y install apt-utils

RUN apt-get update \
 && apt-get install -y \
  mariadb-server \
  mariadb-client \
  galera-3 \
  rsync \
  wget \
  procps \
  nano

COPY my-galera.cnf /etc/mysql/my.cnf
COPY docker-innodb.sql /docker-innodb.sql 

#MySQL client connections
EXPOSE 3306
#State Snapshot Transfer
EXPOSE 4444
#replication traffic
EXPOSE 4567
#Incremental State Transfer
EXPOSE 4568


ENTRYPOINT ["/usr/bin/mysqld_safe"]
